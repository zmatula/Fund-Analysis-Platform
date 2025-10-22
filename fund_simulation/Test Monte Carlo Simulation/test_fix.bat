@echo off
REM Test WITH EnableDelayedExpansion (might break)
SETLOCAL EnableDelayedExpansion

set "TEST_PATH=C:\Program Files (x86)\Monte Carlo Fund Simulation\python\python.exe"

echo Testing WITH EnableDelayedExpansion:
if not exist "%TEST_PATH%" (
    echo File not found: "%TEST_PATH%"
)
echo Done with test 1
ENDLOCAL

echo.
echo ----------------------------------------
echo.

REM Test WITHOUT EnableDelayedExpansion (should work)
SETLOCAL

set "TEST_PATH=C:\Program Files (x86)\Monte Carlo Fund Simulation\python\python.exe"

echo Testing WITHOUT EnableDelayedExpansion:
if not exist "%TEST_PATH%" (
    echo File not found: "%TEST_PATH%"
)
echo Done with test 2
ENDLOCAL

pause
