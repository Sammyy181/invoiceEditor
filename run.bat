@echo off
setlocal

set VENV_DIR=venv

echo Activating virtual environment
call %VENV_DIR%\Scripts\activate.bat

echo Starting Ollama server...
start /min ollama serve

echo Waiting for Ollama to initialize...
timeout /t 5 >nul

echo Starting your application...
python app.py

REM Optional: stop Ollama when done
REM taskkill /IM ollama.exe /F

pause
