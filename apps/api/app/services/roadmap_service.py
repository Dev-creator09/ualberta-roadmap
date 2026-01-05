"""
AI-powered roadmap generation service.

This service uses OpenAI's GPT-4 to generate personalized semester-by-semester
academic roadmaps based on program requirements, prerequisites, and student preferences.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional

import openai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import Course, Program, Requirement
from app.schemas.roadmap import (
    CourseInSemester,
    RequirementProgress,
    RoadmapRequest,
    RoadmapResponse,
    SemesterPlan,
)
from app.services.prerequisite_service import check_prerequisites, get_prerequisite_tree
from app.services.requirement_service import (
    get_next_available_courses,
    validate_requirements,
)

logger = logging.getLogger(__name__)

# In-memory cache for roadmap generation (can be upgraded to Redis later)
_roadmap_cache: dict[str, tuple[RoadmapResponse, datetime]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


class RoadmapGenerationError(Exception):
    """Raised when roadmap generation fails."""

    pass


def _get_cache_key(request: RoadmapRequest) -> str:
    """Generate a cache key from the request parameters."""
    cache_data = {
        "program_code": request.program_code,
        "starting_year": request.starting_year,
        "starting_term": request.starting_term,
        "completed_courses": sorted(request.completed_courses),
        "preferences": request.preferences,
        "credit_load_preference": request.credit_load_preference,
        "max_years": request.max_years,
    }
    cache_str = json.dumps(cache_data, sort_keys=True)
    return hashlib.sha256(cache_str.encode()).hexdigest()


def _get_cached_roadmap(cache_key: str) -> Optional[RoadmapResponse]:
    """Retrieve a cached roadmap if it exists and is not expired."""
    if cache_key in _roadmap_cache:
        roadmap, cached_at = _roadmap_cache[cache_key]
        if datetime.utcnow() - cached_at < timedelta(seconds=CACHE_TTL_SECONDS):
            logger.info(f"Cache hit for roadmap: {cache_key}")
            return roadmap
        else:
            # Expired, remove from cache
            del _roadmap_cache[cache_key]
            logger.info(f"Cache expired for roadmap: {cache_key}")
    return None


def _cache_roadmap(cache_key: str, roadmap: RoadmapResponse) -> None:
    """Cache a generated roadmap."""
    _roadmap_cache[cache_key] = (roadmap, datetime.utcnow())
    logger.info(f"Cached roadmap: {cache_key}")


async def _load_program_data(
    program_code: str, db: AsyncSession
) -> tuple[Program, list[Requirement]]:
    """Load program and its requirements from the database."""
    # Load program with requirements
    result = await db.execute(
        select(Program)
        .options(selectinload(Program.program_requirements))
        .where(Program.code == program_code)
    )
    program = result.scalar_one_or_none()

    if not program:
        raise ValueError(f"Program '{program_code}' not found")

    # Get requirements sorted by order
    requirements = sorted(program.program_requirements, key=lambda r: r.order_index)

    return program, requirements


async def _get_available_courses_map(
    completed_courses: list[str], db: AsyncSession
) -> dict[str, Course]:
    """Get all available courses as a map for quick lookup."""
    result = await db.execute(select(Course))
    all_courses = result.scalars().all()

    courses_map = {course.code: course for course in all_courses}
    return courses_map


def _format_requirements_for_prompt(
    requirements: list[Requirement],
    completed_courses: list[str],
    courses_map: dict[str, Course],
) -> str:
    """Format requirements for the LLM prompt."""
    lines = []

    for req in requirements:
        req_type = req.requirement_type
        name = req.name

        # Calculate current progress
        completed_set = set(c.upper() for c in completed_courses)
        courses_in_req = [c.upper() for c in req.courses]
        completed_in_req = [c for c in courses_in_req if c in completed_set]

        # Calculate credits
        credits_completed = sum(
            courses_map.get(code, Course(credits=3)).credits for code in completed_in_req
        )
        credits_needed = req.credits_needed or 0

        if req_type == "REQUIRED":
            if len(completed_in_req) == len(courses_in_req):
                status = "✓ SATISFIED"
            else:
                remaining = [c for c in courses_in_req if c not in completed_set]
                status = f"○ NOT SATISFIED (need: {', '.join(remaining)})"
            lines.append(f"- {name} (REQUIRED, {credits_needed} credits): {status}")

        elif req_type == "CHOICE":
            choose_count = req.choose_count or 1
            if len(completed_in_req) >= choose_count:
                status = "✓ SATISFIED"
            else:
                status = f"○ NOT SATISFIED (need {choose_count - len(completed_in_req)} more from {len(courses_in_req)} options)"
            lines.append(
                f"- {name} (CHOICE, need {choose_count} from {len(courses_in_req)} options, {credits_needed} credits): {status}"
            )

        elif req_type == "LEVEL_REQUIREMENT":
            if credits_completed >= credits_needed:
                status = "✓ SATISFIED"
            else:
                status = f"{credits_completed}/{credits_needed} completed"
            lines.append(f"- {name} (LEVEL_REQUIREMENT, {credits_needed} credits): {status}")

        elif req_type == "ELECTIVE":
            if credits_completed >= credits_needed:
                status = "✓ SATISFIED"
            else:
                status = f"{credits_completed}/{credits_needed} completed"
            lines.append(f"- {name} (ELECTIVE, {credits_needed} credits): {status}")

    return "\n".join(lines)


def _format_available_courses_for_prompt(
    available_courses: list[Any], courses_map: dict[str, Course]
) -> str:
    """Format available courses for the LLM prompt, grouped by level."""
    courses_by_level: dict[str, list[Any]] = {}

    for course_info in available_courses:
        code = course_info.course_code
        course = courses_map.get(code)
        if course:
            level = course.level
            if level not in courses_by_level:
                courses_by_level[level] = []
            courses_by_level[level].append(course_info)

    lines = []
    for level in sorted(courses_by_level.keys()):
        lines.append(f"\n{level}-level courses:")
        for course_info in courses_by_level[level]:
            code = course_info.course_code
            course = courses_map.get(code)
            if course:
                terms = ", ".join(course.typically_offered) if course.typically_offered else "Any term"
                reqs = ", ".join(course_info.satisfies_requirements) if course_info.satisfies_requirements else "None"
                lines.append(
                    f"  - {code}: {course.title} ({course.credits} cr, typically: {terms}, satisfies: {reqs})"
                )

    return "\n".join(lines)


def _build_llm_prompt(
    program: Program,
    requirements: list[Requirement],
    request: RoadmapRequest,
    completed_courses: list[str],
    available_courses: list[Any],
    courses_map: dict[str, Course],
) -> str:
    """Build the comprehensive LLM prompt for roadmap generation."""
    completed_count = sum(
        courses_map.get(code.upper(), Course(credits=3)).credits for code in completed_courses
    )

    # Calculate credit load based on preference
    credit_load_map = {"LIGHT": 12, "STANDARD": 15, "HEAVY": 18}
    target_credits = credit_load_map.get(request.credit_load_preference, 15)

    requirements_text = _format_requirements_for_prompt(requirements, completed_courses, courses_map)
    available_courses_text = _format_available_courses_for_prompt(available_courses, courses_map)

    # Format completed courses
    completed_text = ""
    if completed_courses:
        completed_lines = []
        for code in completed_courses:
            course = courses_map.get(code.upper())
            if course:
                completed_lines.append(f"  - {code}: {course.title} ({course.credits} cr)")
            else:
                completed_lines.append(f"  - {code}: Unknown course (3 cr)")
        completed_text = "\n".join(completed_lines)
    else:
        completed_text = "  None"

    # Format preferences
    preferences_text = json.dumps(request.preferences, indent=2) if request.preferences else "None specified"

    # Format special rules
    special_rules_text = json.dumps(program.special_rules, indent=2) if program.special_rules else "None"

    prompt = f"""You are a UAlberta Computing Science academic advisor helping a student plan their degree.

