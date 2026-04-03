#!/usr/bin/env bash
set -e
echo "AI Dashboard Generator -- Setup"

python3 --version >/dev/null 2>&1 || { echo "Python3 not found. Install Python 3.10+"; exit 1; }

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
mkdir -p uploads

if command -v ollama >/dev/null 2>&1; then
  nohup ollama pull llama3.1 >/dev/null 2>&1 &
else
  echo "Please install Ollama from https://ollama.com"
fi

echo "Setup complete!"
echo "Run ./start.sh to launch"
echo "Open http://localhost:8000"
