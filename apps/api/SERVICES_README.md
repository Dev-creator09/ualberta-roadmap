# Service Layer Documentation

This document describes the service layer implementation for prerequisite and requirement validation in the UAlberta Roadmap API.

## Overview

The service layer contains business logic for:
- **Prerequisite validation**: Checking if a student has completed prerequisite courses
- **Requirement tracking**: Validating program requirements and tracking progress
- **Course recommendations**: Suggesting next courses to take

## Architecture

```
app/
├── services/
│   ├── __init__.py
│   ├── prerequisite_service.py  # Prerequisite validation logic
│   └── requirement_service.py   # Requirement validation logic
├── schemas/
│   └── services.py               # Pydantic response models
└── tests/
    └── services/
        ├── conftest.py                      # Test fixtures
        ├── test_prerequisite_service.py     # Prerequisite tests
        └── test_requirement_service.py      # Requirement tests
```

## Prerequisite Service

### Functions

#### `check_prerequisites(course_code, completed_courses, db)`

Check if prerequisites are satisfied for a given course.

**Parameters:**
- `course_code` (str): Course code to check (e.g., "CMPUT 204")
- `completed_courses` (list[str]): List of completed course codes
- `db` (AsyncSession): Database session

**Returns:** `PrerequisiteCheckResult`
```python
{
    "is_valid": bool,
    "missing_courses": list[str],
    "satisfied_prerequisites": list[str],
    "formula_description": str
}
```

**Example:**
```python
from app.services import check_prerequisites

result = await check_prerequisites(
    "CMPUT 204",
    ["CMPUT 174", "CMPUT 175"],
    db
)

if result.is_valid:
    print("Prerequisites satisfied!")
else:
    print(f"Missing: {result.missing_courses}")
```

#### `get_prerequisite_tree(course_code, db, depth, max_depth)`

Build prerequisite tree for visualization.

**Parameters:**
- `course_code` (str): Course to build tree for
- `db` (AsyncSession): Database session
- `depth` (int, optional): Current depth (default: 0)
- `max_depth` (int, optional): Maximum depth to traverse (default: 5)

**Returns:** `PrerequisiteNode`
```python
{
    "course_code": "CMPUT 204",
    "title": "Algorithms I",
    "depth": 0,
    "prerequisites": [
        {
            "course_code": "CMPUT 175",
            "title": "Foundations II",
            "depth": 1,
            "prerequisites": [...]
        }
    ],
    "formula": {...}
}
```

**Example:**
```python
tree = await get_prerequisite_tree("CMPUT 466", db, max_depth=3)

# Visualize the tree
def print_tree(node, indent=0):
    print("  " * indent + f"- {node.course_code}: {node.title}")
    for prereq in node.prerequisites:
        print_tree(prereq, indent + 1)

print_tree(tree)
```

#### `validate_prerequisite_formula(formula, completed, db)`

Validate a prerequisite formula against completed courses.

**Parameters:**
- `formula` (dict): Prerequisite formula (JSONB structure)
- `completed` (set[str]): Set of completed course codes
- `db` (AsyncSession): Database session

**Returns:** `bool` (True if satisfied)

**Formula Structure:**
```python
# Simple prerequisite
{
    "type": "COURSE",
    "code": "CMPUT 174"
}

# AND logic (all required)
{
    "type": "AND",
    "conditions": [
        {"type": "COURSE", "code": "CMPUT 174"},
        {"type": "COURSE", "code": "CMPUT 175"}
    ]
}

# OR logic (at least one required)
{
    "type": "OR",
    "conditions": [
        {"type": "COURSE", "code": "MATH 125"},
        {"type": "COURSE", "code": "MATH 127"}
    ]
}

# Nested (complex logic)
{
    "type": "OR",
    "conditions": [
        {
            "type": "AND",
            "conditions": [
                {"type": "COURSE", "code": "CMPUT 204"},
                {"type": "COURSE", "code": "CMPUT 272"}
            ]
        },
        {"type": "COURSE", "code": "CMPUT 303"}
    ]
}
```

## Requirement Service

### Functions

#### `validate_requirements(program_code, completed_courses, db)`

