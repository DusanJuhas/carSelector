@echo off
rem Downloads the current Opel CZ personal-car price lists into
rem scraper\tests\fixtures\. Thin wrapper around download_opel_pricelists.py
rem (in this same directory) - the actual download logic lives there,
rem using Python's `requests` library, because Windows' own curl.exe uses
rem a different TLS stack (Schannel) that opel.cz's Akamai WAF blocks even
rem with a full browser header set, while `requests` gets through with the
rem exact same headers - see that script's own module docstring.
rem
rem Requires the same Python environment the rest of this project uses
rem (the repo-root venv - `requests` is already a dependency there, see
rem requirements.txt). Run from anywhere; paths resolve relative to this
rem script's own location, not the current directory.

python "%~dp0download_opel_pricelists.py"
exit /b %ERRORLEVEL%
