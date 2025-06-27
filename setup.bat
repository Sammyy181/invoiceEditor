@echo off
setlocal

set VENV_DIR=venv

echo [1/5] Creating virtual environment in %VENV_DIR%
python -m venv %VENV_DIR%

echo [2/5] Activating virtual environment
call %VENV_DIR%\Scripts\activate.bat

echo [3/5] Installing Python packages
pip install --upgrade pip
pip install -r requirements.txt

echo [4/5] Installing Ollama...
powershell -Command "Invoke-WebRequest https://ollama.com/download/OllamaSetup.exe -OutFile OllamaSetup.exe"
start /wait OllamaSetup.exe /silent

echo [5/5] Pulling Mistral model
ollama pull mistral

echo Setup complete.
pause
