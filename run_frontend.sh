#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/frontend"

echo "🌐 Starting PyroGuard AI Next.js Frontend on http://localhost:3000..."
npm run dev