STUDENT PROFILE:
- Program: {program.name} ({program.code})
- Core CS requirements: {program.total_credits} credits
- Starting: {request.starting_term} {request.starting_year}
- Completed: {len(completed_courses)} courses ({completed_count} credits)
- Interests: {preferences_text}

COMPLETED COURSES:
{completed_text}

CORE DEGREE REQUIREMENTS (CS-specific, {program.total_credits} credits total):
{requirements_text}

AVAILABLE CS COURSES (prerequisites met):
{available_courses_text}

PLANNING CONSTRAINTS:
- Credit load: {request.credit_load_preference} (~{target_credits} credits/semester preferred)
- Time frame: {request.max_years} years
- Special program rules: {special_rules_text}

IMPORTANT PLANNING PHILOSOPHY:
This is NOT just a degree completion tool - it's a course recommendation system. Your goal is to help the student:
1. Build a well-rounded education with CS, math, and breadth courses
2. Explore their interests (especially: {preferences_text})
3. Balance workload across semesters realistically
4. Progress through prerequisites naturally
5. Have flexibility for electives and personal interests

CRITICAL RULES:
1. **Realistic Prerequisites**: Don't schedule CMPUT 175 and CMPUT 201 in the same semester - 175 is a prerequisite for 201!
2. **Breadth Requirements**: A typical UAlberta degree requires ~120 credits total. Since CS core is {program.total_credits} credits, include:
   - Non-CS electives (~15-20 credits): humanities, sciences, business, arts
   - Additional math/stats beyond core requirements
   - Open electives for exploring interests
