#!/usr/bin/env python3
"""One-time setup script: create the PostgreSQL database if it doesn't exist.

Reads connection details from PG_ADMIN_USER / PG_ADMIN_PASSWORD env vars
if set, otherwise prompts interactively. Not run against DATABASE_URL
directly since that points at the target database, which may not exist
yet on first run.

Usage:
    python scripts/create_pg_db.py
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv
from getpass import getpass

load_dotenv()

TARGET_DB_NAME = os.getenv("PG_DB_NAME", "travel_agency_db")


def create_database():
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    user = os.getenv("PG_ADMIN_USER") or input(f"PostgreSQL admin user [postgres]: ") or "postgres"
    password = os.getenv("PG_ADMIN_PASSWORD") or getpass(f"PostgreSQL password for {user}: ")

    conn = None
    try:
        print("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres",
        )
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET_DB_NAME,))
        exists = cursor.fetchone()

        if exists:
            print(f"Database '{TARGET_DB_NAME}' already exists")
        else:
            print(f"Creating database '{TARGET_DB_NAME}'...")
            cursor.execute(f'CREATE DATABASE "{TARGET_DB_NAME}"')
            print("Database created successfully")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.close()
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
