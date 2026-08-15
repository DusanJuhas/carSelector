@echo off
REM Starts the DriveWise AI frontend UI locally (just the frontend process -
REM the chat flow calls the real backend API, see backend\README.md, and
REM expects it running at http://localhost:8000 unless VITE_API_BASE_URL
REM says otherwise).

set "FRONTEND_DIR=%~dp0..\frontend"
cd /d "%FRONTEND_DIR%" || exit /b 1

if not exist node_modules (
    call npm install
)

call npm run dev
