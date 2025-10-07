#!/usr/bin/env bash

# Test script for running project tests

# Get project root (going up from py/bin/ci to root)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../.." && pwd )"

# Source shared utilities from project root
source "$PROJECT_ROOT/bin/utils"

# Default values
VERBOSE=false
SPECIFIC_TEST=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    --test=*)
      SPECIFIC_TEST="${1#*=}"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  -v, --verbose     Run tests with verbose output"
      echo "  --test=PATH       Run specific test file or directory"
      echo "  -h, --help        Show this help message"
      echo ""
      echo "Environment:"
      echo "  POSTGRES_URL      PostgreSQL connection URL (required)"
      echo ""
      echo "Example:"
      echo "  POSTGRES_URL=postgresql://user:pass@localhost:5432/db $0"
      echo "  POSTGRES_URL=\$(./bin/postgres.sh endpoint) $0 -v"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Setup PostgreSQL
print_header "Database Setup"

# Check if POSTGRES_URL is already set
if [ -n "$POSTGRES_URL" ]; then
    echo -e "${GREEN}✓ Using existing POSTGRES_URL${NC}"
    echo "  Database: $(echo $POSTGRES_URL | sed 's/postgresql:\/\/[^@]*@/postgresql:\/\/***@/')"
else
    # Try to get it from running container
    if ./bin/db.sh endpoint >/dev/null 2>&1; then
        export POSTGRES_URL=$(./bin/db.sh endpoint)
        echo -e "${GREEN}✓ Using running PostgreSQL container${NC}"
    else
        # Start PostgreSQL
        echo "Starting PostgreSQL container..."
        ./bin/db.sh up >/dev/null 2>&1
        check_result "PostgreSQL startup"
        
        # Get the endpoint
        export POSTGRES_URL=$(./bin/db.sh endpoint)
        echo -e "${GREEN}✓ Started new PostgreSQL container${NC}"
    fi
    echo "  Database: $(echo $POSTGRES_URL | sed 's/postgresql:\/\/[^@]*@/postgresql:\/\/***@/')"
fi

# Export for tools that expect DATABASE_URL
export DATABASE_URL="$POSTGRES_URL"

# Run database migrations
print_header "Running Database Migrations"
uv run alembic upgrade head
check_result "Database migrations"

# Build pytest command
PYTEST_CMD="uv run pytest"

# Add verbose flag if requested
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add specific test if provided
if [ -n "$SPECIFIC_TEST" ]; then
    PYTEST_CMD="$PYTEST_CMD $SPECIFIC_TEST"
else
    PYTEST_CMD="$PYTEST_CMD tests/"
fi

# Run tests
print_header "Running Tests"
echo "Command: $PYTEST_CMD"
echo ""

# Execute tests and capture result
if $PYTEST_CMD; then
    TEST_RESULT=0
else
    TEST_RESULT=1
fi

check_result "Test suite"

# Show coverage if available
if [ -f .coverage ]; then
    print_header "Coverage Report"
    uv run coverage report
fi

# Final summary
print_summary "All tests passed!" "test(s) failed"
exit $?