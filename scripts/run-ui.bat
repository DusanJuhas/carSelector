@echo off
REM Starts the DriveWise AI frontend UI locally.
REM The chat flow is currently backed by a scripted mock (frontend\src\api\mock\conversation.ts),
REM so this is self-contained: no backend, database, or ANTHROPIC_API_KEY required.

set "FRONTEND_DIR=%~dp0..\frontend"
cd /d "%FRONTEND_DIR%" || exit /b 1

if not exist node_modules (
    call npm install
)

call npm run dev
