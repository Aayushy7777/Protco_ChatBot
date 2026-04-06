@echo off
echo.
echo ========================================
echo  AI Dashboard Backend Startup Script
echo ========================================
echo.

REM Check if venv exists
if not exist ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate venv
echo [2/3] Activating virtual environment...
call .\.venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Skip dependency install if already installed
echo [3/3] Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install --prefer-binary -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo.
        echo Try: pip install --only-binary :all: -r requirements.txt
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed ✓
)

REM Check Ollama
echo.
echo ========================================
echo  Checking Prerequisites
echo ========================================
echo.

REM Check if Ollama is running
timeout /t 1 >nul 2>&1
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama is not running!
    echo.
    echo Please start Ollama in another terminal:
    echo   ollama serve
    echo.
    echo Or pull a model first:
    echo   ollama pull llama3.1
    echo.
    pause
)

REM Start backend
echo ========================================
echo  Starting Backend Server
echo ========================================
echo.
echo Server will be available at:
echo   http://localhost:8011
echo.
echo 📊 Open in browser: http://localhost:8011
echo 📈 View dashboard: http://localhost:8011/dashboard
echo 💚 Health check: http://localhost:8011/api/health
echo.
echo Press CTRL+C to stop the server
echo.

python -m uvicorn main:app --reload --port 8011 --log-level info

pause
