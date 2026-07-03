# PostgreSQL Setup & Migration Guide

## Quick Overview

You're moving from SQLite (single-file database) to PostgreSQL (production-grade database). The good news: **your Flask code stays almost identical!**

---

## Part 1: Local PostgreSQL Setup

### Windows Users

#### Option A: PostgreSQL Installer (Recommended)
1. Download from https://www.postgresql.org/download/windows/
2. Run installer, note the password you set for `postgres` user
3. In pgAdmin (comes with installer), create a new database:
   - Right-click "Databases" → Create → Database
   - Name: `travel_agency`
   - Owner: `postgres`

#### Option B: Docker (Easiest, No Installation)
Skip to **Part 4: Docker Setup** below

---

### Mac Users

Using Homebrew:
```bash
brew install postgresql@15
brew services start postgresql@15
createdb travel_agency
```

---

### Linux Users

```bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb travel_agency
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your_secure_password';"
```

---

## Part 2: Update Configuration

### 1. Create `.env` file with PostgreSQL credentials:

```bash
# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/travel_agency

# Or for production, Railway/Render will provide this automatically
# DATABASE_URL=postgresql://user:pass@your-db-host:5432/travel_agency

# Keep existing settings
SECRET_KEY=your_secret_key_here
FLASK_DEBUG=false
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

### 2. Update `requirements.txt` (already done ✓)
- Added `psycopg2-binary` (PostgreSQL driver)
- Added `Flask-Migrate` (database migrations)

### 3. Install packages:
```bash
pip install -r requirements.txt
```

---

## Part 3: Migrate Your Data

### Step 1: Backup SQLite (Just in case!)
```bash
cp travel_agency.db travel_agency.db.backup
```

### Step 2: Run migration script
```bash
python scripts/migrate_sqlite_to_postgres.py
```

This script will:
- ✅ Read all data from SQLite
- ✅ Create all tables in PostgreSQL
- ✅ Copy all data over
- ✅ Verify everything worked
- ✅ Keep SQLite untouched (safe!)

### Step 3: Verify the migration
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
>>>     tables = db.inspect(db.engine).get_table_names()
>>>     print(f"Tables: {tables}")
>>>     from models.package import TourPackage
>>>     count = TourPackage.query.count()
>>>     print(f"Packages: {count}")
```

### Step 4: Update your `.env` to use PostgreSQL
In your `.env`, change:
```bash
# Old (SQLite)
# DATABASE_URL=sqlite:///travel_agency.db

# New (PostgreSQL)
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/travel_agency
```

### Step 5: Restart Flask
```bash
flask run
```

---

## Part 4: Docker Setup (Production-Ready)

No PostgreSQL installation needed! Docker handles everything.

### 1. Install Docker
- **Windows/Mac**: https://www.docker.com/products/docker-desktop
- **Linux**: `sudo apt-get install docker.io docker-compose`

### 2. Files included:
- `docker-compose.yml` - PostgreSQL + pgAdmin
- `.dockerignore` - Excludes uploads, cache
- `Dockerfile` (optional) - For Flask app

### 3. Start PostgreSQL with Docker:
```bash
docker-compose up -d
```

This creates:
- PostgreSQL database (port 5432)
- pgAdmin (port 5050) - Visual database manager
- Auto-creates `travel_agency` database

### 4. Access pgAdmin
- URL: http://localhost:5050
- Email: `admin@admin.com`
- Password: `admin`

Then:
1. Right-click "Servers" → Register → Server
2. Name: `Local PostgreSQL`
3. Host: `db` (hostname in docker-compose)
4. Username: `postgres`
5. Password: `postgres`

### 5. Update `.env`:
```bash
DATABASE_URL=postgresql://postgres:postgres@db:5432/travel_agency
```

### 6. Run migration:
```bash
python scripts/migrate_sqlite_to_postgres.py
```

### 7. Stop Docker:
```bash
docker-compose down
```

---

## Part 5: Production Deployment

### Option A: Railway.app (Recommended for Beginners)

1. Sign up at https://railway.app
2. Connect your GitHub repo
3. Railway auto-detects Flask app
4. Add PostgreSQL plugin
5. Railway auto-sets `DATABASE_URL` environment variable
6. Deploy! 🚀

### Option B: Render.com

1. Sign up at https://render.com
2. Create PostgreSQL database
3. Copy connection string to `.env`
4. Deploy Flask app
5. Set environment variables in dashboard

### Option C: Your Own VPS

Affordable VPS (~$5-10/month):
- DigitalOcean
- Linode
- Vultr
- Hetzner

Install PostgreSQL, deploy Flask app, use your own database.

---

## Part 6: Verify Everything Works

### Test PostgreSQL connection:
```bash
python scripts/test_postgres_connection.py
```

### Check database health:
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
>>>     result = db.session.execute(db.text("SELECT version()"))
>>>     print(result.fetchone())
```

---

## Troubleshooting

### Error: `psycopg2` not installed
```bash
pip install psycopg2-binary
```

### Error: Cannot connect to database
Check your `.env` DATABASE_URL:
```bash
# Format: postgresql://user:password@host:port/database
postgresql://postgres:mypassword@localhost:5432/travel_agency
```

### Error: Database doesn't exist
```bash
# Create it manually
psql -U postgres -c "CREATE DATABASE travel_agency;"
```

### Error: Permission denied
On Linux, use:
```bash
sudo -u postgres psql -c "CREATE DATABASE travel_agency;"
```

---

## Summary

| Step | Command | Time |
|------|---------|------|
| Install PostgreSQL | See Part 1 | 5 min |
| Update config | Create `.env` | 2 min |
| Migrate data | `python scripts/migrate_sqlite_to_postgres.py` | 1 min |
| Test connection | `python scripts/test_postgres_connection.py` | 1 min |
| Deploy | Railway/Render/VPS | varies |

**Total: ~10 minutes to switch!** ⚡

---

## What's Different in PostgreSQL?

✅ Handles 100+ concurrent users (SQLite can't)  
✅ Better backups & recovery  
✅ Faster queries with many users  
✅ Better data integrity  
✅ Production-ready  
✅ **Your Flask code is unchanged!**

---

## Rollback Plan (If needed)

```bash
# Switch .env back to SQLite
DATABASE_URL=sqlite:///travel_agency.db

# Your SQLite database is untouched in travel_agency.db.backup
```

All changes are reversible! 🔄
