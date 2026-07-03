#!/usr/bin/env python
"""Setup scheduled backup task for Windows Task Scheduler."""

import os
import sys
import subprocess
from pathlib import Path


def create_scheduled_task(interval_minutes: int = 1440):  # 24 hours default
    """Create a Windows scheduled task for backups.

    Args:
        interval_minutes: Interval between backups in minutes (default: 1440 = 24 hours)
    """
    script_path = Path(__file__).parent / "run_backup.py"
    python_exe = sys.executable

    # Task name
    task_name = "TravelAgency_DatabaseBackup"

    # Create the scheduled task
    cmd = [
        "schtasks",
        "/create",
        "/tn",
        task_name,
        "/tr",
        f'"{python_exe}" "{script_path}"',
        "/sc",
        "minute",
        "/mo",
        str(interval_minutes),
        "/ru",
        "SYSTEM",
        "/f",  # Force creation, replace if exists
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓ Scheduled task '{task_name}' created successfully")
            print(f"  Interval: Every {interval_minutes} minutes")
            print(f"  Script: {script_path}")
            return True
        else:
            print(f"✗ Failed to create scheduled task")
            print(f"  Error: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ Error creating scheduled task: {e}")
        return False


def delete_scheduled_task():
    """Delete the Windows scheduled backup task."""
    task_name = "TravelAgency_DatabaseBackup"

    cmd = ["schtasks", "/delete", "/tn", task_name, "/f"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓ Scheduled task '{task_name}' deleted successfully")
            return True
        else:
            print(f"✗ Failed to delete scheduled task")
            print(f"  Error: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ Error deleting scheduled task: {e}")
        return False


def list_scheduled_tasks():
    """List all backup-related scheduled tasks."""
    cmd = ["schtasks", "/query", "/tn", "TravelAgency_DatabaseBackup", "/v", "/fo", "list"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout)
        else:
            print("No backup scheduled tasks found")

    except Exception as e:
        print(f"Error querying scheduled tasks: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup_backup_scheduler.py create [minutes]")
        print("  python setup_backup_scheduler.py delete")
        print("  python setup_backup_scheduler.py list")
        print("")
        print("Examples:")
        print("  # Create task that runs every 24 hours (default)")
        print("  python setup_backup_scheduler.py create")
        print("")
        print("  # Create task that runs every 12 hours")
        print("  python setup_backup_scheduler.py create 720")
        print("")
        print("  # Delete existing task")
        print("  python setup_backup_scheduler.py delete")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "create":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 1440
        success = create_scheduled_task(interval)
        sys.exit(0 if success else 1)

    elif command == "delete":
        success = delete_scheduled_task()
        sys.exit(0 if success else 1)

    elif command == "list":
        list_scheduled_tasks()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
