@echo off
REM Batch file to run backup script
REM Can be scheduled with Windows Task Scheduler

echo.
echo ========================================
echo Travel Agency Backup Task
echo Time: %date% %time%
echo ========================================
echo.

REM Navigate to project directory
cd /d "C:\Users\ENZO KOPS\Desktop\TryNewWebsite\travel_agency_enhanced\fixed"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run backup script
echo Starting backup...
python scripts\backup_uploads.py

REM Check if successful
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Backup completed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Backup failed with error code: %errorlevel%
    echo ========================================
)

echo.
pause
