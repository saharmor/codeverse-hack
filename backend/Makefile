.PHONY: install format lint typecheck quality test clean dev

# Install dependencies
install:
	pip install -r requirements.txt

# Install development dependencies and pre-commit hooks
install-dev: install
	pre-commit install

# Format code with Black and isort
format:
	black .
	isort .

# Run linting checks
lint:
	flake8 .

# Run type checking
typecheck:
	mypy .

# Run all quality checks
quality: format lint typecheck

# Run tests (when added)
test:
	python -m pytest tests/ -v

# Clean up cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type d -name ".pytest_cache" -delete

# Run development server
dev:
	python run.py

# Run pre-commit on all files
pre-commit-all:
	pre-commit run --all-files