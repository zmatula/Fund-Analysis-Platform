@echo off
REM ==============================================================================
REM  Monte Carlo Fund Simulation - Build Installer with Embedded Python
REM ==============================================================================
REM  This creates a FULLY STANDALONE installer with Python embedded
REM  NO Python installation required on target machines!
REM ==============================================================================

SETLOCAL EnableDelayedExpansion

echo.
echo ================================================================================
echo   Monte Carlo Fund Simulation
echo   Building Installer with Embedded Python
echo ================================================================================
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM ==============================================================================
REM Step 1: Check if Embedded Python Already Downloaded
REM ==============================================================================

echo [1/3] Checking for embedded Python...
echo.

if exist "python_embedded\python\python.exe" (
    echo   Embedded Python found!
    echo   Location: python_embedded\python\
    echo.
) else (
    echo   Embedded Python NOT found
    echo.
    echo   You need to download it first. This is a one-time ~20 MB download.
    echo.
    set /p DOWNLOAD="   Download embedded Python now? (Y/N): "

    if /i "!DOWNLOAD!" NEQ "Y" (
        echo.
        echo   Build cancelled. Run download_python_embedded.bat first.
        pause
        exit /b 1
    )

    echo.
    echo   Downloading embedded Python...
    call download_python_embedded.bat

    if errorlevel 1 (
        echo.
        echo   ERROR: Failed to download embedded Python
        pause
        exit /b 1
    )
)

REM ==============================================================================
REM Step 2: Verify Inno Setup
REM ==============================================================================

echo [2/3] Checking for Inno Setup...
echo.

set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" (
    echo   ERROR: Inno Setup not found at: %INNO_PATH%
    echo.
    echo   Please install Inno Setup 6 from:
    echo   https://jrsoftware.org/isinfo.php
    echo.
    pause
    exit /b 1
)
echo   Inno Setup: OK
echo.

REM ==============================================================================
REM Step 3: Build Installer
REM ==============================================================================

echo [3/3] Building installer with Inno Setup...
echo.
echo   This may take 30-60 seconds due to Python compression...
echo.

REM Create output directory
if not exist "installer_output" mkdir installer_output

REM Build with Inno Setup
"%INNO_PATH%" "installer_with_python.iss"

if errorlevel 1 (
    echo.
    echo   ERROR: Installer build failed
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo   BUILD SUCCESSFUL!
echo ================================================================================
echo.
echo   Your standalone installer is ready:
echo.

dir installer_output\FundSimulation_WithPython_Setup*.exe | find "FundSimulation"

echo.
echo   This installer:
echo     Includes Python (NO installation needed on target machines!)
echo     Size: ~30 MB (includes Python + your app)
echo     Works on ANY Windows 10/11 computer
echo     Fully self-contained
echo.
echo   Distribution:
echo     1. Test the installer on this machine
echo     2. Share the .exe file with your team
echo     3. Users just run it - no prerequisites!
echo.
echo ================================================================================
echo.

pause
