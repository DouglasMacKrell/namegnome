#!/usr/bin/env bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message "$BLUE" "========== Windows Test Debug Helper =========="
print_message "$YELLOW" "This script helps debug Windows-specific test issues"

# Check if we're on Windows
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" && "$OSTYPE" != "cygwin" ]]; then
    print_message "$YELLOW" "Not running on Windows. This script is primarily for Windows debugging."
    print_message "$YELLOW" "Continuing anyway to check for potential cross-platform issues..."
fi

# Make sure we have the required dependencies
print_message "$YELLOW" "Checking dependencies..."
if ! python -m pip show pytest pytest-cov pytest-mock types-PyYAML >/dev/null 2>&1; then
    print_message "$YELLOW" "Installing test dependencies..."
    python -m pip install -e ".[dev]"
fi

# Run specific tests with verbose output to debug path issues
print_message "$BLUE" "Running tests with extra verbosity to debug path issues..."
python -m pytest -vv --no-header --showlocals tests/utils/test_plan_store.py

# Test path handling 
print_message "$BLUE" "Testing platform-specific path handling..."
python -c "
import os
from pathlib import Path
print(f'Current platform: {os.name}')
print(f'Path separator: {os.path.sep}')
print(f'Current working directory: {os.getcwd()}')
test_path = Path('/test/path')
print(f'Unix path conversion: {test_path}')
abs_path = Path(test_path).absolute()
print(f'Absolute path: {abs_path}')
"

# Test symlink capability
print_message "$BLUE" "Testing symlink capabilities..."
TEMP_DIR=$(mktemp -d)
touch "${TEMP_DIR}/source.txt"

print_message "$YELLOW" "Attempting to create a symlink..."
if ln -s "${TEMP_DIR}/source.txt" "${TEMP_DIR}/link.txt" 2>/dev/null; then
    print_message "$GREEN" "Symlink created successfully!"
else
    print_message "$RED" "Failed to create symlink. This might cause issues with plan_store tests."
    print_message "$YELLOW" "On Windows, this requires admin privileges or Developer Mode enabled."
fi

# Clean up
rm -rf "${TEMP_DIR}"

print_message "$BLUE" "========== Debug Report Complete =========="