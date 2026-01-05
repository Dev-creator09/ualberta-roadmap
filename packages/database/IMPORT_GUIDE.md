# Data Import Guide

This guide explains how to import course and program data from JSON files into the database.

## Overview

The import system consists of three main scripts:

1. **import-courses.ts** - Imports courses from `course-data.json`
2. **import-programs.ts** - Imports programs and requirements from `degree-requirements.json`
3. **import-all.ts** - Orchestrates both imports in the correct order

## Quick Start

```bash
cd packages/database

# Import everything (recommended)
pnpm run import:all

# Or import individually
pnpm run import:courses
pnpm run import:programs
```

## JSON File Structure

### course-data.json

Located in the project root, this file contains an array of courses:

```json
{
  "courses": [
    {
      "code": "CMPUT 174",
      "title": "Introduction to the Foundations of Computation I",
      "credits": 3,
      "description": "Course description here",
      "prerequisites": ["CMPUT 101"],
      "typically_offered": ["Fall", "Winter"]
    }
  ]
}
```

#### Course Fields

- **code** (required): Unique course code (e.g., "CMPUT 174")
- **title** (required): Full course name
- **credits** (optional): Number of credits (default: 3)
- **description** (optional): Course description
- **prerequisites** (optional): See prerequisite structure below
- **typically_offered** (optional): Array of terms: ["Fall", "Winter", "Spring", "Summer"]

#### Prerequisite Structure

Prerequisites support both simple arrays and complex nested logic:

**Simple Array** (treated as AND):
```json
"prerequisites": ["CMPUT 174", "MATH 125"]
```

**Nested AND/OR Logic**:
```json
"prerequisites": {
  "type": "AND",
  "conditions": [
    { "type": "COURSE", "code": "CMPUT 204" },
    {
      "type": "OR",
      "conditions": [
        { "type": "COURSE", "code": "MATH 125" },
        { "type": "COURSE", "code": "MATH 127" }
      ]
    }
  ]
}
```

**Alternative Nested Format**:
```json
"prerequisites": {
  "type": "OR",
  "courses": ["CMPUT 174", "MATH 122"]
}
```

### degree-requirements.json

Located in the project root, this file contains an array of programs:

```json
{
  "programs": [
    {
      "id": "honors-cs",
      "name": "Honours Computing Science",
      "total_credits": 120,
      "requirements": [...],
      "special_rules": [...]
    }
  ]
}
```

#### Program Fields

- **id** (required): Unique program identifier (e.g., "honors-cs")
- **name** (required): Full program name
- **total_credits** (optional): Total credits required (default: 120)
- **requirements** (required): Array of requirement objects
- **special_rules** (optional): Array of special rules
- Additional fields like `min_credits`, `min_cmput_credits` are stored as JSONB

#### Requirement Structure

```json
{
  "name": "Core CS Foundation",
  "type": "required",
  "courses": ["CMPUT 174", "CMPUT 175", "CMPUT 201"],
  "credits_needed": 9,
  "order_index": 1
}
```

**Requirement Types:**

1. **required** - Must take all listed courses
   ```json
   {
     "name": "Core Required Courses",
     "type": "required",
     "courses": ["CMPUT 174", "CMPUT 175"],
     "credits_needed": 6
   }
   ```

2. **choice** - Choose N courses from a list
   ```json
   {
     "name": "Choose 2 Math Courses",
     "type": "choice",
     "choose_count": 2,
     "courses": ["MATH 125", "MATH 127", "MATH 225"],
     "credits_needed": 6
   }
   ```

3. **level_requirement** - Take X credits at certain levels
   ```json
   {
     "name": "Senior CMPUT Electives",
     "type": "level_requirement",
     "level_filter": ["300", "400"],
     "subject_filter": "CMPUT",
     "credits_needed": 18
   }
   ```

4. **elective** - Free electives
   ```json
   {
     "name": "General Electives",
     "type": "elective",
     "credits_needed": 12
   }
   ```

