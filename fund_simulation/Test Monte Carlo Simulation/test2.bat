@echo off
SETLOCAL EnableDelayedExpansion

REM This simulates the issue
set "MY_PATH=C:\Program Files (x86)\Monte Carlo Fund Simulation\python"
echo Path is: "%MY_PATH%"

REM Test with %VAR% inside IF block (might cause parsing error)
if not exist "%MY_PATH%\python.exe" (
    echo File not found at: "%MY_PATH%"
)

echo If you see this, it worked!
pause
