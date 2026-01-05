"""
Program-related Pydantic schemas.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class RequirementResponse(BaseModel):
    """
    Program requirement details.
    """

    id: str
    program_id: str
    name: str = Field(..., description="Requirement name")
    requirement_type: str = Field(
        ..., description="Type: REQUIRED, CHOICE, LEVEL_REQUIREMENT, or ELECTIVE"
    )
    courses: list[str] = Field(default_factory=list, description="List of course codes")
    credits_needed: Optional[int] = Field(None, description="Minimum credits required")
    choose_count: Optional[int] = Field(
        None, description="Number of courses to choose (for CHOICE type)"
    )
    level_filter: list[str] = Field(
        default_factory=list, description="Level filters (e.g., ['300', '400'])"
    )
    subject_filter: Optional[str] = Field(None, description="Subject filter (e.g., CMPUT)")
    order_index: int = Field(default=0, description="Display order")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "req123",
                "program_id": "prog456",
                "name": "Core CS Foundation",
                "requirement_type": "REQUIRED",
                "courses": ["CMPUT 174", "CMPUT 175", "CMPUT 201"],
                "credits_needed": 9,
                "choose_count": None,
                "level_filter": [],
                "subject_filter": None,
                "order_index": 1,
            }
        }


class ProgramResponse(BaseModel):
    """
    Program details response model.
    """

    id: str
    code: str = Field(..., description="Program code (e.g., honors-cs)")
    name: str = Field(..., description="Full program name")
    total_credits: int = Field(default=120, description="Total credits required")
    requirements_data: Optional[dict[str, Any]] = Field(
        None, alias="requirements", description="General requirements as JSON"
    )
    special_rules: Optional[dict[str, Any]] = Field(
        None, description="Special rules and exclusions"
    )
    program_requirements: list[RequirementResponse] = Field(
        default_factory=list, description="List of program requirements"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "prog123",
                "code": "honors-cs",
                "name": "BSc Honours in Computing Science",
                "total_credits": 120,
                "requirements": {
                    "minCredits": 120,
                    "minCMPUTCredits": 60,
                    "minSeniorLevel": 18,
                },
                "special_rules": {
                    "exclusions": [
                        {
                            "courses": ["CMPUT 174", "CMPUT 114"],
                            "rule": "Cannot take both",
                        }
                    ]
                },
                "program_requirements": [],
            }
        }


class ProgramListResponse(BaseModel):
    """
    Response model for list of programs.
    """

    programs: list[ProgramResponse]
    total: int

    class Config:
        json_schema_extra = {"example": {"programs": [], "total": 6}}
