@echo off
REM Run PowerShell script as Administrator for Task Scheduler setup

cls
echo.
echo ========================================
echo Travel Agency Inquiry Cleanup Setup
echo ========================================
echo.
echo This will create a daily inquiry cleanup task in Windows Task Scheduler.
echo.

REM Get current directory
cd /d "%~dp0"

REM Run PowerShell as Administrator
powershell -NoProfile -ExecutionPolicy Bypass -Command "& {Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0setup_inquiry_cleanup_scheduler.ps1\"' -Verb RunAs}"

echo.
echo Setup complete! Check Task Scheduler for the inquiry cleanup task.
echo.
pause
