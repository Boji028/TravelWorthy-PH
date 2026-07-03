# Automated Backup Setup Guide

## Option 1: Manual Backup (Quick Test)

Run this in your terminal to test the backup:
```bash
python scripts/backup_uploads.py
```

This will create a compressed backup in `backups/` folder with:
- All uploaded images (uploads folder)
- Database dump (if using PostgreSQL)
- Compressed as ZIP file

---

## Option 2: Automatic Daily Backup (Windows Task Scheduler)

### Step 1: Open Task Scheduler
- Press `Win + R`
- Type: `taskschd.msc`
- Click OK

### Step 2: Create Basic Task
- Right-click "Task Scheduler Library" → "Create Basic Task"
- **Name:** `Travel Agency Backup`
- **Description:** `Automated daily backup of uploads and database`
- Click Next

### Step 3: Set Schedule
- Select: **Daily**
- Click Next
- Set time: `2:00 AM` (or your preferred time)
- Click Next

### Step 4: Set Action
- Select: **Start a program**
- Click Next
- **Program/script:**
  ```
  C:\Users\ENZO KOPS\Desktop\TryNewWebsite\travel_agency_enhanced\fixed\scripts\backup_uploads.bat
  ```
- Click Next

### Step 5: Finish
- Check "Open the Properties dialog..."
- Click Finish

### Step 6: Configure Additional Settings
In the Properties dialog:
- **General tab:**
  - Check "Run with highest privileges"
- **Triggers tab:**
  - Edit the trigger if needed
- **Conditions tab:**
  - Uncheck "Start the task only if the computer is on AC power" (optional)
- **Settings tab:**
  - Check "Allow task to be run on demand"
  - Check "If the running task does not end when requested, force it to stop"
- Click OK

---

## Option 3: Manual Cleanup of Old Uploads

Run this to remove orphaned images:
```bash
# Preview (shows what will be deleted, doesn't delete)
python scripts/clean_uploads.py

# Actually delete orphaned files
python scripts/clean_uploads.py --delete
```

Or cleanup old files:
```bash
# Delete images older than 90 days
python scripts/cleanup_old_uploads.py --days 90
```

---

## Backup File Locations

Your backups will be stored here:
```
C:\Users\ENZO KOPS\Desktop\TryNewWebsite\travel_agency_enhanced\fixed\backups\
```

Structure:
```
backups/
├── backup_2026-06-04_02-00-00.zip    (June 4th backup)
├── backup_2026-06-05_02-00-00.zip    (June 5th backup)
└── backup_2026-06-06_02-00-00.zip    (June 6th backup)
```

### Extract a Backup

To restore from a backup:
```bash
# Extract backup zip file
# Right-click > Extract All

# Or using PowerShell:
Expand-Archive -Path backups\backup_2026-06-04_02-00-00.zip -DestinationPath restore_location
```

---

## Automatic Cleanup of Old Backups

The backup script automatically:
- Keeps backups for 30 days
- Deletes backups older than 30 days
- This happens after every backup

To change retention period, edit `backup_uploads.py`:
```python
cleanup_old_backups(days=30)  # Change 30 to your preferred days
```

---

## Backup Contents

Each backup contains:
```
backup_2026-06-04_02-00-00/
├── uploads/
│   └── 2026-06/
│       ├── blog_*.jpg
│       ├── package_*.jpg
│       ├── review_*.png
│       └── visa_*.jpg
└── database.sql           (PostgreSQL dump)
```

---

## Restore Instructions

### Restore Database (PostgreSQL)

If you need to restore from a backup:

```bash
# 1. Extract the backup
Expand-Archive -Path backups\backup_2026-06-04_02-00-00.zip

# 2. Restore database
psql -U postgres -d travel_agency_db < database.sql

# 3. Restore uploads folder
Copy-Item restore_location\uploads -Destination . -Recurse -Force
```

### Restore Uploads Only

```bash
# 1. Backup current uploads (just in case)
Copy-Item uploads uploads_backup_latest -Recurse

# 2. Extract and copy old uploads
Expand-Archive -Path backups\backup_2026-06-04_02-00-00.zip
Copy-Item restore_location\uploads -Destination . -Recurse -Force
```

---

## Troubleshooting

### Task Scheduler doesn't run the backup

1. Check Windows Event Viewer:
   - Windows Logs → System or Application
   - Look for error messages

2. Run task manually:
   - Right-click task → Run
   - Check if it works

3. Check permissions:
   - Task Scheduler → Run with highest privileges ✓
   - User account has permissions to run batch file

### `pg_dump` command not found

If PostgreSQL backup fails:
1. Install PostgreSQL (if not installed)
2. Add to system PATH:
   - Control Panel → System → Environment Variables
   - Edit PATH, add: `C:\Program Files\PostgreSQL\15\bin`
   - Restart terminal

### Backup file too large

- Delete old backups manually
- Reduce retention days from 30 to 7
- Run cleanup script on old uploads

---

## Next Steps

1. **Test backup manually:**
   ```bash
   cd c:\Users\ENZO KOPS\Desktop\TryNewWebsite\travel_agency_enhanced\fixed
   .venv\Scripts\activate
   python scripts\backup_uploads.py
   ```

2. **Set up Windows Task Scheduler** (follow steps above)

3. **Verify backup files** in `backups/` folder

4. **Test restore** (optional but recommended)

---

Questions? Need help? Let me know!
