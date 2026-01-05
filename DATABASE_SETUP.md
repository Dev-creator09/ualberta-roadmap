# Database Setup Guide

This guide explains the database schema and how to set up and manage the database for the UAlberta Roadmap system.

## Schema Overview

The database is designed to support a comprehensive course planning system with the following key entities:

### Core Tables

#### 1. **Course** - Course Catalog
- Stores all available courses with metadata
- **Key fields:**
  - `code`: Unique course identifier (e.g., "CMPUT 174")
  - `title`: Full course name
  - `credits`: Number of credits (default 3)
  - `prerequisiteFormula`: JSON object with nested AND/OR logic for prerequisites
  - `typicallyOffered`: Array of terms when course is usually offered
  - `level`: Course level (100, 200, 300, 400, 500)
  - `subject`: Department code (CMPUT, MATH, STAT, etc.)

**Prerequisite Formula Example:**
```json
{
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

#### 2. **Program** - Degree Programs
- Defines academic programs (Honors CS, Specialization, etc.)
- **Key fields:**
  - `code`: Unique program identifier (e.g., "honors-cs")
  - `name`: Full program name
  - `totalCredits`: Total credits required for graduation
  - `requirements`: JSON with general program rules
  - `specialRules`: JSON with exclusions and substitutions

#### 3. **Requirement** - Program Requirements
- Defines specific requirements for each program
- **Types:**
  - `REQUIRED`: Must take all listed courses
  - `CHOICE`: Choose N courses from a list
  - `LEVEL_REQUIREMENT`: Take X credits at certain level(s)
  - `ELECTIVE`: Free electives
- **Key fields:**
  - `courses`: Array of course codes
  - `creditsNeeded`: Minimum credits to fulfill
  - `chooseCount`: For CHOICE type - how many to choose
  - `levelFilter`: Filter by course level (e.g., ["300", "400"])
  - `subjectFilter`: Filter by subject (e.g., "CMPUT")
  - `orderIndex`: Display order in UI

#### 4. **Student** - Student Records
- Student information and program enrollment
- Links to their program and roadmaps

#### 5. **Roadmap** - Student Degree Plans
- Represents a student's planned course schedule
- A student can have multiple roadmaps (different scenarios)
- Only one roadmap can be `isActive` at a time

#### 6. **RoadmapCourse** - Courses in a Roadmap
- Links courses to a specific roadmap with scheduling info
- **Key fields:**
  - `semester`: 1-8 (or more)
  - `year`: Academic year (1, 2, 3, 4)
  - `term`: FALL, WINTER, SPRING, SUMMER
  - `status`: PLANNED, IN_PROGRESS, COMPLETED, DROPPED, WAITLISTED
  - `satisfiesRequirements`: Array of requirement IDs this course fulfills

#### 7. **User** - Authentication
- User accounts for authentication (future expansion)
- Roles: STUDENT, ADVISOR, ADMIN

## Database Setup

### 1. Start Database Services

Using Docker (recommended):

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps

# Check logs if needed
docker-compose logs postgres
docker-compose logs redis
```

Or manually:
- PostgreSQL 16 on port 5433
- Redis 7 on port 6380

### 2. Configure Environment Variables

Copy the example files:

```bash
cp packages/database/.env.example packages/database/.env
cp apps/web/.env.example apps/web/.env
cp apps/api/.env.example apps/api/.env
```

Verify the DATABASE_URL in each `.env` file:
```
DATABASE_URL="postgresql://postgres:postgres@localhost:5433/ualberta_roadmap"
```

### 3. Generate Prisma Client

```bash
cd packages/database
pnpm run db:generate
```

This generates the TypeScript types and Prisma Client based on the schema.

### 4. Create Initial Migration

For a new database (first time setup):

```bash
cd packages/database

# Create and apply the initial migration
pnpm run db:migrate

# When prompted, name it: "init" or "initial_schema"
```

This will:
1. Create a migration file in `prisma/migrations/`
2. Apply the migration to your database
3. Create all tables, indexes, and relationships

### 5. Seed the Database

You have two options for populating the database:

#### Option A: Import from JSON Files (Recommended for Production)

Import real course and program data from JSON files:

```bash
cd packages/database

# Import all data (courses + programs)
pnpm run import:all

# Or import individually
pnpm run import:courses   # Import from course-data.json
pnpm run import:programs  # Import from degree-requirements.json
```

This will load:
- All courses from `course-data.json` in the project root
- All programs and requirements from `degree-requirements.json`
- Validates prerequisites and program requirements
- Safe to run multiple times (idempotent with upsert)

**📘 See [IMPORT_GUIDE.md](./IMPORT_GUIDE.md) for detailed import documentation**

#### Option B: Run Seed Script (For Development)

Populate with sample data for development:

```bash
cd packages/database
pnpm run db:seed
```

This will create:
- 13 sample courses (CMPUT, MATH, STAT)
- 2 programs (Honors CS, Specialization CS)
- 8 program requirements
- 1 sample student (Alice Johnson)
- 1 sample roadmap with planned courses
- 1 sample user account

