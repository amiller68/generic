#!/usr/bin/env bash
# Script to manage a local PostgreSQL container for development (Mac-optimized)
# TODO (amiller68): on a rainy day, i'd love
#  to move this into a nested dir

set -o errexit
set -o nounset

# NOTE (amiller68): points back to the project root
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
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

    # Check if container has the expected listening port
    if ! $CONTAINER_RUNTIME exec $POSTGRES_CONTAINER_NAME netstat -an | grep -q "LISTEN.*:5432"; then
        echo -e "${YELLOW}Warning: PostgreSQL may not be listening properly inside the container.${NC}"
    fi

    echo "Testing connection from host to container..."
    if command -v pg_isready &>/dev/null; then
        if pg_isready -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER; then
            echo -e "${GREEN}✅ Connection successful!${NC}"
        else
            echo -e "${RED}⚠️ Connection test failed. See troubleshooting tips below.${NC}"
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

# Helper functions for container management
function start_postgres_container {
    $CONTAINER_RUNTIME pull $POSTGRES_IMAGE_NAME

    if ! $CONTAINER_RUNTIME ps -a | grep $POSTGRES_CONTAINER_NAME &>/dev/null; then
        echo "Creating new PostgreSQL container..."
        $CONTAINER_RUNTIME volume create $POSTGRES_VOLUME_NAME || true

        # Mac-optimized container settings
        $CONTAINER_RUNTIME run \
            --name $POSTGRES_CONTAINER_NAME \
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
    check_runtime
    if $CONTAINER_RUNTIME ps -a | grep $POSTGRES_CONTAINER_NAME &>/dev/null; then
        echo "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
    else
        echo -e "${RED}PostgreSQL container is not running. Start it with: $0 run${NC}" >&2
        exit 1
    fi
}

function connect {
    psql ""$(./bin/postgres.sh endpoint)""
}

function migrate {
    print_header "Running Database Migrations"

    # Check if POSTGRES_URL is set (using ${VAR:-} to handle unset variable with nounset)
    if [ -z "${POSTGRES_URL:-}" ]; then
        echo -e "${YELLOW}POSTGRES_URL environment variable is not set${NC}"
        echo -e "${YELLOW}Setting POSTGRES_URL environment variable to local container${NC}"
        export POSTGRES_URL=$(endpoint)
    fi

    echo "Running migrations with Alembic..."

    # Check if uv command exists
    if ! command -v uv &>/dev/null; then
        echo -e "${RED}Error: 'uv' command not found. Please install uv first.${NC}"
        exit 1
    fi

    # Run the migrations
    uv run alembic upgrade head
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

    # Run alembic revision and capture output
    if [ "$manual" = true ]; then
        echo "Creating manual migration..."
        uv run alembic revision -m "$description"
    else
        echo "Auto-generating migration from model changes..."
        uv run alembic revision --autogenerate -m "$description"
    fi

    check_result "Migration generation"

    print_summary "Migration prepared successfully!" "migration preparation failed"
}

function status {
    check_runtime
    print_header "PostgreSQL Status"

    if $CONTAINER_RUNTIME ps | grep -q "$POSTGRES_CONTAINER_NAME"; then
        echo -e "${GREEN}✓ PostgreSQL container is running.${NC}"
        echo ""
        echo -e "${YELLOW}Recent logs:${NC}"
        $CONTAINER_RUNTIME logs --tail 20 $POSTGRES_CONTAINER_NAME
        echo ""

        if command -v pg_isready &>/dev/null; then
            echo -e "${YELLOW}Connection status:${NC}"
            if pg_isready -h localhost -p $POSTGRES_PORT -U $POSTGRES_USER; then
                echo -e "${GREEN}✓ Connection active${NC}"
            else
                echo -e "${RED}✗ Connection failed${NC}"
            fi
        fi
    else
        echo -e "${RED}✗ PostgreSQL container is not running.${NC}"
        echo ""
        echo "Start it with: $0 run"
    fi
}

function help {
    echo -e "${YELLOW}PostgreSQL Container Manager & Database Tools${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Container Management Commands:"
    echo "  up                 - Start a local PostgreSQL container for development"
    echo "  down               - Remove the PostgreSQL container and volume"
    echo "  endpoint           - Print the PostgreSQL connection URLs"
    echo "  connect            - Connect to the postgres instance"
    echo "  status             - Check container status and connection"
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
up | down | endpoint | connect | status | help | migrate | prepare)
    $CMD "$@"
    ;;
*)
    echo -e "${RED}Unknown command: $CMD${NC}"
    help
    exit 1
    ;;
esac
