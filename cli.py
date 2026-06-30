"""Flask CLI commands for administrative tasks."""
import os
import click
from flask import current_app


def register_commands(app):
    """Register all CLI commands with the Flask app."""

    @app.cli.command('seed-admin')
    def seed_admin():
        """Create the default admin user from ADMIN_EMAIL / ADMIN_PASSWORD env vars.

        Usage:
            flask seed-admin
        """
        from app import db
        from models.user import User
        from werkzeug.security import generate_password_hash

        admin_email    = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')

        if not admin_email or not admin_password:
            click.echo(
                'ERROR: ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env',
                err=True
            )
            raise SystemExit(1)

        existing = User.query.filter_by(email=admin_email).first()
        if existing:
            click.echo(f'Admin {admin_email} already exists. Skipping.')
            return

        admin = User(
            name='Admin',
            email=admin_email,
            password=generate_password_hash(admin_password),
            is_admin=True,
            email_verified=True,
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f'✅ Admin {admin_email} created successfully.')

    @app.cli.command('list-users')
    def list_users():
        """Print all users in the database."""
        from models.user import User
        users = User.query.order_by(User.id).all()
        if not users:
            click.echo('No users found.')
            return
        for u in users:
            click.echo(
                f'[{u.id}] {u.email:40s} | admin={u.is_admin} | verified={u.email_verified}'
            )

    @app.cli.command('cleanup-tokens')
    def cleanup_tokens():
        """Delete expired email verification tokens.

        Usage:
            flask cleanup-tokens

        Run this periodically (e.g. daily via cron) to keep the table small.
        """
        from email_verification_service import EmailVerificationService
        deleted = EmailVerificationService.cleanup_expired_tokens()
        click.echo(f'Deleted {deleted} expired verification token(s).')