"""
Course-related Pydantic schemas.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class PrerequisiteNode(BaseModel):
    """
    Represents a prerequisite condition node.
    Can be a single course or a logical combination (AND/OR).
    """

    type: str = Field(..., description="Type: COURSE, AND, or OR")
    code: Optional[str] = Field(None, description="Course code if type is COURSE")
    conditions: Optional[list["PrerequisiteNode"]] = Field(
        None, description="Nested conditions for AND/OR types"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "AND",
                "conditions": [
                    {"type": "COURSE", "code": "CMPUT 204"},
                    {
                        "type": "OR",
                        "conditions": [
                            {"type": "COURSE", "code": "MATH 125"},
                            {"type": "COURSE", "code": "MATH 127"},
                        ],
                    },
                ],
            }
        }


class CourseResponse(BaseModel):
    """
    Course details response model.
    """

    id: str
    code: str = Field(..., description="Course code (e.g., CMPUT 174)")
    title: str = Field(..., description="Full course name")
    credits: int = Field(default=3, description="Number of credits")
    description: Optional[str] = Field(None, description="Course description")
    prerequisite_formula: Optional[dict[str, Any]] = Field(
        None, description="Prerequisite structure as JSON"
    )
    prerequisites_parsed: Optional[PrerequisiteNode] = Field(
        None, description="Parsed prerequisite tree"
    )
    typically_offered: list[str] = Field(
        default_factory=list, description="Terms when typically offered"
    )
    level: str = Field(..., description="Course level (100, 200, 300, 400, 500)")
    subject: str = Field(..., description="Subject code (CMPUT, MATH, etc.)")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "clx123abc",
                "code": "CMPUT 204",
                "title": "Algorithms I",
                "credits": 3,
                "description": "Introduction to algorithm design and analysis",
                "prerequisite_formula": {
                    "type": "AND",
                    "conditions": [
                        {"type": "COURSE", "code": "CMPUT 175"},
                        {"type": "COURSE", "code": "MATH 125"},
                    ],
                },
                "typically_offered": ["Fall", "Winter"],
                "level": "200",
                "subject": "CMPUT",
            }
        }


class CourseListResponse(BaseModel):
    """
    Response model for list of courses.
    """

    courses: list[CourseResponse]
    total: int
    page: int = 1
    page_size: int = 100

    class Config:
        json_schema_extra = {
            "example": {
                "courses": [],
                "total": 50,
                "page": 1,
                "page_size": 100,
            }
        }
