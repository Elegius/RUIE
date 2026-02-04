@echo off
REM RUIE - Electron + Flask App Launcher
REM This batch file launches the RUIE theme customization app

cd /d "%~dp0"

REM Check if npm is installed
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js and npm are not installed
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if node_modules exists, if not run npm install
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

REM Start the Electron app
echo Starting RUIE...
call npm start
