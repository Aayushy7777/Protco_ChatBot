@echo off
setlocal

echo Starting AI Dashboard + Mission Control...
echo.

REM 1. Start Ollama
echo [1/4] Starting Ollama...
start "Ollama" cmd /k "ollama serve"
timeout /t 3 /nobreak > nul

REM 2. Start Mission Control
echo [2/4] Starting Mission Control (port 3000)...
start "Mission Control" cmd /k "cd mission-control && pnpm dev"
timeout /t 5 /nobreak > nul

REM 3. Start AI Dashboard Backend
echo [3/4] Starting AI Dashboard Backend (port 8011)...
start "AI Dashboard" cmd /k "cd ai-dashboard\backend && call ..\..\.venv\Scripts\activate && uvicorn main:app --reload --port 8011"
timeout /t 3 /nobreak > nul

REM 4. Open browsers
echo [4/4] Opening dashboards...
timeout /t 3 /nobreak > nul
start "" "http://localhost:3000"
start "" "http://localhost:8011"

echo.
echo ================================================
echo  Mission Control:    http://localhost:3000
echo  AI Dashboard:       http://localhost:8011
echo  Ollama:             http://localhost:11434
echo  API Docs:           http://localhost:8011/docs
echo  MC API Docs:        http://localhost:3000/api-docs
echo ================================================
echo.
pause

