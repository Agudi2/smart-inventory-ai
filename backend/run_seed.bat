@echo off
REM Script to seed the database with sample data (Windows)
REM Usage: run_seed.bat

echo ==========================================
echo Database Seeding Script
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
echo Checking dependencies...
pip install -q -r requirements.txt

REM Run migrations
echo Running database migrations...
alembic upgrade head

REM Run seed script
echo.
python seed_data.py

echo.
echo ==========================================
echo Seeding complete!
echo ==========================================
pause
