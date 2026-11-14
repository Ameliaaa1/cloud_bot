@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python or add it to PATH.
  pause
  exit /b 1
)
python emotion_control.py %*
if errorlevel 1 (
  echo.
  echo cloud_bot stopped with an error. Read the message above.
  pause
)
