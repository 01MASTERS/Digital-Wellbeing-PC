@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
py -3 -m pip install Pillow PyInstaller
if errorlevel 1 exit /b 1
py -3 -m scripts.create_icon
if errorlevel 1 exit /b 1
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name DigitalWellbeing --icon "assets\icon.ico" --add-data "digital_wellbeing\web;digital_wellbeing\web" --add-data "assets\icon.ico;assets" --add-data "assets\icon.png;assets" --hidden-import PIL --hidden-import win32com --hidden-import win32com.client run.py
if errorlevel 1 exit /b 1
echo Built dist\DigitalWellbeing.exe
