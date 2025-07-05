#!/usr/bin/env bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're in a virtual environment, but skip this check in CI environment
if [[ -z "${VIRTUAL_ENV:-}" ]] && [[ "${CI:-}" != "true" ]]; then
    print_message "$RED" "Error: Not in a virtual environment. Please activate your virtual environment first."
    exit 1
fi

# Parse command line arguments
FORMAT_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --format-only)
            FORMAT_ONLY=true
            shift
            ;;
        *)
            print_message "$RED" "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Detect platform-specific issues and apply fixes
print_message "$YELLOW" "Detecting platform..."
IS_WINDOWS=false
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    IS_WINDOWS=true
    print_message "$YELLOW" "Running on Windows, applying platform-specific fixes..."
    # Windows-specific fixes
    export PYTHONIOENCODING=utf-8  # Ensure proper encoding for Windows
fi

# Install development dependencies if not already installed
if ! python -m pip show ruff mypy pytest pytest-cov pytest-mock types-PyYAML >/dev/null 2>&1; then
    print_message "$YELLOW" "Installing development dependencies..."
    python -m pip install -e ".[dev]"
fi

# Make sure pre-commit is installed
if ! command_exists pre-commit; then
    print_message "$YELLOW" "Installing pre-commit..."
    python -m pip install pre-commit
fi

# Run formatting checks
print_message "$YELLOW" "Running formatting checks..."
if [[ "$FORMAT_ONLY" == "true" ]]; then
    print_message "$YELLOW" "Fixing formatting issues..."
    # Use pre-commit for formatting to match the pre-commit hook behavior
    if [[ "$IS_WINDOWS" == "true" ]]; then
        # On Windows, use python to run pre-commit directly
        python -m pre_commit run ruff --all-files || true
        python -m pre_commit run ruff-format --all-files || true
    else
        pre-commit run ruff --all-files || true
        pre-commit run ruff-format --all-files || true
    fi
    print_message "$GREEN" "Formatting fixed successfully!"
    exit 0
else
    # Check formatting using pre-commit to ensure consistency with pre-commit hook
    FORMAT_STATUS=0
    if [[ "$IS_WINDOWS" == "true" ]]; then
        python -m pre_commit run ruff --all-files --hook-stage push || FORMAT_STATUS=$?
        python -m pre_commit run ruff-format --all-files --hook-stage push || FORMAT_STATUS=$?
    else
        pre-commit run ruff --all-files --hook-stage push || FORMAT_STATUS=$?
        pre-commit run ruff-format --all-files --hook-stage push || FORMAT_STATUS=$?
    fi
    
    if [[ $FORMAT_STATUS -ne 0 ]]; then
        print_message "$YELLOW" "Formatting issues detected but continuing..."
    fi
fi

# Run linting checks and fix automatically
print_message "$YELLOW" "Running linting checks..."
LINT_STATUS=0
python -m ruff check . --ignore=E501 --fix || LINT_STATUS=$?
if [[ $LINT_STATUS -ne 0 ]]; then
    print_message "$YELLOW" "Linting issues detected but continuing..."
fi

# Run type checking
print_message "$YELLOW" "Running type checking..."
MYPY_STATUS=0
python -m mypy . --strict --ignore-missing-imports --disable-error-code=misc || MYPY_STATUS=$?
if [[ $MYPY_STATUS -ne 0 ]]; then
    print_message "$YELLOW" "Type checking issues detected but continuing..."
fi

# Run tests with coverage including integration tests
print_message "$YELLOW" "Running tests with coverage (including integration tests)..."
TEST_STATUS=0
# Use pytest configuration from pyproject.toml which includes coverage settings
python -m pytest tests/ || TEST_STATUS=$?

# Check test results
if [[ $TEST_STATUS -eq 0 ]]; then
    print_message "$GREEN" "All tests passed successfully!"
    exit 0
else
    print_message "$RED" "Some tests failed. Please fix the issues before pushing."
    exit 1
fi 