"""
Roadmap and RoadmapCourse models.
"""

from datetime import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.db import Base
from app.db_types import JSONEncodedList


class Term(str, enum.Enum):
    """Term enumeration."""

    FALL = "FALL"
    WINTER = "WINTER"
    SPRING = "SPRING"
    SUMMER = "SUMMER"


class CourseStatus(str, enum.Enum):
    """Course status enumeration."""

    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"
    WAITLISTED = "WAITLISTED"


class Roadmap(Base):
    """Roadmap model."""

    __tablename__ = "roadmaps"

    id = Column(String, primary_key=True)
    student_id = Column("studentId", String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    program_id = Column("programId", String, ForeignKey("programs.id"), nullable=False)
    name = Column(String, nullable=False)
    is_active = Column("isActive", Boolean, default=True, nullable=False, index=True)
    generated_at = Column("generatedAt", DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column("createdAt", DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column("updatedAt", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    student = relationship("Student", back_populates="roadmaps")
    program = relationship("Program", back_populates="roadmaps")
    roadmap_courses = relationship(
        "RoadmapCourse", back_populates="roadmap", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Roadmap {self.name} (Active: {self.is_active})>"


class RoadmapCourse(Base):
    """RoadmapCourse model."""

    __tablename__ = "roadmap_courses"

    id = Column(String, primary_key=True)
    roadmap_id = Column("roadmapId", String, ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False)
    course_code = Column("courseCode", String, ForeignKey("courses.code"), nullable=False)
    semester = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    term = Column(String, nullable=False, index=True)
    status = Column(String, default="PLANNED", nullable=False, index=True)
    satisfies_requirements = Column("satisfiesRequirements", JSONEncodedList, default=list, nullable=False)
    created_at = Column("createdAt", DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    roadmap = relationship("Roadmap", back_populates="roadmap_courses")
    course = relationship("Course", back_populates="roadmap_courses")

    def __repr__(self) -> str:
        return f"<RoadmapCourse {self.course_code} - Semester {self.semester} ({self.term})>"
