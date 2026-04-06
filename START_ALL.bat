@echo off
title AI Dashboard & Chatbot - Full Stack Startup
color 0A

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║     AI Dashboard Generator - Full Stack Startup Script        ║
echo ║               All Systems Starting...                         ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Check if Ollama is running
echo.
echo [1/3] Checking Ollama Status...
echo.
timeout /t 1 >nul 2>&1
for /f %%i in ('powershell -Command "try{(Invoke-WebRequest -Uri http://localhost:11434 -TimeoutSec 2).StatusCode} catch{echo 0}"') do set ollama_status=%%i

if "%ollama_status%"=="200" (
    echo ✓ Ollama is running on http://localhost:11434
) else (
    echo ⚠ WARNING: Ollama is NOT running!
    echo.
    echo   You need to start Ollama in a separate terminal:
    echo   $ ollama serve
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

REM Start Backend in new terminal
echo.
echo [2/3] Starting Backend Server...
echo.
cd /d "%~dp0ai-dashboard-generator\backend" >nul
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    start "AI Dashboard Backend" cmd /k "echo Backend starting on http://localhost:8011... && echo. && python -m uvicorn main:app --reload --port 8011 --log-level info"
) else (
    start "AI Dashboard Backend" cmd /k "echo. && echo ERROR: Virtual environment not found! && echo Run: cd ai-dashboard-generator\backend ^&^& python -m venv .venv && pause"
)

REM Start Mission Control in new terminal
echo.
echo [3/3] Starting Mission Control Frontend...
echo.
cd /d "%~dp0mission-control" >nul
start "Mission Control Frontend" cmd /k "echo Frontend starting on http://localhost:3000... && echo. && pnpm dev"

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║              ✅ All Systems Starting!                         ║
echo ╠═══════════════════════════════════════════════════════════════╣
echo ║                                                               ║
echo ║  📊 Dashboard Panel:    http://localhost:3000               ║
echo ║  🔌 Backend API:        http://localhost:8011               ║
echo ║  🤖 Ollama:             http://localhost:11434              ║
echo ║                                                               ║
echo ║  Note: If Ollama is not running, start it in another        ║
echo ║        terminal with: ollama serve                          ║
echo ║                                                               ║
echo ║  Wait 5-10 seconds for all services to start...             ║
echo ║                                                               ║
echo ║  📖 Read SETUP_GUIDE.md for detailed instructions           ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Optional: Open browser automatically
echo Opening browser in 3 seconds...
timeout /t 3 >nul
start http://localhost:3000

echo.
echo Press any key to close this window...
pause >nul
