o# Automated Database Backup System

## Overview

The Travel Agency application now includes a comprehensive automated database backup system that:

- ✅ Creates automatic database backups on a configurable schedule (default: every 24 hours)
- ✅ Compresses backups with gzip to save disk space
- ✅ Stores backup metadata (timestamp, size, database name)
- ✅ Supports manual backup creation and restoration
- ✅ Automatically cleans up old backups based on retention policy
- ✅ Verifies backup integrity before and after creation
- ✅ Includes comprehensive error handling and logging
- ✅ Supports Windows Task Scheduler integration
- ✅ Command-line interface for backup management

## Architecture

### Components

1. **BackupService** (`backup_service.py`)
   - Core backup functionality
   - Creates, restores, verifies, and manages backups
   - Parses database URLs
   - Manages backup metadata

2. **BackupScheduler** (`backup_scheduler.py`)
   - Runs backups on schedule in background thread
   - Configurable interval (default: 24 hours)
   - Supports callbacks after each backup
   - Thread-safe implementation

3. **BackupConfig** (`backup_config.py`)
   - Centralized configuration management
   - Environment variable support
   - Configuration validation

4. **Backup Scripts** (`scripts/`)
   - `manage_backups.py` - CLI for backup management
   - `run_backup.py` - Single backup execution
   - `setup_backup_scheduler_py.py` - Windows Task Scheduler setup

## Getting Started

### Prerequisites

- PostgreSQL installed and on PATH (`pg_dump`, `psql` commands available)
- Python 3.7+
- `tabulate` package (for CLI formatting): `pip install tabulate`

### Configuration

Set environment variables in `.env`:

```bash
# Database configuration
DATABASE_URL=postgresql://user:password@localhost:5432/travel_agency

# Backup configuration
BACKUP_DIR=./backups                      # Directory to store backups
BACKUP_INTERVAL_HOURS=24                  # Hours between backups (default: 24)
BACKUP_RETENTION_DAYS=7                   # Keep backups for this many days
BACKUP_COMPRESS=true                      # Compress backups (default: true)
BACKUP_INCLUDE_METADATA=true              # Include metadata file (default: true)
BACKUP_AUTO_CLEANUP=true                  # Auto-cleanup old backups (default: true)
BACKUP_CLEANUP_INTERVAL_HOURS=168         # Cleanup interval in hours (default: 7 days)
BACKUP_SCHEDULER_ENABLED=true             # Start scheduler on app startup (default: true)
BACKUP_VERIFY_AFTER_CREATION=true         # Verify backup after creation (default: true)

# Notifications
BACKUP_NOTIFY_ON_SUCCESS=false            # Email on success
BACKUP_NOTIFY_ON_FAILURE=true             # Email on failure
BACKUP_NOTIFICATION_EMAIL=admin@example.com
```

### Enable Scheduler on Startup

Add to `app.py`:

```python
from backup_scheduler import start_scheduler

@app.before_request
def init_backup_scheduler():
    """Initialize backup scheduler if not already running."""
    if not hasattr(app, 'backup_scheduler_started'):
        from backup_config import BackupConfig
        if BackupConfig.BACKUP_SCHEDULER_ENABLED:
            start_scheduler()
            app.backup_scheduler_started = True
```

Or in a Flask CLI command:

```python
@app.cli.command()
def start_backups():
    """Start the automated backup scheduler."""
    from backup_scheduler import start_scheduler
    start_scheduler()
    print("Backup scheduler started")
```

## Usage

### Command Line Interface

#### Create a Backup

```bash
# Create backup now
python scripts/manage_backups.py create

# Create uncompressed backup
python scripts/manage_backups.py create --no-compress
```

#### List Backups

```bash
# List all backups
python scripts/manage_backups.py list

# List last 10 backups
python scripts/manage_backups.py list --limit 10
```

#### Verify Backup

```bash
# Verify backup integrity
python scripts/manage_backups.py verify backups/backup_20260604_120000.sql.gz
```

#### Restore from Backup

```bash
# Restore database from backup (requires confirmation)
python scripts/manage_backups.py restore backups/backup_20260604_120000.sql.gz
```

#### Cleanup Old Backups

```bash
# Delete backups older than 7 days
python scripts/manage_backups.py cleanup --days 7

# Delete backups older than 30 days
python scripts/manage_backups.py cleanup --days 30
```

#### Show Statistics

```bash
# Display backup statistics
python scripts/manage_backups.py stats
```

### Python API

#### Basic Usage

```python
from backup_service import BackupService

# Create service
backup_service = BackupService()

# Create backup
success, message, backup_path = backup_service.create_backup()
if success:
    print(f"Backup created: {backup_path}")

# List backups
backups = backup_service.list_backups()
for backup in backups:
    print(f"{backup['name']}: {backup['actual_size_mb']:.2f} MB")

# Get statistics
stats = backup_service.get_backup_stats()
print(f"Total backups: {stats['total_backups']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
```

#### Restore Database

