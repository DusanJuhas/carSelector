@echo off
REM Starts the DriveWise AI app: one process serves both the REST API
REM (/api/*) and the chat UI (/) - see backend/app/ui/ and
REM backend/README.md's "Run (API + UI)" section. There's no separate
REM frontend to start since the Node.js/React frontend was replaced by a
REM NiceGUI UI mounted directly onto this same FastAPI app.

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
python -m uvicorn app.main:app --reload

endlocal
