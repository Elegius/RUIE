@echo off
REM RUIE Production Server Launcher (Windows)
REM ==========================================
REM
REM This batch script starts the RUIE server in production mode.
REM Features:
REM   - Waitress WSGI server (production-grade)
REM   - Proper logging and error handling
REM   - Security headers enabled
REM   - Multi-threaded request handling
REM

echo.
echo ===============================================================
echo RUIE Production Server v0.2 Alpha
echo ===============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.10+ and add it to your PATH
    echo.
    pause
    exit /b 1
)

echo Checking dependencies...

REM Check if required packages are installed
python -c "import waitress" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Waitress not found. Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo ===============================================================
echo Starting Production Server (Waitress WSGI)...
echo ===============================================================
echo.
echo Configuration:
echo   Host: 127.0.0.1
echo   Port: 5000
echo   Environment: Production
echo   Debug: Off
echo   Server: Waitress
echo.
echo Open http://127.0.0.1:5000 in your browser
echo Press Ctrl+C to stop the server
echo ===============================================================
echo.

REM Run the production server
python run_production.py

if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start
    echo.
    pause
    exit /b 1
)

pause
