#!/usr/bin/env bash
# Starts the DriveWise AI frontend UI locally (just the frontend process -
# the chat flow calls the real backend API, see backend/README.md, and
# expects it running at http://localhost:8000 unless VITE_API_BASE_URL
# says otherwise).
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
frontend_dir="$script_dir/../frontend"

cd "$frontend_dir"
if [ ! -d node_modules ]; then
    npm install
fi
npm run dev
