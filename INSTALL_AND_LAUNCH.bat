@echo off
setlocal
cd /d "%~dp0"
title NexClick Control Studio - Installer
echo.
echo  NEXCLICK CONTROL STUDIO
echo  -----------------------
echo  Installing required Python package...
py -m pip install --user --upgrade pynput
if errorlevel 1 (
  echo.
  echo Could not install pynput. Check your Python installation and internet connection.
  pause
  exit /b 1
)
echo.
echo Starting NexClick...
py nexclick_control_studio.py
if errorlevel 1 (
  echo.
  echo NexClick closed with an error. Read the message above.
  pause
)
endlocal