3. **Workload Balance**: Mix difficulty levels in each semester:
   - Don't put all 400-level courses together
   - Balance foundational (100-200) with advanced (300-400) courses
   - Include lighter breadth courses with heavy CS courses
4. **Course Sequencing**:
   - Year 1: Focus on 100-200 level foundations (CMPUT 174, 175, MATH courses)
   - Year 2: 200-level CS courses + breadth requirements
   - Year 3-4: 300-400 level specialization courses aligned with interests
5. **Interest Alignment**: If student interested in "{request.preferences.get('specialization', 'general CS')}", recommend relevant electives
6. **Semester Load**: Aim for {target_credits} credits but NEVER exceed 18 credits per semester

SAMPLE REALISTIC SEMESTER (Year 1, Fall):
{{
  "courses": [
    {{"code": "CMPUT 175", "title": "Intro to Foundations II", "credits": 3}},
    {{"code": "MATH 125", "title": "Linear Algebra I", "credits": 3}},
    {{"code": "ENGL 103", "title": "English Composition", "credits": 3}},
    {{"code": "PHYS 124", "title": "Physics for Engineers", "credits": 3}},
    {{"code": "MUSIC 100", "title": "Music Appreciation", "credits": 3}}
  ],
  "total_credits": 15
}}

Return a {request.max_years * 2}-semester plan as JSON:
{{
  "semesters": [
    {{
      "number": 1,
      "term": "FALL",
      "year": 1,
      "courses": [...],
      "total_credits": 15
    }}
  ],
  "warnings": ["Include warnings about course availability, workload, etc."],
  "notes": "Brief explanation of the plan's structure and how it aligns with student interests"
}}
"""

    return prompt


async def _call_openai_api(prompt: str, max_retries: int = 3) -> dict[str, Any]:
    """Call OpenAI API with exponential backoff retry logic."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise RoadmapGenerationError("OPENAI_API_KEY environment variable not set")

    client = openai.AsyncOpenAI(api_key=api_key)

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",  # or gpt-4-turbo-preview
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert academic advisor. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise RoadmapGenerationError("Empty response from OpenAI API")

            result = json.loads(content)
            return result

        except openai.RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Rate limit hit, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                raise RoadmapGenerationError(f"OpenAI rate limit exceeded: {e}")

        except openai.APIError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"API error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                raise RoadmapGenerationError(f"OpenAI API error: {e}")

        except json.JSONDecodeError as e:
            raise RoadmapGenerationError(f"Failed to parse OpenAI response as JSON: {e}")

    raise RoadmapGenerationError("Failed to get valid response from OpenAI after retries")


