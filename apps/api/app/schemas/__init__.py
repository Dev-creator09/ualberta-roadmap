"""
Pydantic schemas for API request/response models.
"""

from .courses import CourseResponse, CourseListResponse, PrerequisiteNode
from .programs import ProgramResponse, RequirementResponse, ProgramListResponse
from .roadmap import (
    RoadmapRequest,
    RoadmapResponse,
    SemesterPlan,
    CourseInSemester,
    RequirementProgress,
    RoadmapValidationRequest,
    RoadmapValidationResponse,
    RequirementCheckRequest,
    RequirementCheckResponse,
)
from .services import (
    PrerequisiteCheckResult,
    PrerequisiteNode as PrerequisiteTreeNode,
    RequirementProgress as RequirementProgressDetailed,
    AvailableCourse,
    RequirementValidationResult,
    SpecialRulesResult,
)

__all__ = [
    # Courses
    "CourseResponse",
    "CourseListResponse",
    "PrerequisiteNode",
    # Programs
    "ProgramResponse",
    "RequirementResponse",
    "ProgramListResponse",
    # Roadmap
    "RoadmapRequest",
    "RoadmapResponse",
    "SemesterPlan",
    "CourseInSemester",
    "RequirementProgress",
    "RoadmapValidationRequest",
    "RoadmapValidationResponse",
    "RequirementCheckRequest",
    "RequirementCheckResponse",
    # Services
    "PrerequisiteCheckResult",
    "PrerequisiteTreeNode",
    "RequirementProgressDetailed",
    "AvailableCourse",
    "RequirementValidationResult",
    "SpecialRulesResult",
]
