# Starts the DriveWise AI frontend UI locally (just the frontend process -
# the chat flow calls the real backend API, see backend/README.md, and
# expects it running at http://localhost:8000 unless VITE_API_BASE_URL
# says otherwise).

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
