@echo off
setlocal enabledelayedexpansion

REM Change to the directory where this batch file is located
cd /d "%~dp0"

title RUIE

REM Check if we're already running as admin
net session >nul 2>&1
if %errorlevel% equ 0 (
    goto :ADMIN_CONFIRMED
)

REM Not admin - show message and request elevation
cls
echo.
echo ===== RUIE =====
echo.
echo [!] Admin privileges required for Program Files access
echo [!] A UAC prompt will appear - please click "Yes"
echo.
echo Requesting elevation...
timeout /t 2 /nobreak >nul

REM Use PowerShell to re-run this batch file with elevation
powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
exit /b

:ADMIN_CONFIRMED
REM Now running as admin - verify and show status
title RUIE - Launching (Admin)
cd /d "%~dp0"
cls
echo.
echo ===== RUIE =====
echo Current directory: %cd%
echo.

REM Verify admin status
net session >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Running with Administrator privileges
) else (
    echo [WARNING] Not running as Administrator
    echo [WARNING] Theme deployment may fail
)
echo.

REM Check if launcher.py exists
if not exist "launcher.py" (
    echo [ERROR] launcher.py not found in %cd%
    echo Please run this from the RUIE folder
    pause
    exit /b 1
)

REM Check if Python is installed
echo Checking Python...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

REM Install Python dependencies
echo.
echo Installing dependencies...
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies may not have installed correctly
)

REM Run the app
echo.
echo ===== Launching App =====
echo Starting RUIE...
echo.
timeout /t 2 /nobreak >nul

REM Use pythonw.exe to run the GUI without console window
pythonw launcher.py
set APP_EXIT_CODE=%errorlevel%

REM Hide this window after app starts (use invisible VBScript to close console)
if %errorlevel% equ 0 (
    exit /b 0
) else (
    echo.
    echo ===== App Error =====
    echo App exited with error code: %APP_EXIT_CODE%
    echo.
    echo Type 'exit' and press Enter to close this window
    cmd /k
)
