"""
Tests for prerequisite validation service.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course
from app.services.prerequisite_service import (
    check_prerequisites,
    get_prerequisite_tree,
    validate_prerequisite_formula,
)


@pytest.mark.asyncio
async def test_simple_prerequisite(db: AsyncSession):
    """Test simple prerequisite: A requires B."""
    # Create courses
    course_a = Course(
        id="test-a",
        code="TEST 101",
        title="Test Course A",
        credits=3,
        level="100",
        subject="TEST",
        prerequisite_formula={
            "type": "COURSE",
            "code": "TEST 100",
        },
    )
    course_b = Course(
        id="test-b",
        code="TEST 100",
        title="Test Course B",
        credits=3,
        level="100",
        subject="TEST",
    )

    db.add_all([course_a, course_b])
    await db.commit()

    # Test with prerequisite not completed
    result = await check_prerequisites("TEST 101", [], db)
    assert not result.is_valid
    assert "TEST 100" in result.missing_courses
    assert len(result.satisfied_prerequisites) == 0

    # Test with prerequisite completed
    result = await check_prerequisites("TEST 101", ["TEST 100"], db)
    assert result.is_valid
    assert len(result.missing_courses) == 0
    assert "TEST 100" in result.satisfied_prerequisites


@pytest.mark.asyncio
async def test_or_logic_prerequisite(db: AsyncSession):
    """Test OR logic: A requires B or C."""
    course_a = Course(
        id="test-a",
        code="TEST 201",
        title="Test Course A",
        credits=3,
        level="200",
        subject="TEST",
        prerequisite_formula={
            "type": "OR",
            "conditions": [
                {"type": "COURSE", "code": "TEST 100"},
                {"type": "COURSE", "code": "TEST 101"},
            ],
        },
    )
    course_b = Course(
        id="test-b",
        code="TEST 100",
        title="Test Course B",
        credits=3,
        level="100",
        subject="TEST",
    )
    course_c = Course(
        id="test-c",
        code="TEST 101",
        title="Test Course C",
        credits=3,
        level="100",
        subject="TEST",
    )

    db.add_all([course_a, course_b, course_c])
    await db.commit()

    # Test with no prerequisites completed
    result = await check_prerequisites("TEST 201", [], db)
    assert not result.is_valid

    # Test with one prerequisite completed (should be valid)
    result = await check_prerequisites("TEST 201", ["TEST 100"], db)
    assert result.is_valid
    assert "TEST 100" in result.satisfied_prerequisites

    # Test with other prerequisite completed (should also be valid)
    result = await check_prerequisites("TEST 201", ["TEST 101"], db)
    assert result.is_valid
    assert "TEST 101" in result.satisfied_prerequisites

    # Test with both completed (should be valid)
    result = await check_prerequisites("TEST 201", ["TEST 100", "TEST 101"], db)
    assert result.is_valid


@pytest.mark.asyncio
async def test_and_logic_prerequisite(db: AsyncSession):
    """Test AND logic: A requires B and C."""
    course_a = Course(
        id="test-a",
        code="TEST 301",
        title="Test Course A",
        credits=3,
        level="300",
        subject="TEST",
        prerequisite_formula={
            "type": "AND",
            "conditions": [
                {"type": "COURSE", "code": "TEST 200"},
                {"type": "COURSE", "code": "TEST 201"},
            ],
        },
    )
    course_b = Course(
        id="test-b",
        code="TEST 200",
        title="Test Course B",
        credits=3,
        level="200",
        subject="TEST",
    )
    course_c = Course(
        id="test-c",
        code="TEST 201",
        title="Test Course C",
        credits=3,
        level="200",
        subject="TEST",
    )

    db.add_all([course_a, course_b, course_c])
    await db.commit()

    # Test with no prerequisites completed
    result = await check_prerequisites("TEST 301", [], db)
    assert not result.is_valid
    assert len(result.missing_courses) == 2

    # Test with only one prerequisite completed (should not be valid)
    result = await check_prerequisites("TEST 301", ["TEST 200"], db)
    assert not result.is_valid
    assert "TEST 201" in result.missing_courses
    assert "TEST 200" in result.satisfied_prerequisites

    # Test with both prerequisites completed (should be valid)
    result = await check_prerequisites("TEST 301", ["TEST 200", "TEST 201"], db)
    assert result.is_valid
    assert len(result.missing_courses) == 0
    assert len(result.satisfied_prerequisites) == 2


@pytest.mark.asyncio
async def test_nested_prerequisites(db: AsyncSession):
    """Test nested prerequisites: A requires B, B requires C."""
    course_c = Course(
        id="test-c",
        code="TEST 100",
        title="Test Course C (Foundation)",
        credits=3,
        level="100",
        subject="TEST",
    )
    course_b = Course(
        id="test-b",
        code="TEST 200",
        title="Test Course B (Intermediate)",
        credits=3,
        level="200",
        subject="TEST",
        prerequisite_formula={
            "type": "COURSE",
            "code": "TEST 100",
        },
    )
    course_a = Course(
        id="test-a",
        code="TEST 300",
        title="Test Course A (Advanced)",
        credits=3,
        level="300",
        subject="TEST",
        prerequisite_formula={
            "type": "COURSE",
            "code": "TEST 200",
        },
    )

    db.add_all([course_a, course_b, course_c])
    await db.commit()

    # Test prerequisite tree
    tree = await get_prerequisite_tree("TEST 300", db)
    assert tree.course_code == "TEST 300"
    assert len(tree.prerequisites) == 1
    assert tree.prerequisites[0].course_code == "TEST 200"
    assert len(tree.prerequisites[0].prerequisites) == 1
    assert tree.prerequisites[0].prerequisites[0].course_code == "TEST 100"

    # Test validation - need both TEST 200 and TEST 100 to take TEST 300
    # But TEST 300 only directly requires TEST 200
    result = await check_prerequisites("TEST 300", ["TEST 200"], db)
    assert result.is_valid  # Direct prerequisite satisfied


@pytest.mark.asyncio
async def test_no_prerequisites(db: AsyncSession):
    """Test course with no prerequisites."""
    course = Course(
        id="test-a",
        code="TEST 101",
        title="Test Course",
        credits=3,
        level="100",
        subject="TEST",
    )

    db.add(course)
    await db.commit()

    result = await check_prerequisites("TEST 101", [], db)
    assert result.is_valid
    assert len(result.missing_courses) == 0
    assert result.formula_description == "No prerequisites required"


@pytest.mark.asyncio
async def test_complex_nested_formula(db: AsyncSession):
    """Test complex formula: (A AND B) OR (C AND D)."""
    target_course = Course(
        id="test-target",
        code="TEST 401",
        title="Advanced Test Course",
        credits=3,
        level="400",
        subject="TEST",
        prerequisite_formula={
            "type": "OR",
            "conditions": [
                {
                    "type": "AND",
                    "conditions": [
                        {"type": "COURSE", "code": "TEST 301"},
                        {"type": "COURSE", "code": "TEST 302"},
                    ],
                },
                {
                    "type": "AND",
                    "conditions": [
                        {"type": "COURSE", "code": "TEST 310"},
                        {"type": "COURSE", "code": "TEST 311"},
                    ],
                },
            ],
        },
    )

    # Create prerequisite courses
    courses = [
        Course(id=f"test-{code}", code=code, title=f"Course {code}", credits=3, level="300", subject="TEST")
        for code in ["TEST 301", "TEST 302", "TEST 310", "TEST 311"]
    ]

    db.add_all([target_course] + courses)
    await db.commit()

    # Test with first AND branch satisfied
    result = await check_prerequisites("TEST 401", ["TEST 301", "TEST 302"], db)
    assert result.is_valid

    # Test with second AND branch satisfied
    result = await check_prerequisites("TEST 401", ["TEST 310", "TEST 311"], db)
    assert result.is_valid

    # Test with only partial first branch (should not be valid)
    result = await check_prerequisites("TEST 401", ["TEST 301"], db)
    assert not result.is_valid

    # Test with mixed courses from both branches but neither complete
    result = await check_prerequisites("TEST 401", ["TEST 301", "TEST 311"], db)
    assert not result.is_valid


@pytest.mark.asyncio
async def test_course_not_found(db: AsyncSession):
    """Test error handling when course doesn't exist."""
    with pytest.raises(ValueError, match="Course 'NONEXISTENT' not found"):
        await check_prerequisites("NONEXISTENT", [], db)