**Requirement Fields:**
- **name** (required): Requirement name
- **type** (required): One of: required, choice, level_requirement, elective
- **courses** (optional): Array of course codes
- **credits_needed** (optional): Minimum credits needed
- **choose_count** (optional): For "choice" type - how many courses to choose
- **level_filter** (optional): For "level_requirement" - array like ["300", "400"]
- **subject_filter** (optional): For "level_requirement" - subject code like "CMPUT"
- **order_index** (optional): Display order (default: 0)

#### Special Rules Structure

```json
"special_rules": [
  {
    "rule": "cmput-275-exclusion",
    "description": "Students who take CMPUT 275 cannot take CMPUT 201 for credit",
    "condition": {
      "if_course": "CMPUT 275",
      "then_exclude": ["CMPUT 201"],
      "replacement_required": {
        "subject": "CMPUT",
        "min_level": 200,
        "credits": 3
      }
    }
  }
]
```

## Import Scripts

### import:courses

Imports courses from `course-data.json`:

```bash
cd packages/database
pnpm run import:courses
```

**Features:**
- Extracts course level and subject from course code
- Parses prerequisite formulas (simple and nested)
- Uses upsert - safe to run multiple times
- Validates course code format
- Provides detailed progress logging

**Output:**
```
📚 Starting course import...

Found 20 courses to import

✓ Imported: CMPUT 174 - Introduction to the Foundations of Computation I
✓ Imported: CMPUT 175 - Introduction to the Foundations of Computation II
...

============================================================
📊 Import Summary:
============================================================
Total courses processed: 20
✅ Successfully imported: 18
🔄 Updated existing: 2
❌ Failed: 0
============================================================
```

### import:programs

Imports programs and requirements from `degree-requirements.json`:

```bash
cd packages/database
pnpm run import:programs
```

**Features:**
- Creates Program records
- Creates associated Requirement records
- Validates that referenced courses exist
- Deletes old requirements when updating programs
- Stores special rules as JSONB
- Uses upsert - safe to run multiple times
- Warns about missing course references

**Output:**
```
🎓 Starting program import...

Found 6 programs to import

Processing: Honours Computing Science (honors-cs)
  ✓ Created program: Honours Computing Science
  📋 Processing 11 requirements...
    ✓ Foundation CMPUT (required: 2 courses)
    ✓ Calculus I (choice: 4 courses)
    ...

============================================================
📊 Import Summary:
============================================================
Total programs processed: 6
✅ Successfully imported: 6
🔄 Updated existing: 0
❌ Failed: 0
📋 Requirements created: 64
⚠️  Missing course references: 3 (check warnings above)
============================================================
```

### import:all

Runs both imports in sequence:

```bash
cd packages/database
pnpm run import:all
```

**Order:**
1. Courses first (programs reference them)
2. Programs second

**Output:**
```
======================================================================
🚀 Starting complete data import
======================================================================

Step 1/2: Importing courses...
----------------------------------------------------------------------
[... course import output ...]

Step 2/2: Importing programs...
----------------------------------------------------------------------
[... program import output ...]

======================================================================
✨ Complete Import Summary
======================================================================
✅ Courses: SUCCESS
✅ Programs: SUCCESS
⏱️  Total time: 3.45s
======================================================================

🎉 All data imported successfully!
```

## Error Handling

### Missing Course References

If a program requirement references courses that don't exist in the database, you'll see warnings:

```
⚠️  Program "honors-cs", Requirement "Core CS Foundation":
    2 course(s) not found: CMPUT 399, CMPUT 499
```

**Resolution:**
1. Add the missing courses to `course-data.json`
2. Run `pnpm run import:courses` again
3. Re-run `pnpm run import:programs`

### Invalid Course Code Format

If a course code doesn't match the expected format (e.g., "CMPUT 174"):

