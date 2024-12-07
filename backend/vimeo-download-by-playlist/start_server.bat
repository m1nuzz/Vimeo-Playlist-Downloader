@echo off
setlocal enabledelayedexpansion

echo [%date% %time%] Starting server setup... >> download_system.log

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [%date% %time%] Python not installed! >> download_system.log
    echo Python is not installed!
    echo Please install Python from python.org
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist "venv" (
    echo [%date% %time%] Creating virtual environment... >> download_system.log
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [%date% %time%] Error creating virtual environment! >> download_system.log
        echo Error creating virtual environment!
        pause
        exit /b 1
    )
)

:: Activate virtual environment and verify activation
echo [%date% %time%] Activating virtual environment... >> download_system.log
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [%date% %time%] Error activating virtual environment! >> download_system.log
    echo Error activating virtual environment!
    pause
    exit /b 1
)

:: Verify virtual environment is active
python -c "import sys; print('Virtual environment:', sys.prefix)" >> download_system.log

:: Upgrade pip
echo [%date% %time%] Upgrading pip... >> download_system.log
venv\Scripts\python.exe -m pip install --upgrade pip

:: Install dependencies
echo [%date% %time%] Installing dependencies... >> download_system.log
venv\Scripts\pip.exe install -r requirements.txt

:: Start server
echo.
echo [%date% %time%] Starting server... >> download_system.log
echo Starting Vimeo Downloader Server...
echo Please do not close this window while downloading videos
echo.
venv\Scripts\python.exe server.py

:: Deactivate virtual environment on exit
echo [%date% %time%] Server stopped. Deactivating virtual environment... >> download_system.log
deactivate
