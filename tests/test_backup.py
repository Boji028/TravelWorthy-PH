"""Tests for backup functionality."""
import pytest
import os
import json
from pathlib import Path
from backup_service import BackupService
from backup_scheduler import BackupScheduler
from backup_config import BackupConfig
from datetime import datetime, timezone, timedelta


class TestBackupService:
    """Test BackupService functionality."""

    def test_parse_db_url(self):
        """Test database URL parsing."""
        test_urls = [
            (
                "postgresql://user:pass@localhost:5432/dbname",
                {"host": "localhost", "port": "5432", "user": "user", "password": "pass", "database": "dbname"},
            ),
            (
                "postgresql://user@localhost/dbname",
                {"host": "localhost", "port": "5432", "user": "user", "password": "", "database": "dbname"},
            ),
        ]

        for url, expected in test_urls:
            result = BackupService._parse_db_url(url)
            assert result["user"] == expected["user"]
            assert result["database"] == expected["database"]

    def test_backup_directory_creation(self, tmp_path):
        """Test backup directory is created."""
        backup_dir = tmp_path / "backups"
        service = BackupService(backup_dir=str(backup_dir), db_url="postgresql://user@localhost/testdb")

        assert backup_dir.exists()
        assert backup_dir.is_dir()

    def test_list_backups_empty(self, tmp_path):
        """Test listing backups when none exist."""
        service = BackupService(backup_dir=str(tmp_path), db_url="postgresql://user@localhost/testdb")
        backups = service.list_backups()

        assert backups == []

    def test_list_backups_with_metadata(self, tmp_path):
        """Test listing backups with metadata files."""
        service = BackupService(backup_dir=str(tmp_path), db_url="postgresql://user@localhost/testdb")

        # Create fake backup files and metadata
        backup_name = "backup_20260604_120000"
        metadata = {
            "backup_name": backup_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "testdb",
            "host": "localhost",
            "file_size_mb": 50.0,
            "compressed": True,
            "version": "1.0",
        }

        # Create backup file (dummy)
        backup_file = tmp_path / f"{backup_name}.sql.gz"
        backup_file.write_text("dummy backup data")

        # Create metadata file
        metadata_file = tmp_path / f"{backup_name}.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

        # List backups
        backups = service.list_backups()

        assert len(backups) == 1
        assert backups[0]["name"] == backup_name
        assert backups[0]["database"] == "testdb"

    def test_cleanup_old_backups(self, tmp_path):
        """Test cleanup of old backups."""
        service = BackupService(backup_dir=str(tmp_path), db_url="postgresql://user@localhost/testdb")

        # Create old and new backup files
        old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        new_time = datetime.now(timezone.utc).isoformat()

        # Old backup
        old_backup = "backup_20260525_120000"
        old_metadata = {
            "backup_name": old_backup,
            "timestamp": old_time,
            "database": "testdb",
            "host": "localhost",
            "file_size_mb": 50.0,
            "compressed": True,
            "version": "1.0",
        }

        old_file = tmp_path / f"{old_backup}.sql.gz"
        old_file.write_text("old backup data")

        with open(tmp_path / f"{old_backup}.json", "w") as f:
            json.dump(old_metadata, f)

        # New backup
        new_backup = "backup_20260604_120000"
        new_metadata = {
            "backup_name": new_backup,
            "timestamp": new_time,
            "database": "testdb",
            "host": "localhost",
            "file_size_mb": 50.0,
            "compressed": True,
            "version": "1.0",
        }

        new_file = tmp_path / f"{new_backup}.sql.gz"
        new_file.write_text("new backup data")

        with open(tmp_path / f"{new_backup}.json", "w") as f:
            json.dump(new_metadata, f)

        # Cleanup backups older than 7 days
        deleted_count, freed_space = service.cleanup_old_backups(retention_days=7)

        assert deleted_count == 1
        assert not old_file.exists()
        assert new_file.exists()

    def test_verify_backup_missing_file(self, tmp_path):
        """Test verifying non-existent backup."""
        service = BackupService(backup_dir=str(tmp_path), db_url="postgresql://user@localhost/testdb")

        success, message = service.verify_backup("nonexistent.sql.gz")

        assert success == False
        assert "not found" in message.lower()

    def test_verify_backup_empty_file(self, tmp_path):
        """Test verifying empty backup file."""
        service = BackupService(backup_dir=str(tmp_path), db_url="postgresql://user@localhost/testdb")

        # Create empty file
        backup_file = tmp_path / "backup.sql"
        backup_file.write_text("")

        success, message = service.verify_backup(str(backup_file))

        assert success == False
        assert "empty" in message.lower()

    def test_get_backup_stats(self, tmp_path):
        """Test getting backup statistics."""
        service = BackupService(backup_dir=str(tmp_path), db_url="postgresql://user@localhost/testdb")

        # Create fake backup
        backup_name = "backup_20260604_120000"
        metadata = {
            "backup_name": backup_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "testdb",
            "host": "localhost",
            "file_size_mb": 50.0,
            "compressed": True,
            "version": "1.0",
        }

        backup_file = tmp_path / f"{backup_name}.sql.gz"
        backup_file.write_text("x" * 1024 * 100)  # ~100KB

        with open(tmp_path / f"{backup_name}.json", "w") as f:
            json.dump(metadata, f)

        # Get stats
        stats = service.get_backup_stats()

        assert stats["total_backups"] == 1
        assert stats["total_size_mb"] > 0
        assert stats["latest_backup"] is not None


