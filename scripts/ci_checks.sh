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

# Check if we're in a virtual environment
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
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

# Install development dependencies if not already installed
if ! pip show namegnome[dev] >/dev/null 2>&1; then
    print_message "$YELLOW" "Installing development dependencies..."
    pip install -e ".[dev]"
fi

# Run formatting checks
print_message "$YELLOW" "Running formatting checks..."
if [[ "$FORMAT_ONLY" == "true" ]]; then
    print_message "$YELLOW" "Fixing formatting issues..."
    ruff format .
    print_message "$GREEN" "Formatting fixed successfully!"
    exit 0
else
    ruff format . --check
    if [[ $? -ne 0 ]]; then
        print_message "$RED" "Formatting check failed. Run with --format-only to fix issues."
        exit 1
    fi
fi

# Run linting checks and fix automatically
print_message "$YELLOW" "Running linting checks..."
ruff check . --ignore=E501 --fix

# Run type checking
print_message "$YELLOW" "Running type checking..."
mypy . --strict --ignore-missing-imports --disable-error-code=misc

# Run tests with coverage
print_message "$YELLOW" "Running tests with coverage..."
pytest --cov=namegnome --cov-report=term-missing

# Check if all tests passed
if [[ $? -eq 0 ]]; then
    print_message "$GREEN" "All checks passed successfully!"
    exit 0
else
    print_message "$RED" "Some checks failed. Please fix the issues before pushing."
    exit 1
fi 