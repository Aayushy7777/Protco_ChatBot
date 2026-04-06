@echo off
echo AI Dashboard Generator Setup
echo.
where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found.
  echo Install from https://python.org
  pause & exit /b 1
)
cd backend
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt
cd ..
if not exist uploads mkdir uploads
where ollama >nul 2>&1
if errorlevel 1 (
  echo.
  echo WARNING: Ollama not found.
  echo Install from https://ollama.com then run:
  echo   ollama pull llama3.1
) else (
  echo Pulling llama3.1 model...
  ollama pull llama3.1
)
echo.
echo Setup complete! Run start.bat to launch.
pause

