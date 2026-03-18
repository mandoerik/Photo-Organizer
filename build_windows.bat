@echo off
echo ============================================
echo  Photo Organizer - Windows Build Script
echo ============================================
echo.

REM Handle UNC paths (e.g. VMware shared folders) by mapping a drive letter
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~0,2%"=="\\" (
    echo Detected UNC path, mapping drive letter...
    net use Z: /delete >nul 2>&1
    net use Z: "%SCRIPT_DIR:~0,-1%" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Could not map UNC path to drive letter.
        pause
        exit /b 1
    )
    Z:
    cd \
) else (
    cd /d "%SCRIPT_DIR%"
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv_win" (
    echo Creating virtual environment...
    python -m venv venv_win
)

REM Activate virtual environment and install dependencies
echo Installing dependencies...
call venv_win\Scripts\activate.bat
pip install -r requirements.txt

REM Generate .ico if it doesn't exist (requires Pillow)
if not exist "photo_organizer.ico" (
    echo Generating Windows icon...
    python generate_ico.py
)

REM Build the executable
echo Building Windows executable...
pyinstaller photo_organizer_win.spec --clean

echo.
echo ============================================
echo  Build complete!
echo  Output: dist\PhotoOrganizer.exe
echo ============================================
pause
