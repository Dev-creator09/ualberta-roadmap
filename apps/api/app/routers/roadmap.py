"""
Roadmap-related API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import (
    CourseInSemester,
    RoadmapRequest,
    RoadmapResponse,
    RoadmapValidationRequest,
    RoadmapValidationResponse,
    RequirementCheckRequest,
    RequirementCheckResponse,
    RequirementProgress,
    SemesterPlan,
)
from app.services import generate_roadmap as generate_roadmap_service

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap(
    request: RoadmapRequest,
    db: AsyncSession = Depends(get_db),
) -> RoadmapResponse:
    """
    Generate a 4-year roadmap based on program requirements and student preferences.

    Uses AI (GPT-4) to create an optimized semester-by-semester course plan that:
    - Satisfies all program requirements
    - Respects prerequisites and course offerings
    - Balances course load across semesters
    - Considers student preferences

    - **program_code**: Program code (e.g., honors-cs)
    - **starting_year**: Year student starts (e.g., 2024)
    - **starting_term**: Starting term (FALL, WINTER, SPRING)
    - **completed_courses**: List of already completed courses
    - **preferences**: Student preferences (specialization, etc.)
    - **credit_load_preference**: LIGHT (12), STANDARD (15), or HEAVY (18)
    """
    try:
        roadmap = await generate_roadmap_service(request, db)
        return roadmap

    except ValueError as e:
        # Program not found or validation error
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        # OpenAI API error or other generation failure
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate roadmap: {str(e)}"
        )


@router.post("/validate", response_model=RoadmapValidationResponse)
async def validate_roadmap(
    request: RoadmapValidationRequest,
    db: AsyncSession = Depends(get_db),
) -> RoadmapValidationResponse:
    """
    Validate a proposed semester schedule.

    **Note:** This is a stub implementation.
    The actual validation logic will be implemented in a future update.

    - **program_code**: Program code
    - **semester_number**: Semester number (1-8)
    - **courses**: List of course codes to validate
    - **completed_courses**: Previously completed courses

    Returns validation results including errors and warnings.
    """
    # TODO: Implement actual validation logic
    # For now, return a simple validation response

    total_credits = len(request.courses) * 3  # Assume 3 credits per course

    warnings = []
    if total_credits > 18:
        warnings.append(f"Heavy course load ({total_credits} credits)")
    elif total_credits < 9:
        warnings.append(f"Light course load ({total_credits} credits)")

    return RoadmapValidationResponse(
        is_valid=True,
        errors=[],
        warnings=warnings,
        total_credits=total_credits,
        prerequisite_issues=[],
    )


@router.post("/requirements/check", response_model=RequirementCheckResponse)
async def check_requirements(
    request: RequirementCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> RequirementCheckResponse:
    """
    Check which requirements a given list of courses satisfies.

    **Note:** This is a stub implementation.
    The actual requirement checking logic will be implemented in a future update.

    - **program_code**: Program code
    - **courses**: List of course codes

    Returns requirement progress for all program requirements.
    """
    # TODO: Implement actual requirement checking logic
    # For now, return a simple mock response

    total_credits = len(request.courses) * 3  # Assume 3 credits per course

    mock_requirement = RequirementProgress(
        requirement_id="req_foundation",
        requirement_name="Foundation CMPUT",
        requirement_type="REQUIRED",
        credits_needed=6,
        credits_completed=total_credits if total_credits >= 6 else total_credits,
        credits_planned=total_credits,
        is_satisfied=total_credits >= 6,
        courses_used=request.courses[:2] if len(request.courses) >= 2 else request.courses,
        remaining=None if total_credits >= 6 else f"{6 - total_credits} more credits needed",
    )

    return RequirementCheckResponse(
        program_code=request.program_code,
        requirements=[mock_requirement],
        total_credits=total_credits,
        satisfied_count=1 if total_credits >= 6 else 0,
        partial_count=0 if total_credits >= 6 else 1,
    )
