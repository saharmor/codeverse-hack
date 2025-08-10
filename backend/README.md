# CodeVerse Backend

Smart Code Planning with Claude Code - Backend API

## Quick Start

### Prerequisites

- Python 3.11 (managed by pyenv recommended)
- Make (for running development commands)

### Setup

1. **Complete setup in one command:**
   ```bash
   make setup
   ```

   This will:
   - Create a Python 3.11 virtual environment (`.venv`)
   - Install all dependencies (production + development)
   - Set up pre-commit hooks
   - Configure code quality tools

2. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Initialize the database:**
   ```bash
   make dev  # This will run setup_db.py if needed
   # OR manually:
   python setup_db.py
   ```

### Development Commands

```bash
# Show all available commands
make help

# Code quality
make quality      # Run all quality checks (format + lint + typecheck)
make format       # Format code with Black and isort
make lint         # Run flake8 linting
make typecheck    # Run mypy type checking

# Development
make dev          # Run development server
make test         # Run tests

# Environment
make venv-info    # Show virtual environment info
make clean        # Clean cache files and remove .venv
```

## Database

- **SQLite** database file: `codeverse.db`
- **Models**: Repository, Plan, PlanArtifact, ChatSession
- **ORM**: SQLAlchemy with async support
- **Setup**: `python setup_db.py` or `make dev`

## API Endpoints

- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- More endpoints will be added as development continues

## Code Quality

This project enforces high code quality standards:

- **Black**: Code formatting (120 char lines)
- **isort**: Import sorting
- **Flake8**: Linting and style checking
- **MyPy**: Static type checking
- **Pre-commit**: Git hooks for automatic quality checks

All quality checks run automatically on `git commit` via pre-commit hooks.

## Project Structure

```
backend/
├── .venv/                   # Virtual environment (auto-created)
├── .python-version          # Python version for pyenv
├── .pre-commit-config.yaml  # Pre-commit hooks
├── .flake8                  # Flake8 configuration
├── pyproject.toml           # Python project configuration
├── Makefile                 # Development commands
├── models/                  # Database models
├── config.py                # Configuration settings
├── database.py              # Database connection
├── main.py                  # FastAPI application
├── setup_db.py              # Database setup script
└── test_db.py               # Database test script
```

## Development Workflow

1. Make changes to code
2. Run `make quality` to check code quality
3. Run `make test` to run tests
4. Commit changes (pre-commit hooks will run automatically)

## Environment Management

The project uses:
- **pyenv** for Python version management (`.python-version`)
- **venv** for virtual environment isolation (`.venv/`)
- **pyproject.toml** for dependency management (PEP 518)

This provides a modern, standards-compliant Python development setup.
