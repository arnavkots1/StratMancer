@echo off
REM Installation script for StratMancer (Windows)

echo ==========================================
echo StratMancer Installation
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Setup .env
if not exist .env (
    echo Setting up .env file...
    copy .env.example .env
    echo OK .env created
    echo WARNING Please edit .env and add your Riot API key
) else (
    echo OK .env already exists
)
echo.

REM Create directories
echo Creating directories...
if not exist data mkdir data
if not exist data\raw mkdir data\raw
if not exist data\processed mkdir data\processed
if not exist logs mkdir logs
echo OK Directories created
echo.

REM Run status check
echo Running status check...
python check_status.py
echo.

echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env and add your Riot API key
echo 2. Run: python quickstart.py
echo 3. Read: GET_STARTED.md
echo.
pause

