# Scripts

## One-time migration scripts

These scripts were used during development to perform one-off database migrations.
They are kept here for reference but should NOT be run on a production database
that has already been migrated.

For ongoing schema changes, use Flask-Migrate:
  flask db migrate -m "description of change"
  flask db upgrade

---

## Cleanup Script: Remove Old Uploads

**File:** `cleanup_old_uploads.py`

This script removes orphaned (unreferenced) images older than 90 days.

### Why use it?
- Prevents `uploads/` folder from growing indefinitely
- Removes images that are no longer used in your database
- Keeps your website responsive and saves disk space

### Usage

**Preview what will be deleted (safe):**
```bash
python scripts/cleanup_old_uploads.py --dry-run
```

**Actually delete old orphaned images:**
```bash
python scripts/cleanup_old_uploads.py
```

**Delete images older than 60 days (instead of default 90):**
```bash
python scripts/cleanup_old_uploads.py --days 60
```

### Automation

**Linux/Mac - Add to crontab (runs monthly):**
```bash
crontab -e
# Add this line:
0 2 1 * * cd /path/to/travel_agency_enhanced/fixed && python scripts/cleanup_old_uploads.py >> cleanup.log 2>&1
```

**Windows - Use Task Scheduler:**
1. Open Task Scheduler
2. Create task: Run `python scripts/cleanup_old_uploads.py` 
3. Set trigger: Monthly or as needed
4. Run with admin privileges

### What it checks
- BlogPost images
- Package images
- Testimonial images
- Visa images
- Country images
- Continent images

Only images NOT referenced in the database are deleted.