```python
# Restore from backup
success, message = backup_service.restore_backup('backups/backup_20260604_120000.sql.gz')
if success:
    print("Database restored successfully")
else:
    print(f"Restore failed: {message}")
```

#### Verify Backup

```python
# Verify backup integrity
success, message = backup_service.verify_backup('backups/backup_20260604_120000.sql.gz')
if success:
    print(f"Backup is valid: {message}")
else:
    print(f"Backup verification failed: {message}")
```

#### Cleanup Old Backups

```python
# Delete backups older than 7 days
deleted_count, freed_space = backup_service.cleanup_old_backups(retention_days=7)
print(f"Deleted {deleted_count} backups, freed {freed_space:.2f} MB")
```

### Automated Scheduler

#### Start Scheduler

```python
from backup_scheduler import get_scheduler

scheduler = get_scheduler()
scheduler.start()
```

#### Add Callback

```python
from backup_scheduler import get_scheduler

scheduler = get_scheduler()

def backup_callback(success, message, backup_path):
    if success:
        print(f"Backup completed: {message}")
    else:
        print(f"Backup failed: {message}")

scheduler.add_callback(backup_callback)
scheduler.start()
```

#### Get Scheduler Status

```python
from backup_scheduler import get_scheduler

scheduler = get_scheduler()
status = scheduler.get_status()
print(f"Scheduler running: {status['is_running']}")
print(f"Total backups: {status['backup_count']}")
print(f"Last backup: {status['last_backup_time']}")
```

#### Run Backup Now (Outside Schedule)

```python
from backup_scheduler import get_scheduler

scheduler = get_scheduler()
success, message, backup_path = scheduler.run_backup_now()
```

## Database Backup Structure

### Backup Files

Backups are stored with the following naming convention:

```
backup_YYYYMMDD_HHMMSS.sql.gz      (compressed backup)
backup_YYYYMMDD_HHMMSS.sql         (uncompressed backup)
backup_YYYYMMDD_HHMMSS.json        (metadata file)
```

### Metadata File Structure

```json
{
  "backup_name": "backup_20260604_120000",
  "timestamp": "2026-06-04T12:00:00+00:00",
  "database": "travel_agency",
  "host": "localhost",
  "file_size_mb": 45.23,
  "compressed": true,
  "version": "1.0"
}
```

## Windows Task Scheduler Integration

### Setup Automatic Backups (Windows)

```bash
# Create scheduled task (runs every 24 hours)
python scripts/setup_backup_scheduler_py.py create

# Create task that runs every 12 hours
python scripts/setup_backup_scheduler_py.py create 720

# List scheduled backup tasks
python scripts/setup_backup_scheduler_py.py list

# Delete scheduled backup task
python scripts/setup_backup_scheduler_py.py delete
```

This creates a Windows Task Scheduler task named `TravelAgency_DatabaseBackup` that runs automatically.

## Retention Policy

### Default Retention

- Backups older than 7 days are automatically deleted
- Cleanup runs automatically based on `BACKUP_CLEANUP_INTERVAL_HOURS`

### Custom Retention

```python
from backup_service import BackupService

service = BackupService()

# Delete backups older than 30 days
deleted, freed = service.cleanup_old_backups(retention_days=30)
```

### Manual Cleanup Schedule

Run periodically via cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Delete backups older than 30 days
python scripts/manage_backups.py cleanup --days 30
```

## Disaster Recovery

### Backup Verification

Backups are automatically verified after creation. To manually verify:

```bash
python scripts/manage_backups.py verify backups/backup_20260604_120000.sql.gz
```

### Restore Procedure

1. **Stop the application** (if it's running)

2. **Restore from backup:**
   ```bash
   python scripts/manage_backups.py restore backups/backup_20260604_120000.sql.gz
   ```

3. **Verify the restore:**
   ```bash
   # Test application functionality
   ```

4. **Start the application**

### Recovery from Corrupted Database

If database is corrupted or lost:

1. Drop the corrupted database:
   ```bash
   psql -U postgres -c "DROP DATABASE travel_agency;"
   ```

2. Create new empty database:
   ```bash
   psql -U postgres -c "CREATE DATABASE travel_agency;"
   ```

3. Restore from backup:
   ```bash
   python scripts/manage_backups.py restore backups/backup_20260604_120000.sql.gz
   ```

4. Verify data integrity

## Monitoring and Logging

### Backup Logs

All backup events are logged via `StructuredLogger`:

```python
# Logs include:
# - backup_created: Successful backup creation
# - backup_completed: Scheduler completion
# - backup_failed: Backup failures
# - backup_restored: Successful restore
# - backup_verified: Successful verification
# - backup_cleanup: Cleanup operations
```

### Log Examples

```bash
# View backup logs
tail -f logs/app.log | grep backup

# Filter for errors
grep "ERROR" logs/app.log | grep backup
```

### Statistics

Get backup statistics:

```bash
python scripts/manage_backups.py stats
```

Output:
```
Backup Statistics:
==================================================
Total Backups: 7
Total Size: 315.64 MB
Average Backup Size: 45.09 MB
Backup Directory: ./backups