## Database Commands Reference

### Generate Prisma Client
```bash
pnpm run db:generate
```
Run this whenever you modify the schema.

### Create Migration
```bash
pnpm run db:migrate
```
Creates a new migration file and applies it.

### Deploy Migrations (Production)
```bash
pnpm run db:migrate:deploy
```
Applies pending migrations without prompting.

### Push Schema (Development Only)
```bash
pnpm run db:push
```
Pushes schema changes directly without creating migration files. **Warning:** Can cause data loss.

### Open Prisma Studio
```bash
pnpm run db:studio
```
Opens a GUI database browser at http://localhost:5555

### Reset Database
```bash
pnpm run db:reset
```
**Warning:** Drops all data, recreates schema, and runs seed script.

### Seed Database
```bash
pnpm run db:seed
```
Runs the seed script to populate with sample data.

### Import from JSON Files
```bash
# Import all data
pnpm run import:all

# Import courses only
pnpm run import:courses

# Import programs only
pnpm run import:programs
```
Imports real course and program data from JSON files. Safe to run multiple times (idempotent).

## Schema Modifications

When you need to modify the schema:

1. **Edit the schema file:**
   ```bash
   # Edit packages/database/prisma/schema.prisma
   ```

2. **Generate updated client:**
   ```bash
   cd packages/database
   pnpm run db:generate
   ```

3. **Create migration:**
   ```bash
   pnpm run db:migrate
   # Name it descriptively: "add_course_ratings", "update_roadmap_status", etc.
   ```

4. **Update seed script if needed:**
   ```bash
   # Edit packages/database/src/seed.ts
   ```

## Indexes and Performance

The schema includes indexes on:
- All foreign keys (automatic)
- Course codes (`course.code`)
- Program codes (`program.code`)
- Student emails (`student.email`)
- Subject fields (`course.subject`)
- Course levels (`course.level`)
- Roadmap status fields (`roadmap.isActive`, `roadmapCourse.status`)

## Connecting from Applications

### Next.js (apps/web)

```typescript
import { prisma } from '@ualberta-roadmap/database'

// Use in API routes or server components
const courses = await prisma.course.findMany({
  where: { subject: 'CMPUT' },
  orderBy: { code: 'asc' }
})
```

### FastAPI (apps/api)

Use SQLAlchemy with the same database URL:
```python
from sqlalchemy import create_engine
from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL))
```

## Troubleshooting

### Migration Failed

```bash
# Reset and try again (development only)
pnpm run db:reset

# Or manually fix:
# 1. Drop the database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE ualberta_roadmap;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE ualberta_roadmap;"

# 2. Reapply migrations
cd packages/database
pnpm run db:migrate:deploy
```

### Prisma Client Out of Sync

```bash
cd packages/database
pnpm run db:generate
```

### Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U postgres -d ualberta_roadmap -c "SELECT 1;"
```

### Port Already in Use

If port 5433 is already in use, either:
1. Stop the conflicting service
2. Change the port in `docker-compose.yml` and update all `.env` files

## Production Considerations

1. **Environment Variables:**
   - Use strong passwords for `POSTGRES_PASSWORD`
   - Never commit `.env` files to version control

2. **Migrations:**
   - Always test migrations in staging first
   - Use `db:migrate:deploy` in production
   - Keep migration files in version control

3. **Backups:**
   ```bash
   # Backup
   docker-compose exec postgres pg_dump -U postgres ualberta_roadmap > backup.sql

   # Restore
   docker-compose exec -T postgres psql -U postgres ualberta_roadmap < backup.sql
   ```

4. **Connection Pooling:**
   - Use PgBouncer or similar for connection pooling
   - Configure Prisma connection limits in production

## Data Model Examples

### Creating a Course with Prerequisites

```typescript
await prisma.course.create({
  data: {
    code: 'CMPUT 301',
    title: 'Introduction to Software Engineering',
    credits: 3,
    prerequisiteFormula: {
      type: 'AND',
      conditions: [
        { type: 'COURSE', code: 'CMPUT 201' },
        { type: 'COURSE', code: 'CMPUT 204' }
      ]
    },
    typicallyOffered: ['Fall', 'Winter'],
    level: 'LEVEL_300',
    subject: 'CMPUT'
  }
})
```

### Creating a Student Roadmap

```typescript
const roadmap = await prisma.roadmap.create({
  data: {
    studentId: student.id,
    programId: program.id,
    name: 'Standard 4-Year Plan',
    isActive: true,
    roadmapCourses: {
      create: [
        {
          courseCode: 'CMPUT 174',
          semester: 1,
          year: 1,
          term: 'FALL',
          status: 'PLANNED',
          satisfiesRequirements: [requirementId]
        }
      ]
    }
  }
})
```

## Next Steps

After setting up the database:
1. Explore the data using Prisma Studio: `pnpm run db:studio`
2. Review the seed data to understand the structure
3. Start building API endpoints to interact with the data
4. Implement prerequisite validation logic
5. Build the roadmap generation algorithm
