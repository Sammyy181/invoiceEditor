@echo off

REM Activate the virtual environment
call venv\Scripts\activate

REM Start the Flask app in a new window
start "" python app.py

REM Wait until server is reachable
:waitloop
curl -s --head http://127.0.0.1:7000 >nul
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto waitloop
)

REM Open browser after server is ready
start "" "http://127.0.0.1:7000"

exit
