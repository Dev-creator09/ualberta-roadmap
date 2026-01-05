"""
Pydantic schemas for service layer responses.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class PrerequisiteCheckResult(BaseModel):
    """Result of prerequisite validation for a course."""

    is_valid: bool = Field(
        ..., description="Whether all prerequisites are satisfied"
    )
    missing_courses: list[str] = Field(
        default_factory=list,
        description="List of prerequisite courses that are not completed",
    )
    satisfied_prerequisites: list[str] = Field(
        default_factory=list, description="List of prerequisite courses that are completed"
    )
    formula_description: Optional[str] = Field(
        None, description="Human-readable description of prerequisite requirements"
    )


class PrerequisiteNode(BaseModel):
    """Node in a prerequisite tree for visualization."""

    course_code: str = Field(..., description="Course code (e.g., 'CMPUT 204')")
    title: str = Field(..., description="Course title")
    depth: int = Field(..., description="Depth in prerequisite tree (0 = root)")
    prerequisites: list["PrerequisiteNode"] = Field(
        default_factory=list, description="Direct prerequisites of this course"
    )
    formula: Optional[dict[str, Any]] = Field(
        None, description="Raw prerequisite formula from database"
    )


class RequirementProgress(BaseModel):
    """Progress tracking for a single program requirement."""

    requirement_id: str = Field(..., description="Unique requirement ID")
    requirement_name: str = Field(..., description="Name of the requirement")
    requirement_type: str = Field(
        ..., description="Type: REQUIRED, CHOICE, LEVEL_REQUIREMENT, ELECTIVE"
    )
    required_count: Optional[int] = Field(
        None, description="Number of courses/credits required"
    )
    completed_count: int = Field(
        ..., description="Number of courses/credits completed"
    )
    is_satisfied: bool = Field(..., description="Whether requirement is fully satisfied")
    completed_courses: list[str] = Field(
        default_factory=list, description="Courses that satisfy this requirement"
    )
    remaining_courses: list[str] = Field(
        default_factory=list,
        description="Available courses that could satisfy this requirement",
    )
    progress_percentage: float = Field(
        ..., description="Progress as percentage (0-100)"
    )


class AvailableCourse(BaseModel):
    """Course available for a student to take next."""

    course_code: str = Field(..., description="Course code")
    title: str = Field(..., description="Course title")
    credits: int = Field(..., description="Course credits")
    level: str = Field(..., description="Course level (100, 200, 300, 400, 500)")
    prerequisites_met: bool = Field(
        ..., description="Whether all prerequisites are satisfied"
    )
    satisfies_requirements: list[str] = Field(
        default_factory=list,
        description="List of requirement IDs this course would satisfy",
    )
    priority_score: float = Field(
        ...,
        description="Priority score for recommendation (higher = more important)",
    )
    typically_offered: list[str] = Field(
        default_factory=list, description="Terms when course is typically offered"
    )


class RequirementValidationResult(BaseModel):
    """Complete validation result for a program's requirements."""

    program_code: str = Field(..., description="Program code")
    program_name: str = Field(..., description="Program name")
    total_credits_required: int = Field(..., description="Total credits needed")
    total_credits_completed: int = Field(..., description="Total credits completed")
    requirements: list[RequirementProgress] = Field(
        ..., description="Progress for each requirement"
    )
    overall_progress: float = Field(
        ..., description="Overall program completion percentage (0-100)"
    )
    is_complete: bool = Field(
        ..., description="Whether all requirements are satisfied"
    )


class SpecialRulesResult(BaseModel):
    """Result of applying special program rules."""

    excluded_courses: list[str] = Field(
        default_factory=list,
        description="Courses excluded due to special rules (e.g., 'CMPUT 275 excludes CMPUT 201')",
    )
    warnings: list[str] = Field(
        default_factory=list, description="Warnings about course conflicts or issues"
    )
    substitutions_needed: list[dict[str, str]] = Field(
        default_factory=list,
        description="Required substitutions (e.g., {'from': 'CMPUT 115', 'to': 'CMPUT 174'})",
    )
    additional_requirements: list[str] = Field(
        default_factory=list,
        description="Additional requirements imposed by special rules",
    )
