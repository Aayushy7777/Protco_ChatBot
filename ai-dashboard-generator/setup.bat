@echo off
setlocal
echo AI Dashboard Generator -- Setup
echo.

set "PYTHON_EXE=python"
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
  set "PYTHON_EXE=py -3.12"
) else (
  python --version >nul 2>&1
  if errorlevel 1 (
    echo Python not found. Please install Python 3.10+ and retry.
    exit /b 1
  )
)

if not exist venv (
  echo Creating virtual environment...
  %PYTHON_EXE% -m venv venv
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

if not exist uploads mkdir uploads

ollama --version >nul 2>&1
if errorlevel 1 (
  echo Please install Ollama from https://ollama.com
) else (
  echo Pulling llama3.1 in background...
  start "" cmd /c "ollama pull llama3.1"
)

echo.
echo Setup complete!
echo Run start.bat to launch the server
echo Then open http://localhost:8010
endlocal