Validate all requirements for a program.

**Parameters:**
- `program_code` (str): Program code (e.g., "honors-cs-ai")
- `completed_courses` (list[str]): Completed course codes
- `db` (AsyncSession): Database session

**Returns:** `RequirementValidationResult`
```python
{
    "program_code": "honors-cs-ai",
    "program_name": "Honours CS - AI Option",
    "total_credits_required": 90,
    "total_credits_completed": 36,
    "requirements": [
        {
            "requirement_id": "req-1",
            "requirement_name": "Foundation CMPUT",
            "requirement_type": "REQUIRED",
            "required_count": 2,
            "completed_count": 2,
            "is_satisfied": true,
            "completed_courses": ["CMPUT 174", "CMPUT 175"],
            "remaining_courses": [],
            "progress_percentage": 100.0
        },
        ...
    ],
    "overall_progress": 40.0,
    "is_complete": false
}
```

**Example:**
```python
result = await validate_requirements(
    "honors-cs-ai",
    ["CMPUT 174", "CMPUT 175", "CMPUT 204"],
    db
)

print(f"Overall progress: {result.overall_progress}%")
for req in result.requirements:
    print(f"{req.requirement_name}: {req.progress_percentage}%")
    if not req.is_satisfied:
        print(f"  Missing: {req.remaining_courses}")
```

#### `find_satisfiable_requirements(program_code, course_code, completed, db)`

Find which requirements a course would satisfy.

**Parameters:**
- `program_code` (str): Program code
- `course_code` (str): Course to check
- `completed` (list[str]): Already completed courses
- `db` (AsyncSession): Database session

**Returns:** `list[str]` (requirement IDs)

**Example:**
```python
# Which requirements does CMPUT 267 satisfy?
satisfies = await find_satisfiable_requirements(
    "honors-cs-ai",
    "CMPUT 267",
    ["CMPUT 174", "CMPUT 175"],
    db
)

# Returns: ["req-5"]  (AI Core Courses requirement)
```

#### `get_next_available_courses(program_code, completed, db)`

Get courses student can take next.

**Parameters:**
- `program_code` (str): Program code
- `completed` (list[str]): Completed courses
- `db` (AsyncSession): Database session

**Returns:** `list[AvailableCourse]` (sorted by priority)
```python
[
    {
        "course_code": "CMPUT 204",
        "title": "Algorithms I",
        "credits": 3,
        "level": "200",
        "prerequisites_met": true,
        "satisfies_requirements": ["req-2"],
        "priority_score": 15.4,
        "typically_offered": ["Fall", "Winter"]
    },
    ...
]
```

**Priority Scoring:**
- +10 points: REQUIRED courses
- +5 points: CHOICE courses
- +2 points: LEVEL_REQUIREMENT courses
- +3 points: Prerequisites met
- +(600-level)/100 points: Lower level courses (foundational first)

**Example:**
```python
available = await get_next_available_courses(
    "honors-cs-ai",
    ["CMPUT 174", "CMPUT 175"],
    db
)

print("Recommended courses:")
for course in available[:5]:  # Top 5
    status = "✓" if course.prerequisites_met else "✗"
    print(f"{status} {course.course_code}: {course.title}")
    print(f"   Priority: {course.priority_score:.1f}")
    print(f"   Satisfies: {len(course.satisfies_requirements)} requirements")
```

#### `apply_special_rules(program, courses)`

Apply special program rules.

**Parameters:**
- `program` (Program): Program object
- `courses` (list[str]): List of course codes

**Returns:** `SpecialRulesResult`
```python
{
    "excluded_courses": ["CMPUT 201"],
    "warnings": [
        "CMPUT 275 excludes CMPUT 201. Cannot count both."
    ],
    "substitutions_needed": [
        {"from": "CMPUT 115", "to": "CMPUT 174"}
    ],
    "additional_requirements": [
        "Must maintain 3.0 GPA"
    ]
}
```

## Requirement Types

### REQUIRED
All courses in the list must be completed.

**Example:**
```python
{
    "name": "Foundation CMPUT",
    "type": "REQUIRED",
    "courses": ["CMPUT 174", "CMPUT 175"]
}
# Student must complete both courses
```

