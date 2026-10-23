@echo off
title ANI HARDWARE INFO
cd /d "%~dp0"
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
py -3 main.py
if errorlevel 1 pause
