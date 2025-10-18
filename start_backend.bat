@echo off
echo ========================================
echo  Starting StratMancer Backend API
echo ========================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if exist "Scripts\activate.bat" (
    echo Activating virtual environment...
    call Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
    echo Using system Python...
)

echo.
echo Starting API server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

pause

