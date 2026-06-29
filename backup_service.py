"""Database backup service for creating, managing, and restoring backups."""
import os
import subprocess
import gzip
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Tuple
from logging_service import StructuredLogger
import shutil


class BackupService:
    """Service for managing database backups."""

    def __init__(self, backup_dir: str = None, db_url: str = None):
        """Initialize backup service.
        
        Args:
            backup_dir: Directory to store backups (default: ./backups)
            db_url: Database connection URL (default: from environment)
        """
        self.backup_dir = Path(backup_dir or './backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse database URL
        self.db_url = db_url or os.getenv('DATABASE_URL', '')
        self.db_config = self._parse_db_url(self.db_url)

    @staticmethod
    def _parse_db_url(db_url: str) -> Dict:
        """Parse database connection URL.
        
        Args:
            db_url: Database URL (format: postgresql://user:password@host:port/dbname)
        
        Returns:
            Dictionary with connection details
        """
        try:
            # Remove protocol
            if '://' in db_url:
                db_url = db_url.split('://', 1)[1]
            
            # Split credentials and host
            if '@' in db_url:
                creds, host_db = db_url.split('@', 1)
                if ':' in creds:
                    user, password = creds.split(':', 1)
                else:
                    user, password = creds, ''
            else:
                user, password = '', ''
                host_db = db_url
            
            # Split host and database
            if '/' in host_db:
                host_port, database = host_db.rsplit('/', 1)
            else:
                host_port, database = host_db, ''
            
            # Split host and port
            if ':' in host_port:
                host, port = host_port.rsplit(':', 1)
            else:
                host, port = host_port, '5432'
            
            return {
                'host': host,
                'port': port,
                'user': user,
                'password': password,
                'database': database
            }
        
        except Exception as e:
            StructuredLogger.log_error(
                'backup',
                f"Failed to parse database URL: {str(e)}",
                {'db_url': db_url[:20] + '...'},
                'ERROR'
            )
            return {}

    def create_backup(self, compress: bool = True, include_metadata: bool = True) -> Tuple[bool, str, Optional[Path]]:
        """Create a database backup.
        
        Args:
            compress: Compress backup with gzip (default: True)
            include_metadata: Include backup metadata file (default: True)
        
        Returns:
            Tuple of (success: bool, message: str, backup_path: Path or None)
        """
        try:
            if not self.db_config or not self.db_config.get('database'):
                return False, "Database configuration missing", None
            
            # Create timestamp-based filename
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            if compress:
                backup_file = f"{backup_path}.sql.gz"
            else:
                backup_file = f"{backup_path}.sql"
            
            # Build pg_dump command
            env = os.environ.copy()
            if self.db_config.get('password'):
                env['PGPASSWORD'] = self.db_config['password']
            
            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', self.db_config['database'],
                '--verbose',
                '--no-password'
            ]
            
            # Execute backup
            with open(backup_file, 'wb') as f:
                if compress:
                    # Pipe through gzip
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                    gzip_process = subprocess.Popen(['gzip'], stdin=process.stdout, stdout=f, stderr=subprocess.PIPE)
                    process.stdout.close()
                    gzip_returncode = gzip_process.wait()
                    pg_returncode = process.wait()
                    
                    if gzip_returncode != 0 or pg_returncode != 0:
                        raise RuntimeError(f"Backup process failed with code {pg_returncode}")
                else:
                    process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.PIPE, env=env)
                    returncode = process.wait()
                    
                    if returncode != 0:
                        raise RuntimeError(f"pg_dump failed with code {returncode}")
            
            # Get backup file size
            file_size_mb = os.path.getsize(backup_file) / (1024 * 1024)
            
            # Create metadata file
            if include_metadata:
                metadata = {
                    'backup_name': backup_name,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'database': self.db_config['database'],
                    'host': self.db_config['host'],
                    'file_size_mb': round(file_size_mb, 2),
                    'compressed': compress,
                    'version': '1.0'
                }
                
                metadata_file = f"{backup_path}.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            StructuredLogger.log_admin_action(
                'backup_created',
                'database',
                None,
                {
                    'backup_name': backup_name,
                    'file_size_mb': round(file_size_mb, 2),
                    'compressed': compress
                }
            )
            
            return True, f"Backup created successfully: {backup_name} ({file_size_mb:.2f} MB)", Path(backup_file)
        
        except FileNotFoundError:
            message = "pg_dump not found. Install PostgreSQL client tools."
            StructuredLogger.log_error('backup', message, {}, 'ERROR')
            return False, message, None
        
        except Exception as e:
            message = f"Backup failed: {str(e)}"
            StructuredLogger.log_error('backup', message, {'db': self.db_config.get('database')}, 'ERROR')
            return False, message, None

    def restore_backup(self, backup_file: str) -> Tuple[bool, str]:
        """Restore database from backup file.
        
        Args:
            backup_file: Path to backup file (can be .sql or .sql.gz)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                return False, f"Backup file not found: {backup_file}"
            
            if not self.db_config or not self.db_config.get('database'):
                return False, "Database configuration missing"
            
            # Build psql command
            env = os.environ.copy()
            if self.db_config.get('password'):
                env['PGPASSWORD'] = self.db_config['password']
            
            # Handle compressed and uncompressed backups
            if str(backup_path).endswith('.gz'):
                # Decompress on the fly
                with gzip.open(backup_path, 'rt') as f:
                    process = subprocess.Popen(
                        [
                            'psql',
                            '-h', self.db_config['host'],
                            '-p', str(self.db_config['port']),
                            '-U', self.db_config['user'],
                            '-d', self.db_config['database'],
                            '--no-password'
                        ],
                        stdin=f,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    stdout, stderr = process.communicate()
                    
                    if process.returncode != 0:
                        raise RuntimeError(f"psql failed: {stderr.decode()}")
            else:
                # Direct restore
                with open(backup_path, 'r') as f:
                    process = subprocess.Popen(
                        [
                            'psql',
                            '-h', self.db_config['host'],
                            '-p', str(self.db_config['port']),
                            '-U', self.db_config['user'],
                            '-d', self.db_config['database'],
                            '--no-password'
                        ],
                        stdin=f,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    stdout, stderr = process.communicate()
                    
                    if process.returncode != 0:
                        raise RuntimeError(f"psql failed: {stderr.decode()}")
            
            StructuredLogger.log_admin_action(
                'backup_restored',
                'database',
                None,
                {'backup_file': str(backup_path)}
            )
            
            return True, f"Database restored successfully from {backup_path.name}"
        
        except FileNotFoundError:
            message = "psql not found. Install PostgreSQL client tools."
            StructuredLogger.log_error('backup', message, {}, 'ERROR')
            return False, message
        
        except Exception as e:
            message = f"Restore failed: {str(e)}"
            StructuredLogger.log_error('backup', message, {'backup_file': backup_file}, 'ERROR')
            return False, message

    def list_backups(self, limit: int = None) -> List[Dict]:
        """List available backups.
        
        Args:
            limit: Maximum number of backups to return (None = all)
        
        Returns:
            List of backup information dictionaries
        """
        try:
            backups = []
            
            for metadata_file in sorted(self.backup_dir.glob('backup_*.json'), reverse=True):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Find corresponding backup file
                    backup_name = metadata['backup_name']
                    # Exclude the metadata file itself — f"{backup_name}.*" also
                    # matches "{backup_name}.json", so without this filter,
                    # backup_files[0] can non-deterministically pick the tiny
                    # metadata file instead of the actual backup archive,
                    # making actual_size_mb silently round down to 0.
                    backup_files = [
                        f for f in self.backup_dir.glob(f"{backup_name}.*")
                        if f.suffix != '.json'
                    ]
                    
                    if backup_files:
                        backup_file = backup_files[0]
                        file_size = os.path.getsize(backup_file)
                        
                        backups.append({
                            'name': backup_name,
                            'timestamp': metadata['timestamp'],
                            'file_size_mb': metadata['file_size_mb'],
                            'actual_size_mb': round(file_size / (1024 * 1024), 2),
                            'database': metadata['database'],
                            'host': metadata['host'],
                            'compressed': metadata['compressed'],
                            'file_path': str(backup_file)
                        })
                
                except Exception as e:
                    StructuredLogger.log_error(
                        'backup',
                        f"Failed to read backup metadata: {str(e)}",
                        {'file': str(metadata_file)},
                        'WARNING'
                    )
            
            if limit:
                backups = backups[:limit]
            
            return backups
        
        except Exception as e:
            StructuredLogger.log_error(
                'backup',
                f"Failed to list backups: {str(e)}",
                {},
                'ERROR'
            )
            return []

    def cleanup_old_backups(self, retention_days: int = 7) -> Tuple[int, int]:
        """Clean up backups older than retention period.
        
        Args:
            retention_days: Keep backups newer than this many days
        
        Returns:
            Tuple of (deleted_count: int, freed_space_mb: float)
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            deleted_count = 0
            freed_space_mb = 0
            
            for backup_file in self.backup_dir.glob('backup_*'):
                if backup_file.suffix == '.json':
                    continue
                
                try:
                    # backup_file.with_suffix('') only strips the LAST suffix
                    # (.gz), leaving a stray ".sql" — e.g. "backup_X.sql.gz"
                    # becomes "backup_X.sql.json" instead of the metadata
                    # file's real name, "backup_X.json". Strip everything
                    # after the first dot instead, since backup names
                    # themselves never contain a dot.
                    metadata_name = backup_file.name.split('.')[0]
                    metadata_file_path = self.backup_dir / f"{metadata_name}.json"
                    with open(metadata_file_path, 'r') as f:
                        metadata = json.load(f)
                    
                    backup_datetime = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
                    
                    if backup_datetime < cutoff_date:
                        # Delete backup file
                        file_size = os.path.getsize(backup_file)
                        freed_space_mb += file_size / (1024 * 1024)
                        backup_file.unlink()
                        
                        # Delete metadata file
                        if metadata_file_path.exists():
                            metadata_file_path.unlink()
                        
                        deleted_count += 1
                
                except Exception as e:
                    StructuredLogger.log_error(
                        'backup',
                        f"Failed to delete old backup: {str(e)}",
                        {'file': str(backup_file)},
                        'WARNING'
                    )
            
            StructuredLogger.log_admin_action(
                'backup_cleanup',
                'database',
                None,
                {
                    'deleted_count': deleted_count,
                    'freed_space_mb': round(freed_space_mb, 2),
                    'retention_days': retention_days
                }
            )
            
            return deleted_count, round(freed_space_mb, 2)
        
        except Exception as e:
            StructuredLogger.log_error(
                'backup',
                f"Failed to cleanup old backups: {str(e)}",
                {},
                'ERROR'
            )
            return 0, 0

    def verify_backup(self, backup_file: str) -> Tuple[bool, str]:
        """Verify backup file integrity.
        
        Args:
            backup_file: Path to backup file
        
        Returns:
            Tuple of (valid: bool, message: str)
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                return False, f"Backup file not found: {backup_file}"
            
            # Check file size
            file_size = os.path.getsize(backup_file)
            if file_size == 0:
                return False, "Backup file is empty"
            
            # Try to read file
            if str(backup_path).endswith('.gz'):
                # Test gzip integrity
                try:
                    with gzip.open(backup_path, 'rt') as f:
                        # Read first line to verify it's valid SQL
                        first_line = f.readline()
                        if not first_line.startswith('--'):
                            return False, "Backup file does not appear to be a valid PostgreSQL dump"
                except Exception as e:
                    return False, f"Backup file is corrupted: {str(e)}"
            else:
                # Check plain text file
                try:
                    with open(backup_path, 'r') as f:
                        first_line = f.readline()
                        if not first_line.startswith('--'):
                            return False, "Backup file does not appear to be a valid PostgreSQL dump"
                except Exception as e:
                    return False, f"Backup file is corrupted: {str(e)}"
            
            # Check metadata file
            metadata_file = f"{backup_path.with_suffix('')}.json"
            if not Path(metadata_file).exists():
                return False, "Backup metadata file missing"
            
            StructuredLogger.log_admin_action(
                'backup_verified',
                'database',
                None,
                {'backup_file': str(backup_path)}
            )
            
            return True, f"Backup file is valid ({file_size / (1024 * 1024):.2f} MB)"
        
        except Exception as e:
            StructuredLogger.log_error(
                'backup',
                f"Failed to verify backup: {str(e)}",
                {'backup_file': backup_file},
                'ERROR'
            )
            return False, f"Verification failed: {str(e)}"

    def get_backup_stats(self) -> Dict:
        """Get backup statistics.
        
        Returns:
            Dictionary with backup statistics
        """
        try:
            backups = self.list_backups()
            
            total_size = sum(b['actual_size_mb'] for b in backups)
            
            if backups:
                latest_backup = backups[0]
                oldest_backup = backups[-1]
            else:
                latest_backup = None
                oldest_backup = None
            
            return {
                'total_backups': len(backups),
                'total_size_mb': round(total_size, 2),
                'average_size_mb': round(total_size / len(backups), 2) if backups else 0,
                'latest_backup': latest_backup,
                'oldest_backup': oldest_backup,
                'backup_directory': str(self.backup_dir)
            }
        
        except Exception as e:
            StructuredLogger.log_error(
                'backup',
                f"Failed to get backup stats: {str(e)}",
                {},
                'ERROR'
            )
            return {}
