#!/usr/bin/env bash
set -euo pipefail

echo "Starting AI Dashboard Generator..."
echo

if command -v ollama >/dev/null 2>&1; then
  (ollama serve >/dev/null 2>&1 &)
else
  echo "WARNING: ollama not found. Install from https://ollama.com"
fi

cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8010 --host 0.0.0.0

