#!/usr/bin/env bash
# scripts/build.sh — Build frontend + package
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building frontend..."
(cd "$ROOT_DIR/frontend" && npm run build)

echo "Frontend built to frontend/dist/"
echo "Run 'uv build' to create Python package."
