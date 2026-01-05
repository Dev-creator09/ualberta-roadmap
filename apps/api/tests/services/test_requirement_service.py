"""
Tests for requirement validation service.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course, Program, Requirement
from app.services.requirement_service import (
    apply_special_rules,
    find_satisfiable_requirements,
    get_next_available_courses,
    validate_requirements,
)


@pytest.mark.asyncio
async def test_validate_required_courses(db: AsyncSession):
    """Test required courses validation."""
    # Create program with required courses
    program = Program(
        id="test-prog",
        code="TEST-PROG",
        name="Test Program",
        total_credits=12,
    )

    req = Requirement(
        id="req-1",
        program_id="test-prog",
        name="Foundation Courses",
        requirement_type="REQUIRED",
        courses=["TEST 101", "TEST 102", "TEST 103"],
        order_index=0,
    )

    # Create courses
    courses = [
        Course(id=f"test-{i}", code=f"TEST {100+i}", title=f"Test {100+i}", credits=3, level="100", subject="TEST")
        for i in [1, 2, 3]
    ]

    db.add_all([program, req] + courses)
    await db.commit()

    # Test with no courses completed
    result = await validate_requirements("TEST-PROG", [], db)
    assert not result.is_complete
    assert result.total_credits_completed == 0
    assert len(result.requirements) == 1
    assert not result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 0
    assert result.requirements[0].progress_percentage == 0

    # Test with some courses completed
    result = await validate_requirements("TEST-PROG", ["TEST 101", "TEST 102"], db)
    assert not result.is_complete
    assert result.requirements[0].completed_count == 2
    assert result.requirements[0].progress_percentage == pytest.approx(66.67, rel=0.1)
    assert "TEST 103" in result.requirements[0].remaining_courses

    # Test with all courses completed
    result = await validate_requirements(
        "TEST-PROG", ["TEST 101", "TEST 102", "TEST 103"], db
    )
    assert result.is_complete
    assert result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 3
    assert result.requirements[0].progress_percentage == 100


@pytest.mark.asyncio
async def test_validate_choice_requirements(db: AsyncSession):
    """Test choice requirements (need 2 of 5)."""
    program = Program(
        id="test-prog",
        code="TEST-PROG",
        name="Test Program",
        total_credits=6,
    )

    req = Requirement(
        id="req-1",
        program_id="test-prog",
        name="Choose 2 from 5",
        requirement_type="CHOICE",
        courses=["TEST 201", "TEST 202", "TEST 203", "TEST 204", "TEST 205"],
        choose_count=2,
        order_index=0,
    )

    courses = [
        Course(id=f"test-{i}", code=f"TEST {200+i}", title=f"Test {200+i}", credits=3, level="200", subject="TEST")
        for i in [1, 2, 3, 4, 5]
    ]

    db.add_all([program, req] + courses)
    await db.commit()

    # Test with 0 courses (not satisfied)
    result = await validate_requirements("TEST-PROG", [], db)
    assert not result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 0

    # Test with 1 course (not satisfied, need 2)
    result = await validate_requirements("TEST-PROG", ["TEST 201"], db)
    assert not result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 1
    assert result.requirements[0].progress_percentage == 50

    # Test with 2 courses (satisfied)
    result = await validate_requirements("TEST-PROG", ["TEST 201", "TEST 202"], db)
    assert result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 2
    assert result.requirements[0].progress_percentage == 100

    # Test with 3 courses (still satisfied, extra courses don't hurt)
    result = await validate_requirements(
        "TEST-PROG", ["TEST 201", "TEST 202", "TEST 203"], db
    )
    assert result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 3


@pytest.mark.asyncio
async def test_validate_level_requirements(db: AsyncSession):
    """Test level requirements (18 credits from 300/400 level)."""
    program = Program(
        id="test-prog",
        code="TEST-PROG",
        name="Test Program",
        total_credits=18,
    )

    req = Requirement(
        id="req-1",
        program_id="test-prog",
        name="Upper Level Courses",
        requirement_type="LEVEL_REQUIREMENT",
        level_filter=["300", "400"],
        subject_filter="TEST",
        credits_needed=18,
        order_index=0,
    )

    courses = [
        Course(id="test-1", code="TEST 301", title="Test 301", credits=6, level="300", subject="TEST"),
        Course(id="test-2", code="TEST 302", title="Test 302", credits=6, level="300", subject="TEST"),
        Course(id="test-3", code="TEST 401", title="Test 401", credits=6, level="400", subject="TEST"),
        Course(id="test-4", code="TEST 201", title="Test 201", credits=6, level="200", subject="TEST"),
    ]

    db.add_all([program, req] + courses)
    await db.commit()

    # Test with no courses completed
    result = await validate_requirements("TEST-PROG", [], db)
    assert not result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 0

    # Test with 1 course (6 credits, not enough)
    result = await validate_requirements("TEST-PROG", ["TEST 301"], db)
    assert not result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 6
    assert result.requirements[0].progress_percentage == pytest.approx(33.33, rel=0.1)

    # Test with 200-level course (doesn't count)
    result = await validate_requirements("TEST-PROG", ["TEST 201"], db)
    assert not result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 0

    # Test with 3 courses (18 credits, satisfied)
    result = await validate_requirements(
        "TEST-PROG", ["TEST 301", "TEST 302", "TEST 401"], db
    )
    assert result.requirements[0].is_satisfied
    assert result.requirements[0].completed_count == 18
    assert result.requirements[0].progress_percentage == 100


@pytest.mark.asyncio
async def test_find_satisfiable_requirements(db: AsyncSession):
    """Test finding which requirements a course satisfies."""
    program = Program(
        id="test-prog",
        code="TEST-PROG",
        name="Test Program",
        total_credits=12,
    )

    req1 = Requirement(
        id="req-1",
        program_id="test-prog",
        name="Required Math",
        requirement_type="REQUIRED",
        courses=["MATH 101", "MATH 102"],
        order_index=0,
    )

    req2 = Requirement(
        id="req-2",
        program_id="test-prog",
        name="Choose Math or Stats",
        requirement_type="CHOICE",
        courses=["MATH 201", "STAT 201"],
        choose_count=1,
        order_index=1,
    )

    req3 = Requirement(
        id="req-3",
        program_id="test-prog",
        name="300-level Courses",
        requirement_type="LEVEL_REQUIREMENT",
        level_filter=["300"],
        subject_filter="MATH",
        credits_needed=6,
        order_index=2,
    )

    courses = [
        Course(id="m1", code="MATH 101", title="Calculus I", credits=3, level="100", subject="MATH"),
        Course(id="m2", code="MATH 201", title="Calculus II", credits=3, level="200", subject="MATH"),
        Course(id="m3", code="MATH 301", title="Analysis", credits=3, level="300", subject="MATH"),
    ]

    db.add_all([program, req1, req2, req3] + courses)
    await db.commit()

    # MATH 101 should satisfy req-1 (required)
    satisfies = await find_satisfiable_requirements("TEST-PROG", "MATH 101", [], db)
    assert "req-1" in satisfies

    # MATH 201 should satisfy req-2 (choice)
    satisfies = await find_satisfiable_requirements("TEST-PROG", "MATH 201", [], db)
    assert "req-2" in satisfies

    # MATH 301 should satisfy both req-2 (if in list) and req-3 (level requirement)
    satisfies = await find_satisfiable_requirements("TEST-PROG", "MATH 301", [], db)
    assert "req-3" in satisfies

    # If MATH 101 already completed, it shouldn't satisfy req-1
    satisfies = await find_satisfiable_requirements(
        "TEST-PROG", "MATH 101", ["MATH 101"], db
    )
    assert "req-1" not in satisfies


@pytest.mark.asyncio
async def test_get_next_available_courses(db: AsyncSession):
    """Test getting next available courses."""
    program = Program(
        id="test-prog",
        code="TEST-PROG",
        name="Test Program",
        total_credits=12,
    )

    req1 = Requirement(
        id="req-1",
        program_id="test-prog",
        name="Foundation",
        requirement_type="REQUIRED",
        courses=["TEST 101", "TEST 102"],
        order_index=0,
    )

    req2 = Requirement(
        id="req-2",
        program_id="test-prog",
        name="Advanced",
        requirement_type="CHOICE",
        courses=["TEST 201", "TEST 202"],
        choose_count=1,
        order_index=1,
    )

    courses = [
        Course(
            id="c1",
            code="TEST 101",
            title="Intro",
            credits=3,
            level="100",
            subject="TEST",
            typically_offered=["Fall", "Winter"],
        ),
        Course(
            id="c2",
            code="TEST 102",
            title="Fundamentals",
            credits=3,
            level="100",
            subject="TEST",
            typically_offered=["Winter"],
        ),
        Course(
            id="c3",
            code="TEST 201",
            title="Advanced A",
            credits=3,
            level="200",
            subject="TEST",
            prerequisite_formula={"type": "COURSE", "code": "TEST 101"},
            typically_offered=["Fall"],
        ),
        Course(
            id="c4",
            code="TEST 202",
            title="Advanced B",
            credits=3,
            level="200",
            subject="TEST",
            typically_offered=["Winter"],
        ),
    ]

    db.add_all([program, req1, req2] + courses)
    await db.commit()

    # With no courses completed, should suggest foundation courses
    available = await get_next_available_courses("TEST-PROG", [], db)
    codes = [c.course_code for c in available]
    assert "TEST 101" in codes
    assert "TEST 102" in codes

    # Foundation courses should have high priority (REQUIRED)
    test_101 = next(c for c in available if c.course_code == "TEST 101")
    assert test_101.priority_score > 10  # Should have REQUIRED bonus

    # With TEST 101 completed, TEST 201 should become available
    available = await get_next_available_courses("TEST-PROG", ["TEST 101"], db)
    codes = [c.course_code for c in available]
    assert "TEST 101" not in codes  # Already completed
    assert "TEST 102" in codes
    assert "TEST 201" in codes

    # TEST 201 should have prerequisites_met=True
    test_201 = next(c for c in available if c.course_code == "TEST 201")
    assert test_201.prerequisites_met


@pytest.mark.asyncio
async def test_apply_special_rules(db: AsyncSession):
    """Test applying special program rules."""
    program = Program(
        id="test-prog",
        code="TEST-PROG",
        name="Test Program",
        total_credits=12,
        special_rules={
            "exclusions": [
                {"course": "CMPUT 275", "excludes": ["CMPUT 201"]},
                {"course": "MATH 134", "excludes": ["MATH 144", "MATH 154"]},
            ],
            "substitutions": [
                {"from": "CMPUT 115", "to": "CMPUT 174"},
            ],
            "additional_requirements": [
                "Must maintain 3.0 GPA",
                "Complete within 5 years",
            ],
        },
    )

    # Test exclusions
    result = await apply_special_rules(
        program, ["CMPUT 275", "CMPUT 201", "MATH 134", "MATH 144"]
    )

    assert "CMPUT 201" in result.excluded_courses
    assert "MATH 144" in result.excluded_courses
    assert len(result.warnings) >= 2
    assert any("CMPUT 275" in w and "CMPUT 201" in w for w in result.warnings)

    # Test substitutions
    result = await apply_special_rules(program, ["CMPUT 115"])
    assert len(result.substitutions_needed) == 1
    assert result.substitutions_needed[0]["from"] == "CMPUT 115"
    assert result.substitutions_needed[0]["to"] == "CMPUT 174"

    # Test additional requirements
    result = await apply_special_rules(program, [])
    assert len(result.additional_requirements) == 2
    assert "Must maintain 3.0 GPA" in result.additional_requirements


@pytest.mark.asyncio
async def test_program_not_found(db: AsyncSession):
    """Test error handling when program doesn't exist."""
    with pytest.raises(ValueError, match="Program 'NONEXISTENT' not found"):
        await validate_requirements("NONEXISTENT", [], db)


