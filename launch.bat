@echo off
REM RUIE - Clean Launcher
REM This batch file requests admin and launches the app cleanly

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% equ 0 goto :ADMIN_OK

REM Request elevation using PowerShell (more reliable than VBScript)
powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs" -WindowStyle Hidden
exit /b

:ADMIN_OK
REM Now running as admin - hide this window and run the app
cd /d "%~dp0"

REM Check if compiled exe exists
if exist "dist\RUIE.exe" (
    start "" "dist\RUIE.exe"
) else (
    REM Fall back to Python version if exe doesn't exist
    start "" pythonw launcher.py
)
exit /b
