@echo off
REM Download Python Embeddable Package for bundling with installer

echo ========================================
echo  Downloading Python Embeddable Package
echo ========================================
echo.

REM Create directory for embedded Python
if not exist "python_embedded" mkdir python_embedded

REM Download Python 3.11 Embeddable Package (AMD64)
echo Downloading Python 3.11.9 Embeddable (AMD64)...
echo This is a ~20 MB download...
echo.

curl -L -o python_embedded\python-3.11.9-embed-amd64.zip https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip

if errorlevel 1 (
    echo.
    echo ERROR: Download failed
    echo Please check your internet connection
    pause
    exit /b 1
)

echo.
echo Extracting Python...
powershell -Command "Expand-Archive -Path python_embedded\python-3.11.9-embed-amd64.zip -DestinationPath python_embedded\python -Force"

echo.
echo Cleaning up...
del python_embedded\python-3.11.9-embed-amd64.zip

REM Enable pip in embedded Python
echo.
echo Configuring embedded Python to support pip...

REM Uncomment the import site line in python311._pth
powershell -Command "(Get-Content python_embedded\python\python311._pth) -replace '#import site', 'import site' | Set-Content python_embedded\python\python311._pth"

REM Download get-pip.py
echo Downloading pip installer...
curl -o python_embedded\python\get-pip.py https://bootstrap.pypa.io/get-pip.py

REM Install pip
echo Installing pip...
python_embedded\python\python.exe python_embedded\python\get-pip.py

echo.
echo ========================================
echo  SUCCESS!
echo ========================================
echo.
echo Embedded Python is ready in: python_embedded\python\
echo.
echo Next step: Run build_installer_with_python.bat
echo.
pause
