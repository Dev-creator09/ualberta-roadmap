"""
Tests for roadmap generation service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.roadmap_service import (
    _get_cache_key,
    _format_requirements_for_prompt,
    optimize_course_distribution,
    RoadmapGenerationError,
)
from app.schemas.roadmap import RoadmapRequest, SemesterPlan, CourseInSemester
from app.models import Course, Program, Requirement


class TestCaching:
    """Test caching functionality."""

    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        request1 = RoadmapRequest(
            program_code="honors-cs",
            starting_year=2024,
            starting_term="FALL",
            completed_courses=["CMPUT 174", "CMPUT 175"],
            credit_load_preference="STANDARD",
            max_years=4,
        )

        request2 = RoadmapRequest(
            program_code="honors-cs",
            starting_year=2024,
            starting_term="FALL",
            completed_courses=["CMPUT 175", "CMPUT 174"],  # Different order
            credit_load_preference="STANDARD",
            max_years=4,
        )

        # Same parameters should produce same cache key regardless of order
        key1 = _get_cache_key(request1)
        key2 = _get_cache_key(request2)

        assert key1 == key2
        assert len(key1) == 64  # SHA-256 produces 64-char hex string

    def test_cache_key_different_for_different_requests(self):
        """Test that different requests produce different cache keys."""
        request1 = RoadmapRequest(
            program_code="honors-cs",
            starting_year=2024,
            starting_term="FALL",
            completed_courses=["CMPUT 174"],
            credit_load_preference="STANDARD",
            max_years=4,
        )

        request2 = RoadmapRequest(
            program_code="honors-cs",
            starting_year=2024,
            starting_term="FALL",
            completed_courses=["CMPUT 175"],  # Different course
            credit_load_preference="STANDARD",
            max_years=4,
        )

        key1 = _get_cache_key(request1)
        key2 = _get_cache_key(request2)

        assert key1 != key2


class TestPromptFormatting:
    """Test prompt formatting functions."""

    def test_format_requirements_for_prompt(self):
        """Test requirement formatting for LLM prompt."""
        # Create test requirements
        req1 = Requirement(
            id="req1",
            program_id="prog1",
            name="Foundation CMPUT",
            requirement_type="REQUIRED",
            courses=["CMPUT 174", "CMPUT 175"],
            credits_needed=6,
            order_index=1,
        )

        req2 = Requirement(
            id="req2",
            program_id="prog1",
            name="Calculus",
            requirement_type="CHOICE",
            courses=["MATH 125", "MATH 127", "MATH 134"],
            credits_needed=3,
            choose_count=1,
            order_index=2,
        )

        requirements = [req1, req2]
        completed_courses = ["CMPUT 174", "CMPUT 175"]
        courses_map = {
            "CMPUT 174": Course(id="1", code="CMPUT 174", title="Test", credits=3, level="100", subject="CMPUT"),
            "CMPUT 175": Course(id="2", code="CMPUT 175", title="Test", credits=3, level="100", subject="CMPUT"),
        }

        result = _format_requirements_for_prompt(requirements, completed_courses, courses_map)

        assert "Foundation CMPUT" in result
        assert "REQUIRED" in result
        assert "✓ SATISFIED" in result
        assert "Calculus" in result
        assert "CHOICE" in result


class TestCourseOptimization:
    """Test course distribution optimization."""

    def test_optimize_course_distribution_sorts_by_level(self):
        """Test that courses are sorted by level within semesters."""
        # Create test courses
        courses_map = {
            "CMPUT 401": Course(id="1", code="CMPUT 401", title="Advanced", credits=3, level="400", subject="CMPUT"),
            "CMPUT 174": Course(id="2", code="CMPUT 174", title="Intro", credits=3, level="100", subject="CMPUT"),
            "CMPUT 204": Course(id="3", code="CMPUT 204", title="Algorithms", credits=3, level="200", subject="CMPUT"),
        }

        # Create semester with unsorted courses
        semester = SemesterPlan(
            number=1,
            term="FALL",
            year=1,
            courses=[
                CourseInSemester(code="CMPUT 401", title="Advanced", credits=3),
                CourseInSemester(code="CMPUT 174", title="Intro", credits=3),
                CourseInSemester(code="CMPUT 204", title="Algorithms", credits=3),
            ],
            total_credits=9,
        )

        result = optimize_course_distribution([semester], courses_map)

        # Check that courses are sorted by level
        assert result[0].courses[0].code == "CMPUT 174"  # 100-level first
        assert result[0].courses[1].code == "CMPUT 204"  # 200-level second
        assert result[0].courses[2].code == "CMPUT 401"  # 400-level last


class TestErrorHandling:
    """Test error handling."""

    def test_roadmap_generation_error(self):
        """Test RoadmapGenerationError can be raised."""
        with pytest.raises(RoadmapGenerationError):
            raise RoadmapGenerationError("Test error")


# Integration tests would require mocking OpenAI API
# These are placeholder tests to get started

class TestIntegration:
    """Integration tests (require mocking)."""

    @pytest.mark.asyncio
    async def test_generate_roadmap_with_missing_program(self, db: AsyncSession):
        """Test that generate_roadmap raises error for missing program."""
        from app.services.roadmap_service import generate_roadmap

        request = RoadmapRequest(
            program_code="nonexistent-program",
            starting_year=2024,
            starting_term="FALL",
            completed_courses=[],
            credit_load_preference="STANDARD",
            max_years=4,
        )

        with pytest.raises(ValueError, match="Program 'nonexistent-program' not found"):
            await generate_roadmap(request, db)

    @pytest.mark.asyncio
    @patch.dict("os.environ", {}, clear=True)
    async def test_generate_roadmap_without_api_key(self, db: AsyncSession):
        """Test that generate_roadmap raises error when OPENAI_API_KEY is not set."""
        from app.services.roadmap_service import generate_roadmap

        # Create a minimal program
        program = Program(
            id="test-prog",
            code="test-cs",
            name="Test Program",
            total_credits=120,
        )
        db.add(program)
        await db.commit()

        request = RoadmapRequest(
            program_code="test-cs",
            starting_year=2024,
            starting_term="FALL",
            completed_courses=[],
            credit_load_preference="STANDARD",
            max_years=4,
        )

        with pytest.raises(RoadmapGenerationError, match="OPENAI_API_KEY"):
            await generate_roadmap(request, db)
