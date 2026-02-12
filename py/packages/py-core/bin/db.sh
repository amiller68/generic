#!/usr/bin/env bash
# Script to manage a local PostgreSQL container for development (Mac-optimized)

set -o errexit
set -o nounset

# NOTE (amiller68): points back to the project root
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../../.." && pwd )"
# py-core package root (where alembic.ini lives)
PY_CORE_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
# which lets us easily source utils
source "$PROJECT_ROOT/bin/utils"
source "$PROJECT_ROOT/bin/config"

if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Error: PROJECT_NAME is not set${NC}"
    exit 1
fi

POSTGRES_CONTAINER_NAME="${PROJECT_NAME}-postgres"
POSTGRES_VOLUME_NAME="${PROJECT_NAME}-postgres-data"
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_IMAGE_NAME=postgres:17
POSTGRES_DB="${PROJECT_NAME}"

# Check if docker or podman is available
CONTAINER_RUNTIME="docker"
if ! which docker &>/dev/null && which podman &>/dev/null; then
    CONTAINER_RUNTIME="podman"
fi

# Detect OS and set network flags accordingly
OS_TYPE=$(uname -s)
NETWORK_FLAGS=""
if [[ "$OS_TYPE" == "Linux" ]]; then
    NETWORK_FLAGS="--network host"
