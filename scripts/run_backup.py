#!/usr/bin/env python
"""Run a single backup (for use with system scheduler)."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backup_service import BackupService
from logging_service import StructuredLogger


def main():
    """Run a backup."""
    try:
        backup_service = BackupService()
        success, message, backup_path = backup_service.create_backup()
        
        if success:
            print(f"Backup successful: {message}")
            StructuredLogger.log_admin_action(
                'backup_executed',
                'database',
                None,
                {'message': message}
            )
            return 0
        else:
            print(f"Backup failed: {message}")
            StructuredLogger.log_error(
                'backup',
                f"Backup execution failed: {message}",
                {},
                'ERROR'
            )
            return 1
    
    except Exception as e:
        print(f"Error running backup: {e}")
        StructuredLogger.log_error(
            'backup',
            f"Error running backup: {str(e)}",
            {},
            'ERROR'
        )
        return 1


if __name__ == '__main__':
    sys.exit(main())
