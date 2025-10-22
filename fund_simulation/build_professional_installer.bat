@echo off
REM ==============================================================================
REM  Monte Carlo Fund Simulation - Professional Installer Build Script
REM ==============================================================================
REM  This script creates a standalone Windows installer that:
REM    - Bundles Python and all dependencies into a single .exe
REM    - Requires NO Python installation on target machines
REM    - Creates a professional Windows installer (.exe)
REM
REM  Prerequisites:
REM    1. Python 3.8+ with all dependencies installed
REM    2. PyInstaller: pip install pyinstaller
REM    3. Inno Setup 6.0+: https://jrsoftware.org/isinfo.php
REM ==============================================================================

SETLOCAL EnableDelayedExpansion

echo.
echo ================================================================================
echo   Monte Carlo Fund Simulation - Professional Installer Build
echo ================================================================================
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM ==============================================================================
REM Step 1: Environment Check
REM ==============================================================================

echo [1/5] Checking environment...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found in PATH
    echo   Please install Python 3.8 or higher
    pause
    exit /b 1
)
echo   Python: OK

REM Check PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo   ERROR: PyInstaller not installed
    echo   Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo   ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)
echo   PyInstaller: OK

REM Check Inno Setup
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

REM Check required files
echo.
echo   Verifying project files...
set FILES_MISSING=0

if not exist "launcher.py" (
    echo     ERROR: launcher.py not found
    set FILES_MISSING=1
)

if not exist "app.py" (
    echo     ERROR: app.py not found
    set FILES_MISSING=1
)

if not exist "FundSimulation.spec" (
    echo     ERROR: FundSimulation.spec not found
    set FILES_MISSING=1
)

if not exist "fund_simulation" (
    echo     ERROR: fund_simulation directory not found
    set FILES_MISSING=1
)

if not exist "installer_professional.iss" (
    echo     ERROR: installer_professional.iss not found
    set FILES_MISSING=1
)

if %FILES_MISSING%==1 (
    echo.
    echo   Build failed: Missing required files
    pause
    exit /b 1
)

echo     All required files found
echo.

REM ==============================================================================
REM Step 2: Clean Previous Build
REM ==============================================================================

echo [2/5] Cleaning previous build artifacts...
echo.

if exist "build" (
    echo   Removing build directory...
    rmdir /s /q build
)

if exist "dist" (
    echo   Removing dist directory...
    rmdir /s /q dist
)

if exist "installer_output" (
    echo   Removing installer_output directory...
    rmdir /s /q installer_output
)

REM Clean Python cache
echo   Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
if exist "*.pyc" del /s /q *.pyc >nul 2>&1

echo   Clean complete
echo.

REM ==============================================================================
REM Step 3: Build Standalone Executable with PyInstaller
REM ==============================================================================

echo [3/5] Building standalone executable...
echo.
echo   This may take 5-10 minutes...
echo   (PyInstaller is analyzing dependencies and bundling everything)
echo.

pyinstaller --clean --noconfirm FundSimulation.spec

if errorlevel 1 (
    echo.
    echo   ERROR: PyInstaller build failed
    echo   Check the error messages above
    pause
    exit /b 1
)

REM Verify executable was created
if not exist "dist\MonteCarloFundSimulation.exe" (
    echo.
    echo   ERROR: Executable not found after build
    echo   Expected: dist\MonteCarloFundSimulation.exe
    pause
    exit /b 1
)

echo.
echo   Executable built successfully!
echo   Location: dist\MonteCarloFundSimulation.exe
echo.

REM Show file size
for %%A in (dist\MonteCarloFundSimulation.exe) do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo   Size: !sizeMB! MB
)

echo.

REM ==============================================================================
REM Step 4: Test Executable (Optional)
REM ==============================================================================

echo [4/5] Would you like to test the executable before packaging? (Y/N)
set /p TEST_EXE="      "

if /i "%TEST_EXE%"=="Y" (
    echo.
    echo   Launching test...
    echo   Close the application window when done testing.
    echo.
    start /wait dist\MonteCarloFundSimulation.exe
    echo.
    echo   Did the application work correctly? (Y/N)
    set /p TEST_OK="      "

    if /i "!TEST_OK!" NEQ "Y" (
        echo.
        echo   Build stopped by user - application test failed
        echo   Please fix issues and try again
        pause
        exit /b 1
    )
)

echo.

REM ==============================================================================
REM Step 5: Build Windows Installer with Inno Setup
REM ==============================================================================

echo [5/5] Building Windows installer...
echo.

REM Create output directory
mkdir installer_output >nul 2>&1

"%INNO_PATH%" "installer_professional.iss"

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
echo   Your professional installer is ready:
echo.

dir installer_output\*.exe | find "MonteCarloFundSimulation_Setup"

echo.
echo   This installer:
echo     - Requires NO Python on target machines
echo     - Bundles ALL dependencies (200MB+)
echo     - Creates professional Windows installation
echo     - Includes Start Menu and Desktop shortcuts
echo     - Can be distributed to non-technical users
echo.
echo   Next steps:
echo     1. Test the installer on a clean Windows machine
echo     2. Verify the application runs without Python installed
echo     3. Distribute to your team!
echo.
echo ================================================================================
echo.

pause
