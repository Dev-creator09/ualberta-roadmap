# FastAPI Testing Guide

## Setup Summary

✅ **Data Import**: 54 CMPUT courses and 7 programs imported successfully
✅ **Database**: PostgreSQL with Prisma schema
✅ **API**: FastAPI with SQLAlchemy async models
✅ **All Models**: Fixed and tested

## Running the API

```bash
cd apps/api
uvicorn main:app --reload --port 8000
```

## API Endpoints

### Health Check
```bash
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ualberta-roadmap-api",
  "version": "1.0.0"
}
```

### Courses Endpoints

#### 1. List All Courses (Paginated)
```bash
curl "http://127.0.0.1:8000/api/v1/courses?page=1&page_size=10"
```

Returns:
- `total`: Total number of courses (54)
- `page`: Current page
- `page_size`: Items per page
- `courses`: Array of course objects

#### 2. Filter Courses by Level
```bash
# Get all 400-level courses
curl "http://127.0.0.1:8000/api/v1/courses?level=400"

# Get all 300-level courses
curl "http://127.0.0.1:8000/api/v1/courses?level=300"
```

**Available levels**: 100, 200, 300, 400, 500

#### 3. Filter by Subject
```bash
curl "http://127.0.0.1:8000/api/v1/courses?subject=CMPUT"
```

#### 4. Filter by Term
```bash
curl "http://127.0.0.1:8000/api/v1/courses?term=Fall"
curl "http://127.0.0.1:8000/api/v1/courses?term=Winter"
```

**Available terms**: Fall, Winter, Spring, Summer

#### 5. Combined Filters
```bash
# 400-level courses offered in Fall
curl "http://127.0.0.1:8000/api/v1/courses?level=400&term=Fall"
```

#### 6. Get Single Course
```bash
curl "http://127.0.0.1:8000/api/v1/courses/CMPUT%20174"
curl "http://127.0.0.1:8000/api/v1/courses/CMPUT%20204"
```

Returns detailed course information including:
- Code, title, credits, description
- Level and subject
- Prerequisites (parsed)
- Terms typically offered

### Programs Endpoints

#### 1. List All Programs
```bash
curl http://127.0.0.1:8000/api/v1/programs
```

Returns all 7 programs:
- `honors-cs`: Honours Computing Science (72 credits)
- `honors-cs-ai`: Honours CS - AI Option (90 credits)
- `honors-cs-software`: Honours CS - Software Practice (93 credits)
- `major-cs`: Major in Computing Science (54 credits)
- `major-cs-ai`: Major in CS - AI Option (72 credits)
- `major-cs-software`: Major in CS - Software Practice (78 credits)
- `minor-cs`: Minor in Computing Science (24 credits)

#### 2. Get Single Program with Requirements
```bash
curl "http://127.0.0.1:8000/api/v1/programs/honors-cs-ai"
curl "http://127.0.0.1:8000/api/v1/programs/major-cs"
```

Returns:
- Program details (code, name, total credits)
- List of requirements with:
  - Requirement name and type (REQUIRED, CHOICE, LEVEL_REQUIREMENT, ELECTIVE)
  - Course lists
  - Credits needed
  - Level/subject filters

### Roadmap Endpoints (Stubs)

#### 1. Generate Roadmap
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/roadmap/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test-student",
    "program_code": "honors-cs-ai",
    "starting_year": 2024,
    "completed_courses": ["CMPUT 174", "CMPUT 175"]
  }'
```

#### 2. Validate Roadmap
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/roadmap/validate" \
  -H "Content-Type": application/json" \
  -d '{
    "roadmap_id": "test-roadmap-id"
  }'
```

#### 3. Check Requirements
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/roadmap/requirements/check" \
  -H "Content-Type: application/json" \
  -d '{
    "program_code": "honors-cs-ai",
    "completed_courses": ["CMPUT 174", "CMPUT 175", "CMPUT 204"]
  }'
```

## Testing Examples

### Example 1: Find AI-related courses
```bash
# Search for 400-level courses (likely advanced AI courses)
curl "http://127.0.0.1:8000/api/v1/courses?level=400" | jq '.courses[] | select(.code | contains("CMPUT")) | {code, title}'
```

### Example 2: Check program requirements
```bash
# Get AI option requirements
curl "http://127.0.0.1:8000/api/v1/programs/honors-cs-ai" | jq '.requirements[] | {name, requirement_type, courses}'
```

### Example 3: Pretty print course list
```bash
curl -s "http://127.0.0.1:8000/api/v1/courses?level=300&page_size=5" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); \
  [print(f\"{c['code']}: {c['title']}\") for c in data['courses']]"
```

## Database Statistics

- **Total Courses**: 54 CMPUT courses
- **Course Levels**:
  - 100-level: 5 courses
  - 200-level: 13 courses
  - 300-level: 20 courses
  - 400-level: 16 courses
- **Total Programs**: 7 (3 honors, 3 major, 1 minor)
- **Total Requirements**: 73 requirement groups across all programs

## Known Limitations

1. **Missing Non-CMPUT Courses**: The database only contains CMPUT courses. Math (MATH) and Statistics (STAT) courses referenced in program requirements are not imported yet.

2. **Roadmap Endpoints**: Currently return stub/mock data. Roadmap generation algorithm needs to be implemented.

3. **Authentication**: No authentication implemented yet. All endpoints are publicly accessible.

## Model Fixes Applied

1. ✅ Fixed database connection (using `roadmap` database)
2. ✅ Updated all SQLAlchemy models to use camelCase column mapping (matching Prisma schema)
3. ✅ Converted enum columns to String type (Prisma manages enum types)
4. ✅ Added type casting for enum comparisons in queries
5. ✅ Removed `.value` access on string fields in routers
6. ✅ Fixed Pydantic Settings ALLOWED_ORIGINS parsing

## Next Steps

1. **Implement Roadmap Generation**: Create algorithm in `app/routers/roadmap.py`
2. **Add Authentication**: Implement JWT-based auth
3. **Import Additional Courses**: Add MATH, STAT, and other department courses
4. **Add Tests**: Create pytest test suite
5. **Add Documentation**: Auto-generate OpenAPI docs

## Troubleshooting

If you encounter issues:

1. **500 Errors**: Restart the FastAPI server to reload code changes
   ```bash
   # Kill the server and restart
   uvicorn main:app --reload --port 8000
   ```

2. **No Data**: Ensure import scripts ran successfully
   ```bash
   cd packages/database
   pnpm run import:all
   ```

3. **Database Connection**: Check PostgreSQL is running
   ```bash
   # Should return 54
   psql postgresql://postgres:postgres@localhost:5433/roadmap \
     -c "SELECT COUNT(*) FROM courses"
   ```

## Success Indicators

✅ Health endpoint returns `{"status": "healthy"}`
✅ `/api/v1/courses` returns 54 total courses
✅ `/api/v1/courses?level=400` returns 16 courses
✅ `/api/v1/programs` returns 7 programs
✅ Single course/program endpoints return detailed data
