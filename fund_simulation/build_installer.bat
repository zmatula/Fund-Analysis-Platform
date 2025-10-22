@echo off
REM Build script for creating Windows installer
REM Requires Inno Setup to be installed: https://jrsoftware.org/isinfo.php

echo ========================================
echo  Monte Carlo Fund Simulation
echo  Installer Build Script
echo ========================================
echo.

REM Check if Inno Setup is installed
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" (
    echo ERROR: Inno Setup not found at: %INNO_PATH%
    echo.
    echo Please install Inno Setup 6 from:
    echo https://jrsoftware.org/isinfo.php
    echo.
    pause
    exit /b 1
)

REM Clean previous build
echo Step 1: Cleaning previous build...
if exist "installer_output" (
    rmdir /s /q installer_output
)
mkdir installer_output

REM Verify required files exist
echo Step 2: Verifying files...
set FILES_MISSING=0

if not exist "app.py" (
    echo   ERROR: app.py not found
    set FILES_MISSING=1
)

if not exist "requirements.txt" (
    echo   ERROR: requirements.txt not found
    set FILES_MISSING=1
)

if not exist "launch_fund_simulation.bat" (
    echo   ERROR: launch_fund_simulation.bat not found
    set FILES_MISSING=1
)

if not exist "fund_simulation" (
    echo   ERROR: fund_simulation directory not found
    set FILES_MISSING=1
)

if not exist "installer.iss" (
    echo   ERROR: installer.iss not found
    set FILES_MISSING=1
)

if %FILES_MISSING%==1 (
    echo.
    echo Build failed: Missing required files
    pause
    exit /b 1
)

echo   All required files found!

REM Build installer
echo.
echo Step 3: Building installer with Inno Setup...
echo.

"%INNO_PATH%" "installer.iss"

if errorlevel 1 (
    echo.
    echo ERROR: Installer build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo  BUILD SUCCESSFUL!
echo ========================================
echo.
echo Installer created in: installer_output\
echo.
dir installer_output\*.exe
echo.
echo You can now distribute this installer to your team.
echo.
pause
