# UAlberta Roadmap

An AI-powered course planning and recommendation system for University of Alberta Computing Science students.

## Features

- **AI-Powered Roadmap Generation**: Get personalized semester-by-semester course recommendations using GPT-4
- **Smart Course Selection**: Balance CS requirements with breadth courses and electives
- **Interest-Based Recommendations**: Tailored course suggestions based on your specialization (AI, Software Engineering, etc.)
- **Prerequisite Tracking**: Automatic validation of course prerequisites
- **Interactive Planning**: Mark courses as completed and visualize your degree progress
- **Realistic Workload**: Balanced semesters with appropriate credit loads

## Project Structure

```
ualberta-roadmap/
├── apps/
│   ├── api/          # FastAPI backend
│   │   ├── app/
│   │   │   ├── models/      # Database models
│   │   │   ├── routers/     # API endpoints
│   │   │   ├── services/    # Business logic
│   │   │   └── schemas/     # Pydantic schemas
│   │   └── tests/
│   └── web/          # Next.js frontend
│       ├── app/             # App router pages
│       ├── components/      # React components
│       └── lib/            # Utilities and API client
└── packages/         # Shared packages (if any)
```

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Database for courses and programs
- **SQLAlchemy**: ORM with async support
- **OpenAI GPT-4**: AI-powered roadmap generation
- **Redis**: Caching layer

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **shadcn/ui**: UI components
- **Zustand**: State management
- **React Query**: Data fetching

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis
- OpenAI API key

### Backend Setup

1. Navigate to the API directory:
```bash
cd apps/api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create `.env` file):
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/roadmap
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002
```

5. Run database migrations and seed data:
```bash
# Run the database initialization
python -m app.db
```

6. Start the API server:
```bash
uvicorn main:app --reload --port 8000
```

API will be available at `http://localhost:8000`
- Docs: `http://localhost:8000/api/v1/docs`

### Frontend Setup

1. Navigate to the web directory:
```bash
cd apps/web
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables (create `.env.local` file):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

4. Start the development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Usage

1. **Select Your Program**: Choose from available CS programs (Honors CS, Major CS, etc.)
2. **Add Completed Courses**: Mark any courses you've already taken
3. **Set Preferences**: Indicate your specialization interests and credit load preference
4. **Generate Roadmap**: Get an AI-generated semester-by-semester course plan
5. **Review and Adjust**: View your personalized roadmap with course recommendations

## API Endpoints

- `GET /api/v1/programs` - List all available programs
- `GET /api/v1/courses` - List courses with filtering
- `POST /api/v1/roadmap/generate` - Generate AI-powered roadmap
- `POST /api/v1/roadmap/validate` - Validate a semester schedule

## Development

### Running Tests

Backend:
```bash
cd apps/api
pytest
```

Frontend:
```bash
cd apps/web
npm test
```

### Code Quality

Backend:
```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

Frontend:
```bash
# Lint
npm run lint

# Type check
npm run type-check
```

## Contributing

This is a student project for UAlberta CS students. Contributions are welcome!

## Disclaimer

This is an unofficial tool for UAlberta Computing Science students. Always verify your course plan with an academic advisor before registering for courses.

## License

MIT License
