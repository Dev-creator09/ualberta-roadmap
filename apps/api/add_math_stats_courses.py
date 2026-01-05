"""
Add missing Math and Statistics courses to the database.

This script adds the Math and Stats courses referenced in degree requirements
but missing from the course database.
"""

import asyncio
from datetime import datetime
import uuid

from sqlalchemy import select
from app.db import get_db
from app.models import Course
from app.models.course import CourseLevel


# Math and Stats courses required by the degree programs
MATH_STATS_COURSES = [
    # Calculus I options
    {
        "code": "MATH 114",
        "title": "Elementary Calculus I",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Introduction to calculus. Limits, derivatives, and applications.",
        "typically_offered": ["Fall", "Winter", "Spring"],
    },
    {
        "code": "MATH 117",
        "title": "Honors Calculus I",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Honors version of MATH 114 with emphasis on theory.",
        "typically_offered": ["Fall"],
    },
    {
        "code": "MATH 134",
        "title": "Calculus for the Life Sciences I",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Calculus with biological applications.",
        "typically_offered": ["Fall", "Winter"],
    },
    {
        "code": "MATH 144",
        "title": "Calculus for the Physical Sciences I",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Calculus with physics applications.",
        "typically_offered": ["Fall", "Winter"],
    },
    {
        "code": "MATH 154",
        "title": "Calculus for Business and Economics I",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Calculus with business applications.",
        "typically_offered": ["Fall", "Winter"],
    },
    # Calculus II options
    {
        "code": "MATH 115",
        "title": "Elementary Calculus II",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Continuation of MATH 114. Integration and applications.",
        "typically_offered": ["Fall", "Winter", "Spring"],
    },
    {
        "code": "MATH 118",
        "title": "Honors Calculus II",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Honors version of MATH 115.",
        "typically_offered": ["Winter"],
    },
    {
        "code": "MATH 136",
        "title": "Calculus for the Life Sciences II",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Continuation of MATH 134.",
        "typically_offered": ["Winter"],
    },
    {
        "code": "MATH 146",
        "title": "Calculus for the Physical Sciences II",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Continuation of MATH 144.",
        "typically_offered": ["Winter"],
    },
    {
        "code": "MATH 156",
        "title": "Calculus for Business and Economics II",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Continuation of MATH 154.",
        "typically_offered": ["Winter"],
    },
    # Linear Algebra options
    {
        "code": "MATH 125",
        "title": "Linear Algebra I",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Systems of equations, matrices, determinants, vectors.",
        "typically_offered": ["Fall", "Winter", "Spring"],
    },
    {
        "code": "MATH 127",
        "title": "Honors Linear Algebra I",
        "credits": 3,
        "level": "100",
        "subject": "MATH",
        "description": "Honors version of MATH 125 with emphasis on proofs.",
        "typically_offered": ["Fall"],
    },
    # Statistics I options
    {
        "code": "STAT 151",
        "title": "Introduction to Applied Statistics I",
        "credits": 3,
        "level": "100",
        "subject": "STAT",
        "description": "Descriptive statistics, probability, distributions.",
        "typically_offered": ["Fall", "Winter", "Spring"],
    },
    {
        "code": "STAT 235",
        "title": "Statistics for Life Sciences",
        "credits": 3,
        "level": "200",
        "subject": "STAT",
        "description": "Statistical methods for biological sciences.",
        "typically_offered": ["Fall", "Winter"],
    },
    {
        "code": "STAT 265",
        "title": "Statistics for Business and Economics",
        "credits": 3,
        "level": "200",
        "subject": "STAT",
        "description": "Statistical methods for business applications.",
        "typically_offered": ["Fall", "Winter"],
    },
    # Statistics II options
    {
        "code": "STAT 252",
        "title": "Introduction to Applied Statistics II",
        "credits": 3,
        "level": "200",
        "subject": "STAT",
        "description": "Continuation of STAT 151. Hypothesis testing, regression.",
        "typically_offered": ["Fall", "Winter", "Spring"],
        "prerequisite_formula": {
            "type": "COURSE",
            "code": "STAT 151"
        }
    },
    {
        "code": "STAT 266",
        "title": "Statistical Inference for Business and Economics",
        "credits": 3,
        "level": "200",
        "subject": "STAT",
        "description": "Continuation of STAT 265.",
        "typically_offered": ["Winter"],
        "prerequisite_formula": {
            "type": "COURSE",
            "code": "STAT 265"
        }
    },
]


async def add_courses():
    """Add Math and Stats courses to database using raw SQL."""
    from sqlalchemy import text
    import json as json_lib

    added_count = 0
    skipped_count = 0

    async for db in get_db():
        try:
            for course_data in MATH_STATS_COURSES:
                # Check if course already exists
                result = await db.execute(
                    text("SELECT code FROM courses WHERE code = :code"),
                    {"code": course_data["code"]}
                )
                existing = result.first()

                if existing:
                    print(f"⏭️  Skipping {course_data['code']} (already exists)")
                    skipped_count += 1
                    continue

                # Prepare data
                course_id = str(uuid.uuid4())
                prereq_formula = course_data.get("prerequisite_formula")
                prereq_json = json_lib.dumps(prereq_formula) if prereq_formula else None

                # Use raw SQL with CAST to enum type
                sql = text("""
                    INSERT INTO courses
                    (id, code, title, credits, description, "prerequisiteFormula",
                     "typicallyOffered", level, subject, "createdAt", "updatedAt")
                    VALUES
                    (:id, :code, :title, :credits, :description, CAST(:prereq_formula AS json),
                     :typically_offered, CAST(:level AS "CourseLevel"), :subject, NOW(), NOW())
                """)

                await db.execute(sql, {
                    "id": course_id,
                    "code": course_data["code"],
                    "title": course_data["title"],
                    "credits": course_data["credits"],
                    "description": course_data["description"],
                    "prereq_formula": prereq_json,
                    "typically_offered": course_data["typically_offered"],
                    "level": course_data["level"],
                    "subject": course_data["subject"],
                })

                print(f"✅ Added {course_data['code']}: {course_data['title']}")
                added_count += 1

            # Commit all changes
            await db.commit()
            print(f"\n🎉 Successfully added {added_count} courses!")
            if skipped_count > 0:
                print(f"⏭️  Skipped {skipped_count} courses (already existed)")

            break  # Exit after first db session

        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("Adding Math and Statistics courses to database...\n")
    asyncio.run(add_courses())
    print("\n✨ Done! You can now generate roadmaps that include Math and Stats courses.")
