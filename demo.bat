@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 server.py --demo) else (python server.py --demo)
if errorlevel 1 pause
