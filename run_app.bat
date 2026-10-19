@echo off
cd /d "%~dp0"

echo Installing / verifying dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Exiting.
    pause
    exit /b %errorlevel%
)

echo.
echo Starting the ALS progress app (opens in your browser). Close this window to stop it.
python -m streamlit run app.py
pause
