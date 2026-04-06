@echo off
echo Starting AI Dashboard Generator...
echo.
start "Ollama" /min cmd /k "ollama serve"
timeout /t 2 /nobreak >nul
start "Backend" cmd /k "cd backend && .venv\Scripts\activate && uvicorn main:app --reload --port 8011 --host 0.0.0.0"
timeout /t 3 /nobreak >nul
start "" "http://localhost:8011"
echo.
echo Dashboard: http://localhost:8011
echo API Docs:  http://localhost:8011/docs
echo.
pause

