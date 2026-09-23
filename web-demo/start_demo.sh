#!/usr/bin/env bash
# start_demo.sh — install dependencies and start the iTantra M3 Web Demo on Linux/macOS.
#
#   ./start_demo.sh
#
#   Backend API  + standalone chat UI : http://localhost:8000
#   React tactical dashboard          : http://localhost:5173
#
# Ctrl+C stops both servers.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "=================================================="
echo "   iTantra M3 Protocol Demo - Startup Script"
echo "=================================================="

# --- 1. Backend (FastAPI + uvicorn) -----------------------------------------
echo "[1/2] Starting FastAPI Backend..."
cd "$BACKEND_DIR"

if [ ! -d .venv ]; then
    PYTHON_BIN="$(command -v python3 || command -v python)"
    "$PYTHON_BIN" -m venv .venv
    echo "      created virtualenv at backend/.venv"
fi
# shellcheck disable=SC1091
. .venv/bin/activate
# --prefer-binary: never trade a wheel for an sdist build. A failure here must
# not keep the demo from starting when the environment is already provisioned.
if ! python -m pip install -q --prefer-binary -r requirements.txt; then
    echo "      WARNING: dependency install reported errors —"
    echo "               continuing with the existing environment."
fi

uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info &
BACKEND_PID=$!

# --- 2. Frontend (React + Vite) ---------------------------------------------
echo "[2/2] Starting React Frontend..."
cd "$FRONTEND_DIR"
if [ ! -d node_modules ]; then
    npm install
fi
npm run dev &
FRONTEND_PID=$!

# --- Cleanup on exit / Ctrl+C ----------------------------------------------
cleanup() {
    trap - INT TERM EXIT
    echo ""
    echo "Shutting down demo servers..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# --- Wait for the backend to answer /health, then print the URLs ------------
for _ in $(seq 1 30); do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

echo "=================================================="
echo "   Demo is starting:"
echo "     Backend API + chat UI : http://localhost:8000"
echo "     React dashboard UI    : http://localhost:5173"
echo "   Press Ctrl+C to stop."
echo "=================================================="

wait
