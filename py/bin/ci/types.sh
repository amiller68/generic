#!/usr/bin/env bash

# Type checking script for the project using mypy

# Get project root (going up from py/bin/ci to root)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../.." && pwd )"

# Source shared utilities from project root
source "$PROJECT_ROOT/bin/utils"

# Parse arguments
STRICT_MODE=false
if [[ "$1" == "--strict" ]]; then
    STRICT_MODE=true
fi

if $STRICT_MODE; then
    print_header "Running MyPy in Strict Mode"
    
    echo "Type checking with strict settings..."
    uvx mypy "$PROJECT_ROOT/py/src" --strict
    check_result "MyPy strict check"
else
    print_header "Running MyPy Type Checker"
    
    echo "Type checking src directory..."
    uvx mypy "$PROJECT_ROOT/py/src"
    check_result "MyPy check"
fi

# Check if there's a mypy cache to report on
if [ -d "$PROJECT_ROOT/py/.mypy_cache" ]; then
    echo
    echo "MyPy cache exists (use 'rm -rf .mypy_cache' to clear if needed)"
fi

# Final summary
if $STRICT_MODE; then
    print_summary "All strict type checks passed!" "type check(s) failed"
else
    print_summary "All type checks passed!" "type check(s) failed"
fi
exit $?