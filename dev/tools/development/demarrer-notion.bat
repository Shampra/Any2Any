@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0..\..\.."
set "ANY2ANY_PROFILE=notion-dev"
where py >nul 2>nul
if %errorlevel%==0 (py -3 app\server.py --profile notion-dev %*) else (python app\server.py --profile notion-dev %*)
if errorlevel 1 pause
