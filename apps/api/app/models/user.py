"""
User model.
"""

from datetime import datetime
import enum

from sqlalchemy import Column, DateTime, Enum, String

from app.db import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""

    STUDENT = "STUDENT"
    ADVISOR = "ADVISOR"
    ADMIN = "ADMIN"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="STUDENT", nullable=False)
    created_at = Column("createdAt", DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column("updatedAt", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
