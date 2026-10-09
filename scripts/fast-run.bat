@echo off
REM Starts the DriveWise AI app (API + UI, one process) like run.bat, but
REM skips the startup housekeeping: no alembic migrations and no scraper
REM data import - the database is used exactly as it is. Use run.bat
REM after pulling new migrations or when the catalog should pick up
REM fresh scraper data.

setlocal
cd /d "%~dp0.."

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo No .venv found at repo root - run this first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements-dev.txt
    exit /b 1
)

cd backend
echo Starting DriveWise AI at http://localhost:8000/  (API docs at /docs)
echo (fast run: database migrations and scraper import skipped)
python -m uvicorn app.main:app --reload

endlocal
