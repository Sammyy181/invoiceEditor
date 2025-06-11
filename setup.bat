@echo off
SET VENV_NAME=venv

echo Creating virtual environment...
python -m venv %VENV_NAME%

echo Activating virtual environment...
call %VENV_NAME%\Scripts\activate

echo Installing dependencies from requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ✅ Setup complete!
echo Run your app using:
echo.
echo     call %VENV_NAME%\Scripts\activate
echo     python app.py
echo.
pause
