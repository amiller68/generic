#!/usr/bin/env bash
# Script to seed the database with initial data

set -o errexit
set -o nounset

PY_CORE_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../../.." && pwd )"
source "$PROJECT_ROOT/bin/utils"
source "$PROJECT_ROOT/bin/config"

# Default values
TARGET="all"
DRY_RUN=false

function usage {
    echo "Usage: $0 [options] [target]"
    echo ""
    echo "Targets:"
    echo "  all       Seed all data (default)"
    echo "  users     Seed users only"
    echo "  widgets   Seed widgets only"
    echo ""
    echo "Options:"
    echo "  --dry-run  Show what would be seeded without making changes"
    echo "  -h, --help Show this help message"
    echo ""
    echo "Configuration:"
    echo "  Seed data is defined in:"
    echo "    ${PY_CORE_ROOT}/seed/users.yaml"
    echo "    ${PY_CORE_ROOT}/seed/widgets.yaml"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        all|users|widgets)
            TARGET=$1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

echo "=== Database Seeding ==="

# Ensure POSTGRES_URL is set
if [ -z "${POSTGRES_URL:-}" ]; then
    echo "POSTGRES_URL not set, using local container default"
    export POSTGRES_URL="postgresql://postgres:postgres@localhost:5432/${PROJECT_NAME}"
fi

echo "Target: $TARGET"
echo "Database: $POSTGRES_URL"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "Dry run mode - no changes will be made"
    echo ""
fi

# Run the seeder
pushd "$PY_CORE_ROOT" > /dev/null
if [ "$DRY_RUN" = true ]; then
    uv run python -m py_core.seed.cli --target "$TARGET" --dry-run
else
    uv run python -m py_core.seed.cli --target "$TARGET"
fi
EXIT_CODE=$?
popd > /dev/null

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Seeding completed successfully!"
else
    echo ""
    echo "Seeding failed!"
    exit $EXIT_CODE
fi
