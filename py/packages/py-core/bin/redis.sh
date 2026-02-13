#!/usr/bin/env bash
# Script to manage a local Redis container for development (Mac-optimized)

set -o errexit
set -o nounset

# NOTE (amiller68): points back to the project root
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../../.." && pwd )"
# which lets us easily source utils
source "$PROJECT_ROOT/bin/utils"
source "$PROJECT_ROOT/bin/config"

if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Error: PROJECT_NAME is not set${NC}"
    exit 1
fi

REDIS_CONTAINER_NAME="${PROJECT_NAME}-redis"
REDIS_VOLUME_NAME="${PROJECT_NAME}-redis-data"
REDIS_PORT=6379
REDIS_IMAGE_NAME=redis:7-alpine

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

# Start local Redis for development
function up {
    check_runtime

    print_header "Starting Redis"

    # Check if container exists (running or stopped)
    if $CONTAINER_RUNTIME ps -a --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER_NAME}$"; then
        # Container exists - check if it's running
        if $CONTAINER_RUNTIME ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER_NAME}$"; then
            echo -e "${GREEN}Redis container is already running.${NC}"
            verify_connection
            return 0
        else
            # Container exists but is stopped - start it
            echo "Starting existing Redis container..."
            $CONTAINER_RUNTIME start $REDIS_CONTAINER_NAME
            sleep 2
            verify_connection

            echo ""
            echo -e "${GREEN}Redis started!${NC}"
            show_connection_info
            return 0
        fi
    fi

    # Container doesn't exist - create and start it
    echo "Creating new Redis container..."
    start_redis_container

    # Wait for Redis to be ready
    echo -e "${YELLOW}Waiting for Redis to be ready...${NC}"
    sleep 2

    # Verify network connectivity to container
    verify_connection

    echo ""
    echo -e "${GREEN}Redis started!${NC}"
    show_connection_info
}

# Helper function to display connection information
function show_connection_info {
    echo ""
    echo -e "${YELLOW}Set environment variables:${NC}"
    echo "  export REDIS_URL=redis://localhost:${REDIS_PORT}"
    echo ""
    echo -e "${YELLOW}Connection command:${NC}"
    echo "  redis-cli -h localhost -p ${REDIS_PORT}"
}

# Verify connection to Redis
function verify_connection {
    echo -e "${YELLOW}Verifying container status...${NC}"
    $CONTAINER_RUNTIME logs --tail 5 $REDIS_CONTAINER_NAME

    echo "Testing connection from host to container..."
    if command -v redis-cli &>/dev/null; then
        if redis-cli -h localhost -p ${REDIS_PORT} ping 2>/dev/null | grep -q "PONG"; then
            echo -e "${GREEN}Connection successful!${NC}"
        else
            echo -e "${RED}Connection test failed. See troubleshooting tips below.${NC}"
            show_troubleshooting
        fi
    else
        # Fallback to checking if the container is healthy
        if $CONTAINER_RUNTIME exec $REDIS_CONTAINER_NAME redis-cli ping 2>/dev/null | grep -q "PONG"; then
            echo -e "${GREEN}Container is healthy (redis-cli not installed locally)${NC}"
        else
            echo -e "${YELLOW}redis-cli not found locally. Install Redis tools to test connectivity.${NC}"
            show_troubleshooting
        fi
    fi
}

# Helper function to show troubleshooting tips
function show_troubleshooting {
    echo ""
    print_header "Troubleshooting Tips for macOS"
    echo "1. Check Docker Desktop settings - ensure port forwarding is enabled"
    echo "2. Try restarting Docker Desktop completely"
    echo "3. Check if another service is using port $REDIS_PORT:"
    echo "   lsof -i :$REDIS_PORT"
    echo "4. Verify your Mac firewall settings allow Docker connections"
    echo "5. Try explicitly connecting with host.docker.internal instead of localhost:"
    echo "   export REDIS_URL=redis://host.docker.internal:${REDIS_PORT}"
    echo ""
}

# Helper function to create and start a new Redis container
function start_redis_container {
    $CONTAINER_RUNTIME pull $REDIS_IMAGE_NAME
    $CONTAINER_RUNTIME volume create $REDIS_VOLUME_NAME || true

    # OS-optimized container settings
    $CONTAINER_RUNTIME run \
        --name $REDIS_CONTAINER_NAME \
        $NETWORK_FLAGS \
        --publish $REDIS_PORT:6379 \
        --volume $REDIS_VOLUME_NAME:/data \
        --health-cmd="redis-cli ping || exit 1" \
        --health-interval=5s \
        --health-timeout=5s \
        --health-retries=5 \
        --detach \
        $REDIS_IMAGE_NAME \
        redis-server --appendonly yes
}

function down {
    check_runtime
    print_header "Cleaning Redis Container"

    echo "Stopping Redis container..."
    $CONTAINER_RUNTIME stop $REDIS_CONTAINER_NAME 2>/dev/null || true
    check_result "Container stop"

    echo "Removing Redis container..."
    $CONTAINER_RUNTIME rm -f $REDIS_CONTAINER_NAME 2>/dev/null || true
    check_result "Container removal"

    echo "Removing Redis volume..."
    $CONTAINER_RUNTIME volume rm -f $REDIS_VOLUME_NAME 2>/dev/null || true
    check_result "Volume removal"

    print_summary "Redis cleaned up successfully!" "cleanup step(s) failed"
}

function endpoint {
    check_runtime
    if $CONTAINER_RUNTIME ps -a | grep $REDIS_CONTAINER_NAME &>/dev/null; then
        echo "redis://localhost:${REDIS_PORT}"
    else
        echo -e "${RED}Redis container is not running. Start it with: $0 up${NC}" >&2
        exit 1
    fi
}

function status {
    check_runtime
    print_header "Redis Status"

    if $CONTAINER_RUNTIME ps | grep -q "$REDIS_CONTAINER_NAME"; then
        echo -e "${GREEN}Redis container is running.${NC}"
        echo ""
        echo -e "${YELLOW}Recent logs:${NC}"
        $CONTAINER_RUNTIME logs --tail 10 $REDIS_CONTAINER_NAME
        echo ""

        echo -e "${YELLOW}Connection status:${NC}"
        if command -v redis-cli &>/dev/null; then
            if redis-cli -h localhost -p ${REDIS_PORT} ping 2>/dev/null | grep -q "PONG"; then
                echo -e "${GREEN}Connection active${NC}"
            else
                echo -e "${RED}Connection failed${NC}"
            fi
        else
            if $CONTAINER_RUNTIME exec $REDIS_CONTAINER_NAME redis-cli ping 2>/dev/null | grep -q "PONG"; then
                echo -e "${GREEN}Container healthy${NC}"
            else
                echo -e "${RED}Container unhealthy${NC}"
            fi
        fi
    else
        echo -e "${RED}Redis container is not running.${NC}"
        echo ""
        echo "Start it with: $0 up"
    fi
}

function help {
    echo -e "${YELLOW}Redis Container Manager${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Container Management Commands:"
    echo "  up                 - Start a local Redis container for development"
    echo "  down               - Remove the Redis container and volume"
    echo "  endpoint           - Print the Redis connection URL"
    echo "  status             - Check container status and connection"
    echo "  help               - Show this help message"
    echo ""
    echo "Redis provides the message broker for background jobs."
}

# Process command
CMD=${1:-help}
shift || true  # Shift to remove command from arguments

case "$CMD" in
up | down | endpoint | status | help)
    $CMD "$@"
    ;;
*)
    echo -e "${RED}Unknown command: $CMD${NC}"
    help
    exit 1
    ;;
esac