@pytest.mark.asyncio
async def test_prerequisite_tree_depth_limit(db: AsyncSession):
    """Test that prerequisite tree respects max depth."""
    # Create a long chain of prerequisites
    courses = []
    for i in range(10):
        prereq = {"type": "COURSE", "code": f"TEST {i}"} if i > 0 else None
        course = Course(
            id=f"test-{i}",
            code=f"TEST {i+1}",
            title=f"Test Course {i+1}",
            credits=3,
            level="100",
            subject="TEST",
            prerequisite_formula=prereq,
        )
        courses.append(course)

    db.add_all(courses)
    await db.commit()

    # Get tree with max_depth=3
    tree = await get_prerequisite_tree("TEST 10", db, max_depth=3)

    # Should have depth 0, 1, 2, 3 but not go deeper
    assert tree.depth == 0
    if tree.prerequisites:
        assert tree.prerequisites[0].depth == 1
        if tree.prerequisites[0].prerequisites:
            assert tree.prerequisites[0].prerequisites[0].depth == 2
            # Can go to depth 3 (max_depth)
            if tree.prerequisites[0].prerequisites[0].prerequisites:
                assert tree.prerequisites[0].prerequisites[0].prerequisites[0].depth == 3
                # Should not go deeper than max_depth
                assert len(tree.prerequisites[0].prerequisites[0].prerequisites[0].prerequisites) == 0


@pytest.mark.asyncio
async def test_validate_prerequisite_formula_directly(db: AsyncSession):
    """Test validate_prerequisite_formula function directly."""
    formula = {
        "type": "AND",
        "conditions": [
            {"type": "COURSE", "code": "CMPUT 174"},
            {"type": "COURSE", "code": "CMPUT 175"},
        ],
    }

    completed = {"CMPUT 174", "CMPUT 175"}
    is_valid = await validate_prerequisite_formula(formula, completed, db)
    assert is_valid

    completed = {"CMPUT 174"}
    is_valid = await validate_prerequisite_formula(formula, completed, db)
    assert not is_valid
