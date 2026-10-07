@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0dist\DigitalWellbeing.exe" (
  start "" "%~dp0dist\DigitalWellbeing.exe"
  exit /b 0
)
py -3 -c "import psutil, win32gui" >nul 2>&1
if errorlevel 1 (
  echo Missing Python dependencies. Run build.cmd or: py -3 -m pip install -r requirements.txt
  pause
  exit /b 1
)
start "" pyw -3 "%~dp0run.py"
