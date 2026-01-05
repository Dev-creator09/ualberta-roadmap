"""
Program and Requirement models.
"""

from datetime import datetime
import enum

from sqlalchemy import (
    JSON,
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


class RequirementType(str, enum.Enum):
    """Requirement type enumeration."""

    REQUIRED = "REQUIRED"
    CHOICE = "CHOICE"
    LEVEL_REQUIREMENT = "LEVEL_REQUIREMENT"
    ELECTIVE = "ELECTIVE"


class Program(Base):
    """Program model."""

    __tablename__ = "programs"

    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    total_credits = Column("totalCredits", Integer, default=120, nullable=False)
    requirements = Column(JSON, nullable=True)
    special_rules = Column("specialRules", JSON, nullable=True)
    created_at = Column("createdAt", DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column("updatedAt", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    program_requirements = relationship(
        "Requirement", back_populates="program", cascade="all, delete-orphan"
    )
    roadmaps = relationship("Roadmap", back_populates="program")
    students = relationship("Student", back_populates="program")

    def __repr__(self) -> str:
        return f"<Program {self.code}: {self.name}>"


class Requirement(Base):
    """Requirement model."""

    __tablename__ = "requirements"

    id = Column(String, primary_key=True)
    program_id = Column("programId", String, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    requirement_type = Column("requirementType", String, nullable=False, index=True)
    courses = Column(JSONEncodedList, default=list, nullable=False)
    credits_needed = Column("creditsNeeded", Integer, nullable=True)
    choose_count = Column("chooseCount", Integer, nullable=True)
    level_filter = Column("levelFilter", JSONEncodedList, default=list, nullable=False)
    subject_filter = Column("subjectFilter", String, nullable=True)
    order_index = Column("orderIndex", Integer, default=0, nullable=False)

    # Relationships
    program = relationship("Program", back_populates="program_requirements")

    def __repr__(self) -> str:
        return f"<Requirement {self.name} ({self.requirement_type})>"
