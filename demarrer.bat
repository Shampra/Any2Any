@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"
if exist "%~dp0Any2Any.exe" (
  "%~dp0Any2Any.exe" %*
  exit /b
)
where py >nul 2>nul
if %errorlevel%==0 (py -3 app\server.py --profile unified %*) else (python app\server.py --profile unified %*)
if errorlevel 1 pause
