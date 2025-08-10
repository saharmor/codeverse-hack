.PHONY: help setup install install-dev format lint typecheck quality test clean dev pre-commit-all venv-info

# Default target
help:
	@echo "CodeVerse Backend Development Setup"
	@echo ""
	@echo "Available targets:"
	@echo "  setup        - Complete setup (Python, venv, dependencies, pre-commit)"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies and pre-commit hooks"
	@echo "  format       - Format code with Black and isort"
	@echo "  lint         - Run linting checks with flake8"
	@echo "  typecheck    - Run type checking with mypy"
	@echo "  quality      - Run all quality checks (format + lint + typecheck)"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean up cache files"
	@echo "  dev          - Run development server"
	@echo "  venv-info    - Show virtual environment information"

# Python and virtual environment setup
VENV_NAME = .venv
VENV_BIN = $(VENV_NAME)/bin
PYTHON = $(VENV_BIN)/python
PIP = $(VENV_BIN)/pip

# Check if we're in a virtual environment
venv-info:
	@echo "Virtual Environment Information:"
	@echo "VIRTUAL_ENV: $(VIRTUAL_ENV)"
	@if [ -d "$(VENV_NAME)" ]; then \
		echo "Local venv exists: $(VENV_NAME)"; \
		echo "Python version: $$($(PYTHON) --version 2>/dev/null || echo 'Not available')"; \
	else \
		echo "Local venv does not exist: $(VENV_NAME)"; \
	fi

# Create virtual environment if it doesn't exist
$(VENV_NAME):
	@echo "Creating virtual environment..."
	python3.11 -m venv $(VENV_NAME)
	@echo "Upgrading pip..."
	$(PIP) install --upgrade pip

# Complete setup from scratch
setup: $(VENV_NAME) install-dev
	@echo "✅ Setup complete! Activate with: source $(VENV_BIN)/activate"

# Install production dependencies
install: $(VENV_NAME)
	@echo "Installing production dependencies..."
	$(PIP) install -r requirements.txt

# Install development dependencies and setup pre-commit
install-dev: $(VENV_NAME)
	@echo "Installing all dependencies..."
	$(PIP) install -r requirements.txt
	@echo "Setting up pre-commit hooks..."
	$(VENV_BIN)/pre-commit install

# Format code with Black and isort
format: $(VENV_NAME)
	$(VENV_BIN)/black .
	$(VENV_BIN)/isort .

# Run linting checks
lint: $(VENV_NAME)
	$(VENV_BIN)/flake8 .

# Run type checking
typecheck: $(VENV_NAME)
	$(VENV_BIN)/mypy .

# Run all quality checks
quality: format lint typecheck

# Run tests
test: $(VENV_NAME)
	$(PYTHON) -m pytest tests/ -v

# Clean up cache files and virtual environment
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	@if [ -d "$(VENV_NAME)" ]; then \
		echo "Removing virtual environment..."; \
		rm -rf $(VENV_NAME); \
	fi

# Run development server
dev: $(VENV_NAME)
	$(PYTHON) run.py

# Run pre-commit on all files
pre-commit-all: $(VENV_NAME)
	$(VENV_BIN)/pre-commit run --all-files
