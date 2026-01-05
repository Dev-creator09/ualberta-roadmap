"""
Student model.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base


class Student(Base):
    """Student model."""

    __tablename__ = "students"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    starting_year = Column("startingYear", Integer, nullable=False)
    program_code = Column("programCode", String, ForeignKey("programs.code"), nullable=False)
    specialization = Column(String, nullable=True)
    created_at = Column("createdAt", DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    program = relationship("Program", back_populates="students")
    roadmaps = relationship("Roadmap", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Student {self.name} ({self.email})>"