elif [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS uses bridge networking (default)
    NETWORK_FLAGS=""
fi

# Verify Docker/Podman is running
function check_runtime {
    if ! $CONTAINER_RUNTIME ps &>/dev/null; then
        echo -e "${RED}Error: $CONTAINER_RUNTIME is not running. Please start it first.${NC}"
        exit 1
    fi
}

# Start local PostgreSQL for development
function up {
    check_runtime

    print_header "Starting PostgreSQL"

    if ! $CONTAINER_RUNTIME ps | grep -q "$POSTGRES_CONTAINER_NAME"; then
        echo "Starting PostgreSQL container..."
        start_postgres_container

        # Wait for PostgreSQL to be ready
        echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
        sleep 3

        # Mac-specific: Verify network connectivity to container
        verify_connection

        echo ""
        echo -e "${GREEN}PostgreSQL started!${NC}"
        echo ""
        echo -e "${YELLOW}Set environment variables:${NC}"
        echo "  export POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
        echo ""
        echo -e "${YELLOW}Connection command:${NC}"
        echo "  psql postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
    elif ! $CONTAINER_RUNTIME ps | grep -q "$POSTGRES_CONTAINER_NAME.*Up"; then
        echo "Starting existing PostgreSQL container..."
        $CONTAINER_RUNTIME start $POSTGRES_CONTAINER_NAME
        sleep 3
        verify_connection
    else
        echo -e "${GREEN}PostgreSQL container is already running.${NC}"
        verify_connection
    fi
}

# Verify connection to PostgreSQL
function verify_connection {
    echo -e "${YELLOW}Verifying container status...${NC}"
    $CONTAINER_RUNTIME logs --tail 10 $POSTGRES_CONTAINER_NAME

    # Check if container has the expected listening port (PostgreSQL default is 5432 inside container)
    if ! $CONTAINER_RUNTIME exec $POSTGRES_CONTAINER_NAME pg_isready -U $POSTGRES_USER &>/dev/null; then
        echo -e "${YELLOW}Warning: PostgreSQL may not be listening properly inside the container.${NC}"
    fi

    echo "Testing connection from host to container..."
    if command -v pg_isready &>/dev/null; then
        if pg_isready -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER; then
            echo -e "${GREEN}Connection successful!${NC}"
        else
            echo -e "${RED}Connection test failed. See troubleshooting tips below.${NC}"
            show_troubleshooting
        fi
    else
        echo -e "${YELLOW}pg_isready not found. Install PostgreSQL client tools to test connectivity.${NC}"
        show_troubleshooting
    fi
}

# Helper function to show troubleshooting tips
function show_troubleshooting {
    echo ""
    print_header "Troubleshooting Tips for macOS"
    echo "1. Check Docker Desktop settings - ensure port forwarding is enabled"
    echo "2. Try restarting Docker Desktop completely"
    echo "3. Check if another service is using port $POSTGRES_PORT:"
    echo "   lsof -i :$POSTGRES_PORT"
    echo "4. Verify your Mac firewall settings allow Docker connections"
    echo "5. Try explicitly connecting with host.docker.internal instead of localhost:"
    echo "   export POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@host.docker.internal:${POSTGRES_PORT}/${POSTGRES_DB}"
    echo ""
}

# Create a database if it doesn't exist (for multi-worktree support)
function ensure_database {
    local db_name="${1:-$POSTGRES_DB}"

    echo -e "${YELLOW}Checking if database '$db_name' exists...${NC}"

    if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$db_name"; then
        echo -e "${YELLOW}Creating database '$db_name'...${NC}"
        PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER -c "CREATE DATABASE \"$db_name\";" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Database '$db_name' created successfully.${NC}"
        else
            echo -e "${RED}Failed to create database '$db_name'.${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}Database '$db_name' already exists.${NC}"
    fi
    return 0
}

# Helper functions for container management
function start_postgres_container {
    $CONTAINER_RUNTIME pull $POSTGRES_IMAGE_NAME

    if ! $CONTAINER_RUNTIME ps -a | grep $POSTGRES_CONTAINER_NAME &>/dev/null; then
        echo "Creating new PostgreSQL container..."
        $CONTAINER_RUNTIME volume create $POSTGRES_VOLUME_NAME || true

        # OS-optimized container settings
        $CONTAINER_RUNTIME run \
            --name $POSTGRES_CONTAINER_NAME \
            $NETWORK_FLAGS \
            --publish $POSTGRES_PORT:5432 \
            --volume $POSTGRES_VOLUME_NAME:/var/lib/postgresql/data \
            --env POSTGRES_USER=$POSTGRES_USER \
            --env POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
            --env POSTGRES_DB=$POSTGRES_DB \
            --env POSTGRES_HOST_AUTH_METHOD=trust \
            --health-cmd="pg_isready -U postgres" \
            --health-interval=5s \
            --health-timeout=5s \
            --health-retries=5 \
            --detach \
            $POSTGRES_IMAGE_NAME
    else
        echo "Starting existing PostgreSQL container..."
        $CONTAINER_RUNTIME start $POSTGRES_CONTAINER_NAME
    fi
}

function down {
    check_runtime
    print_header "Cleaning PostgreSQL Container"

    echo "Stopping PostgreSQL container..."
    $CONTAINER_RUNTIME stop $POSTGRES_CONTAINER_NAME 2>/dev/null || true
    check_result "Container stop"

    echo "Removing PostgreSQL container..."
    $CONTAINER_RUNTIME rm -f $POSTGRES_CONTAINER_NAME 2>/dev/null || true
    check_result "Container removal"

    echo "Removing PostgreSQL volume..."
    $CONTAINER_RUNTIME volume rm -f $POSTGRES_VOLUME_NAME 2>/dev/null || true
    check_result "Volume removal"

    print_summary "PostgreSQL cleaned up successfully!" "cleanup step(s) failed"
}

function endpoint {
    local db_name="${1:-$POSTGRES_DB}"
    check_runtime
    if $CONTAINER_RUNTIME ps -a | grep $POSTGRES_CONTAINER_NAME &>/dev/null; then
        echo "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${db_name}"
    else
        echo -e "${RED}PostgreSQL container is not running. Start it with: $0 up${NC}" >&2
        exit 1
    fi
}

function connect {
    psql "$(endpoint)"
}

function migrate {
    print_header "Running Database Migrations"

    # Check if POSTGRES_URL is set (using ${VAR:-} to handle unset variable with nounset)
    if [ -z "${POSTGRES_URL:-}" ]; then
        echo -e "${YELLOW}POSTGRES_URL environment variable is not set${NC}"
        echo -e "${YELLOW}Setting POSTGRES_URL environment variable to local container${NC}"
        export POSTGRES_URL=$(endpoint)
    fi

    echo "Using POSTGRES_URL: $POSTGRES_URL"

    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if command -v pg_isready &>/dev/null; then
            if pg_isready -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER &>/dev/null; then
                echo -e "${GREEN}Database is ready!${NC}"
                break
            fi
        else
            # Fallback if pg_isready is not available
            if $CONTAINER_RUNTIME exec $POSTGRES_CONTAINER_NAME pg_isready -U $POSTGRES_USER &>/dev/null 2>&1; then
                echo -e "${GREEN}Database is ready!${NC}"
                break
            fi
        fi

        if [ $attempt -eq $max_attempts ]; then
            echo -e "${RED}Database did not become ready in time${NC}"
            exit 1
        fi

        echo "Waiting... (attempt $attempt/$max_attempts)"
        sleep 1
        ((attempt++))
    done

    echo "Running migrations with Alembic..."

    # Check if uv command exists
    if ! command -v uv &>/dev/null; then
        echo -e "${RED}Error: 'uv' command not found. Please install uv first.${NC}"
        exit 1
    fi

    # Run the migrations with the environment variable explicitly passed
    # Alembic config is in py-core package root
    pushd "$PY_CORE_ROOT" > /dev/null
    POSTGRES_URL="$POSTGRES_URL" uv run alembic upgrade head
    popd > /dev/null
    check_result "Database migrations"

    print_summary "Migrations completed successfully!" "migration(s) failed"
}

function prepare {
    print_header "Preparing Database Migration"

    local manual=false
    local description=""

    # Check environment variable for manual flag
    if [ "${MANUAL:-}" = "1" ] || [ "${MANUAL:-}" = "true" ]; then
        manual=true
    fi

    # Parse arguments
    while [[ "$#" -gt 0 ]]; do
        case $1 in
        --manual)
            manual=true
            shift
            ;;
        *)
            # Concatenate all remaining arguments as the description
            description="$*"
            break
            ;;
        esac
    done

    # Check for description
    if [ -z "$description" ]; then
        echo -e "${RED}Error: Please provide a description for the migration.${NC}"
        echo "Usage: $0 prepare [--manual] <description>"
        echo "Example: $0 prepare 'Add user table'"
        echo "Example: $0 prepare --manual 'Custom migration for data cleanup'"
        exit 1
    fi

    # Start PostgreSQL if needed (for development)
    up
    export POSTGRES_URL=$(endpoint)
    echo -e "${YELLOW}Using local PostgreSQL for migration generation${NC}"

    # Check if uv command exists
    if ! command -v uv &>/dev/null; then
        echo -e "${RED}Error: 'uv' command not found. Please install uv first.${NC}"
        exit 1
    fi

    # Generate alembic migrations
    echo "Generating migration: $description"

    # Alembic config is in py-core package root
    pushd "$PY_CORE_ROOT" > /dev/null

    # Run alembic revision and capture output
    if [ "$manual" = true ]; then
        echo "Creating manual migration..."
        uv run alembic revision -m "$description"
    else
        echo "Auto-generating migration from model changes..."
        uv run alembic revision --autogenerate -m "$description"
    fi

    popd > /dev/null
    check_result "Migration generation"

    print_summary "Migration prepared successfully!" "migration preparation failed"
}

