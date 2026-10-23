# ANI HARDWARE INFO

A Cyber Blue Windows desktop dashboard for viewing hardware details reported by your PC.

## Features
- CPU name, manufacturer, cores, logical processors and reported maximum clock
- Physical memory capacity and current RAM usage
- Windows graphics adapter names, reported VRAM and driver versions
- Physical disks and mounted-volume capacity / free space
- Windows version, computer manufacturer/model, motherboard and BIOS details
- Battery details when Windows reports a battery
- Refresh button for a new hardware snapshot

## Requirements
- Windows 10 or Windows 11
- Python 3.10 or newer
- Internet access the first time to install dependencies

## Run from source
1. Install Python from https://www.python.org/downloads/ and enable Add Python to PATH.
2. Download this repository using Code > Download ZIP, then extract it.
3. Double-click run.bat, or open Command Prompt in the folder and run:
   - py -3 -m pip install -r requirements.txt
   - py -3 main.py

## Build a Windows EXE
Double-click build_exe.bat. PyInstaller should create the app in the dist folder.

## Data accuracy notes
The app reads information from Windows CIM/WMI and the local operating system. Some manufacturers do not expose every field. Missing values are shown as Not reported rather than guessed. GPU memory can be incomplete. This app does not claim to measure live CPU/GPU temperatures, fan speeds, or voltage sensors.

## Troubleshooting
- If py is not recognized, reinstall Python and enable Add Python to PATH, or use python in the commands.
- If PowerShell hardware details are blank, try running on Windows with permission to query CIM.
- If a value says Not reported, Windows may not expose that field on your device.
