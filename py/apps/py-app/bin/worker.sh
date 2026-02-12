#!/bin/bash
# Start the TaskIQ worker process

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKIP_DB_SETUP=1 source "$SCRIPT_DIR/env.sh"

echo "[worker] Starting TaskIQ worker (branch: ${WORKTREE_BRANCH}, redis: ${WORKTREE_REDIS_DB})"
run_with_vault --stage development -- uv run taskiq worker src.tasks:broker --fs-discover
