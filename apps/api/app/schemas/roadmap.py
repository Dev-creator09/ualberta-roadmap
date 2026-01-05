"""
Roadmap-related Pydantic schemas.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class CourseInSemester(BaseModel):
    """
    Course within a semester plan.
    """

    code: str = Field(..., description="Course code")
    title: str = Field(..., description="Course title")
    credits: int = Field(default=3, description="Number of credits")
    satisfies_requirements: list[str] = Field(
        default_factory=list, description="List of requirement IDs this course satisfies"
    )
    prerequisites_met: bool = Field(
        default=True, description="Whether prerequisites are met"
    )
    warnings: list[str] = Field(default_factory=list, description="Any warnings for this course")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "CMPUT 204",
                "title": "Algorithms I",
                "credits": 3,
                "satisfies_requirements": ["req_core_theory"],
                "prerequisites_met": True,
                "warnings": [],
            }
        }


class SemesterPlan(BaseModel):
    """
    Plan for a single semester.
    """

    number: int = Field(..., description="Semester number (1-8)")
    term: str = Field(..., description="Term: FALL, WINTER, SPRING, or SUMMER")
    year: int = Field(..., description="Academic year (1, 2, 3, 4)")
    courses: list[CourseInSemester] = Field(
        default_factory=list, description="Courses in this semester"
    )
    total_credits: int = Field(default=0, description="Total credits for this semester")

    class Config:
        json_schema_extra = {
            "example": {
                "number": 1,
                "term": "FALL",
                "year": 1,
                "courses": [],
                "total_credits": 15,
            }
        }


class RequirementProgress(BaseModel):
    """
    Progress toward a specific requirement.
    """

    requirement_id: str
    requirement_name: str
    requirement_type: str
    credits_needed: int
    credits_completed: int
    credits_planned: int
    is_satisfied: bool = Field(default=False)
    courses_used: list[str] = Field(
        default_factory=list, description="Courses counting toward this requirement"
    )
    remaining: Optional[str] = Field(
        None, description="What's still needed (e.g., '2 more courses', '6 more credits')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "requirement_id": "req123",
                "requirement_name": "Core CS Foundation",
                "requirement_type": "REQUIRED",
                "credits_needed": 9,
                "credits_completed": 6,
                "credits_planned": 9,
                "is_satisfied": True,
                "courses_used": ["CMPUT 174", "CMPUT 175", "CMPUT 201"],
                "remaining": None,
            }
        }


class RoadmapRequest(BaseModel):
    """
    Request to generate a roadmap.
    """

    program_code: str = Field(..., description="Program code (e.g., 'honors-cs')")
    starting_year: int = Field(..., description="Starting year (e.g., 2024)")
    starting_term: str = Field(
        default="FALL", description="Starting term: FALL, WINTER, SPRING"
    )
    completed_courses: list[str] = Field(
        default_factory=list, description="List of already completed course codes"
    )
    preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="Student preferences (e.g., specialization, preferred_terms)",
    )
    credit_load_preference: str = Field(
        default="STANDARD",
        description="Credit load: LIGHT (12), STANDARD (15), HEAVY (18)",
    )
    max_years: int = Field(default=4, description="Maximum years to plan (typically 4)")

    class Config:
        json_schema_extra = {
            "example": {
                "program_code": "honors-cs",
                "starting_year": 2024,
                "starting_term": "FALL",
                "completed_courses": ["CMPUT 174"],
                "preferences": {
                    "specialization": "ai",
                    "avoid_terms": ["SUMMER"],
                },
                "credit_load_preference": "STANDARD",
                "max_years": 4,
            }
        }


class RoadmapResponse(BaseModel):
    """
    Generated roadmap response.
    """

    program_code: str
    program_name: str
    semesters: list[SemesterPlan] = Field(
        default_factory=list, description="Semester-by-semester plan"
    )
    requirement_progress: list[RequirementProgress] = Field(
        default_factory=list, description="Progress toward each requirement"
    )
    total_credits: int = Field(default=0, description="Total credits in the plan")
    credits_needed: int = Field(
        default=120, description="Total credits needed for graduation"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings about the plan (conflicts, unmet prereqs, etc.)",
    )
    graduation_term: Optional[str] = Field(
        None, description="Expected graduation term (e.g., 'Spring 2028')"
    )
    is_valid: bool = Field(
        default=True, description="Whether the plan meets all requirements"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "program_code": "honors-cs",
                "program_name": "BSc Honours in Computing Science",
                "semesters": [],
                "requirement_progress": [],
                "total_credits": 120,
                "credits_needed": 120,
                "warnings": [],
                "graduation_term": "Spring 2028",
                "is_valid": True,
            }
        }


class RoadmapValidationRequest(BaseModel):
    """
    Request to validate a proposed semester schedule.
    """

    program_code: str
    semester_number: int
    courses: list[str] = Field(..., description="Course codes to validate")
    completed_courses: list[str] = Field(
        default_factory=list, description="Previously completed courses"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "program_code": "honors-cs",
                "semester_number": 1,
                "courses": ["CMPUT 174", "MATH 125", "ENGL 103"],
                "completed_courses": [],
            }
        }


class RoadmapValidationResponse(BaseModel):
    """
    Validation result for a semester schedule.
    """

    is_valid: bool
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Warnings")
    total_credits: int
    prerequisite_issues: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Courses with unmet prerequisites",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Heavy course load (18 credits)"],
                "total_credits": 18,
                "prerequisite_issues": [],
            }
        }


class RequirementCheckRequest(BaseModel):
    """
    Request to check which requirements a course list satisfies.
    """

    program_code: str
    courses: list[str] = Field(..., description="List of course codes")

    class Config:
        json_schema_extra = {
            "example": {
                "program_code": "honors-cs",
                "courses": ["CMPUT 174", "CMPUT 175", "CMPUT 201", "MATH 125"],
            }
        }


class RequirementCheckResponse(BaseModel):
    """
    Result of requirement checking.
    """

    program_code: str
    requirements: list[RequirementProgress]
    total_credits: int
    satisfied_count: int = Field(
        default=0, description="Number of requirements fully satisfied"
    )
    partial_count: int = Field(
        default=0, description="Number of requirements partially satisfied"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "program_code": "honors-cs",
                "requirements": [],
                "total_credits": 12,
                "satisfied_count": 1,
                "partial_count": 2,
            }
        }