function status {
    check_runtime
    print_header "PostgreSQL Status"

    if $CONTAINER_RUNTIME ps | grep -q "$POSTGRES_CONTAINER_NAME"; then
        echo -e "${GREEN}PostgreSQL container is running.${NC}"
        echo ""
        echo -e "${YELLOW}Recent logs:${NC}"
        $CONTAINER_RUNTIME logs --tail 20 $POSTGRES_CONTAINER_NAME
        echo ""

        if command -v pg_isready &>/dev/null; then
            echo -e "${YELLOW}Connection status:${NC}"
            if pg_isready -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER; then
                echo -e "${GREEN}Connection active${NC}"
            else
                echo -e "${RED}Connection failed${NC}"
            fi
        fi
    else
        echo -e "${RED}PostgreSQL container is not running.${NC}"
        echo ""
        echo "Start it with: $0 up"
    fi
}

function wipe {
    local db_name="${1:-$POSTGRES_DB}"

    check_runtime
    print_header "Wiping Database"

    echo -e "${YELLOW}Dropping database '$db_name'...${NC}"

    # Check if database exists first
    if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$db_name"; then
        echo -e "${YELLOW}Database '$db_name' does not exist.${NC}"
        return 0
    fi

    # Terminate existing connections to the database
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$db_name' AND pid <> pg_backend_pid();" 2>/dev/null || true

    # Drop the database
    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER -c "DROP DATABASE \"$db_name\";" 2>/dev/null; then
        echo -e "${GREEN}Database '$db_name' dropped successfully.${NC}"
    else
        echo -e "${RED}Failed to drop database '$db_name'.${NC}"
        return 1
    fi

    print_summary "Database wiped successfully!" "wipe failed"
}

function help {
    echo -e "${YELLOW}PostgreSQL Container Manager & Database Tools${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Container Management Commands:"
    echo "  up                 - Start a local PostgreSQL container for development"
    echo "  down               - Remove the PostgreSQL container and volume"
    echo "  endpoint           - Print the PostgreSQL connection URL"
    echo "    [database_name]  - Optional database name (defaults to ${PROJECT_NAME})"
    echo "  connect            - Connect to the postgres instance"
    echo "  status             - Check container status and connection"
    echo "  ensure_database    - Create a database if it doesn't exist"
    echo "    <database_name>  - Name of database to create (for multi-worktree support)"
    echo "  wipe               - Drop a database (keeps container running)"
    echo "    [database_name]  - Optional database name (defaults to ${PROJECT_NAME})"
    echo ""
    echo "Migration Commands:"
    echo "  migrate            - Run database migrations (auto-starts local DB if needed)"
    echo "  prepare            - Create a new migration"
    echo "    [--manual] <description>"
    echo "                     - Use --manual for manual migration (no auto-generate)"
    echo ""
    echo "  help               - Show this help message"
    echo ""
    echo "For production, set the POSTGRES_URL environment variable."
}

# Process command
CMD=${1:-help}
shift || true  # Shift to remove command from arguments

# NOTE (amiller68): these cannot conflict with
#  our make directives
case "$CMD" in
up | down | endpoint | connect | status | help | migrate | prepare | ensure_database | wipe)
    $CMD "$@"
    ;;
*)
    echo -e "${RED}Unknown command: $CMD${NC}"
    help
    exit 1
    ;;
esac
