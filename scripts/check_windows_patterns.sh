#!/usr/bin/env bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Forbidden patterns (add more as needed)
PATTERNS=(
    '/tmp'
    'os\.path'
    '\\\\'
    'C:/'
    'C:\\'
)

# Files to check (all staged Python files)
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$' || true)

if [[ -z "$FILES" ]]; then
    exit 0
fi

EXIT_CODE=0

for pattern in "${PATTERNS[@]}"; do
    for file in $FILES; do
        if grep -E --color=always -n "$pattern" "$file" > /dev/null; then
            echo -e "${RED}Windows compatibility issue: Pattern '$pattern' found in $file:${NC}"
            grep -E --color=always -n "$pattern" "$file"
            EXIT_CODE=1
        fi
    done
done

if [[ $EXIT_CODE -ne 0 ]]; then
    echo -e "${YELLOW}Commit aborted due to Windows-incompatible patterns. Please fix the above issues.${NC}"
    exit $EXIT_CODE
fi

exit 0 