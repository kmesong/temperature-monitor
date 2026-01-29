@echo off
echo ==========================================
echo   Temperature Monitor - Quick Start
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
pip show opencv-python >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting Temperature Monitor...
echo Press 'q' to quit, 'c' to capture image
echo ==========================================
echo.

python temperature_monitor.py

pause