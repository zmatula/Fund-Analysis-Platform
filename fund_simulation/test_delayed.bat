@echo off
SETLOCAL EnableDelayedExpansion

echo Test 1: WITH EnableDelayedExpansion > test_output.txt
set "APP_DIR=C:\Program Files (x86)\Monte Carlo Fund Simulation\" >> test_output.txt
set "PYTHON_DIR=%APP_DIR%python" >> test_output.txt
echo PYTHON_DIR=%PYTHON_DIR% >> test_output.txt

if not exist "%PYTHON_DIR%\python.exe" (
    echo File not found at: "%PYTHON_DIR%" >> test_output.txt
) else (
    echo File exists at: "%PYTHON_DIR%" >> test_output.txt
)

echo Test 1 complete >> test_output.txt
ENDLOCAL

SETLOCAL

echo. >> test_output.txt
echo Test 2: WITHOUT EnableDelayedExpansion >> test_output.txt
set "APP_DIR=C:\Program Files (x86)\Monte Carlo Fund Simulation\" >> test_output.txt
set "PYTHON_DIR=%APP_DIR%python" >> test_output.txt
echo PYTHON_DIR=%PYTHON_DIR% >> test_output.txt

if not exist "%PYTHON_DIR%\python.exe" (
    echo File not found at: "%PYTHON_DIR%" >> test_output.txt
) else (
    echo File exists at: "%PYTHON_DIR%" >> test_output.txt
)

echo Test 2 complete >> test_output.txt
ENDLOCAL

echo Tests complete - check test_output.txt
