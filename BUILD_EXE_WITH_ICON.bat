@echo off
setlocal
cd /d "%~dp0"
title Build NexClick Control Studio
echo Installing PyInstaller...
py -m pip install --user --upgrade pyinstaller pynput
if errorlevel 1 (echo Installation failed.& pause & exit /b 1)
echo Building standalone EXE with NexClick icon...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "NexClick Control Studio" --icon "nexclick.ico" --add-data "nexclick.ico;." nexclick_control_studio.py
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)
echo.
echo Done. EXE is in the dist folder.
pause
endlocal
