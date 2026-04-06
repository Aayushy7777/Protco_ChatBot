#!/usr/bin/env bash
set -euo pipefail

echo "AI Dashboard Generator Setup"
echo

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found."; exit 1; }

cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip -q
pip install -r requirements.txt
cd ..

mkdir -p uploads

if command -v ollama >/dev/null 2>&1; then
  echo "Pulling llama3.1 model..."
  ollama pull llama3.1 || true
else
  echo
  echo "WARNING: Ollama not found."
  echo "Install from https://ollama.com then run:"
  echo "  ollama pull llama3.1"
fi

echo
echo "Setup complete! Run start.sh to launch."