class TestBackupScheduler:
    """Test BackupScheduler functionality."""

    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = BackupScheduler(backup_interval_hours=24)

        assert scheduler.is_running == False
        assert scheduler.backup_interval_hours == 24
        assert scheduler.backup_interval_seconds == 86400
        assert scheduler.backup_count == 0

    def test_scheduler_status(self):
        """Test getting scheduler status."""
        scheduler = BackupScheduler(backup_interval_hours=24)
        status = scheduler.get_status()

        assert status["is_running"] == False
        assert status["backup_interval_hours"] == 24
        assert status["backup_count"] == 0

    def test_scheduler_add_callback(self):
        """Test adding callback to scheduler."""
        scheduler = BackupScheduler()
        callback_called = []

        def test_callback(success, message, path):
            callback_called.append((success, message))

        scheduler.add_callback(test_callback)
        assert len(scheduler.callbacks) == 1


class TestBackupConfig:
    """Test BackupConfig functionality."""

    def test_config_defaults(self):
        """Test default configuration values."""
        # These should use environment defaults
        assert BackupConfig.BACKUP_INTERVAL_HOURS >= 1
        assert BackupConfig.BACKUP_RETENTION_DAYS >= 1
        assert isinstance(BackupConfig.BACKUP_COMPRESS, bool)

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config_dict = BackupConfig.to_dict()

        assert "backup_dir" in config_dict
        assert "backup_interval_hours" in config_dict
        assert "retention_days" in config_dict
        assert "compress" in config_dict

    def test_config_validate(self):
        """Test configuration validation."""
        valid, errors = BackupConfig.validate()

        # Should be valid or have errors we can handle
        assert isinstance(valid, bool)
        assert isinstance(errors, list)


@pytest.fixture
def backup_service_temp(tmp_path):
    """Fixture for backup service with temporary directory."""
    return BackupService(backup_dir=str(tmp_path), db_url="postgresql://user@localhost/testdb")


class TestBackupIntegration:
    """Integration tests for backup functionality."""

    def test_backup_workflow_simulation(self, backup_service_temp, tmp_path):
        """Simulate complete backup workflow."""
        service = backup_service_temp

        # Create fake backups
        for i in range(3):
            backup_name = f"backup_202606{i:02d}_120000"
            metadata = {
                "backup_name": backup_name,
                "timestamp": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(),
                "database": "testdb",
                "host": "localhost",
                "file_size_mb": 50.0 + i,
                "compressed": True,
                "version": "1.0",
            }

            backup_file = tmp_path / f"{backup_name}.sql.gz"
            backup_file.write_text(f"backup data {i}")

            with open(tmp_path / f"{backup_name}.json", "w") as f:
                json.dump(metadata, f)

        # List backups
        backups = service.list_backups()
        assert len(backups) == 3

        # Get stats
        stats = service.get_backup_stats()
        assert stats["total_backups"] == 3

        # Cleanup old backups
        deleted, freed = service.cleanup_old_backups(retention_days=1)
        assert deleted >= 0
