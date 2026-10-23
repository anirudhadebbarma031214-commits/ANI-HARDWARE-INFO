@echo off
title Build ANI HARDWARE INFO
cd /d "%~dp0"
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt pyinstaller
py -3 -m PyInstaller --noconfirm --clean --windowed --name "ANI-HARDWARE-INFO" main.py
echo.
echo If successful, your app is in the dist folder.
pause