def optimize_course_distribution(semesters: list[SemesterPlan], courses_map: dict[str, Course]) -> list[SemesterPlan]:
    """
    Optimize course distribution across semesters.

    - Balance course difficulty across semesters
    - Front-load foundational courses (100-200 level)
    - Save easier electives for final semesters
    - Avoid clustering all hard courses in one term
    """
    # For now, this is a simple implementation
    # In a more advanced version, we could:
    # 1. Assign difficulty scores to courses
    # 2. Calculate semester difficulty balance
    # 3. Swap courses between semesters to balance load
    # 4. Ensure prerequisites are still met after swaps

    # Current implementation: just validate and return as-is
    # The LLM should handle most of the balancing

    for semester in semesters:
        # Ensure courses are sorted by level (foundational first)
        semester.courses.sort(key=lambda c: (
            courses_map.get(c.code.upper(), Course(level="999")).level,
            c.code
        ))

    return semesters


async def _validate_generated_plan(
    program: Program,
    semesters: list[SemesterPlan],
    completed_courses: list[str],
    courses_map: dict[str, Course],
    db: AsyncSession,
) -> tuple[bool, list[str], list[RequirementProgress]]:
    """
    Validate the generated roadmap plan.

    Returns:
        - is_valid: Whether all requirements are satisfied
        - errors: List of validation errors
        - requirement_progress: Progress toward each requirement
    """
    errors = []

    # Collect all courses in the plan
    all_planned_courses = completed_courses.copy()
    for semester in semesters:
        for course in semester.courses:
            all_planned_courses.append(course.code)

    # Validate requirements
    try:
        validation_result = await validate_requirements(program.code, all_planned_courses, db)

        # Check if all requirements are satisfied
        unsatisfied = [
            req for req in validation_result.requirements
            if not req.is_satisfied
        ]

        if unsatisfied:
            for req in unsatisfied:
                errors.append(
                    f"Requirement '{req.requirement_name}' not satisfied: {req.progress_percentage:.0f}% complete"
                )

        # Convert to RequirementProgress format
        requirement_progress = []
        for req in validation_result.requirements:
            # Calculate credits: use required_count as credits_needed
            credits_needed = req.required_count if req.required_count else 0
            credits_completed = req.completed_count

            # For credits_planned, count all courses in the planned roadmap that satisfy this requirement
            credits_planned = credits_needed if req.is_satisfied else credits_completed

            requirement_progress.append(
                RequirementProgress(
                    requirement_id=req.requirement_id,
                    requirement_name=req.requirement_name,
                    requirement_type=req.requirement_type,
                    credits_needed=credits_needed,
                    credits_completed=credits_completed,
                    credits_planned=credits_planned,
                    is_satisfied=req.is_satisfied,
                    courses_used=req.completed_courses,
                    remaining=None if req.is_satisfied else f"{len(req.remaining_courses)} more courses needed",
                )
            )

        is_valid = len(errors) == 0
        return is_valid, errors, requirement_progress

    except Exception as e:
        logger.error(f"Validation error: {e}")
        errors.append(f"Validation failed: {str(e)}")
        return False, errors, []


