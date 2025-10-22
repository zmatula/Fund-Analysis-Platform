@echo off
REM Monte Carlo Fund Simulation Launcher (Uses Embedded Python)
REM This script uses the bundled portable Python - no system Python needed!

SETLOCAL

cls
echo.
echo ========================================
echo   Monte Carlo Fund Simulation
echo   Version 1.0.0
echo ========================================
echo.

REM Get the directory where this script is located (includes trailing backslash)
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM Path to embedded Python (APP_DIR already has trailing backslash)
set "PYTHON_DIR=%APP_DIR%python"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

REM Check if embedded Python exists
if not exist "%PYTHON_EXE%" (
    echo ERROR: Embedded Python not found!
    echo Expected location: "%PYTHON_DIR%"
    echo.
    echo Please reinstall the application.
    pause
    exit /b 1
)

REM Check if packages are installed (check for streamlit)
echo Initializing...
"%PYTHON_EXE%" -c "import streamlit" 2>nul
if errorlevel 1 (
    echo.
    echo ----------------------------------------
    echo   FIRST-TIME SETUP
    echo ----------------------------------------
    echo.
    echo This is your first time running the application.
    echo Installing required packages...
    echo.
    echo This will take 2-3 minutes. Please wait.
    echo ----------------------------------------
    echo.

    REM Ensure pip is available
    echo [1/3] Checking for pip package manager...
    "%PYTHON_EXE%" -m ensurepip --default-pip 2>nul
    if errorlevel 1 (
        echo       Installing pip...
        "%PYTHON_EXE%" "%PYTHON_DIR%\get-pip.py"
        echo       ✓ Pip installed
    ) else (
        echo       ✓ Pip already available
    )
    echo.

    REM Upgrade pip
    echo [2/3] Upgrading pip to latest version...
    "%PYTHON_EXE%" -m pip install --upgrade pip --quiet
    echo       ✓ Pip upgraded
    echo.

    REM Install dependencies
    echo [3/3] Installing application packages:
    echo       - streamlit (web framework)
    echo       - pandas (data processing)
    echo       - plotly (charts and graphs)
    echo       - numpy (numerical computing)
    echo       - openpyxl (Excel export)
    echo       - kaleido (chart rendering)
    echo       - and more...
    echo.
    echo       This may take 2-3 minutes...
    echo.
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ✗ ERROR: Failed to install dependencies.
        echo.
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
    echo.
    echo ========================================
    echo   ✓ SETUP COMPLETE!
    echo ========================================
    echo.
    echo All packages installed successfully.
    echo Starting application...
    echo.
	echo ========================================
	echo   BRO LOLLOLOLO
	echo  ========================================
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo YoU InStAlLeD RuSsIaN MaLwAre LOLOLOLOLOLOLOLOLO
	echo HAHAHAHAHAHAHAHAHAH!!!
	echo SUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKERSUCKER
	echo !&^%&^%$*$%*)_(*&)*&%*^%$*&^(*_*(&*&^%$
	echo  ========================================
) else (
    echo ✓ Packages already installed
    echo.
)

REM Clear any existing Python cache
echo Preparing application...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

REM Launch Streamlit
echo.
echo ========================================
echo   LAUNCHING APPLICATION
echo ========================================
echo.
echo Opening browser at http://localhost:8501
echo.
echo The application will start in a few seconds...
echo.
echo To stop: Close this window or press Ctrl+C
echo ========================================
echo.

REM Start Streamlit with auto-open browser
start "" http://localhost:8501
"%PYTHON_EXE%" -m streamlit run app.py --server.port 8501 --server.headless true

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application stopped with an error.
    pause
)
