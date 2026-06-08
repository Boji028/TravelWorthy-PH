# PostgreSQL Migration - Complete Setup Guide

## Overview

You're upgrading from SQLite to PostgreSQL. This guide covers everything in order.

---

## Choose Your Path

### Path A: Quick Docker Setup (Easiest) ⭐
- No installation needed
- Works on Windows/Mac/Linux
- Best for beginners
- **Time: 5 minutes**

→ Go to **Step 1: Docker Setup**

### Path B: Local PostgreSQL Installation (More Control)
- Install PostgreSQL on your machine
- Full control
- Better for production prep
- **Time: 15 minutes**

→ Go to **Step 2: Local PostgreSQL**

### Path C: Hybrid (Docker for Dev, Cloud for Production)
- Use Docker locally
- Deploy to Railway/Render
- Scalable
- **Time: 20 minutes total**

→ Go to **Step 1 + Step 3**

---

## Step 1: Docker Setup (If choosing Path A or C)

**File:** [DOCKER_QUICK_START.md](DOCKER_QUICK_START.md)

1. Install Docker Desktop
2. Run: `docker-compose up -d`
3. Update `.env`: `DATABASE_URL=postgresql://postgres:postgres@db:5432/travel_agency`
4. Continue to **Step 3: Data Migration**

---

## Step 2: Local PostgreSQL Installation (If choosing Path B)

**File:** [POSTGRES_SETUP_GUIDE.md](POSTGRES_SETUP_GUIDE.md) - Part 1

Follow instructions for your OS:
- **Windows**: Use installer or WSL
- **Mac**: Use Homebrew
- **Linux**: Use apt-get/yum

After installation:
1. Create database: `createdb travel_agency`
2. Update `.env`: `DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/travel_agency`
3. Continue to **Step 3: Data Migration**

---

## Step 3: Data Migration (All Paths)

### Prerequisite
```bash
# Install PostgreSQL driver
pip install -r requirements.txt
```

### Run Migration
```bash
# Backup your SQLite (just in case)
cp travel_agency.db travel_agency.db.backup

# Run migration script
python scripts/migrate_sqlite_to_postgres.py
```

This will:
- ✅ Keep SQLite untouched (safe!)
- ✅ Create tables in PostgreSQL
- ✅ Copy all data
- ✅ Verify everything worked

### Test Connection
```bash
python scripts/test_postgres_connection.py
```

Expected output:
```
✅ Connection successful!
PostgreSQL version: PostgreSQL 15.x
Database: travel_agency
Tables (12):
  • blog_posts: 5 rows
  • tour_packages: 10 rows
  • users: 3 rows
  ...
```

---

## Step 4: Update Your Routes (Optional But Recommended)

Add image metadata tracking to your routes.

**File:** [IMAGE_METADATA_GUIDE.md](IMAGE_METADATA_GUIDE.md)

This lets you monitor storage usage. Skip if you want to do it later.

---

## Step 5: Test Everything Works

### Start your app
```bash
flask run
```

### Check logs
You should see:
```
[INFO] Using PostgreSQL database
[INFO] WARNING in app.run_simple: This is a development server...
```

### Visit your site
- Homepage: http://localhost:5000
- Admin dashboard: http://localhost:5000/admin
- Login: Use your ADMIN_EMAIL from .env

### Verify data
Everything should work exactly like before!

---

## Step 6: Production Deployment (If needed)

**File:** [POSTGRES_SETUP_GUIDE.md](POSTGRES_SETUP_GUIDE.md) - Part 5

Choose one:

### Option 1: Railway.app (Easiest) ⭐
1. Sign up: https://railway.app
2. Connect your GitHub repo
3. Railway auto-detects Flask app
4. Add PostgreSQL plugin
5. Railway auto-sets DATABASE_URL
6. Deploy! 🚀

### Option 2: Render.com
1. Sign up: https://render.com
2. Create PostgreSQL instance
3. Create Web Service
4. Set environment variables
5. Deploy!

### Option 3: Your Own VPS
- DigitalOcean, Linode, Vultr, Hetzner (~$5-10/month)
- Install PostgreSQL yourself
- Deploy Flask app
- You manage everything

---

## Troubleshooting

### "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### "Cannot connect to database"
Check .env DATABASE_URL format:
```
postgresql://user:password@host:port/database
```

For Docker: host should be `db` not `localhost`

### "Connection refused"
- **Docker**: Is `docker-compose up -d` running?
- **Local**: Is PostgreSQL running?

### "Database does not exist"
```bash
# Docker
docker-compose exec db createdb -U postgres travel_agency

# Local
createdb travel_agency
```

---

## Comparison: Before vs After

| Factor | SQLite | PostgreSQL |
|--------|--------|-----------|
| **Users** | Works fine < 50 | Handles 1000+ easily |
| **Concurrent requests** | ⚠️ Locks database | ✅ Unlimited |
| **Backups** | 📁 Copy single file | ✅ Automated, reliable |
| **Production ready** | ❌ No | ✅ Yes |
| **Code changes** | — | None! (SQLAlchemy handles it) |
| **Cost** | Free | Free (or $5-20/month if cloud) |

---

## Files Created

| File | Purpose |
|------|---------|
| `POSTGRES_SETUP_GUIDE.md` | Complete PostgreSQL setup guide |
| `DOCKER_QUICK_START.md` | Docker-specific instructions |
| `docker-compose.yml` | PostgreSQL + pgAdmin setup |
| `.dockerignore` | Files to exclude from Docker |
| `.env.example` | Environment variable template |
| `scripts/migrate_sqlite_to_postgres.py` | Data migration script |
| `scripts/test_postgres_connection.py` | Connection test script |

---

## Quick Reference

### Docker Users
```bash
docker-compose up -d
python scripts/migrate_sqlite_to_postgres.py
python scripts/test_postgres_connection.py
flask run
```

### Local PostgreSQL Users
```bash
# Create database first
createdb travel_agency

# Then migrate
python scripts/migrate_sqlite_to_postgres.py
python scripts/test_postgres_connection.py
flask run
```

### Production (Railway)
```bash
# Push to GitHub
git push origin main
# Railway auto-deploys with DATABASE_URL
```

---

## Next Steps

1. ✅ Choose your path (Docker / Local / Hybrid)
2. ✅ Run setup (Step 1 or 2)
3. ✅ Migrate data (Step 3)
4. ✅ Test (Step 5)
5. ✅ Deploy to production (Step 6)

**Estimated total time: 15-30 minutes**

Questions? Check the relevant guide file above. 🚀

---

## Rollback Plan (Emergency)

If something goes wrong:

```bash
# Switch back to SQLite
# In .env, change DATABASE_URL to:
DATABASE_URL=sqlite:///travel_agency.db

# Your data is safe!
# SQLite backup is at: travel_agency.db.backup
```

All changes are reversible!
