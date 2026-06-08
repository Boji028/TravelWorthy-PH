#!/usr/bin/env python3
"""Setup PostgreSQL database for travel agency."""

import psycopg2
from psycopg2 import sql
import sys

def create_database():
    """Create travel_agency_db database if it doesn't exist."""
    
    # Connection to default postgres database
    conn = None
    try:
        print("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="Enzo123",
            database="postgres"
        )
        
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", ("travel_agency_db",))
        exists = cursor.fetchone()
        
        if exists:
            print("✓ Database 'travel_agency_db' already exists")
        else:
            print("Creating database 'travel_agency_db'...")
            cursor.execute("CREATE DATABASE travel_agency_db")
            print("✓ Database created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {e}")
        if conn:
            conn.close()
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
