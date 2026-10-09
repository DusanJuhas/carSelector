@echo off
rem Prints a file/line/size summary of this repository's files - by
rem top-level directory (with a sub-row per file category) and by file
rem type. Thin wrapper around statistics.py (in this same directory) - the
rem actual scan logic, the category table and the exclusion rules
rem (venv/.git/caches) live there, see that script's own module docstring.
rem
rem Requires the same Python environment the rest of this project uses
rem (the repo-root venv) - though statistics.py itself only needs the
rem standard library (plus git for --tracked), so any Python 3.11+ on
rem PATH works too.
rem Run from anywhere; paths resolve relative to this script's own
rem location, not the current directory. Any arguments are forwarded
rem as-is to statistics.py, e.g.:
rem   scripts\statistics.bat --path backend
rem   scripts\statistics.bat --ext py              (the old Python-only report)
rem   scripts\statistics.bat --exclude storage --by type
rem   scripts\statistics.bat --tracked             (only files git tracks)

python "%~dp0statistics.py" %*
exit /b %ERRORLEVEL%
