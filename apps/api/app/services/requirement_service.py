"""
Requirement validation and progress tracking service.

This module handles program requirement validation, progress calculation,
and course recommendation logic.
"""

from typing import Any, Optional

from sqlalchemy import cast, select, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Course, Program, Requirement
from app.schemas.services import (
    AvailableCourse,
    RequirementProgress as RequirementProgressDetailed,
    RequirementValidationResult,
    SpecialRulesResult,
)
from app.services.prerequisite_service import check_prerequisites


async def validate_requirements(
    program_code: str,
    completed_courses: list[str],
    db: AsyncSession,
) -> RequirementValidationResult:
    """
    Validate all requirements for a program against completed courses.

    Args:
        program_code: Program code (e.g., "honors-cs-ai")
        completed_courses: List of completed course codes
        db: Database session

    Returns:
        RequirementValidationResult with detailed progress for each requirement

    Raises:
        ValueError: If program not found
    """
    # Fetch program with requirements
    result = await db.execute(
        select(Program)
        .where(Program.code == program_code)
        .options(selectinload(Program.program_requirements))
    )
    program = result.scalar_one_or_none()

    if not program:
        raise ValueError(f"Program '{program_code}' not found")

    # Normalize completed courses
    completed_set = set(c.upper().strip() for c in completed_courses)

    # Fetch all completed course details for credit calculation
    result = await db.execute(
        select(Course).where(Course.code.in_(list(completed_set)))
    )
    completed_course_objects = result.scalars().all()
    completed_courses_map = {c.code: c for c in completed_course_objects}

    # Calculate total credits completed
    total_credits_completed = sum(c.credits for c in completed_course_objects)

    # Validate each requirement
    requirements_progress = []
    satisfied_count = 0

    for req in program.program_requirements:
        progress = await _validate_single_requirement(
            req, completed_set, completed_courses_map, db
        )
        requirements_progress.append(progress)
        if progress.is_satisfied:
            satisfied_count += 1

    # Calculate overall progress
    total_requirements = len(program.program_requirements)
    overall_progress = (
        (satisfied_count / total_requirements * 100) if total_requirements > 0 else 0
    )

    is_complete = all(r.is_satisfied for r in requirements_progress)

    return RequirementValidationResult(
        program_code=program.code,
        program_name=program.name,
        total_credits_required=program.total_credits,
        total_credits_completed=total_credits_completed,
        requirements=requirements_progress,
        overall_progress=overall_progress,
        is_complete=is_complete,
    )


async def find_satisfiable_requirements(
    program_code: str,
    course_code: str,
    completed: list[str],
    db: AsyncSession,
) -> list[str]:
    """
    Find which requirements a course would satisfy.

    Args:
        program_code: Program code
        course_code: Course code to check
        completed: List of already completed courses
        db: Database session

    Returns:
        List of requirement IDs that this course would satisfy

    Raises:
        ValueError: If program or course not found
    """
    # Fetch program with requirements
    result = await db.execute(
        select(Program)
        .where(Program.code == program_code)
        .options(selectinload(Program.program_requirements))
    )
    program = result.scalar_one_or_none()

    if not program:
        raise ValueError(f"Program '{program_code}' not found")

    # Fetch the course
    result = await db.execute(select(Course).where(Course.code == course_code))
    course = result.scalar_one_or_none()

    if not course:
        raise ValueError(f"Course '{course_code}' not found")

    # Normalize completed courses
    completed_set = set(c.upper().strip() for c in completed)

    satisfiable = []

    for req in program.program_requirements:
        if _course_satisfies_requirement(course, req, completed_set):
            satisfiable.append(req.id)

    return satisfiable


