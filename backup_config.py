"""Backup configuration module."""
import os
from datetime import timedelta


class BackupConfig:
    """Configuration settings for database backups."""
    
    # Backup directory
    BACKUP_DIR = os.getenv('BACKUP_DIR', './backups')
    
    # Backup interval (hours between backups)
    BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))
    
    # Retention policy (days to keep backups)
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '7'))
    
    # Compression
    BACKUP_COMPRESS = os.getenv('BACKUP_COMPRESS', 'true').lower() == 'true'
    
    # Include metadata
    BACKUP_INCLUDE_METADATA = os.getenv('BACKUP_INCLUDE_METADATA', 'true').lower() == 'true'
    
    # Auto-cleanup old backups
    BACKUP_AUTO_CLEANUP = os.getenv('BACKUP_AUTO_CLEANUP', 'true').lower() == 'true'
    
    # Backup cleanup interval (hours)
    BACKUP_CLEANUP_INTERVAL_HOURS = int(os.getenv('BACKUP_CLEANUP_INTERVAL_HOURS', '168'))  # 7 days
    
    # Enable scheduler on startup
    BACKUP_SCHEDULER_ENABLED = os.getenv('BACKUP_SCHEDULER_ENABLED', 'true').lower() == 'true'
    
    # Database URL (defaults to DATABASE_URL if not specified)
    BACKUP_DATABASE_URL = os.getenv('BACKUP_DATABASE_URL', os.getenv('DATABASE_URL', ''))
    
    # Backup notification settings
    BACKUP_NOTIFY_ON_SUCCESS = os.getenv('BACKUP_NOTIFY_ON_SUCCESS', 'false').lower() == 'true'
    BACKUP_NOTIFY_ON_FAILURE = os.getenv('BACKUP_NOTIFY_ON_FAILURE', 'true').lower() == 'true'
    BACKUP_NOTIFICATION_EMAIL = os.getenv('BACKUP_NOTIFICATION_EMAIL', 'admin@travelagency.com')
    
    # Backup verification
    BACKUP_VERIFY_AFTER_CREATION = os.getenv('BACKUP_VERIFY_AFTER_CREATION', 'true').lower() == 'true'
    
    # Logging
    BACKUP_LOG_LEVEL = os.getenv('BACKUP_LOG_LEVEL', 'INFO')
    
    # Pre/post backup hooks (command to run before/after backup)
    BACKUP_PRE_BACKUP_HOOK = os.getenv('BACKUP_PRE_BACKUP_HOOK', '')
    BACKUP_POST_BACKUP_HOOK = os.getenv('BACKUP_POST_BACKUP_HOOK', '')
    
    @classmethod
    def validate(cls) -> tuple:
        """Validate backup configuration.
        
        Returns:
            Tuple of (valid: bool, errors: list)
        """
        errors = []
        
        # Check backup directory is writable
        try:
            import os as os_module
            backup_dir = cls.BACKUP_DIR
            os_module.makedirs(backup_dir, exist_ok=True)
            
            # Try to write test file
            test_file = os_module.path.join(backup_dir, '.test')
            with open(test_file, 'w') as f:
                f.write('test')
            os_module.remove(test_file)
        
        except Exception as e:
            errors.append(f"Backup directory not writable: {e}")
        
        # Validate retention days
        if cls.BACKUP_RETENTION_DAYS < 1:
            errors.append("BACKUP_RETENTION_DAYS must be >= 1")
        
        # Validate interval
        if cls.BACKUP_INTERVAL_HOURS < 1:
            errors.append("BACKUP_INTERVAL_HOURS must be >= 1")
        
        # Validate cleanup interval
        if cls.BACKUP_CLEANUP_INTERVAL_HOURS < 1:
            errors.append("BACKUP_CLEANUP_INTERVAL_HOURS must be >= 1")
        
        # Validate database URL
        if not cls.BACKUP_DATABASE_URL:
            errors.append("DATABASE_URL or BACKUP_DATABASE_URL not configured")
        
        return len(errors) == 0, errors
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary with all configuration settings
        """
        return {
            'backup_dir': cls.BACKUP_DIR,
            'backup_interval_hours': cls.BACKUP_INTERVAL_HOURS,
            'retention_days': cls.BACKUP_RETENTION_DAYS,
            'compress': cls.BACKUP_COMPRESS,
            'include_metadata': cls.BACKUP_INCLUDE_METADATA,
            'auto_cleanup': cls.BACKUP_AUTO_CLEANUP,
            'cleanup_interval_hours': cls.BACKUP_CLEANUP_INTERVAL_HOURS,
            'scheduler_enabled': cls.BACKUP_SCHEDULER_ENABLED,
            'notify_on_success': cls.BACKUP_NOTIFY_ON_SUCCESS,
            'notify_on_failure': cls.BACKUP_NOTIFY_ON_FAILURE,
            'verify_after_creation': cls.BACKUP_VERIFY_AFTER_CREATION,
            'log_level': cls.BACKUP_LOG_LEVEL
        }