```
❌ Failed to import course: INVALID123
    Error: Invalid course code format: INVALID123
```

**Resolution:**
- Ensure course codes follow the pattern: `SUBJECT NUMBER` (e.g., "CMPUT 174", "MATH 125")

### JSON Parse Errors

If the JSON file is malformed:

```
❌ Failed to parse JSON file
```

**Resolution:**
- Validate your JSON file structure
- Use a JSON validator or linter
- Check for missing commas, brackets, or quotes

### Database Connection Issues

If the database is not accessible:

```
❌ Error seeding database: Connection refused
```

**Resolution:**
1. Ensure PostgreSQL is running: `docker-compose ps postgres`
2. Check DATABASE_URL in `.env` file
3. Verify database credentials

## Idempotency

All import scripts are **idempotent** - they can be run multiple times safely:

- **Courses**: Uses `upsert` - creates new courses or updates existing ones
- **Programs**: Uses `upsert` for programs, deletes and recreates requirements
- **No data loss**: Existing data is updated, not duplicated

## Best Practices

### 1. Import Order

Always import courses before programs:
```bash
pnpm run import:all  # Handles order automatically
```

Or manually:
```bash
pnpm run import:courses
pnpm run import:programs
```

### 2. Validate JSON Files

Before importing, validate your JSON:
```bash
# Check JSON syntax
node -e "JSON.parse(require('fs').readFileSync('../../course-data.json', 'utf-8'))"
```

### 3. Backup Before Large Imports

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres ualberta_roadmap > backup.sql
```

### 4. Test with Small Dataset

When developing:
1. Create a small test JSON file
2. Import and verify
3. Expand to full dataset

### 5. Monitor Warnings

Pay attention to warnings about missing course references - they indicate data inconsistencies.

## Troubleshooting

### Import Fails Halfway

If an import fails partway through:
- The import will show which records succeeded/failed
- Re-running the import is safe (idempotent)
- Failed records will be retried

### Courses Not Showing Up

1. Check if the course was actually imported:
   ```bash
   pnpm run db:studio
   # Check the courses table
   ```

2. Verify the JSON structure is correct

3. Check for error messages in the import output

### Requirements Not Created

1. Ensure the program was created successfully
2. Check for course reference warnings
3. Verify requirement structure matches the schema

## Example: Complete Import Workflow

```bash
# 1. Navigate to database package
cd packages/database

# 2. Ensure database is running
cd ../..
docker-compose up -d postgres

# 3. Run migrations (if needed)
cd packages/database
pnpm run db:migrate

# 4. Generate Prisma client
pnpm run db:generate

# 5. Import all data
pnpm run import:all

# 6. Verify in Prisma Studio
pnpm run db:studio
```

## Updating Data

To update courses or programs:

1. Edit `course-data.json` or `degree-requirements.json`
2. Run the appropriate import script
3. The script will update existing records (upsert)

Example:
```bash
# Edit course-data.json to update CMPUT 174 description

# Re-import courses
cd packages/database
pnpm run import:courses

# ✓ Updated: CMPUT 174 - Introduction to the Foundations of Computation I
```

## Integration with Seed Script

The import scripts complement the seed script:

- **Seed script** (`db:seed`): Creates sample data for development
- **Import scripts** (`import:*`): Loads real data from JSON files

You can use either independently or together:

```bash
# Development: Use seed for quick setup
pnpm run db:seed

# Production: Use import for real data
pnpm run import:all
```

## Next Steps

After importing data:

1. **Verify in Prisma Studio:**
   ```bash
   pnpm run db:studio
   ```

2. **Query the data:**
   ```typescript
   import { prisma } from '@ualberta-roadmap/database'

   const courses = await prisma.course.findMany({
     where: { subject: 'CMPUT' },
     orderBy: { code: 'asc' }
   })
   ```

3. **Build API endpoints** to expose this data to your frontend

4. **Create validation logic** to check prerequisites and program requirements
