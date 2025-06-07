@echo off
REM Pi Tank Controller Startup Script for Windows (Testing)
REM This script is for development/testing purposes only

echo === Pi Tank Controller (Windows Test Mode) ===
echo Starting tank controller web server...

REM Get the directory where this script is located
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies (skip hardware-specific ones on Windows)
echo Installing dependencies...
pip install Flask==2.3.3 opencv-python==4.8.1.78 pygame==2.5.2 numpy==1.24.3

echo.
echo === Starting Tank Controller Web Server (Test Mode) ===
echo NOTE: This is test mode - camera and GPIO will be simulated
echo.
echo Access the web interface at:
echo   Local: http://localhost:5000
echo.
echo Controls:
echo   - Web buttons for testing UI
echo   - WASD/Arrow keys for keyboard testing
echo   - Connect gamepad for analog testing
echo.
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Start the Flask application
cd src
python app.py

pause
