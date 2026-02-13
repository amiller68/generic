#!/usr/bin/env bash
# Script to build styles with Tailwind CSS

set -o errexit
set -o nounset

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

WATCH_MODE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --watch|-w)
      WATCH_MODE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

cd "$APP_DIR"

if [ "$WATCH_MODE" = true ]; then
  npx tailwindcss -i ./styles/main.css -o ./static/css/main.css --watch
else
  npx tailwindcss -i ./styles/main.css -o ./static/css/main.css --minify
fi
