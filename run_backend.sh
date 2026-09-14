#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🔥 Starting PyroGuard AI FastAPI Backend on http://localhost:8000..."
export PYTHONPATH="$DIR/backend"
backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

