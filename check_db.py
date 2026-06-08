#!/usr/bin/env python3
"""Quick diagnostic script to check PostgreSQL connection and database state."""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def check_database():
    """Check PostgreSQL connection and tables."""
    print("=" * 60)
    print("DATABASE DIAGNOSTIC CHECK")
    print("=" * 60)
    
    # Check environment
    db_url = os.getenv('DATABASE_URL')
    print(f"\n1. DATABASE_URL: {db_url if db_url else 'NOT SET (will use SQLite)'}")
    
    if not db_url:
        print("   ⚠️  WARNING: DATABASE_URL not set! Using SQLite fallback.")
        print("   To use PostgreSQL, set DATABASE_URL in .env file:")
        print("   DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/travel_agency_db")
    
    # Try to import and connect
    print("\n2. Testing Flask app initialization...")
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            print(f"   ✓ Flask app created")
            print(f"   Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            
            # Try to get database type
            db_type = 'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'
            print(f"   Using: {db_type}")
            
            # Test connection
            print("\n3. Testing database connection...")
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(db.text("SELECT 1"))
                    print("   ✓ Database connection successful!")
            except Exception as e:
                print(f"   ✗ Connection failed: {e}")
                print(f"   ERROR TYPE: {type(e).__name__}")
                return False
            
            # Check tables
            print("\n4. Checking database tables...")
            try:
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"   Found {len(tables)} tables:")
                for table in sorted(tables):
                    print(f"      - {table}")
                
                if 'blog_posts' not in tables:
                    print("\n   ✗ ERROR: 'blog_posts' table not found!")
                    print("   Run: flask db upgrade")
                    return False
                else:
                    print("\n   ✓ All required tables present")
            except Exception as e:
                print(f"   ✗ Error checking tables: {e}")
                return False
            
            # Check upload folder
            print("\n5. Checking upload folder...")
            upload_folder = app.config.get('UPLOAD_FOLDER')
            if os.path.exists(upload_folder):
                print(f"   ✓ Upload folder exists: {upload_folder}")
            else:
                print(f"   ✗ Upload folder missing: {upload_folder}")
                print(f"   Creating folder...")
                os.makedirs(upload_folder, exist_ok=True)
                print(f"   ✓ Created")
    
    except Exception as e:
        print(f"   ✗ Failed to create app: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✓ All checks passed!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = check_database()
    sys.exit(0 if success else 1)
