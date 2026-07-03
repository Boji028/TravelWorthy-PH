#!/usr/bin/env python
"""Reset an admin account's password.

Reads the database connection from DATABASE_URL in .env. Prompts for
the new password interactively rather than hardcoding it in this file.

Usage:
    python scripts/reset_admin_password.py admin@travelworthyph.com
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from getpass import getpass

load_dotenv()


def get_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    db_url = db_url.replace('postgresql+psycopg2://', 'postgresql://')
    return psycopg2.connect(db_url)


def reset_password(email):
    new_password = getpass("Enter new password: ")
    confirm = getpass("Confirm new password: ")

    if new_password != confirm:
        print("Passwords do not match. Aborted.")
        sys.exit(1)
    if len(new_password) < 8:
        print("Password must be at least 8 characters. Aborted.")
        sys.exit(1)

    conn = get_connection()
    cursor = conn.cursor()

    password_hash = generate_password_hash(new_password)
    cursor.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (password_hash, email),
    )

    if cursor.rowcount == 0:
        print(f"No user found with email: {email}")
        conn.rollback()
    else:
        conn.commit()
        print("=" * 70)
        print(f"Password reset for {email}")
        print("=" * 70)

    cursor.close()
    conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/reset_admin_password.py <email>")
        sys.exit(1)
    reset_password(sys.argv[1])
