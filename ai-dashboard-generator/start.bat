@echo off
echo Starting AI Dashboard Generator...
start "Ollama" cmd /k "ollama serve"
timeout /t 3 >nul

call venv\Scripts\activate.bat
cd backend
echo Server running at http://localhost:8010
uvicorn main:app --reload --host 0.0.0.0 --port 8010
