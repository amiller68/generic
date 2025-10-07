#!/usr/bin/env bash
# Script to build styles with Tailwind CSS and manage branding assets

set -o errexit
set -o nounset

# Points back to the project root
export PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
# Source utils for logging
source "$PROJECT_ROOT/bin/utils"

# Configuration
USE_SYMLINKS="${USE_SYMLINKS:-0}"
WATCH_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --watch|-w)
      WATCH_MODE=true
      shift
      ;;
    --symlinks|-s)
      USE_SYMLINKS=1
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  -w, --watch       Watch mode (rebuild on changes)"
      echo "  -s, --symlinks    Use symlinks instead of copying assets"
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

# Change to py directory
cd "$PROJECT_ROOT/py"

# Function to sync branding assets
sync_assets() {
  print_info "Syncing branding assets..."
  mkdir -p static

  if [ "$USE_SYMLINKS" = "1" ]; then
    print_info "Creating symlinks to branding assets..."
    ln -sf ../../branding/assets/favicon.ico static/favicon.ico
    ln -sf ../../branding/assets/favicon.png static/favicon.png
    ln -sf ../../branding/assets/icon.png static/icon.png
    ln -sf ../../branding/assets/icon.svg static/icon.svg
    print_success "Assets symlinked"
  else
    print_info "Copying branding assets..."
    cp ../branding/assets/favicon.ico static/favicon.ico
    cp ../branding/assets/favicon.png static/favicon.png
    cp ../branding/assets/icon.png static/icon.png
    cp ../branding/assets/icon.svg static/icon.svg
    print_success "Assets copied"
  fi
}

# Build CSS
build_css() {
  print_info "Building Tailwind CSS..."
  if [ "$WATCH_MODE" = true ]; then
    npx tailwindcss -i ./styles/main.css -o ./static/css/main.css --watch
  else
    npx tailwindcss -i ./styles/main.css -o ./static/css/main.css --minify
    print_success "Styles built"
  fi
}

# Main execution
print_info "Building Python styles..."

# Sync assets first
sync_assets

# Build CSS (will watch if in watch mode)
build_css
