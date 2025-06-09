@echo off
echo Installing Python packages from requirements.txt...

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed or not added to PATH.
    pause
    exit /b 1
)

REM Upgrade pip just in case
python -m pip install --upgrade pip

REM Install packages from requirements.txt
pip install -r requirements.txt

echo.
echo Done installing packages.
pause