Latest Backup:
  Name: backup_20260604_120000
  Time: 2026-06-04T12:00:00+00:00
  Size: 45.23 MB

Oldest Backup:
  Name: backup_20260528_000000
  Time: 2026-05-28T00:00:00+00:00
  Size: 42.15 MB
```

## Troubleshooting

### PostgreSQL Client Tools Not Found

**Error:** `pg_dump not found` or `psql not found`

**Solution:** Install PostgreSQL client tools:

- **Windows:** Download from postgresql.org and select "Command Line Tools" during installation
- **macOS:** `brew install postgresql`
- **Linux:** `apt-get install postgresql-client` (Ubuntu/Debian) or `yum install postgresql` (RedHat/CentOS)

### Backup Directory Not Writable

**Error:** `Backup directory not writable`

**Solution:** 
1. Check directory permissions
2. Ensure application has write access
3. Change directory in configuration:
   ```bash
   export BACKUP_DIR=/var/backups/travel_agency
   ```

### Database Connection Failed

**Error:** `Failed to connect to database`

**Solution:**
1. Verify `DATABASE_URL` is correct
2. Test connection: `psql -c "SELECT 1" $DATABASE_URL`
3. Ensure PostgreSQL service is running

### Backup File Corrupted

**Error:** `Backup file is corrupted`

**Solution:**
1. Delete corrupted backup
2. Create new backup
3. Store backup in multiple locations for redundancy

## Best Practices

### Backup Strategy

1. **Daily Backups** (recommended for production)
   ```bash
   export BACKUP_INTERVAL_HOURS=24
   ```

2. **Multiple Copies**
   - Store backups in multiple locations
   - Consider cloud backup storage
   - Rotate backups off-site

3. **Regular Testing**
   - Test restore procedure regularly
   - Verify backup integrity
   - Document recovery time objectives (RTO)

### Storage

1. **Local Storage**
   ```bash
   # Default location
   ./backups
   ```

2. **Network Storage (NAS)**
   ```bash
   export BACKUP_DIR=/mnt/nas/backups
   ```

3. **Cloud Storage**
   - Consider using cloud backup services
   - Encrypt backups before uploading
   - Document upload procedures

### Security

1. **Backup Encryption**
   - Backups contain sensitive customer data
   - Store in secure location
   - Consider encryption before storage

2. **Access Control**
   - Restrict backup directory access
   - Use strong credentials for backups
   - Monitor backup access

3. **Retention Policy**
   - Comply with data protection regulations
   - Document retention periods
   - Regularly delete old backups

## Database Migration Guide

### Migrating to PostgreSQL

If you're currently using SQLite:

1. **Create backup of current database**
   ```bash
   sqlite3 travel_agency.db ".dump" > sqlite_backup.sql
   ```

2. **Create PostgreSQL database**
   ```bash
   createdb travel_agency
   ```

3. **Initialize schema**
   ```bash
   flask db upgrade
   ```

4. **Backup PostgreSQL database**
   ```bash
   python scripts/manage_backups.py create
   ```

5. **Migrate data** (use existing migration scripts)

6. **Verify data integrity**

## API Reference

### BackupService

```python
class BackupService:
    def create_backup(compress=True, include_metadata=True) -> (bool, str, Path)
    def restore_backup(backup_file: str) -> (bool, str)
    def list_backups(limit=None) -> List[Dict]
    def verify_backup(backup_file: str) -> (bool, str)
    def cleanup_old_backups(retention_days=7) -> (int, float)
    def get_backup_stats() -> Dict
```

### BackupScheduler

```python
class BackupScheduler:
    def start() -> None
    def stop() -> None
    def run_backup_now() -> (bool, str, Path)
    def add_callback(callback: Callable) -> None
    def get_status() -> Dict
```

### BackupConfig

```python
class BackupConfig:
    BACKUP_DIR: str
    BACKUP_INTERVAL_HOURS: int
    BACKUP_RETENTION_DAYS: int
    BACKUP_COMPRESS: bool
    @classmethod
    def validate() -> (bool, List)
    @classmethod
    def to_dict() -> Dict
```

## Testing

Run backup tests:

```bash
# All backup tests
pytest tests/test_backup.py -v

# Specific test class
pytest tests/test_backup.py::TestBackupService -v

# With coverage
pytest tests/test_backup.py --cov=backup_service --cov=backup_scheduler
```

## Summary

The automated backup system provides:

✅ **Reliability** - Automatic backups ensure data safety
✅ **Flexibility** - Configurable schedules and retention policies
✅ **Verification** - Built-in integrity checking
✅ **Recovery** - Easy restore procedures
✅ **Monitoring** - Comprehensive logging and statistics
✅ **Integration** - Works with Windows Task Scheduler and Linux cron
✅ **Testing** - Full test coverage

Your database is now protected with automated backups! 🔒
