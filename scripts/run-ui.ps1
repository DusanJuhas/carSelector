# Starts the DriveWise AI frontend UI locally.
# The chat flow is currently backed by a scripted mock (frontend/src/api/mock/conversation.ts),
# so this is self-contained: no backend, database, or ANTHROPIC_API_KEY required.

$ErrorActionPreference = "Stop"
$frontendDir = Join-Path $PSScriptRoot "..\frontend"

Push-Location $frontendDir
try {
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run dev
} finally {
    Pop-Location
}
