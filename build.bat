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
REM --windowed: No console window
REM --icon: Window and taskbar icon
REM --add-data: Include public folder with all assets
REM NOTE: Not using --onefile due to path spaces causing DLL loading issues
REM The directory structure in dist/RUIE/ is more reliable for DLL extraction
python -m PyInstaller ^
    --windowed ^
    --icon="%cd%\icon.ico" ^
    --name="RUIE" ^
    --distpath="dist" ^
    --workpath="build" ^
    --specpath="build" ^
    --add-data "%cd%\public;public" ^
    --add-data "%cd%\assets;assets" ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtWebEngineWidgets ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtWebEngineCore ^
    --hidden-import=PyQt5.QtWebChannel ^
    --hidden-import=flask ^
    --hidden-import=flask_cors ^
    --hidden-import=server ^
    --hidden-import=launcher_detector ^
    --hidden-import=color_replacer ^
    --hidden-import=media_replacer ^
    --hidden-import=waitress ^
    --hidden-import=werkzeug ^
    --hidden-import=jinja2 ^
    --hidden-import=markupsafe ^
    --hidden-import=itsdangerous ^
    --hidden-import=click ^
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
echo Created: dist\RUIE\RUIE.exe
echo.
echo To use the portable app:
echo   1. Copy the entire dist\RUIE folder to your desired location
echo   2. Double-click RUIE.exe to run
echo   3. Or move just the RUIE folder to a USB drive for portability
echo.
pause
