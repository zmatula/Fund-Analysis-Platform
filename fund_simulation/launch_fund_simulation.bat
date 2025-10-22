@echo off
REM Monte Carlo Fund Simulation Launcher
REM This script sets up and launches the application

SETLOCAL EnableDelayedExpansion

echo ========================================
echo   Monte Carlo Fund Simulation
echo ========================================
echo.

REM Get the directory where this script is located
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM Check if virtual environment exists
if not exist "venv\" (
    echo First-time setup detected...
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create virtual environment.
        echo Please ensure Python 3.8 or higher is installed.
        echo Download from: https://www.python.org/downloads/
        pause
        exit /b 1
    )

    echo Installing dependencies...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
    echo.
    echo Setup complete!
    echo.
) else (
    call venv\Scripts\activate.bat
)

REM Clear any existing Python cache
echo Clearing cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Launch Streamlit
echo.
echo Starting application...
echo The app will open in your browser automatically.
echo.
echo To stop the application, close this window or press Ctrl+C.
echo ========================================
echo.

REM Start Streamlit with auto-open browser
start "" http://localhost:8501
streamlit run app.py --server.port 8501 --server.headless true

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application stopped with an error.
    pause
)
