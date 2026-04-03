@echo off
REM Quick startup script for CSV Chat Agent v2.0 (Windows)

setlocal enabledelayedexpansion

echo.
echo 🚀 CSV Chat Agent - Production Setup
echo ====================================
echo.

REM Check if BACKEND directory exists
if not exist BACKEND (
    echo ❌ Error: BACKEND directory not found.
    echo    Please run this script from the project root.
    pause
    exit /b 1
)

REM Navigate to backend
cd BACKEND

echo 📦 Installing dependencies...
echo    This may take 2-3 minutes on first run.
echo.

REM Check if virtual environment exists
if not exist .venv (
    echo 📝 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo ✅ Activating virtual environment...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo ❌ Could not activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo 📥 Installing Python packages...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo.
echo ✅ Installation complete!
echo.
echo 📝 Configuration:
echo    - .env file: BACKEND\.env
echo    - Agent config: BACKEND\openclaw\agent_config.yaml
echo.
echo 🚀 Next steps:
echo.
echo Commands (run in separate terminals):
echo   1. Terminal 1: ollama serve
echo   2. Terminal 2: cd BACKEND ^& python -m uvicorn app.main:app --reload
echo   3. Terminal 3 ^(optional^): python verify_setup.py
echo.
echo 📊 Access:
echo    - API Docs: http://localhost:8000/docs
echo    - Health:   http://localhost:8000/health
echo    - Chat:     POST http://localhost:8000/api/chat
echo.
pause
