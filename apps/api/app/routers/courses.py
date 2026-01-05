"""
Course-related API routes.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, func, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Course
from app.schemas import CourseListResponse, CourseResponse, PrerequisiteNode

router = APIRouter(prefix="/courses", tags=["courses"])


def parse_prerequisite_formula(formula: Optional[dict]) -> Optional[PrerequisiteNode]:
    """
    Parse prerequisite formula into PrerequisiteNode.

    Args:
        formula: Prerequisite formula as dict

    Returns:
        PrerequisiteNode or None
    """
    if not formula:
        return None

    try:
        return PrerequisiteNode(**formula)
    except Exception:
        # If parsing fails, return None
        return None


@router.get("", response_model=CourseListResponse)
async def list_courses(
    subject: Optional[str] = Query(None, description="Filter by subject (e.g., CMPUT)"),
    level: Optional[str] = Query(None, description="Filter by level (e.g., 100, 200)"),
    term: Optional[str] = Query(None, description="Filter by term offered (e.g., Fall)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> CourseListResponse:
    """
    Get list of courses with optional filtering.

    - **subject**: Filter by subject code (CMPUT, MATH, etc.)
    - **level**: Filter by course level (100, 200, 300, 400, 500)
    - **term**: Filter by term when typically offered (Fall, Winter, Spring, Summer)
    - **page**: Page number for pagination
    - **page_size**: Number of items per page
    """
    # Build query with filters
    query = select(Course)

    if subject:
        query = query.where(Course.subject == subject.upper())

    if level:
        # Filter by level (cast enum to text for comparison)
        query = query.where(cast(Course.level, String) == level)

    if term:
        # Filter by term in typically_offered array
        # Use array_position to check if the term exists in the array (returns NULL if not found)
        query = query.where(func.array_position(Course.typically_offered, term.capitalize()).isnot(None))

    # Get total count
    count_query = select(Course.id).select_from(Course)
    if subject:
        count_query = count_query.where(Course.subject == subject.upper())
    if level:
        count_query = count_query.where(cast(Course.level, String) == level)
    if term:
        # Use array_position to check if the term exists in the array
        count_query = count_query.where(func.array_position(Course.typically_offered, term.capitalize()).isnot(None))

    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query.order_by(Course.code))
    courses = result.scalars().all()

    # Convert to response models
    course_responses = []
    for course in courses:
        course_dict = {
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "credits": course.credits,
            "description": course.description,
            "prerequisite_formula": course.prerequisite_formula,
            "prerequisites_parsed": parse_prerequisite_formula(course.prerequisite_formula),
            "typically_offered": course.typically_offered or [],
            "level": course.level,
            "subject": course.subject,
            "created_at": course.created_at,
            "updated_at": course.updated_at,
        }
        course_responses.append(CourseResponse(**course_dict))

    return CourseListResponse(
        courses=course_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{code}", response_model=CourseResponse)
async def get_course(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> CourseResponse:
    """
    Get detailed information about a specific course.

    - **code**: Course code (e.g., CMPUT 174)

    Returns course details including parsed prerequisite tree.
    """
    # Normalize course code (uppercase)
    code = code.upper()

    # Query for the course
    query = select(Course).where(Course.code == code)
    result = await db.execute(query)
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail=f"Course {code} not found")

    # Convert to response model
    course_dict = {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "credits": course.credits,
        "description": course.description,
        "prerequisite_formula": course.prerequisite_formula,
        "prerequisites_parsed": parse_prerequisite_formula(course.prerequisite_formula),
        "typically_offered": course.typically_offered or [],
        "level": course.level,
        "subject": course.subject,
        "created_at": course.created_at,
        "updated_at": course.updated_at,
    }

    return CourseResponse(**course_dict)
