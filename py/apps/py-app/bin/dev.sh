#!/bin/bash
# Start the FastAPI dev server with hot reload

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

write_dev_info

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Dev Server Starting                                   ║"
echo "╠════════════════════════════════════════════════════════╣"
printf "║  Branch:   %-43s ║\n" "${WORKTREE_BRANCH}"
printf "║  Backend:  %-43s ║\n" "http://localhost:${WORKTREE_BACKEND_PORT}"
printf "║  Database: %-43s ║\n" "${WORKTREE_DB_NAME}"
printf "║  Redis DB: %-43s ║\n" "${WORKTREE_REDIS_DB}"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
run_with_vault --stage development -- uv run src/__main__.py
