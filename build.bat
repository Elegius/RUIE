@echo off
REM Build script for RUIE
REM Compiles the app into a single standalone executable using PyInstaller

cd /d "%~dp0"

echo.
echo ===== RUIE - Build Standalone EXE =====
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo.
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "build" rmdir /s /q "build" >nul 2>&1

echo.
echo Building standalone executable...
echo This may take a few minutes...
echo.

REM Build the exe with PyInstaller using python -m to avoid PATH issues
REM --onefile: Creates a single executable
REM --windowed: No console window
REM --icon: Window and taskbar icon
REM --add-data: Include public folder with all assets
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --icon="%cd%\icon.ico" ^
    --name="RUIE" ^
    --distpath="dist" ^
    --workpath="build" ^
    --specpath="build" ^
    --add-data "%cd%\public;public" ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtWebEngineWidgets ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=flask ^
    --hidden-import=flask_cors ^
    --hidden-import=server ^
    --hidden-import=launcher_detector ^
    --hidden-import=color_replacer ^
    --hidden-import=media_replacer ^
    launcher.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ===== Build Complete =====
echo.
echo Created: dist\RUIE.exe
echo.
echo You can now:
echo   1. Double-click the exe to run the app
echo   2. Move it anywhere you want
echo.
pause
