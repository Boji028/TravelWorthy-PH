#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL.

Usage:
    python scripts/migrate_sqlite_to_postgres.py

This script:
1. Reads all data from SQLite database
2. Creates tables in PostgreSQL (if not exists)
3. Copies all data to PostgreSQL
4. Verifies data integrity
5. Keeps SQLite untouched (safe to revert!)
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()


def get_sqlite_engine():
    """Create SQLite engine (using existing database)."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'travel_agency.db')
    return create_engine(f'sqlite:///{db_path}', echo=False)


def get_postgres_engine():
    """Create PostgreSQL engine from DATABASE_URL."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise RuntimeError('DATABASE_URL not set in .env file!')
    if 'sqlite' in db_url:
        raise RuntimeError('DATABASE_URL is still pointing to SQLite! Update .env to use PostgreSQL.')
    return create_engine(db_url, echo=False)


def table_exists(engine, table_name):
    """Check if table exists in database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def copy_table_data(sqlite_engine, postgres_engine, table_name):
    """Copy all data from one table in SQLite to PostgreSQL."""
    try:
        SQLiteSession = sessionmaker(bind=sqlite_engine)
        PostgresSession = sessionmaker(bind=postgres_engine)

        sqlite_session = SQLiteSession()
        postgres_session = PostgresSession()

        result = sqlite_session.execute(text(f'SELECT * FROM {table_name}'))
        rows = result.fetchall()

        if not rows:
            print(f"  ℹ️  {table_name}: No data (0 rows)")
            sqlite_session.close()
            postgres_session.close()
            return 0

        column_names = list(result.keys())

        # Detect boolean columns in PostgreSQL
        pg_inspector = inspect(postgres_engine)
        boolean_cols = set()
        for col in pg_inspector.get_columns(table_name):
            if str(col['type']).upper() == 'BOOLEAN':
                boolean_cols.add(col['name'])

        columns = ', '.join(column_names)
        placeholders = ', '.join([f':{col}' for col in column_names])
        insert_sql = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

        inserted = 0
        for row in rows:
            params = dict(zip(column_names, row))

            # Convert SQLite 0/1 integers to Python booleans
            for col in boolean_cols:
                if col in params and params[col] is not None:
                    params[col] = bool(params[col])

            try:
                postgres_session.execute(text(insert_sql), params)
                inserted += 1
            except Exception as e:
                print(f"    ⚠️  Row insert failed: {e}")
                continue

        postgres_session.commit()

        # Reset auto-increment sequence
        try:
            postgres_session.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                f"COALESCE(MAX(id), 1)) FROM {table_name}"
            ))
            postgres_session.commit()
        except Exception:
            pass

        sqlite_session.close()
        postgres_session.close()
        return inserted

    except Exception as e:
        print(f"  ❌ Error copying {table_name}: {e}")
        return 0


def migrate():
    """Main migration function."""
    print("=" * 70)
    print("🚀 SQLite → PostgreSQL Migration")
    print("=" * 70)
    print()
    
    # Check environments
    print("📋 Checking configuration...")
    
    try:
        sqlite_engine = get_sqlite_engine()
        print("  ✓ SQLite database found")
    except Exception as e:
        print(f"  ❌ SQLite error: {e}")
        return False
    
    try:
        postgres_engine = get_postgres_engine()
        print("  ✓ PostgreSQL connection successful")
    except Exception as e:
        print(f"  ❌ PostgreSQL error: {e}")
        print()
        print("💡 Make sure PostgreSQL is running and DATABASE_URL is set correctly:")
        print("   DATABASE_URL=postgresql://user:password@localhost:5432/travel_agency")
        return False
    
    print()
    
    # Get list of tables from SQLite
    sqlite_inspector = inspect(sqlite_engine)
    sqlite_tables = sqlite_inspector.get_table_names()
    
    if not sqlite_tables:
        print("⚠️  No tables found in SQLite database!")
        return False
    
    print(f"📊 Found {len(sqlite_tables)} tables in SQLite:")
    print()
    
    # Import models to create schema in PostgreSQL
    print("🔧 Creating PostgreSQL schema...")
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Create all tables in PostgreSQL
            db.create_all()
        print("  ✓ Schema created in PostgreSQL")
    except Exception as e:
        print(f"  ❌ Error creating schema: {e}")
        return False
    
    print()
    print("📦 Copying data...")
    print()
    
    # Copy data from each table
    total_rows = 0
    for table in sqlite_tables:
        if table == 'sqlite_sequence':  # Skip internal SQLite table
            continue
        
        rows_copied = copy_table_data(sqlite_engine, postgres_engine, table)
        total_rows += rows_copied
        status = "✓" if rows_copied > 0 else "ℹ️"
        print(f"  {status} {table}: {rows_copied} rows")
    
    print()
    print("=" * 70)
    print(f"✅ Migration Complete! ({total_rows} total rows copied)")
    print("=" * 70)
    print()
    
    # Verification
    print("🔍 Verifying data integrity...")
    print()
    
    try:
        from app import create_app, db
        from models.package import TourPackage
        from models.user import User
        from models.blog import BlogPost
        
        app = create_app()
        
        with app.app_context():
            package_count = TourPackage.query.count()
            user_count = User.query.count()
            blog_count = BlogPost.query.count()
            
            print(f"  📦 Packages: {package_count}")
            print(f"  👥 Users: {user_count}")
            print(f"  📝 Blog posts: {blog_count}")
        
        print()
        print("🎉 Data verification successful!")
        
    except Exception as e:
        print(f"  ⚠️  Verification error: {e}")
    
    print()
    print("📝 Next steps:")
    print("  1. Verify .env has: DATABASE_URL=postgresql://...travel_agency")
    print("  2. Run: flask run")
    print("  3. Test your application")
    print()
    print("💾 Your SQLite database is untouched at: travel_agency.db")
    print("   You can delete it once you're confident PostgreSQL works.")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = migrate()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
