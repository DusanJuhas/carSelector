@echo off
rem Backs up the production database (Neon) with pg_dump into a local
rem folder, verifies the dump and prunes old ones. Thin wrapper around
rem backup_neon.py (in this same directory) - configuration, retention
rem rules and the restore command are described in that script's module
rem docstring.
rem
rem Meant for Windows Task Scheduler (daily). Needs, as user environment
rem variables - never on this command line, the URL holds a password:
rem   NEON_BACKUP_URL   Neon's direct connection string
rem   NEON_BACKUP_DIR   backup folder outside the repo
rem   PG_BIN            optional, folder with pg_dump/pg_restore (Postgres 17)
rem Uses the repo-root venv's Python when it exists (the script itself only
rem needs the standard library). Any arguments are forwarded, e.g.:
rem   scripts\backup_neon.bat --keep-daily 30

setlocal
set "PY=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0backup_neon.py" %*
exit /b %ERRORLEVEL%
