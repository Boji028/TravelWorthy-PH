#!/usr/bin/env python
"""Backup management utility script.

Usage:
    python scripts/manage_backups.py create      - Create backup now
    python scripts/manage_backups.py list        - List all backups
    python scripts/manage_backups.py restore <file> - Restore from backup
    python scripts/manage_backups.py verify <file>  - Verify backup file
    python scripts/manage_backups.py cleanup [days] - Delete old backups
    python scripts/manage_backups.py stats       - Show backup statistics
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backup_service import BackupService
from tabulate import tabulate
import click


backup_service = BackupService()


@click.group()
def cli():
    """Database backup management utility."""
    pass


@cli.command()
@click.option("--compress", is_flag=True, default=True, help="Compress backup (default: True)")
@click.option("--metadata", is_flag=True, default=True, help="Include metadata (default: True)")
def create(compress, metadata):
    """Create a new database backup."""
    click.echo("Creating backup...")
    success, message, backup_path = backup_service.create_backup(compress=compress, include_metadata=metadata)

    if success:
        click.secho(f"✓ {message}", fg="green")
    else:
        click.secho(f"✗ {message}", fg="red")
        sys.exit(1)


@cli.command()
@click.option("--limit", type=int, default=None, help="Limit number of backups to show")
def list(limit):
    """List all available backups."""
    backups = backup_service.list_backups(limit=limit)

    if not backups:
        click.echo("No backups found.")
        return

    # Format data for table
    table_data = []
    for backup in backups:
        table_data.append(
            [
                backup["name"],
                backup["timestamp"],
                f"{backup['actual_size_mb']:.2f} MB",
                backup["database"],
                "✓" if backup["compressed"] else "✗",
            ]
        )

    headers = ["Backup Name", "Timestamp", "Size", "Database", "Compressed"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@cli.command()
@click.argument("backup_file")
def restore(backup_file):
    """Restore database from a backup file."""
    if not os.path.exists(backup_file):
        click.secho(f"✗ File not found: {backup_file}", fg="red")
        sys.exit(1)

    if not click.confirm(f"Are you sure you want to restore from {backup_file}? This will overwrite the current database."):
        click.echo("Restore cancelled.")
        return

    click.echo("Restoring database...")
    success, message = backup_service.restore_backup(backup_file)

    if success:
        click.secho(f"✓ {message}", fg="green")
    else:
        click.secho(f"✗ {message}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("backup_file")
def verify(backup_file):
    """Verify the integrity of a backup file."""
    if not os.path.exists(backup_file):
        click.secho(f"✗ File not found: {backup_file}", fg="red")
        sys.exit(1)

    click.echo(f"Verifying {backup_file}...")
    success, message = backup_service.verify_backup(backup_file)

    if success:
        click.secho(f"✓ {message}", fg="green")
    else:
        click.secho(f"✗ {message}", fg="red")
        sys.exit(1)


@cli.command()
@click.option("--days", type=int, default=7, help="Keep backups newer than X days (default: 7)")
def cleanup(days):
    """Delete backups older than specified days."""
    if not click.confirm(f"Delete backups older than {days} days?"):
        click.echo("Cleanup cancelled.")
        return

    click.echo("Cleaning up old backups...")
    deleted_count, freed_space = backup_service.cleanup_old_backups(retention_days=days)

    click.secho(f"✓ Deleted {deleted_count} backups, freed {freed_space:.2f} MB", fg="green")


@cli.command()
def stats():
    """Show backup statistics."""
    stats = backup_service.get_backup_stats()

    if not stats:
        click.echo("No backup statistics available.")
        return

    click.echo("Backup Statistics:")
    click.echo("=" * 50)
    click.echo(f"Total Backups: {stats['total_backups']}")
    click.echo(f"Total Size: {stats['total_size_mb']:.2f} MB")
    click.echo(f"Average Backup Size: {stats['average_size_mb']:.2f} MB")
    click.echo(f"Backup Directory: {stats['backup_directory']}")

    if stats["latest_backup"]:
        click.echo(f"\nLatest Backup:")
        click.echo(f"  Name: {stats['latest_backup']['name']}")
        click.echo(f"  Time: {stats['latest_backup']['timestamp']}")
        click.echo(f"  Size: {stats['latest_backup']['actual_size_mb']:.2f} MB")

    if stats["oldest_backup"]:
        click.echo(f"\nOldest Backup:")
        click.echo(f"  Name: {stats['oldest_backup']['name']}")
        click.echo(f"  Time: {stats['oldest_backup']['timestamp']}")
        click.echo(f"  Size: {stats['oldest_backup']['actual_size_mb']:.2f} MB")


if __name__ == "__main__":
    cli()
