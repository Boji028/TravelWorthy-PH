# Docker Quick Start Guide

## What is Docker?

Docker packages PostgreSQL + pgAdmin in isolated containers. No installation needed, works everywhere.

---

## Quick Start (30 seconds)

### 1. Install Docker
- **Windows/Mac**: https://www.docker.com/products/docker-desktop
- **Linux**: `sudo apt-get install docker.io docker-compose`

### 2. Start PostgreSQL
```bash
cd fixed/
docker-compose up -d
```

That's it! PostgreSQL is running on port 5432.

### 3. Update `.env`
```bash
DATABASE_URL=postgresql://postgres:postgres@db:5432/travel_agency
```

### 4. Migrate your data
```bash
python scripts/migrate_sqlite_to_postgres.py
```

### 5. Test connection
```bash
python scripts/test_postgres_connection.py
```

### 6. Run your app
```bash
flask run
```

---

## Using pgAdmin (Visual Database Manager)

1. Open: http://localhost:5050
2. Login: admin@admin.com / admin
3. Add server:
   - Right-click "Servers" → Register → Server
   - Name: `Travel Agency DB`
   - Host: `db`
   - Username: `postgres`
   - Password: `postgres`

Now you can browse/edit database visually!

---

## Common Commands

### Start PostgreSQL
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs db
```

### Stop PostgreSQL
```bash
docker-compose down
```

### Stop + Delete data (reset)
```bash
docker-compose down -v
```

### Enter PostgreSQL shell
```bash
docker-compose exec db psql -U postgres
```

Then:
```sql
\l                          -- List databases
\dt                         -- List tables
SELECT COUNT(*) FROM users; -- Query data
\q                          -- Exit
```

---

## Troubleshooting

### Port 5432 already in use
```bash
# Find what's using port 5432
lsof -i :5432

# Stop the existing PostgreSQL
docker-compose down
# Or kill the process
```

### `db: command not found` in .env
The hostname `db` only works inside Docker containers. For local testing with docker-compose:
- From Flask app (in Docker): `postgresql://postgres:postgres@db:5432/travel_agency`
- From terminal (host machine): `postgresql://postgres:postgres@localhost:5432/travel_agency`

### Data persists but I want to reset
```bash
docker-compose down -v  # Delete volume
docker-compose up -d    # Recreate fresh
```

### Can't connect from host machine
Make sure port 5432 is mapped:
```yaml
ports:
  - "5432:5432"  # host:container
```

---

## For Production

Docker is great for development. For production:

1. **Railway.app**: Just push to GitHub, they handle deployment
2. **Heroku**: Same process, auto-detects Flask app
3. **VPS**: Install PostgreSQL directly, use native hosting

See [POSTGRES_SETUP_GUIDE.md](POSTGRES_SETUP_GUIDE.md) for production deployment.

---

## File Descriptions

- `docker-compose.yml` - PostgreSQL + pgAdmin setup
- `.dockerignore` - Files to exclude from Docker (uploads, cache, etc)
- `Dockerfile` (optional) - If you want to containerize your Flask app too

---

## Clean Everything

```bash
# Stop containers
docker-compose down

# Remove everything (containers, volumes, images)
docker system prune -a
```

⚠️ This deletes all Docker data!

---

Done! PostgreSQL is ready to use. 🚀
