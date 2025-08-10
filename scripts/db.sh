#!/bin/bash
#
# Database management script for CodeVerse
#
# This script provides convenient commands for managing the database with dummy data.
# It calls the Python script located in backend/tests/utils/populate_dummy_data.py
#
# Usage:
#     ./scripts/db.sh create    # Create dummy repositories and populate database
#     ./scripts/db.sh cleanup   # Clean up dummy repositories and database entries
#     ./scripts/db.sh reset     # Full reset (cleanup + create)
#     ./scripts/db.sh help      # Show this help message
#
# The script automatically handles virtual environment activation and runs from the correct directory.
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
PYTHON_SCRIPT="$BACKEND_DIR/tests/utils/populate_dummy_data.py"
VENV_DIR="$BACKEND_DIR/.venv"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show help
show_help() {
    echo "Database management script for CodeVerse"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  create    Create dummy repositories and populate database"
    echo "  cleanup   Clean up dummy repositories and database entries"
    echo "  reset     Full reset (cleanup then create)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 create     # Set up dummy data for development"
    echo "  $0 cleanup    # Remove all dummy data"
    echo "  $0 reset      # Fresh start with new dummy data"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if backend directory exists
    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "Backend directory not found at: $BACKEND_DIR"
        exit 1
    fi

    # Check if Python script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        print_error "Python script not found at: $PYTHON_SCRIPT"
        exit 1
    fi

    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        print_warning "Virtual environment not found at: $VENV_DIR"
        print_info "You may need to set up the virtual environment first"
        print_info "Run: cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    fi

    print_success "Prerequisites check completed"
}

# Function to run the Python script
run_python_script() {
    local action="$1"

    print_info "Changing to backend directory: $BACKEND_DIR"
    cd "$BACKEND_DIR"

    if [ -f "$VENV_DIR/bin/activate" ]; then
        print_info "Activating virtual environment..."
        source "$VENV_DIR/bin/activate"
        print_success "Virtual environment activated"
    else
        print_warning "Virtual environment not found, using system Python"
    fi

    print_info "Running: python tests/utils/populate_dummy_data.py $action"
    python tests/utils/populate_dummy_data.py "$action"

    if [ $? -eq 0 ]; then
        print_success "Command completed successfully"
    else
        print_error "Command failed"
        exit 1
    fi
}

# Main script logic
main() {
    local action="${1:-help}"

    case "$action" in
        "create"|"cleanup"|"reset")
            print_info "CodeVerse Database Management"
            print_info "Action: $action"
            echo ""

            check_prerequisites
            echo ""

            run_python_script "$action"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $action"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run the main function with all arguments
main "$@"
