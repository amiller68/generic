#!/bin/bash
# Shared environment setup for dev server, worker, and scheduler.
# Source this file, then run your process.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
source "$PROJECT_ROOT/bin/config"
source "$PROJECT_ROOT/bin/vault"
source "$PROJECT_ROOT/bin/worktree-ports"

# Find available port / worktree config
if ! get_worktree_config; then
    exit 1
fi

# Ensure branch-specific database exists and run migrations
PY_CORE_DIR="$PROJECT_ROOT/py/packages/py-core"

if [ "${SKIP_DB_SETUP:-}" != "1" ]; then
    echo "Ensuring database '${WORKTREE_DB_NAME}' exists..."
    "$PY_CORE_DIR/bin/db.sh" ensure_database "${WORKTREE_DB_NAME}"

    echo "Running migrations on '${WORKTREE_DB_NAME}'..."
    POSTGRES_URL=$("$PY_CORE_DIR/bin/db.sh" endpoint "${WORKTREE_DB_NAME}") "$PY_CORE_DIR/bin/db.sh" migrate
fi

export DEV_SERVER_HOST=localhost
export HOST_NAME=http://localhost:${WORKTREE_BACKEND_PORT}
export LISTEN_ADDRESS=0.0.0.0
export LISTEN_PORT=${WORKTREE_BACKEND_PORT}
export DEBUG=True
export DEV_MODE=True
export LOG_PATH=
export POSTGRES_URL=$("$PY_CORE_DIR/bin/db.sh" endpoint "${WORKTREE_DB_NAME}")
export REDIS_URL="${WORKTREE_REDIS_URL}"
export SERVICE_SECRET=veryveryverysecret
