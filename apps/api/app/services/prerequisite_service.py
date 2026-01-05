"""
Prerequisite validation and checking service.

This module handles all prerequisite-related logic including validation,
tree building, and formula evaluation.
"""

import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course
from app.schemas.services import PrerequisiteCheckResult, PrerequisiteNode

logger = logging.getLogger(__name__)


async def check_prerequisites(
    course_code: str,
    completed_courses: list[str],
    db: AsyncSession,
) -> PrerequisiteCheckResult:
    """
    Check if prerequisites are satisfied for a given course.

    Args:
        course_code: Course code to check prerequisites for (e.g., "CMPUT 204")
        completed_courses: List of course codes the student has completed
        db: Database session

    Returns:
        PrerequisiteCheckResult with validation status and missing/satisfied courses

    Raises:
        ValueError: If course not found in database
    """
    # Fetch the course from database
    result = await db.execute(select(Course).where(Course.code == course_code))
    course = result.scalar_one_or_none()

    if not course:
        raise ValueError(f"Course '{course_code}' not found")

    # If no prerequisite formula, all prerequisites are satisfied
    if not course.prerequisite_formula:
        return PrerequisiteCheckResult(
            is_valid=True,
            missing_courses=[],
            satisfied_prerequisites=[],
            formula_description="No prerequisites required",
        )

    # Convert completed courses to set for faster lookup
    completed_set = set(c.upper().strip() for c in completed_courses)

    # Validate the prerequisite formula
    is_valid, missing, satisfied = await _evaluate_formula(
        course.prerequisite_formula, completed_set, db
    )

    # Generate human-readable description
    description = _format_formula_description(course.prerequisite_formula)

    return PrerequisiteCheckResult(
        is_valid=is_valid,
        missing_courses=sorted(missing),
        satisfied_prerequisites=sorted(satisfied),
        formula_description=description,
    )


async def get_prerequisite_tree(
    course_code: str,
    db: AsyncSession,
    depth: int = 0,
    max_depth: int = 5,
    visited: Optional[set[str]] = None,
) -> PrerequisiteNode:
    """
    Recursively build prerequisite tree for visualization.

    Args:
        course_code: Course code to build tree for
        db: Database session
        depth: Current depth in tree (used internally)
        max_depth: Maximum depth to traverse (prevents infinite loops)
        visited: Set of visited courses (prevents circular dependencies)

    Returns:
        PrerequisiteNode representing the tree structure

    Raises:
        ValueError: If course not found
    """
    if visited is None:
        visited = set()

    # Prevent circular dependencies and excessive depth
    if depth >= max_depth or course_code in visited:
        # Return a simple node without further prerequisites
        result = await db.execute(
            select(Course.code, Course.title).where(Course.code == course_code)
        )
        row = result.one_or_none()
        if row:
            return PrerequisiteNode(
                course_code=row[0],
                title=row[1],
                depth=depth,
                prerequisites=[],
                formula=None,
            )
        raise ValueError(f"Course '{course_code}' not found")

    # Mark as visited
    visited.add(course_code)

    # Fetch course
    result = await db.execute(select(Course).where(Course.code == course_code))
    course = result.scalar_one_or_none()

    if not course:
        raise ValueError(f"Course '{course_code}' not found")

    # Build prerequisite nodes
    prerequisite_nodes = []
    if course.prerequisite_formula:
        prerequisite_codes = _extract_course_codes(course.prerequisite_formula)
        for prereq_code in prerequisite_codes:
            try:
                prereq_node = await get_prerequisite_tree(
                    prereq_code, db, depth + 1, max_depth, visited.copy()
                )
                prerequisite_nodes.append(prereq_node)
            except ValueError:
                # Skip courses that don't exist
                pass

    return PrerequisiteNode(
        course_code=course.code,
        title=course.title,
        depth=depth,
        prerequisites=prerequisite_nodes,
        formula=course.prerequisite_formula,
    )


