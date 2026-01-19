#!/bin/bash
cd "$(dirname "$0")"
mkdir -p .tmp

uv run agent-builder &
echo $! > .tmp/backend.pid

cd frontend && npm run dev &
echo $! > ../.tmp/frontend.pid

echo "App running at http://localhost:5173"
