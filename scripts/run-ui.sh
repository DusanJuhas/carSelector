#!/usr/bin/env bash
# Starts the DriveWise AI frontend UI locally.
# The chat flow is currently backed by a scripted mock (frontend/src/api/mock/conversation.ts),
# so this is self-contained: no backend, database, or ANTHROPIC_API_KEY required.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
frontend_dir="$script_dir/../frontend"

cd "$frontend_dir"
if [ ! -d node_modules ]; then
    npm install
fi
npm run dev