async def get_next_available_courses(
    program_code: str,
    completed: list[str],
    db: AsyncSession,
) -> list[AvailableCourse]:
    """
    Get courses student can take next (prerequisites met, requirements not satisfied).

    Args:
        program_code: Program code
        completed: List of completed course codes
        db: Database session

    Returns:
        List of AvailableCourse objects sorted by priority

    Raises:
        ValueError: If program not found
    """
    # Fetch program with requirements
    result = await db.execute(
        select(Program)
        .where(Program.code == program_code)
        .options(selectinload(Program.program_requirements))
    )
    program = result.scalar_one_or_none()

    if not program:
        raise ValueError(f"Program '{program_code}' not found")

    # Normalize completed courses
    completed_set = set(c.upper().strip() for c in completed)

    # Get all courses that could satisfy requirements
    all_requirement_courses = set()
    for req in program.program_requirements:
        all_requirement_courses.update(req.courses or [])

    # Also include courses that match level requirements
    for req in program.program_requirements:
        if req.requirement_type == "LEVEL_REQUIREMENT":
            # Fetch courses matching level filter
            level_filters = req.level_filter or []
            subject_filter = req.subject_filter

            query = select(Course)
            if level_filters:
                # Cast level to string for comparison
                query = query.where(
                    cast(Course.level, String).in_(level_filters)
                )
            if subject_filter:
                query = query.where(Course.subject == subject_filter)

            result = await db.execute(query)
            level_courses = result.scalars().all()
            all_requirement_courses.update(c.code for c in level_courses)

    # Filter out already completed courses
    candidate_codes = all_requirement_courses - completed_set

    # Fetch candidate courses
    if not candidate_codes:
        return []

    result = await db.execute(
        select(Course).where(Course.code.in_(list(candidate_codes)))
    )
    candidate_courses = result.scalars().all()

    # Check prerequisites and build available course list
    available = []

    for course in candidate_courses:
        # Check prerequisites
        try:
            prereq_result = await check_prerequisites(
                course.code, list(completed), db
            )
            prerequisites_met = prereq_result.is_valid
        except ValueError:
            # Course might not exist or other error
            prerequisites_met = False

        # Find which requirements it satisfies
        satisfies = []
        priority_score = 0.0

        for req in program.program_requirements:
            if _course_satisfies_requirement(course, req, completed_set):
                satisfies.append(req.id)
                # Higher priority for required courses
                if req.requirement_type == "REQUIRED":
                    priority_score += 10.0
                elif req.requirement_type == "CHOICE":
                    priority_score += 5.0
                else:
                    priority_score += 2.0

        # Boost priority for courses with prerequisites met
        if prerequisites_met:
            priority_score += 3.0

        # Boost priority for lower-level courses (take foundational courses first)
        level_value = int(course.level) if course.level.isdigit() else 0
        priority_score += (600 - level_value) / 100  # Inverse priority

        available.append(
            AvailableCourse(
                course_code=course.code,
                title=course.title,
                credits=course.credits,
                level=course.level,
                prerequisites_met=prerequisites_met,
                satisfies_requirements=satisfies,
                priority_score=priority_score,
                typically_offered=course.typically_offered or [],
            )
        )

    # Sort by priority (descending)
    available.sort(key=lambda x: x.priority_score, reverse=True)

    return available


async def apply_special_rules(
    program: Program,
    courses: list[str],
) -> SpecialRulesResult:
    """
    Apply special program rules to course list.

    Args:
        program: Program object
        courses: List of course codes

    Returns:
        SpecialRulesResult with exclusions, warnings, and substitutions
    """
    excluded = []
    warnings = []
    substitutions = []
    additional = []

    # Parse special_rules JSONB
    special_rules = program.special_rules or {}

    # Handle exclusions
    exclusions = special_rules.get("exclusions", [])
    courses_set = set(c.upper().strip() for c in courses)

    for exclusion in exclusions:
        if isinstance(exclusion, dict):
            course_a = exclusion.get("course", "").upper()
            excludes = exclusion.get("excludes", [])

            if course_a in courses_set:
                for excluded_course in excludes:
                    excluded_course = excluded_course.upper()
                    if excluded_course in courses_set:
                        excluded.append(excluded_course)
                        warnings.append(
                            f"'{course_a}' excludes '{excluded_course}'. "
                            f"Cannot count both toward degree."
                        )

    # Handle substitutions
    subs = special_rules.get("substitutions", [])
    for sub in subs:
        if isinstance(sub, dict):
            from_course = sub.get("from", "")
            to_course = sub.get("to", "")
            if from_course.upper() in courses_set:
                substitutions.append({"from": from_course, "to": to_course})
                warnings.append(
                    f"'{from_course}' should be substituted with '{to_course}'"
                )

    # Handle additional requirements
    additional_reqs = special_rules.get("additional_requirements", [])
    for req in additional_reqs:
        if isinstance(req, str):
            additional.append(req)

    return SpecialRulesResult(
        excluded_courses=excluded,
        warnings=warnings,
        substitutions_needed=substitutions,
        additional_requirements=additional,
    )


# Private helper functions


