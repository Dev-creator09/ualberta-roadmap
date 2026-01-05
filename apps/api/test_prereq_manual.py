"""
Manual test of prerequisite service.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_session, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db import async_engine
from app.services.prerequisite_service import check_prerequisites, get_prerequisite_tree

async def test_prereqs():
    # Create async session
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        print("=" * 60)
        print("Test 1: Check CMPUT 365 prerequisites")
        print("=" * 60)
        
        # CMPUT 365 requires: (CMPUT 175 or 275) AND (CMPUT 267 or 466 or STAT 265)
        
        # Student has completed nothing
        result = await check_prerequisites("CMPUT 365", [], db)
        print(f"\nWith no courses completed:")
        print(f"  Can take: {result['is_valid']}")
        print(f"  Missing: {result['missing_courses']}")
        
        # Student has CMPUT 175
        result = await check_prerequisites("CMPUT 365", ["CMPUT 175"], db)
        print(f"\nWith CMPUT 175 completed:")
        print(f"  Can take: {result['is_valid']}")
        print(f"  Missing: {result['missing_courses']}")
        
        # Student has CMPUT 175 and STAT 265
        result = await check_prerequisites("CMPUT 365", ["CMPUT 175", "STAT 265"], db)
        print(f"\nWith CMPUT 175 and STAT 265 completed:")
        print(f"  Can take: {result['is_valid']}")
        print(f"  Missing: {result['missing_courses']}")
        
        print("\n" + "=" * 60)
        print("Test 2: Get prerequisite tree for CMPUT 365")
        print("=" * 60)
        
        tree = await get_prerequisite_tree("CMPUT 365", db)
        print(f"\nPrerequisite tree:")
        import json
        print(json.dumps(tree, indent=2))

if __name__ == "__main__":
    asyncio.run(test_prereqs())
