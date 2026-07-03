#!/usr/bin/env python3
"""
Backup script for uploads folder and database.
Backs up to: backups/YYYY-MM-DD_HH-MM-SS/

Usage:
    python scripts/backup_uploads.py
    
This creates a compressed backup of:
- uploads/ folder (all images)
- PostgreSQL database dump
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

# Configuration
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
BACKUP_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///travel_agency.db")


def create_backup():
    """Create backup of uploads and database."""

    # Create timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = os.path.join(BACKUP_BASE_DIR, timestamp)
    os.makedirs(backup_dir, exist_ok=True)

    print(f"📦 Creating backup: {backup_dir}")

    # 1. Backup uploads folder
    if os.path.exists(UPLOADS_DIR):
        uploads_backup = os.path.join(backup_dir, "uploads")
        shutil.copytree(UPLOADS_DIR, uploads_backup)
        print(f"✅ Backed up uploads folder ({len(os.listdir(uploads_backup))} files)")
    else:
        print("⚠️  Uploads folder not found")

    # 2. Backup PostgreSQL database
    if "postgresql" in DB_URL:
        try:
            # Extract connection info from DATABASE_URL
            # Format: postgresql://user:password@host:port/dbname
            db_parts = DB_URL.replace("postgresql+psycopg2://", "").replace("postgresql://", "")
            db_parts = db_parts.split("@")

            if len(db_parts) == 2:
                user_pass = db_parts[0].split(":")
                host_port = db_parts[1].split("/")

                user = user_pass[0]
                password = user_pass[1] if len(user_pass) > 1 else ""
                host = host_port[0].split(":")[0]
                port = host_port[0].split(":")[1] if ":" in host_port[0] else "5432"
                dbname = host_port[1]

                # Create SQL dump
                dump_file = os.path.join(backup_dir, "database.sql")

                # Set PostgreSQL password in environment
                env = os.environ.copy()
                env["PGPASSWORD"] = password

                # Run pg_dump
                cmd = ["pg_dump", "-h", host, "-p", port, "-U", user, "-d", dbname, "-f", dump_file]

                result = subprocess.run(cmd, env=env, capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"✅ Backed up database to {dump_file}")
                else:
                    print(f"❌ Database backup failed: {result.stderr}")
            else:
                print("❌ Could not parse DATABASE_URL")
        except Exception as e:
            print(f"❌ Database backup error: {e}")
    else:
        print("ℹ️  SQLite database backup (if used) is not automated yet")

    # 3. Create compressed archive
    archive_name = f"backup_{timestamp}"
    archive_path = os.path.join(BACKUP_BASE_DIR, archive_name)

    try:
        shutil.make_archive(archive_path, "zip", backup_dir)
        shutil.rmtree(backup_dir)  # Remove uncompressed backup
        print(f"✅ Created compressed backup: {archive_path}.zip")
        print(f"\n💾 Backup saved to: {os.path.dirname(archive_path)}")
        return True
    except Exception as e:
        print(f"❌ Compression failed: {e}")
        return False


def cleanup_old_backups(days=30):
    """Keep only recent backups (delete older than specified days)."""
    if not os.path.exists(BACKUP_BASE_DIR):
        return

    cutoff_date = datetime.now() - __import__("datetime").timedelta(days=days)
    deleted_count = 0

    for filename in os.listdir(BACKUP_BASE_DIR):
        if filename.endswith(".zip") and filename.startswith("backup_"):
            filepath = os.path.join(BACKUP_BASE_DIR, filename)
            file_date = datetime.fromtimestamp(os.path.getmtime(filepath))

            if file_date < cutoff_date:
                os.remove(filepath)
                deleted_count += 1
                print(f"🗑️  Deleted old backup: {filename}")

    if deleted_count > 0:
        print(f"✅ Cleaned up {deleted_count} backups older than {days} days")


if __name__ == "__main__":
    print("=" * 60)
    print("🔄 Travel Agency Backup Script")
    print("=" * 60)

    success = create_backup()

    if success:
        print("\n🧹 Cleaning up old backups (keeping last 30 days)...")
        cleanup_old_backups(days=30)

    print("\n" + "=" * 60)
    print("✨ Backup complete!" if success else "⚠️  Backup completed with errors")
    print("=" * 60)
