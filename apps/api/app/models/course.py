"""
Course model.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base
from app.db_types import JSONEncodedList

import enum


class CourseLevel(str, enum.Enum):
    """Course level enumeration."""

    LEVEL_100 = "100"
    LEVEL_200 = "200"
    LEVEL_300 = "300"
    LEVEL_400 = "400"
    LEVEL_500 = "500"


class Course(Base):
    """Course model."""

    __tablename__ = "courses"

    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    credits = Column(Integer, default=3, nullable=False)
    description = Column(Text, nullable=True)
    prerequisite_formula = Column("prerequisiteFormula", JSON, nullable=True)
    typically_offered = Column("typicallyOffered", JSONEncodedList, default=list, nullable=False)
    level = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False, index=True)
    created_at = Column("createdAt", DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column("updatedAt", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    roadmap_courses = relationship("RoadmapCourse", back_populates="course")

    def __repr__(self) -> str:
        return f"<Course {self.code}: {self.title}>"
