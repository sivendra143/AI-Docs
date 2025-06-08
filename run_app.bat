@echo off
echo Starting application...

REM Run the PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_app.ps1"

REM Keep the window open
pause
