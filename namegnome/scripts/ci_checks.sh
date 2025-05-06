#!/bin/bash

# CI check script for namegnome project
# This script can be run both locally and in the GitHub CI pipeline

set -e  # Exit immediately if a command exits with a non-zero status

echo "Running CI checks..."

# Check if format only flag is passed
FORMAT_ONLY=false
if [ "$1" == "--format-only" ]; then
  FORMAT_ONLY=true
fi

# Run ruff format
echo "Running ruff format..."
python -m ruff format .

# Run ruff linter with fixes
echo "Running ruff check..."
python -m ruff check . --fix

if [ "$FORMAT_ONLY" == "true" ]; then
  echo "Format-only mode, skipping further checks"
  exit 0
fi

# Run mypy type checker
echo "Running mypy..."
python -m mypy --strict --ignore-missing-imports --disable-error-code=misc src/namegnome tests/

# Run tests with coverage
echo "Running tests with coverage..."
python -m pytest --cov=namegnome tests/ --cov-fail-under=80

echo "All CI checks passed!"
exit 0 