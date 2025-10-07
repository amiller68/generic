#!/usr/bin/env bash
# Script to setup branding assets for TypeScript/Vite

set -o errexit
set -o nounset

# Points back to the project root
export PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
# Source utils for logging
source "$PROJECT_ROOT/bin/utils"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Creates symlinks to branding assets in Vite web app public directory"
      echo ""
      echo "Options:"
      echo "  -h, --help        Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Change to web app public directory
WEB_PUBLIC="$PROJECT_ROOT/ts/apps/web/public"

print_info "Setting up branding assets for web app..."

# Ensure public directory exists
mkdir -p "$WEB_PUBLIC"

# Create symlinks to branding assets
cd "$WEB_PUBLIC"

print_info "Creating symlinks to branding assets..."
ln -sf ../../../../branding/assets/favicon.ico favicon.ico
ln -sf ../../../../branding/assets/favicon.png favicon.png
ln -sf ../../../../branding/assets/icon.png icon.png
ln -sf ../../../../branding/assets/icon.svg icon.svg

print_success "Branding asset symlinks created"
print_info "Vite will handle CSS compilation automatically during dev/build"
