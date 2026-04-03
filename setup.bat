@echo off
setlocal enabledelayedexpansion

echo.
echo CSV Chat Agent - Setup (Windows)
echo =================================
echo.

REM 1) Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python is not installed or not on PATH.
  echo Install Python 3.11+ from: https://www.python.org/downloads/
  pause
  exit /b 1
)

REM 2) Create venv if not exists
if not exist ".venv\Scripts\activate.bat" (
  echo Creating virtual environment...
  python -m venv .venv
)

REM 3) Activate
call .venv\Scripts\activate.bat
if errorlevel 1 (
  echo ERROR: Failed to activate .venv
  pause
  exit /b 1
)

REM 4) Install backend deps
echo Installing backend dependencies...
python -m pip install --upgrade pip
pip install -r BACKEND\requirements.txt

REM 5) Check if Ollama is installed
ollama --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Ollama is not installed.
  echo Download: https://ollama.com/download
  pause
  exit /b 1
)

REM 6) Pull required models
echo Pulling Ollama models...
ollama pull llama3.1
ollama pull nomic-embed-text

REM 7) Create backend folders
mkdir BACKEND\data\raw 2>nul
mkdir BACKEND\data\processed 2>nul

REM 8) Create chroma store folder
mkdir BACKEND\chroma_store 2>nul

echo.
echo Setup complete.
echo.
echo Next steps (separate terminals):
echo   1) Run Ollama: ollama serve
echo   2) Run backend: cd BACKEND ^& uvicorn app.main:app --reload --port 8000
echo.
echo Docs: http://localhost:8000/docs
echo Health: http://localhost:8000/api/health

echo.
pause