async def generate_roadmap(
    request: RoadmapRequest,
    db: AsyncSession,
) -> RoadmapResponse:
    """
    Generate an AI-powered semester-by-semester roadmap.

    This function:
    1. Loads program and requirements from database
    2. Validates completed courses against requirements
    3. Gets available courses (prerequisites met)
    4. Builds constraint-aware prompt for GPT-4
    5. Calls OpenAI API with structured JSON output
    6. Parses and validates the generated plan
    7. Calculates requirement progress
    8. Returns RoadmapResponse

    The function includes caching, retry logic, and validation.
    """
    # Check cache first
    cache_key = _get_cache_key(request)
    cached = _get_cached_roadmap(cache_key)
    if cached:
        return cached

    try:
        # Load program data
        program, requirements = await _load_program_data(request.program_code, db)
        logger.info(f"Loaded program: {program.name} with {len(requirements)} requirements")

        # Get all courses for mapping
        courses_map = await _get_available_courses_map(request.completed_courses, db)

        # Get available courses (prerequisites met)
        available_courses = await get_next_available_courses(
            request.program_code,
            request.completed_courses,
            db,
        )
        logger.info(f"Found {len(available_courses)} available courses with prerequisites met")

        # Build LLM prompt
        prompt = _build_llm_prompt(
            program,
            requirements,
            request,
            request.completed_courses,
            available_courses,
            courses_map,
        )

        # Call OpenAI API with retry logic
        max_generation_attempts = 2
        generated_plan = None
        validation_errors = []

        for attempt in range(max_generation_attempts):
            logger.info(f"Generating roadmap (attempt {attempt + 1}/{max_generation_attempts})...")

            # Add validation errors to prompt if this is a retry
            current_prompt = prompt
            if attempt > 0 and validation_errors:
                current_prompt += f"\n\nPREVIOUS ATTEMPT HAD ERRORS - PLEASE FIX:\n" + "\n".join(validation_errors)

            llm_response = await _call_openai_api(current_prompt)

            # Parse LLM response
            raw_semesters = llm_response.get("semesters", [])
            warnings = llm_response.get("warnings", [])
            notes = llm_response.get("notes", "")

            # Convert to Pydantic models
            semesters = []
            for sem_data in raw_semesters:
                courses = [
                    CourseInSemester(
                        code=c["code"],
                        title=c.get("title", ""),
                        credits=c.get("credits", 3),
                        satisfies_requirements=c.get("satisfies_requirements", []),
                        prerequisites_met=True,
                        warnings=[],
                    )
                    for c in sem_data.get("courses", [])
                ]

                semester = SemesterPlan(
                    number=sem_data["number"],
                    term=sem_data["term"],
                    year=sem_data["year"],
                    courses=courses,
                    total_credits=sem_data.get("total_credits", sum(c.credits for c in courses)),
                )
                semesters.append(semester)

            # Optimize course distribution
            semesters = optimize_course_distribution(semesters, courses_map)

            # Validate the generated plan
            is_valid, errors, requirement_progress = await _validate_generated_plan(
                program, semesters, request.completed_courses, courses_map, db
            )

            if is_valid:
                # Success! Build final response
                total_credits = sum(sem.total_credits for sem in semesters)

                # Calculate graduation term
                last_semester = semesters[-1] if semesters else None
                graduation_term = None
                if last_semester:
                    grad_year = request.starting_year + last_semester.year - 1
                    graduation_term = f"{last_semester.term.capitalize()} {grad_year}"

                if notes:
                    warnings.append(f"Plan notes: {notes}")

                response = RoadmapResponse(
                    program_code=program.code,
                    program_name=program.name,
                    semesters=semesters,
                    requirement_progress=requirement_progress,
                    total_credits=total_credits,
                    credits_needed=program.total_credits,
                    warnings=warnings,
                    graduation_term=graduation_term,
                    is_valid=True,
                )

                # Cache the successful result
                _cache_roadmap(cache_key, response)

                logger.info(f"Successfully generated roadmap for {program.code}")
                return response
            else:
                # Validation failed, prepare for retry
                validation_errors = errors
                logger.warning(f"Generated plan validation failed: {errors}")

                if attempt == max_generation_attempts - 1:
                    # Last attempt failed, return with errors
                    total_credits = sum(sem.total_credits for sem in semesters)

                    response = RoadmapResponse(
                        program_code=program.code,
                        program_name=program.name,
                        semesters=semesters,
                        requirement_progress=requirement_progress,
                        total_credits=total_credits,
                        credits_needed=program.total_credits,
                        warnings=warnings + errors,
                        graduation_term=None,
                        is_valid=False,
                    )

                    return response

        # Should not reach here, but just in case
        raise RoadmapGenerationError("Failed to generate valid roadmap")

    except ValueError as e:
        # Program not found or other validation error
        logger.error(f"Validation error: {e}")
        raise

    except RoadmapGenerationError as e:
        # OpenAI API or generation error
        logger.error(f"Generation error: {e}")
        raise

    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error during roadmap generation: {e}", exc_info=True)
        raise RoadmapGenerationError(f"Unexpected error: {str(e)}")
