@echo off
title KQ Sortify Launcher
echo Membuka KQ Sortify Desktop GUI...
cd /d "%~dp0"

if exist "KQ_Sortify.exe" (
    start "" "KQ_Sortify.exe"
    exit
)

python gui.py
pause
