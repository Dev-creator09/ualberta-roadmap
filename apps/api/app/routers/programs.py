"""
Program-related API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Program, Requirement
from app.schemas import ProgramListResponse, ProgramResponse, RequirementResponse

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=ProgramListResponse)
async def list_programs(
    db: AsyncSession = Depends(get_db),
) -> ProgramListResponse:
    """
    Get list of all programs.

    Returns all available degree programs with basic information.
    """
    # Query for all programs with their requirements
    query = select(Program).options(selectinload(Program.program_requirements))
    result = await db.execute(query.order_by(Program.name))
    programs = result.scalars().all()

    # Convert to response models
    program_responses = []
    for program in programs:
        # Convert requirements
        requirements = [
            RequirementResponse(
                id=req.id,
                program_id=req.program_id,
                name=req.name,
                requirement_type=req.requirement_type,
                courses=req.courses or [],
                credits_needed=req.credits_needed,
                choose_count=req.choose_count,
                level_filter=req.level_filter or [],
                subject_filter=req.subject_filter,
                order_index=req.order_index,
            )
            for req in program.program_requirements
        ]

        program_dict = {
            "id": program.id,
            "code": program.code,
            "name": program.name,
            "total_credits": program.total_credits,
            "requirements": program.requirements,
            "special_rules": program.special_rules,
            "program_requirements": requirements,
            "created_at": program.created_at,
            "updated_at": program.updated_at,
        }
        program_responses.append(ProgramResponse(**program_dict))

    return ProgramListResponse(
        programs=program_responses,
        total=len(program_responses),
    )


@router.get("/{code}", response_model=ProgramResponse)
async def get_program(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    """
    Get detailed information about a specific program.

    - **code**: Program code (e.g., honors-cs, major-cs)

    Returns program details including all requirements.
    """
    # Normalize program code (lowercase with hyphens)
    code = code.lower()

    # Query for the program with requirements
    query = (
        select(Program)
        .options(selectinload(Program.program_requirements))
        .where(Program.code == code)
    )
    result = await db.execute(query)
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(status_code=404, detail=f"Program {code} not found")

    # Convert requirements to response models
    requirements = []
    for req in sorted(program.program_requirements, key=lambda x: x.order_index):
        requirements.append(
            RequirementResponse(
                id=req.id,
                program_id=req.program_id,
                name=req.name,
                requirement_type=req.requirement_type,
                courses=req.courses or [],
                credits_needed=req.credits_needed,
                choose_count=req.choose_count,
                level_filter=req.level_filter or [],
                subject_filter=req.subject_filter,
                order_index=req.order_index,
            )
        )

    # Convert to response model
    program_dict = {
        "id": program.id,
        "code": program.code,
        "name": program.name,
        "total_credits": program.total_credits,
        "requirements": program.requirements,
        "special_rules": program.special_rules,
        "program_requirements": requirements,
        "created_at": program.created_at,
        "updated_at": program.updated_at,
    }

    return ProgramResponse(**program_dict)