@pytest.mark.asyncio
async def test_course_not_found_in_find_satisfiable(db: AsyncSession):
    """Test error handling when course doesn't exist."""
    program = Program(
        id="test-prog",
        code="TEST-PROG",
        name="Test Program",
        total_credits=12,
    )
    db.add(program)
    await db.commit()

    with pytest.raises(ValueError, match="Course 'NONEXISTENT' not found"):
        await find_satisfiable_requirements("TEST-PROG", "NONEXISTENT", [], db)


@pytest.mark.asyncio
async def test_multiple_requirements_progress(db: AsyncSession):
    """Test overall program progress with multiple requirements."""
    program = Program(
        id="test-prog",
        code="TEST-PROG",
        name="Test Program",
        total_credits=18,
    )

    req1 = Requirement(
        id="req-1",
        program_id="test-prog",
        name="Foundation",
        requirement_type="REQUIRED",
        courses=["TEST 101", "TEST 102"],
        order_index=0,
    )

    req2 = Requirement(
        id="req-2",
        program_id="test-prog",
        name="Advanced",
        requirement_type="CHOICE",
        courses=["TEST 201", "TEST 202"],
        choose_count=1,
        order_index=1,
    )

    courses = [
        Course(id=f"c{i}", code=code, title=code, credits=3, level=level, subject="TEST")
        for i, (code, level) in enumerate(
            [("TEST 101", "100"), ("TEST 102", "100"), ("TEST 201", "200"), ("TEST 202", "200")]
        )
    ]

    db.add_all([program, req1, req2] + courses)
    await db.commit()

    # Complete first requirement fully, second partially
    result = await validate_requirements(
        "TEST-PROG", ["TEST 101", "TEST 102"], db
    )

    assert len(result.requirements) == 2
    assert result.requirements[0].is_satisfied  # Foundation complete
    assert not result.requirements[1].is_satisfied  # Advanced not complete
    assert not result.is_complete
    # Overall progress: 1 out of 2 requirements satisfied = 50%
    assert result.overall_progress == 50.0

    # Complete both requirements
    result = await validate_requirements(
        "TEST-PROG", ["TEST 101", "TEST 102", "TEST 201"], db
    )

    assert result.is_complete
    assert result.overall_progress == 100.0
