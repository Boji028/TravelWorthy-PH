# PostgreSQL Migration Quick Reference

## One-Page Cheat Sheet

---

## 3 Setup Paths

### 🐳 Docker (Easiest - No Installation)
```bash
docker-compose up -d
```
**Setup time:** 2 minutes  
**Best for:** Beginners, testing

### 🖥️ Local PostgreSQL
```bash
createdb travel_agency
```
**Setup time:** 10-20 minutes  
**Best for:** Development, learning

### ☁️ Production (Railway/Render)
```bash
# Push to GitHub
git push origin main
```
**Setup time:** 5 minutes  
**Best for:** Going live

---

## 5-Minute Setup Guide

### 1. Install Dependency
```bash
pip install psycopg2-binary Flask-Migrate
```

### 2. Start Database (Choose One)
```bash
# Docker
docker-compose up -d

# Local PostgreSQL
createdb travel_agency
```

### 3. Update `.env`
```bash
# Docker
DATABASE_URL=postgresql://postgres:postgres@db:5432/travel_agency

# Local
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/travel_agency
```

### 4. Migrate Data
```bash
python scripts/migrate_sqlite_to_postgres.py
```

### 5. Test & Run
```bash
python scripts/test_postgres_connection.py
flask run
```

---

## Common Commands

| Task | Command |
|------|---------|
| Start PostgreSQL (Docker) | `docker-compose up -d` |
| Stop PostgreSQL | `docker-compose down` |
| View logs | `docker-compose logs db` |
| Enter pgAdmin | http://localhost:5050 |
| Migrate data | `python scripts/migrate_sqlite_to_postgres.py` |
| Test connection | `python scripts/test_postgres_connection.py` |
| Check tables | `docker-compose exec db psql -U postgres travel_agency -c "\dt"` |
| Reset database | `docker-compose down -v && docker-compose up -d` |
| Deploy to Railway | `git push origin main` |

---

## DATABASE_URL Examples

```bash
# SQLite (Development - Default)
sqlite:///travel_agency.db

# PostgreSQL (Local)
postgresql://postgres:password@localhost:5432/travel_agency

# PostgreSQL (Docker)
postgresql://postgres:postgres@db:5432/travel_agency

# PostgreSQL (Railway/Render - Auto)
postgresql://user:pass@host:5432/database
```

---

## Troubleshooting Quick Fix

| Error | Fix |
|-------|-----|
| `psycopg2 not found` | `pip install psycopg2-binary` |
| `Cannot connect` | Check DATABASE_URL, verify service running |
| `Port 5432 in use` | `docker-compose down` or `lsof -i :5432` |
| `DB doesn't exist` | `createdb travel_agency` |
| `No migrations` | `pip install Flask-Migrate` |

---

## File Reference

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Start PostgreSQL + pgAdmin |
| `scripts/migrate_sqlite_to_postgres.py` | Move data SQLite → PostgreSQL |
| `scripts/test_postgres_connection.py` | Test database connection |
| `.env` | Database credentials (add to .gitignore) |
| `requirements.txt` | Python dependencies |

---

## Before/After Checklist

### Before
```
❌ SQLite
❌ Single file database
❌ No concurrent user support
❌ Poor backups
❌ Production-unfriendly
```

### After
```
✅ PostgreSQL
✅ Production database
✅ 1000+ concurrent users
✅ Easy automated backups
✅ Enterprise-grade
```

---

## Cost Comparison

| Provider | Free Tier | Paid |
|----------|-----------|------|
| **Docker (Local)** | ✅ Free forever | N/A |
| **Railway.app** | ✅ $5 free/month | $7+/month |
| **Render.com** | ✅ Free PostgreSQL | $7+/month |
| **AWS RDS** | ✅ 12 months free | $10+/month |
| **DigitalOcean** | ✅ $200 credit | $5+/month |

---

## Performance Gains

```
SQLite:
  - Max 50 concurrent users
  - No query optimization
  - File locking issues
  - Backups = copy file

PostgreSQL:
  - 1000+ concurrent users
  - Advanced query optimization
  - Row-level locking
  - Automated backups
  - Replication support
```

---

## Rollback Plan (Emergency)

```bash
# Switch back to SQLite
# In .env, change to:
DATABASE_URL=sqlite:///travel_agency.db

# Restart Flask
flask run

# Your data is safe!
# SQLite copy: travel_agency.db.backup
```

---

## Quick Links

- 📖 Full Guide: [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md)
- 🐳 Docker: [DOCKER_QUICK_START.md](DOCKER_QUICK_START.md)
- 🖥️ PostgreSQL: [POSTGRES_SETUP_GUIDE.md](POSTGRES_SETUP_GUIDE.md)
- 📊 Complete: [POSTGRES_COMPLETE.md](POSTGRES_COMPLETE.md)

---

## Timeline Estimate

```
Docker Path:        5-10 minutes
Local Path:         15-25 minutes
Production Path:    5 minutes (after setup)
```

---

## Decision Tree

```
? Do you have Docker installed?
├─ YES → Use docker-compose (easiest)
└─ NO → Install PostgreSQL locally

? Ready to go to production?
├─ YES → Try Railway.app (1-click deployment)
└─ NO → Develop locally first

? Want to migrate data now?
├─ YES → python scripts/migrate_sqlite_to_postgres.py
└─ NO → Do it later, Flask still works with SQLite

? Want metadata tracking?
├─ YES → See IMAGE_METADATA_GUIDE.md
└─ NO → Skip for now, can add later
```

---

## Pro Tips

1. ✅ Always backup: `cp travel_agency.db travel_agency.db.backup`
2. ✅ Test connection first: `python scripts/test_postgres_connection.py`
3. ✅ Use docker-compose for development (no installation)
4. ✅ Use Railway/Render for production (simplest)
5. ✅ Never commit `.env` file to git
6. ✅ Keep `travel_agency.db` for backup reference
7. ✅ Monitor uploads folder size (cleanup script available)

---

## Database Comparison Matrix

```
                SQLite    PostgreSQL    MySQL
Concurrent:       ❌          ✅          ✅
Production:       ❌          ✅          ✅
Backups:          ⚠️          ✅          ✅
Queries:          ⚠️          ✅          ✅
ACID:             ⚠️          ✅          ✅
Setup:            ✅          ✅          ⚠️
Cost:             ✅          ✅          ✅
```

---

## Keep It Simple

```
Development:      Docker + local PostgreSQL
Testing:          Docker with test database
Production:       Railway.app or your VPS
Backup:           Database snapshots
```

---

## You're Ready! 🚀

Your PostgreSQL setup is complete. Just follow [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) step by step.

**Total time to production: ~30 minutes**

Good luck! 🎉
