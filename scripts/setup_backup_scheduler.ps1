# PowerShell script to create Windows Task Scheduler for automated backups
# Run this as Administrator

param(
    [string]$Time = "02:00",  # Default: 2:00 AM
    [switch]$Help
)

if ($Help) {
    Write-Host @"
USAGE:
    powershell -ExecutionPolicy Bypass -File setup_backup_scheduler.ps1
    
PARAMETERS:
    -Time "HH:MM"  : Set backup time (default: 02:00)
    
EXAMPLES:
    # Backup at 2:00 AM (default)
    powershell -ExecutionPolicy Bypass -File setup_backup_scheduler.ps1
    
    # Backup at 3:30 AM
    powershell -ExecutionPolicy Bypass -File setup_backup_scheduler.ps1 -Time "03:30"
"@
    exit 0
}

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "`nHow to run as Administrator:"
    Write-Host "1. Press Win+X"
    Write-Host "2. Select 'Windows PowerShell (Admin)' or 'Terminal (Admin)'"
    Write-Host "3. Run: powershell -ExecutionPolicy Bypass -File setup_backup_scheduler.ps1"
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔄 Travel Agency Backup Scheduler Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ProjectPath = "C:\Users\ENZO KOPS\Desktop\TryNewWebsite\travel_agency_enhanced\fixed"
$BatchFile = "$ProjectPath\scripts\backup_uploads.bat"
$TaskName = "Travel Agency Backup"
$TaskDescription = "Automated daily backup of uploads and database"

# Verify batch file exists
if (-not (Test-Path $BatchFile)) {
    Write-Host "❌ ERROR: Batch file not found at: $BatchFile" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Task Name: $TaskName"
Write-Host "   Batch File: $BatchFile"
Write-Host "   Schedule: Daily at $Time"
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "ℹ️  Task already exists. Updating..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create trigger (daily at specified time)
$trigger = New-ScheduledTaskTrigger -Daily -At $Time

# Create action
$action = New-ScheduledTaskAction -Execute $BatchFile

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RunWithoutNetwork `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

# Create principal (run with highest privileges)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName `
        -Description $TaskDescription `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null
    
    Write-Host "✅ Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📅 Schedule Details:" -ForegroundColor Yellow
    Write-Host "   Task: $TaskName"
    Write-Host "   Time: Daily at $Time"
    Write-Host "   Status: Enabled"
    Write-Host ""
    
    # Enable the task
    Enable-ScheduledTask -TaskName $TaskName | Out-Null
    
    Write-Host "🔍 To manage the task:" -ForegroundColor Cyan
    Write-Host "   1. Open Task Scheduler: Press Win+R, type 'taskschd.msc'"
    Write-Host "   2. Go to Task Scheduler Library"
    Write-Host "   3. Find: '$TaskName'"
    Write-Host "   4. Right-click → Properties to configure"
    Write-Host ""
    
    Write-Host "🧪 To test the backup:" -ForegroundColor Cyan
    Write-Host "   1. Open Task Scheduler"
    Write-Host "   2. Find: '$TaskName'"
    Write-Host "   3. Right-click → Run"
    Write-Host ""
    
    Write-Host "✨ Setup complete!" -ForegroundColor Green
    Write-Host ""
    
    # Show next scheduled run
    $task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "ℹ️  Next scheduled run: Check in Task Scheduler" -ForegroundColor Yellow
}
catch {
    Write-Host "❌ ERROR: Failed to create task" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}
