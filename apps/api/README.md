# UAlberta Roadmap API

FastAPI backend for the University of Alberta course roadmap planning system.

## Features

- **RESTful API** for courses, programs, and roadmap management
- **Async/await** throughout for better performance
- **Type-safe** with Pydantic models and SQLAlchemy
- **Auto-generated documentation** with OpenAPI/Swagger
- **Error handling** with custom exception handlers
- **CORS support** for frontend integration
- **Database migrations** with Alembic

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy 2.0** - Async ORM
- **Pydantic v2** - Data validation
- **PostgreSQL** - Database (via asyncpg)
- **Redis** - Caching (future)
- **Python 3.11+** - Latest Python features

## Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 16 running (via Docker or locally)
- Virtual environment (recommended)

### Installation

```bash
cd apps/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Environment Setup

Create a `.env` file:

```bash
cp .env.example .env
```

Update the values:

```env
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5433/ualberta_roadmap"
REDIS_URL="redis://localhost:6380"
SECRET_KEY="your-secret-key-change-in-production"
DEBUG=True
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:3001"
```

### Running the Server

#### Development Mode

```bash
# Using uvicorn directly
uvicorn main:app --reload --port 8000

# Or using Python
python main.py
```

The API will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
- Health Check: http://localhost:8000/health

#### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check

```
GET /health
```

Returns API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "ualberta-roadmap-api",
  "version": "1.0.0"
}
```

### Courses

#### List Courses

```
GET /api/v1/courses
```

Get list of all courses with optional filtering.

**Query Parameters:**
- `subject` (optional): Filter by subject (e.g., CMPUT, MATH)
- `level` (optional): Filter by level (100, 200, 300, 400, 500)
- `term` (optional): Filter by term offered (Fall, Winter, Spring, Summer)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 100, max: 500)

**Example:**
```bash
curl "http://localhost:8000/api/v1/courses?subject=CMPUT&level=300"
```

**Response:**
```json
{
  "courses": [
    {
      "id": "clx123abc",
      "code": "CMPUT 301",
      "title": "Introduction to Software Engineering",
      "credits": 3,
      "description": "...",
      "prerequisite_formula": {...},
      "prerequisites_parsed": {...},
      "typically_offered": ["Fall", "Winter"],
      "level": "300",
      "subject": "CMPUT",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 100
}
```

#### Get Course Details

```
GET /api/v1/courses/{code}
```

Get detailed information about a specific course.

**Parameters:**
- `code`: Course code (e.g., "CMPUT 174")

**Example:**
```bash
curl "http://localhost:8000/api/v1/courses/CMPUT%20174"
```

**Response:**
```json
{
  "id": "clx123abc",
  "code": "CMPUT 174",
  "title": "Introduction to the Foundations of Computation I",
  "credits": 3,
  "description": "...",
  "prerequisite_formula": null,
  "prerequisites_parsed": null,
  "typically_offered": ["Fall", "Winter"],
  "level": "100",
  "subject": "CMPUT",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Programs

#### List Programs

```
GET /api/v1/programs
```

Get list of all degree programs.

**Example:**
```bash
curl "http://localhost:8000/api/v1/programs"
```

**Response:**
```json
{
  "programs": [
    {
      "id": "prog123",
      "code": "honors-cs",
      "name": "BSc Honours in Computing Science",
      "total_credits": 120,
      "requirements": {...},
      "special_rules": {...},
      "program_requirements": [...],
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 6
}
```

#### Get Program Details

```
GET /api/v1/programs/{code}
```

Get detailed information about a specific program including all requirements.

**Parameters:**
- `code`: Program code (e.g., "honors-cs")

**Example:**
```bash
curl "http://localhost:8000/api/v1/programs/honors-cs"
```

### Roadmap

#### Generate Roadmap

```
POST /api/v1/roadmap/generate
```

Generate a 4-year course roadmap based on program requirements and student preferences.

**Note:** This is currently a stub implementation that returns mock data.

**Request Body:**
```json
{
  "program_code": "honors-cs",
  "starting_year": 2024,
  "starting_term": "FALL",
  "completed_courses": ["CMPUT 174"],
  "preferences": {
    "specialization": "ai",
    "avoid_terms": ["SUMMER"]
  },
  "credit_load_preference": "STANDARD",
  "max_years": 4
}
```

**Response:**
```json
{
  "program_code": "honors-cs",
  "program_name": "BSc Honours in Computing Science",
  "semesters": [...],
  "requirement_progress": [...],
  "total_credits": 120,
  "credits_needed": 120,
  "warnings": [],
  "graduation_term": "Spring 2028",
  "is_valid": true
}
```

#### Validate Semester Schedule

```
POST /api/v1/roadmap/validate
```

Validate a proposed semester schedule for prerequisite and credit conflicts.

**Request Body:**
```json
{
  "program_code": "honors-cs",
  "semester_number": 1,
  "courses": ["CMPUT 174", "MATH 125", "ENGL 103"],
  "completed_courses": []
}
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "total_credits": 9,
  "prerequisite_issues": []
}
```

#### Check Requirements

```
POST /api/v1/roadmap/requirements/check
```

Check which program requirements a list of courses satisfies.

**Request Body:**
```json
{
  "program_code": "honors-cs",
  "courses": ["CMPUT 174", "CMPUT 175", "CMPUT 201", "MATH 125"]
}
```

**Response:**
```json
{
  "program_code": "honors-cs",
  "requirements": [...],
  "total_credits": 12,
  "satisfied_count": 1,
  "partial_count": 2
}
```

## Error Handling

The API uses standard HTTP status codes and returns consistent error responses:

### 404 Not Found

```json
{
  "error": "NotFoundError",
  "detail": "Course CMPUT 999 not found",
  "status_code": 404
}
```

### 422 Validation Error

```json
{
  "error": "ValidationError",
  "detail": "Request validation failed",
  "status_code": 422,
  "errors": [
    {
      "field": "program_code",
      "message": "field required",
      "type": "missing"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "error": "InternalServerError",
  "detail": "An internal server error occurred",
  "status_code": 500
}
```

## Development

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Database Migrations

The API uses Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## Project Structure

```
apps/api/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   └── exceptions.py      # Custom exceptions
│   ├── db.py                   # Database connection
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── course.py
│   │   ├── program.py
│   │   ├── roadmap.py
│   │   ├── student.py
│   │   └── user.py
│   ├── routers/                # API route handlers
│   │   ├── __init__.py
│   │   ├── courses.py
│   │   ├── programs.py
│   │   └── roadmap.py
│   └── schemas/                # Pydantic models
│       ├── __init__.py
│       ├── courses.py
│       ├── programs.py
│       └── roadmap.py
├── main.py                     # Application entry point
├── pyproject.toml              # Dependencies and config
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## Docker

### Build Image

```bash
docker build -t ualberta-api -f Dockerfile .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  ualberta-api
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

MIT
