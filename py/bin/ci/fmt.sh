#!/usr/bin/env bash

# Formatting script for the project using black

# Get project root (going up from py/bin/ci to root)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../.." && pwd )"

# Source shared utilities from project root
source "$PROJECT_ROOT/bin/utils"

# Parse arguments
CHECK_ONLY=false
if [[ "$1" == "--check" ]]; then
    CHECK_ONLY=true
fi

if $CHECK_ONLY; then
    print_header "Running Formatters in Check Mode"
    
    echo "Checking black formatting..."
    uvx black "$PROJECT_ROOT/py/src" "$PROJECT_ROOT/py/tests" --line-length 88 --check
    check_result "Black check"
else
    print_header "Running Code Formatters"
    
    echo "Formatting with black..."
    uvx black "$PROJECT_ROOT/py/src" "$PROJECT_ROOT/py/tests" --line-length 88
    check_result "Black format"
fi

# Final summary
if $CHECK_ONLY; then
    print_summary "All formatting checks passed!" "formatter(s) failed"
else
    print_summary "All formatting completed successfully!" "formatter(s) failed"
fi
exit $?