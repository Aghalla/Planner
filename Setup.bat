@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  Planner - Automatic Setup
echo ========================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
    set "PY=py"
) else (
    set "PY=python"
)

%PY% --version >nul 2>&1
if not %errorlevel%==0 (
    echo [ERROR] Python not found! Please install Python 3.12+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
if not exist ".venv" (
    %PY% -m venv .venv
    if not %errorlevel%==0 (
        echo [ERROR] Could not create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists, skipping.
)

echo [2/4] Installing requirements...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if not %errorlevel%==0 (
    echo [ERROR] Could not install requirements.
    pause
    exit /b 1
)

echo [3/4] Running migrations...
".venv\Scripts\python.exe" manage.py migrate
if not %errorlevel%==0 (
    echo [ERROR] Migration failed.
    pause
    exit /b 1
)

echo [4/4] Seeding daily content...
".venv\Scripts\python.exe" manage.py seed_content

echo.
echo ========================================
echo  Setup complete!
echo  1. Create an account at the register page
echo  2. Run Planner.bat to start the app
echo ========================================
pause
