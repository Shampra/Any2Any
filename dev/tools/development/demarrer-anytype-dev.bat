@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0..\..\.."
set "ANY2ANY_PROFILE=anytype-dev"
where py >nul 2>nul
if %errorlevel%==0 (py -3 app\server.py --profile anytype-dev %*) else (python app\server.py --profile anytype-dev %*)
if errorlevel 1 pause
