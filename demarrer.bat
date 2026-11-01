@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 server.py --profile unified %*) else (python server.py --profile unified %*)
if errorlevel 1 pause
