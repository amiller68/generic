#!/usr/bin/env bash
# Script to setup assets for TypeScript/Vite
# Assets now live directly in ts/apps/web/public/ - no branding sync needed

set -o errexit
set -o nounset

# Points back to the project root
export PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
# Source utils for logging
source "$PROJECT_ROOT/bin/utils"

# Ensure public directory exists
WEB_PUBLIC="$PROJECT_ROOT/ts/apps/web/public"
mkdir -p "$WEB_PUBLIC"

print_success "Assets directory ready"
print_info "Vite will handle CSS compilation automatically during dev/build"
