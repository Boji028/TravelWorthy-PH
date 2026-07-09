@echo off
REM Batch file to run inquiry cleanup script
REM Can be scheduled with Windows Task Scheduler

echo.
echo ========================================
echo Travel Agency Inquiry Cleanup Task
echo Time: %date% %time%
echo ========================================
echo.

REM Navigate to project directory
cd /d "C:\Users\ENZO KOPS\Desktop\TryNewWebsite\travel_agency_enhanced\fixed"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run cleanup script
echo Starting inquiry cleanup...
python scripts\run_inquiry_cleanup.py

REM Check if successful
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Inquiry cleanup completed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Inquiry cleanup failed with error code: %errorlevel%
    echo ========================================
)

echo.
pause
