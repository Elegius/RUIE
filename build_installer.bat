@echo off
REM Build RUIE Installer Script
REM This script compiles the PyInstaller exe and then creates an Inno Setup installer

setlocal enabledelayedexpansion

echo.
echo ================================
echo RUIE Installer Build Script
echo ================================
echo.

REM Check if Inno Setup is installed
set INNO_SETUP_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe

if not exist "%INNO_SETUP_PATH%" (
    echo Warning: Inno Setup 6 is not installed at the expected location.
    echo Please install Inno Setup 6 from: https://jrsoftware.org/isdl.php
    echo.
    echo You can still build the portable EXE by continuing.
    echo.
    set SKIP_INSTALLER=1
)

echo Step 1: Cleaning old builds...
echo.

if exist dist (
    echo Removing old dist folder...
    rmdir /s /q dist
)

if exist build (
    echo Removing old build folder...
    rmdir /s /q build
)

echo.
echo Step 2: Building PyInstaller executable...
echo.
echo This may take a few minutes, please wait...
echo.

REM Run PyInstaller
python -m PyInstaller RUIE.spec --clean

if errorlevel 1 (
    echo.
    echo Error: PyInstaller build failed!
    echo.
    echo Troubleshooting steps:
    echo 1. Make sure all dependencies are installed: pip install -r requirements-build.txt
    echo 2. Check that RUIE.spec exists in the current directory
    echo 3. Check that icon.ico exists in the current directory
    echo 4. Try running: python -m PyInstaller RUIE.spec --clean -y
    echo.
    pause
    exit /b 1
)

echo.
echo ================================
echo EXE Build Complete!
echo ================================
echo.
echo Portable EXE created at: dist\RUIE\RUIE.exe
echo.

REM Check if we should skip installer
if defined SKIP_INSTALLER (
    echo.
    echo Note: Skipping installer creation because Inno Setup is not installed.
    echo To create the installer, install Inno Setup 6 from: https://jrsoftware.org/isdl.php
    echo Then run: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" RUIE_Installer.iss
    echo.
    pause
    exit /b 0
)

echo Step 3: Building Inno Setup installer...
echo.

REM Run Inno Setup compiler
"%INNO_SETUP_PATH%" /cc RUIE_Installer.iss

if errorlevel 1 (
    echo.
    echo Error: Inno Setup compilation failed!
    echo.
    echo The portable EXE was created successfully at: dist\RUIE\RUIE.exe
    echo You can use that even if the installer creation fails.
    echo.
    pause
    exit /b 1
)

echo.
echo ================================
echo Build Complete!
echo ================================
echo.
echo Installer created at: dist\RUIE-0.2-Alpha-Installer.exe
echo Portable EXE at: dist\RUIE\RUIE.exe
echo.
pause