async def validate_prerequisite_formula(
    formula: dict[str, Any],
    completed: set[str],
    db: AsyncSession,
) -> bool:
    """
    Validate a prerequisite formula against completed courses.

    Args:
        formula: Prerequisite formula (JSONB structure with type and conditions)
        completed: Set of completed course codes
        db: Database session

    Returns:
        True if formula is satisfied, False otherwise
    """
    is_valid, _, _ = await _evaluate_formula(formula, completed, db)
    return is_valid


# Private helper functions


async def _evaluate_formula(
    formula: dict[str, Any],
    completed: set[str],
    db: AsyncSession,
) -> tuple[bool, list[str], list[str]]:
    """
    Recursively evaluate prerequisite formula.

    Returns:
        Tuple of (is_valid, missing_courses, satisfied_courses)
    """
    if not formula:
        return True, [], []

    formula_type = formula.get("type", "").upper()

    if formula_type == "COURSE":
        # Single course requirement
        course_code = formula.get("code", "")

        # Handle nested formula (if code is a dict instead of string)
        if isinstance(course_code, dict):
            # Recursively evaluate the nested formula
            return await _evaluate_formula(course_code, completed, db)

        # Handle normal case (code is a string)
        if isinstance(course_code, str):
            if course_code.upper() in completed:
                return True, [], [course_code]
            else:
                return False, [course_code], []

        # Invalid formula structure
        logger.warning(f"Invalid course code in prerequisite formula: {course_code}")
        return False, [], []

    elif formula_type == "AND":
        # All conditions must be satisfied
        conditions = formula.get("conditions", [])
        all_missing = []
        all_satisfied = []
        is_valid = True

        for condition in conditions:
            valid, missing, satisfied = await _evaluate_formula(
                condition, completed, db
            )
            if not valid:
                is_valid = False
            all_missing.extend(missing)
            all_satisfied.extend(satisfied)

        return is_valid, all_missing, all_satisfied

    elif formula_type == "OR":
        # At least one condition must be satisfied
        conditions = formula.get("conditions", [])
        all_missing = []
        all_satisfied = []

        for condition in conditions:
            valid, missing, satisfied = await _evaluate_formula(
                condition, completed, db
            )
            if valid:
                # At least one branch is satisfied
                return True, [], satisfied
            all_missing.extend(missing)

        # None of the OR branches were satisfied
        return False, all_missing, []

    else:
        # Unknown formula type, assume not satisfied
        return False, [], []


def _extract_course_codes(formula: dict[str, Any]) -> list[str]:
    """
    Extract all course codes from a prerequisite formula.

    Args:
        formula: Prerequisite formula

    Returns:
        List of unique course codes
    """
    codes = []

    formula_type = formula.get("type", "").upper()

    if formula_type == "COURSE":
        code = formula.get("code")
        if code:
            codes.append(code)
    elif formula_type in ["AND", "OR"]:
        conditions = formula.get("conditions", [])
        for condition in conditions:
            codes.extend(_extract_course_codes(condition))

    return list(set(codes))  # Return unique codes


def _format_formula_description(formula: dict[str, Any]) -> str:
    """
    Generate human-readable description of prerequisite formula.

    Args:
        formula: Prerequisite formula

    Returns:
        Human-readable string
    """
    formula_type = formula.get("type", "").upper()

    if formula_type == "COURSE":
        return formula.get("code", "Unknown course")

    elif formula_type == "AND":
        conditions = formula.get("conditions", [])
        descriptions = [_format_formula_description(c) for c in conditions]
        if len(descriptions) == 1:
            return descriptions[0]
        return " AND ".join(f"({d})" if " OR " in d else d for d in descriptions)

    elif formula_type == "OR":
        conditions = formula.get("conditions", [])
        descriptions = [_format_formula_description(c) for c in conditions]
        if len(descriptions) == 1:
            return descriptions[0]
        return " OR ".join(f"({d})" if " AND " in d else d for d in descriptions)

    return "Unknown prerequisite formula"
