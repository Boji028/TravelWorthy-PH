#!/usr/bin/env python3
"""
Test PostgreSQL connection and database health.

Usage:
    python scripts/test_postgres_connection.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test PostgreSQL connection."""
    print("=" * 70)
    print("🔍 PostgreSQL Connection Test")
    print("=" * 70)
    print()
    
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not set in .env file!")
        return False
    
    print(f"📍 Database URL: {db_url.split('@')[0]}@[hidden]")
    print()
    
    try:
        from sqlalchemy import create_engine, text
        
        print("⏳ Connecting to PostgreSQL...")
        engine = create_engine(db_url, echo=False)
        
        with engine.connect() as connection:
            print("✅ Connection successful!")
            print()
            
            # Get PostgreSQL version
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"📦 PostgreSQL version: {version.split(',')[0]}")
            print()
            
            # Get database info
            result = connection.execute(text("SELECT datname FROM pg_database WHERE datname = current_database()"))
            db_name = result.fetchone()[0]
            print(f"🗄️  Database: {db_name}")
            print()
            
            # Get tables
            result = connection.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📊 Tables ({len(tables)}):")
            for table in tables:
                # Get row count
                row_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                row_count = row_result.fetchone()[0]
                print(f"   • {table}: {row_count} rows")
            
            print()
            print("✅ All checks passed!")
            return True
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Is PostgreSQL running?")
        print("   2. Check DATABASE_URL format:")
        print("      postgresql://user:password@host:port/database")
        print("   3. Verify username and password are correct")
        print("   4. For Docker: host should be 'db' not 'localhost'")
        return False


if __name__ == '__main__':
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