### CHOICE
Choose N courses from a list.

**Example:**
```python
{
    "name": "Calculus",
    "type": "CHOICE",
    "courses": ["MATH 134", "MATH 144", "MATH 154"],
    "choose_count": 1
}
# Student must complete 1 of the 3 courses
```

### LEVEL_REQUIREMENT
Complete N credits from courses matching level/subject filters.

**Example:**
```python
{
    "name": "Upper Level CMPUT",
    "type": "LEVEL_REQUIREMENT",
    "level_filter": ["300", "400"],
    "subject_filter": "CMPUT",
    "credits_needed": 18
}
# Student needs 18 credits from 300/400-level CMPUT courses
```

### ELECTIVE
Any courses (usually satisfied automatically).

**Example:**
```python
{
    "name": "Open Electives",
    "type": "ELECTIVE"
}
# Satisfied by any courses
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
cd apps/api
pip install pytest pytest-asyncio aiosqlite
```

### Run All Tests

```bash
# Run all service tests
pytest tests/services/ -v

# Run with coverage
pytest tests/services/ --cov=app/services --cov-report=html

# Run specific test file
pytest tests/services/test_prerequisite_service.py -v

# Run specific test
pytest tests/services/test_prerequisite_service.py::test_simple_prerequisite -v
```

### Test Output Example

```
tests/services/test_prerequisite_service.py::test_simple_prerequisite PASSED
tests/services/test_prerequisite_service.py::test_or_logic_prerequisite PASSED
tests/services/test_prerequisite_service.py::test_and_logic_prerequisite PASSED
tests/services/test_prerequisite_service.py::test_nested_prerequisites PASSED
tests/services/test_prerequisite_service.py::test_no_prerequisites PASSED
tests/services/test_prerequisite_service.py::test_complex_nested_formula PASSED

tests/services/test_requirement_service.py::test_validate_required_courses PASSED
tests/services/test_requirement_service.py::test_validate_choice_requirements PASSED
tests/services/test_requirement_service.py::test_validate_level_requirements PASSED
tests/services/test_requirement_service.py::test_find_satisfiable_requirements PASSED
tests/services/test_requirement_service.py::test_get_next_available_courses PASSED
tests/services/test_requirement_service.py::test_apply_special_rules PASSED

========================= 12 passed in 2.34s =========================
```

## Integration with API Routes

Example of using services in API routes:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services import check_prerequisites, validate_requirements

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/{student_id}/progress")
async def get_student_progress(
    student_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get student's program progress."""
    # Fetch student's program and completed courses
    student = await db.get(Student, student_id)
    completed = [enrollment.course_code for enrollment in student.enrollments]

    # Validate requirements
    result = await validate_requirements(
        student.program_code,
        completed,
        db
    )

    return result


@router.get("/{student_id}/recommendations")
async def get_course_recommendations(
    student_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get recommended courses for student."""
    student = await db.get(Student, student_id)
    completed = [enrollment.course_code for enrollment in student.enrollments]

    # Get next available courses
    available = await get_next_available_courses(
        student.program_code,
        completed,
        db
    )

    return {"recommendations": available[:10]}  # Top 10
```

## Error Handling

All service functions raise `ValueError` for invalid input:

```python
try:
    result = await check_prerequisites("INVALID_CODE", [], db)
except ValueError as e:
    print(f"Error: {e}")  # "Course 'INVALID_CODE' not found"
```

## Performance Considerations

1. **Database Queries:** Services use async/await and SQLAlchemy's efficient querying
2. **Caching:** Consider caching prerequisite trees and requirement validations
3. **Batch Operations:** When checking multiple courses, batch database queries
4. **Max Depth:** Prerequisite tree traversal limited to prevent infinite loops

## Future Enhancements

- [ ] Add caching layer for frequently-accessed prerequisite trees
- [ ] Implement "what-if" analysis (add/remove courses to see impact)
- [ ] Add conflict detection (time conflicts, workload analysis)
- [ ] Generate degree audit reports
- [ ] Add support for co-requisites (courses that must be taken together)
- [ ] Implement transfer credit evaluation
