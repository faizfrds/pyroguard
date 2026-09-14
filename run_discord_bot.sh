#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🤖 Starting PyroGuard AI Discord Bot with Slash Commands..."
export PYTHONPATH="$DIR/backend"
backend/.venv/bin/python backend/app/discord_bot.py

