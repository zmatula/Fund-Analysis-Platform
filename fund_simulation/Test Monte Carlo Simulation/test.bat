@echo off
SETLOCAL EnableDelayedExpansion

echo Testing batch file with spaces in path
echo.

REM Get the directory where this script is located
set "APP_DIR=%~dp0"
echo APP_DIR is: %APP_DIR%

REM Path to subdirectory
set "PYTHON_DIR=%APP_DIR%python"
echo PYTHON_DIR is: %PYTHON_DIR%

REM Test the problematic line
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
echo PYTHON_EXE is: %PYTHON_EXE%

REM Test if statement
if not exist "%PYTHON_EXE%" (
    echo ERROR: File not found
    echo Expected location: "%PYTHON_DIR%"
)

echo.
echo If you see this, the batch file ran successfully!
pause
