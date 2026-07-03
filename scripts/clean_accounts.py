#!/usr/bin/env python
"""Delete corrupted/test accounts and show remaining users.

Reads the database connection from DATABASE_URL in .env — no
credentials are hardcoded in this file.

Usage:
    python scripts/clean_accounts.py user1@example.com user2@example.com
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    # psycopg2 doesn't understand the '+psycopg2' SQLAlchemy driver suffix
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
    return psycopg2.connect(db_url)


def clean_accounts(emails):
    if not emails:
        print("No emails provided. Usage: python scripts/clean_accounts.py <email1> <email2> ...")
        return

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["%s"] * len(emails))
    print(f"Deleting accounts: {', '.join(emails)}")
    cursor.execute(f"DELETE FROM users WHERE email IN ({placeholders})", tuple(emails))
    conn.commit()
    print(f"Deleted {cursor.rowcount} account(s)")

    cursor.execute("SELECT id, email, name FROM users ORDER BY id")
    users = cursor.fetchall()

    print("\n" + "=" * 60)
    print("REMAINING USERS:")
    print("=" * 60)
    for uid, email, name in users:
        print(f"  ID {uid}: {email:40} ({name})")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    clean_accounts(sys.argv[1:])
