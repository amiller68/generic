#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$PROJECT_DIR/data"
MIGRATIONS_DIR="$PROJECT_DIR/crates/app/migrations"
SEED_DIR="$PROJECT_DIR/crates/app/seed"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Derive DB name from branch
get_branch_name() {
    git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main"
}

sanitize() {
    echo "$1" | sed 's/[^a-zA-Z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//'
}

get_db_path() {
    echo "$DATA_DIR/app.db"
}

COMMAND=""
TAB_OUTPUT=false
SQL_QUERY=""
MIGRATION_NAME=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
    -t)
        TAB_OUTPUT=true
        shift
        ;;
    -n)
        MIGRATION_NAME="$2"
        shift 2
        ;;
    setup | reset | migrate | seed | query | info | clean | nuke)
        COMMAND="$1"
        shift
        if [[ "$COMMAND" == "query" && $# -gt 0 && ! "$1" =~ ^- ]]; then
            SQL_QUERY="$1"
            shift
        fi
        ;;
    *)
        echo "Unknown option: $1"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  setup    - Create data dir and run migrations for current branch"
        echo "  migrate  - Run pending migrations"
        echo "  seed     - Seed the database"
        echo "  reset    - Delete DB, recreate, migrate, and seed"
        echo "  clean    - Delete the current branch's database"
        echo "  query    - Run a SQL query against the current branch's database"
        echo "  info     - Show current database path and branch"
        echo "  nuke     - Delete ALL databases in data/"
        echo ""
        echo "Options:"
        echo "  -n NAME  - Migration name (for migrate command)"
        echo "  -t       - Tab-separated output (for query command)"
        exit 1
        ;;
    esac
done

if [[ -z "$COMMAND" ]]; then
    echo "Error: No command specified"
    echo "Usage: $0 [command] — run '$0 help' for details"
    exit 1
fi

DB_PATH=$(get_db_path)
DB_URL="sqlite://$DB_PATH"

case "$COMMAND" in
info)
    echo "Branch:   $(get_branch_name)"
    echo "Database: $DB_PATH"
    echo "URL:      $DB_URL"
    if [[ -f "$DB_PATH" ]]; then
        echo "Size:     $(du -h "$DB_PATH" | cut -f1)"
        echo ""
        echo "Tables:"
        sqlite3 "$DB_PATH" ".tables"
    else
        echo -e "${YELLOW}Database does not exist yet. Run: $0 setup${NC}"
    fi
    ;;
setup)
    echo "Setting up database..."
    mkdir -p "$DATA_DIR"
    # Migrations are run by the app on connect (sqlx::migrate!),
    # so we just need to start the app briefly or run seed which connects.
    echo "Running seed (which triggers migrations on connect)..."
    SQLITE_DATABASE_URL="$DB_URL" SEED_DIR="$SEED_DIR" \
        cargo run --bin seed --manifest-path "$PROJECT_DIR/Cargo.toml" -- all
    echo -e "${GREEN}Setup complete: $DB_PATH${NC}"
    ;;
migrate)
    echo "Creating migration..."
    if [[ -z "$MIGRATION_NAME" ]]; then
        echo "Error: migration name required. Use: $0 migrate -n <name>"
        exit 1
    fi
    TS=$(date -u +%Y%m%d%H%M%S)
    FILENAME="${TS}_${MIGRATION_NAME}.up.sql"
    touch "$MIGRATIONS_DIR/$FILENAME"
    echo -e "${GREEN}Created: $MIGRATIONS_DIR/$FILENAME${NC}"
    echo "Edit the file, then restart the app to apply."
    ;;
seed)
    echo "Seeding database..."
    mkdir -p "$DATA_DIR"
    SQLITE_DATABASE_URL="$DB_URL" SEED_DIR="$SEED_DIR" \
        cargo run --bin seed --manifest-path "$PROJECT_DIR/Cargo.toml" -- all
    echo -e "${GREEN}Seeding complete${NC}"
    ;;
reset)
    echo -e "${YELLOW}Resetting database: $DB_PATH${NC}"
    rm -f "$DB_PATH" "$DB_PATH-shm" "$DB_PATH-wal"
    echo "Running setup..."
    mkdir -p "$DATA_DIR"
    SQLITE_DATABASE_URL="$DB_URL" SEED_DIR="$SEED_DIR" \
        cargo run --bin seed --manifest-path "$PROJECT_DIR/Cargo.toml" -- all
    echo -e "${GREEN}Reset complete${NC}"
    ;;
clean)
    echo "Cleaning database: $DB_PATH"
    rm -f "$DB_PATH" "$DB_PATH-shm" "$DB_PATH-wal"
    echo -e "${GREEN}Cleaned${NC}"
    ;;
query)
    if [[ -z "$SQL_QUERY" ]]; then
        echo "Error: No SQL query provided"
        echo "Usage: $0 query \"SQL\" [-t]"
        echo ""
        echo "Examples:"
        echo "  $0 query \"SELECT * FROM users\""
        echo "  $0 query \".tables\""
        echo "  $0 query \"SELECT * FROM widgets LIMIT 5\" -t"
        exit 1
    fi
    if [[ ! -f "$DB_PATH" ]]; then
        echo -e "${RED}Database does not exist: $DB_PATH${NC}"
        echo "Run: $0 setup"
        exit 1
    fi
    if [[ "$TAB_OUTPUT" == "true" ]]; then
        sqlite3 -separator $'\t' "$DB_PATH" "$SQL_QUERY"
    else
        sqlite3 -header -column "$DB_PATH" "$SQL_QUERY"
    fi
    ;;
nuke)
    echo -e "${RED}Deleting ALL databases in $DATA_DIR${NC}"
    rm -f "$DATA_DIR"/*.db "$DATA_DIR"/*.db-shm "$DATA_DIR"/*.db-wal
    echo -e "${GREEN}All databases nuked${NC}"
    ;;
esac
