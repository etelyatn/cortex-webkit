#!/usr/bin/env bash
# scripts/dev.sh — Start backend + frontend dev servers
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting Cortex Web Kit development environment..."

# Check if using mock or real backend
if [ "$1" = "--mock" ]; then
    echo "Starting mock backend on :8000..."
    (cd "$ROOT_DIR" && uv run python scripts/mock_server.py) &
    BACKEND_PID=$!
else
    echo "Starting real backend on :8000..."
    (cd "$ROOT_DIR" && uv run uvicorn cortex_webkit.app:create_app --factory --host 127.0.0.1 --port 8000 --reload) &
    BACKEND_PID=$!
fi

echo "Starting frontend dev server on :5173..."
(cd "$ROOT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

# Cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
}
trap cleanup EXIT

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop."

wait
