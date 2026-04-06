@echo off
title Quick Ollama & Backend Starter
color 0B

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║  Quick Ollama + Backend Starter                   ║
echo ║  (Use this to reset everything)                   ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Kill any existing processes on ports
echo Checking for running services...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8011"') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo.

REM Start Ollama
echo [1/2] Starting Ollama...
echo.
start "Ollama Server" cmd /k "ollama serve"
echo.

REM Wait for Ollama to start
echo Waiting for Ollama to initialize (5 seconds)...
timeout /t 5 >nul

REM Start Backend
echo.
echo [2/2] Starting Backend Server...
echo.
cd /d "%~dp0ai-dashboard-generator\backend" >nul

REM Check venv
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate and run
call .venv\Scripts\activate.bat
python -m uvicorn main:app --reload --port 8011 --log-level info

pause
