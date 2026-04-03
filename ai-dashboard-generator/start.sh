#!/usr/bin/env bash
set -e
echo "Starting AI Dashboard Generator..."
if command -v ollama >/dev/null 2>&1; then
  nohup ollama serve >/dev/null 2>&1 &
fi
sleep 3
source venv/bin/activate
cd backend
echo "Server running at http://localhost:8010"
uvicorn main:app --reload --host 0.0.0.0 --port 8010
