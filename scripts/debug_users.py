#!/usr/bin/env python
"""Debug script to inspect user accounts in the database.

Reads the database connection from DATABASE_URL in .env — no
credentials are hardcoded in this file.

Usage:
    python scripts/debug_users.py
    python scripts/debug_users.py --check-password someone@example.com
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
from getpass import getpass

load_dotenv()


def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
    return psycopg2.connect(db_url)


def list_users(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, is_admin, email_verified, password " "FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()

    print("\n" + "=" * 80)
    print("REGISTERED USERS IN DATABASE")
    print("=" * 80)

    for user_id, email, name, is_admin, verified, password_hash in users:
        print(f"\nID: {user_id}")
        print(f"Email: {email}")
        print(f"Name: {name}")
        print(f"Admin: {is_admin}")
        print(f"Verified: {verified}")
        print(f"Has password: {'yes' if password_hash else 'no (OAuth-only account)'}")

    cursor.close()


def check_password(conn, email):
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    cursor.close()

    if not result:
        print(f"\n{email}: NOT FOUND IN DATABASE")
        return
    if not result[0]:
        print(f"\n{email}: has no password set (OAuth-only account)")
        return

    test_pwd = getpass(f"Enter password to test for {email}: ")
    matches = check_password_hash(result[0], test_pwd)
    print(f"\n{email}: password {'MATCHES' if matches else 'does NOT match'}")


if __name__ == "__main__":
    conn = get_connection()

    if "--check-password" in sys.argv:
        idx = sys.argv.index("--check-password")
        target_email = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else None
        if not target_email:
            print("Usage: python scripts/debug_users.py --check-password <email>")
        else:
            check_password(conn, target_email)
    else:
        list_users(conn)

    conn.close()
