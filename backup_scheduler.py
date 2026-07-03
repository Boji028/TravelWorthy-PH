"""Backup scheduler for automated database backups."""
import os
import time
import threading
from datetime import datetime, timezone
from typing import Optional, Callable
from backup_service import BackupService
from logging_service import StructuredLogger


class BackupScheduler:
    """Scheduler for automated database backups."""

    def __init__(self, backup_service: BackupService = None, backup_interval_hours: int = 24):
        """Initialize backup scheduler.

        Args:
            backup_service: BackupService instance (creates new if None)
            backup_interval_hours: Hours between backups (default: 24)
        """
        self.backup_service = backup_service or BackupService()
        self.backup_interval_hours = backup_interval_hours
        self.backup_interval_seconds = backup_interval_hours * 3600

        self.is_running = False
        self.scheduler_thread = None
        self.last_backup_time = None
        self.backup_count = 0
        self.total_backup_time = 0
        self.callbacks = []

    def add_callback(self, callback: Callable) -> None:
        """Add callback to be called after each backup.

        Args:
            callback: Function to call with (success: bool, message: str, backup_path: Path)
        """
        self.callbacks.append(callback)

    def _run_backup(self) -> None:
        """Internal method to run backup and execute callbacks."""
        start_time = datetime.now(timezone.utc)
        success, message, backup_path = self.backup_service.create_backup()
        end_time = datetime.now(timezone.utc)

        backup_duration = (end_time - start_time).total_seconds()
        self.last_backup_time = end_time
        self.backup_count += 1
        self.total_backup_time += backup_duration

        # Execute callbacks
        for callback in self.callbacks:
            try:
                callback(success, message, backup_path)
            except Exception as e:
                StructuredLogger.log_error("backup", f"Callback failed: {str(e)}", {}, "WARNING")

        # Log result
        if success:
            StructuredLogger.log_admin_action(
                "backup_completed",
                "database",
                None,
                {"duration_seconds": backup_duration, "backup_count": self.backup_count, "backup_file": str(backup_path)},
            )
        else:
            StructuredLogger.log_error("backup", f"Automated backup failed: {message}", {}, "ERROR")

    def _scheduler_loop(self) -> None:
        """Internal scheduler loop."""
        StructuredLogger.log_admin_action(
            "backup_scheduler_started", "database", None, {"interval_hours": self.backup_interval_hours}
        )

        try:
            while self.is_running:
                # Check if it's time for backup
                now = datetime.now(timezone.utc)

                if self.last_backup_time is None:
                    # First backup
                    self._run_backup()
                else:
                    time_since_backup = (now - self.last_backup_time).total_seconds()

                    if time_since_backup >= self.backup_interval_seconds:
                        self._run_backup()

                # Sleep for a minute before checking again
                time.sleep(60)

        except Exception as e:
            StructuredLogger.log_error("backup", f"Scheduler error: {str(e)}", {}, "ERROR")

        finally:
            StructuredLogger.log_admin_action(
                "backup_scheduler_stopped",
                "database",
                None,
                {"backup_count": self.backup_count, "total_backup_time": self.total_backup_time},
            )

    def start(self) -> None:
        """Start the backup scheduler."""
        if self.is_running:
            StructuredLogger.log_admin_action(
                "backup_scheduler_warning", "database", None, {"message": "Scheduler already running"}
            )
            return

        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        StructuredLogger.log_admin_action(
            "backup_scheduler_started", "database", None, {"thread_name": self.scheduler_thread.name}
        )

    def stop(self) -> None:
        """Stop the backup scheduler."""
        if not self.is_running:
            return

        self.is_running = False

        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)

        StructuredLogger.log_admin_action(
            "backup_scheduler_stopped",
            "database",
            None,
            {"backup_count": self.backup_count, "total_backup_time": self.total_backup_time},
        )

    def run_backup_now(self) -> tuple:
        """Run a backup immediately (outside schedule).

        Returns:
            Tuple of (success: bool, message: str, backup_path: Path)
        """
        return self.backup_service.create_backup()

    def get_status(self) -> dict:
        """Get scheduler status.

        Returns:
            Dictionary with scheduler status
        """
        return {
            "is_running": self.is_running,
            "backup_interval_hours": self.backup_interval_hours,
            "backup_count": self.backup_count,
            "last_backup_time": self.last_backup_time.isoformat() if self.last_backup_time else None,
            "average_backup_time": round(self.total_backup_time / self.backup_count, 2) if self.backup_count > 0 else 0,
            "total_backup_time": round(self.total_backup_time, 2),
        }


# Global scheduler instance
_scheduler: Optional[BackupScheduler] = None


def get_scheduler() -> BackupScheduler:
    """Get or create global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        interval_hours = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
        _scheduler = BackupScheduler(backup_interval_hours=interval_hours)
    return _scheduler


def start_scheduler() -> None:
    """Start global scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler() -> None:
    """Stop global scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