async def _validate_single_requirement(
    req: Requirement,
    completed_set: set[str],
    completed_courses_map: dict[str, Course],
    db: AsyncSession,
) -> RequirementProgressDetailed:
    """
    Validate a single requirement against completed courses.

    Returns:
        RequirementProgressDetailed object
    """
    req_type = req.requirement_type

    if req_type == "REQUIRED":
        # All courses in list must be completed
        required_courses = set(c.upper() for c in (req.courses or []))
        completed_in_req = required_courses & completed_set
        remaining = required_courses - completed_set

        required_count = len(required_courses)
        completed_count = len(completed_in_req)
        is_satisfied = len(remaining) == 0

        progress = (
            (completed_count / required_count * 100) if required_count > 0 else 100
        )

        return RequirementProgressDetailed(
            requirement_id=req.id,
            requirement_name=req.name,
            requirement_type=req_type,
            required_count=required_count,
            completed_count=completed_count,
            is_satisfied=is_satisfied,
            completed_courses=sorted(list(completed_in_req)),
            remaining_courses=sorted(list(remaining)),
            progress_percentage=progress,
        )

    elif req_type == "CHOICE":
        # Need to complete choose_count courses from list
        choice_courses = set(c.upper() for c in (req.courses or []))
        completed_in_req = choice_courses & completed_set
        remaining = choice_courses - completed_set

        required_count = req.choose_count or 1
        completed_count = len(completed_in_req)
        is_satisfied = completed_count >= required_count

        progress = (
            min(completed_count / required_count * 100, 100) if required_count > 0 else 100
        )

        return RequirementProgressDetailed(
            requirement_id=req.id,
            requirement_name=req.name,
            requirement_type=req_type,
            required_count=required_count,
            completed_count=completed_count,
            is_satisfied=is_satisfied,
            completed_courses=sorted(list(completed_in_req)),
            remaining_courses=sorted(list(remaining)),
            progress_percentage=progress,
        )

    elif req_type == "LEVEL_REQUIREMENT":
        # Count credits from courses matching level and subject filters
        level_filters = req.level_filter or []
        subject_filter = req.subject_filter
        credits_needed = req.credits_needed or 0

        # Find matching completed courses
        matching_credits = 0
        matching_courses = []

        for code in completed_set:
            course = completed_courses_map.get(code)
            if course:
                # Check if course matches filters
                matches = True
                if level_filters and course.level not in level_filters:
                    matches = False
                if subject_filter and course.subject != subject_filter:
                    matches = False

                if matches:
                    matching_credits += course.credits
                    matching_courses.append(course.code)

        is_satisfied = matching_credits >= credits_needed
        progress = (
            min(matching_credits / credits_needed * 100, 100)
            if credits_needed > 0
            else 100
        )

        return RequirementProgressDetailed(
            requirement_id=req.id,
            requirement_name=req.name,
            requirement_type=req_type,
            required_count=credits_needed,
            completed_count=matching_credits,
            is_satisfied=is_satisfied,
            completed_courses=sorted(matching_courses),
            remaining_courses=[],  # Can't list all possible courses
            progress_percentage=progress,
        )

    else:  # ELECTIVE or unknown
        # Treat as satisfied if any courses completed
        completed_count = len(completed_set)
        is_satisfied = completed_count > 0

        return RequirementProgressDetailed(
            requirement_id=req.id,
            requirement_name=req.name,
            requirement_type=req_type,
            required_count=None,
            completed_count=completed_count,
            is_satisfied=is_satisfied,
            completed_courses=sorted(list(completed_set)),
            remaining_courses=[],
            progress_percentage=100 if is_satisfied else 0,
        )


def _course_satisfies_requirement(
    course: Course,
    req: Requirement,
    completed_set: set[str],
) -> bool:
    """
    Check if a course would satisfy a requirement.

    Args:
        course: Course object
        req: Requirement object
        completed_set: Set of already completed courses

    Returns:
        True if course satisfies the requirement
    """
    req_type = req.requirement_type

    if req_type == "REQUIRED":
        # Check if course is in required list and not already completed
        return (
            course.code.upper() in [c.upper() for c in (req.courses or [])]
            and course.code.upper() not in completed_set
        )

    elif req_type == "CHOICE":
        # Check if course is in choice list and not already completed
        return (
            course.code.upper() in [c.upper() for c in (req.courses or [])]
            and course.code.upper() not in completed_set
        )

    elif req_type == "LEVEL_REQUIREMENT":
        # Check if course matches level and subject filters
        level_filters = req.level_filter or []
        subject_filter = req.subject_filter

        matches = True
        if level_filters and course.level not in level_filters:
            matches = False
        if subject_filter and course.subject != subject_filter:
            matches = False

        return matches and course.code.upper() not in completed_set

    elif req_type == "ELECTIVE":
        # Any course not already completed satisfies elective
        return course.code.upper() not in completed_set

    return False
