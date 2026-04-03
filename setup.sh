#!/bin/bash
# Quick startup script for CSV Chat Agent v2.0

set -e

echo "🚀 CSV Chat Agent - Production Setup"
echo "===================================="
echo ""

# Check if BACKEND directory exists
if [ ! -d "BACKEND" ]; then
    echo "❌ Error: BACKEND directory not found."
    echo "   Please run this script from the project root."
    exit 1
fi

# Navigate to backend
cd BACKEND

echo "📦 Installing dependencies..."
echo "   This may take 2-3 minutes on first run."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📝 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
else
    echo "❌ Could not activate virtual environment"
    exit 1
fi

# Install dependencies
echo "📥 Installing Python packages..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Configuration:"
echo "   - .env file: BACKEND/.env"
echo "   - Agent config: BACKEND/openclaw/agent_config.yaml"
echo ""
echo "🚀 Starting application..."
echo ""
echo "Commands:"
echo "  1. Terminal 1: ollama serve"
echo "  2. Terminal 2: cd BACKEND && python -m uvicorn app.main:app --reload"
echo "  3. Terminal 3 (optional): verify with 'python verify_setup.py'"
echo ""
echo "📊 Access:"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health:   http://localhost:8000/health"
echo "  - Chat:     POST http://localhost:8000/api/chat"
echo ""
