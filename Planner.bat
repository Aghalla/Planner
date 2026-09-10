@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
    pause
    exit /b 1
)
echo Starting Planner...
start "" http://127.0.0.1:8000/
".venv\Scripts\python.exe" manage.py runserver 8000
pause
