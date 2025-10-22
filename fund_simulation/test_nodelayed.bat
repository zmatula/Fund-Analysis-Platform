@echo off
REM Test WITHOUT EnableDelayedExpansion
SETLOCAL

echo ========================================
echo   Monte Carlo Fund Simulation
echo ========================================
echo.

REM Simulate the path with spaces
set "APP_DIR=C:\Program Files (x86)\Monte Carlo Fund Simulation\"
set "PYTHON_DIR=%APP_DIR%python"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

echo Testing path variables:
echo APP_DIR=%APP_DIR%
echo PYTHON_DIR=%PYTHON_DIR%
echo PYTHON_EXE=%PYTHON_EXE%
echo.

REM Test IF statement with quoted path
if not exist "%PYTHON_EXE%" (
    echo ERROR: Embedded Python not found!
    echo Expected location: "%PYTHON_DIR%"
    echo.
    echo This is the critical test - if you see this, the IF block worked!
) else (
    echo SUCCESS: Found Python at "%PYTHON_EXE%"
)

echo.
echo If you see this message, the batch file executed successfully!
pause
