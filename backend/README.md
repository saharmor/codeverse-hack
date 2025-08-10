# CodeVerse Backend

FastAPI backend for the CodeVerse smart code planning application.

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Setup

Set up the SQLite database:

```bash
# Create database tables
python setup_db.py

# Test database setup
python test_db.py
```

### 3. Run the Backend

```bash
# Development server
python run.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

## Database

- **SQLite** database file: `codeverse.db`
- **Models**: Repository, Plan, PlanArtifact, ChatSession
- **ORM**: SQLAlchemy with async support
- **Migrations**: Alembic (to be added)

## API Endpoints

- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- More endpoints will be added as development continues

## Development

### Database Operations

- `setup_db.py` - Initialize/reset database
- `test_db.py` - Test database operations
- Models are defined in `models/` directory

### Project Structure

```
backend/
├── models/           # Database models
├── config.py         # Configuration settings
├── database.py       # Database connection
├── main.py          # FastAPI application
├── setup_db.py      # Database setup script
└── test_db.py       # Database test script
```