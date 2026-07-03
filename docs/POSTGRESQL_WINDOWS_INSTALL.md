# PostgreSQL Installation Guide for Windows

## Complete Step-by-Step Setup

You'll have PostgreSQL running and configured in ~15 minutes.

---

## Step 1: Download PostgreSQL Installer

1. Go to: https://www.postgresql.org/download/windows/
2. Click "Download the installer"
3. Choose version **15.x** (latest stable) or **14.x**
4. Download the Windows x86-64 installer (64-bit)

**File size:** ~150 MB  
**Download time:** 2-5 minutes

---

## Step 2: Run the Installer

1. Find the downloaded file (e.g., `postgresql-15.3-1-windows-x64.exe`)
2. Double-click to run
3. Click "Next" to begin setup

### Choose Installation Directory
- **Default:** `C:\Program Files\PostgreSQL\15`
- **Custom:** Any location you prefer
- Click "Next"

### Select Components
✅ **PostgreSQL Server** (keep checked)  
✅ **pgAdmin 4** (keep checked - visual database manager)  
✅ **Stack Builder** (optional - for additional tools)  
✅ **Command Line Tools** (keep checked)

Click "Next"

### Data Directory
- **Default:** `C:\Program Files\PostgreSQL\15\data`
- Keep this unless you have a specific reason to change it
- Click "Next"

---

## Step 3: Set Superuser Password ⚠️ IMPORTANT

You'll be asked to set a password for the `postgres` superuser account.

**Create a password and REMEMBER IT** - you'll need it later!

```
Example password: MySecurePassword123
```

**Tips:**
- Use something you can remember
- Mix uppercase, lowercase, numbers
- Don't use special characters in password
- Write it down somewhere safe (just for now)

Click "Next"

### Port Configuration
- **Default port:** 5432 (keep this)
- Make sure this port isn't used by another application
- Click "Next"

### Locale
- **Default:** English, United States
- Click "Next"

---

## Step 4: Ready to Install

Review your choices:
```
Installation Directory: C:\Program Files\PostgreSQL\15
Database Port: 5432
Locale: English, United States
```

If everything looks good, click "Next" to begin installation.

**Installation time:** 2-3 minutes

---

## Step 5: Stack Builder (Optional)

After installation completes, you may see "Stack Builder" dialog.

**For now, just close it** - we don't need additional tools yet.

Click "Finish"

---

## Step 6: Verify Installation

### Check PostgreSQL is Running

1. Open **Services** (Windows):
   - Press `Win + R`
   - Type: `services.msc`
   - Press Enter

2. Look for **postgresql-x64-15** in the list
3. It should show **Running** status
4. If not running, right-click and select "Start"

### Alternative: Check via Command Line

1. Open **Command Prompt** (cmd.exe)
2. Type:
   ```bash
   psql --version
   ```
3. You should see:
   ```
   psql (PostgreSQL) 15.x
   ```

If you get "psql: command not found", add PostgreSQL to PATH:
- See **Troubleshooting** section below

---

## Step 7: Create Your Travel Agency Database

### Using Command Line (Recommended)

1. Open **Command Prompt**

2. Connect to PostgreSQL:
   ```bash
   psql -U postgres
   ```

3. When prompted, enter the password you set earlier

4. You should see the PostgreSQL prompt:
   ```
   postgres=#
   ```

5. Create the database:
   ```sql
   CREATE DATABASE travel_agency;
   ```

6. Verify it was created:
   ```sql
   \l
   ```

   You should see:
   ```
    Name          │ Owner
   ────────────────┼──────────
    travel_agency  │ postgres
   ```

7. Exit PostgreSQL:
   ```sql
   \q
   ```

### Using pgAdmin (Visual Method)

1. Open **pgAdmin 4** (should have been installed)
   - Look for it in Start Menu or desktop
   - Default login: `postgres` / your password

2. Right-click **Databases** → **Create** → **Database**

3. Fill in:
   - **Name:** `travel_agency`
   - **Owner:** `postgres`

4. Click **Create**

---

## Step 8: Test Connection

### Test via Command Line

```bash
psql -U postgres -d travel_agency
```

Expected output:
```
psql (15.3)
Type "help" for help.

travel_agency=#
```

If you see this, PostgreSQL is working! ✅

Type `\q` to exit.

### Troubleshooting Connection

**Error: "psql: command not found"**

PostgreSQL isn't in your system PATH. Add it:

1. Press `Win + X`, select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "System variables", click "New"
5. Variable name: `PATH`
6. Variable value: `C:\Program Files\PostgreSQL\15\bin`
7. Click OK → Apply → Restart Command Prompt

Then try again: `psql --version`

**Error: "password authentication failed"**

- You entered the wrong password
- Use `ALTER USER postgres PASSWORD 'newpassword';` in pgAdmin to reset it

---

## Step 9: Update Your .env File

Create or edit `.env` file in your travel_agency project:

```bash
DATABASE_URL=postgresql://postgres:MySecurePassword123@localhost:5432/travel_agency
```

Replace `MySecurePassword123` with the password you set!

**Important:**
- Never commit `.env` to GitHub (it has your password)
- Add to `.gitignore`: `.env`

---

## Step 10: Test Connection from Python

Create a test file `test_db.py`:

```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

db_url = os.getenv('DATABASE_URL')
print(f"Testing connection to: {db_url}")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute("SELECT version()")
        print(f"✅ Success! PostgreSQL version: {result.fetchone()[0]}")
except Exception as e:
    print(f"❌ Error: {e}")
```

Run it:
```bash
python test_db.py
```

Expected output:
```
Testing connection to: postgresql://postgres:...@localhost:5432/travel_agency
✅ Success! PostgreSQL version: PostgreSQL 15.3 ...
```

---

## Step 11: Migrate Your Data

Now that PostgreSQL is set up and database exists:

```bash
# Install dependencies
pip install -r requirements.txt

# Migrate your data from SQLite
python scripts/migrate_sqlite_to_postgres.py
```

This will:
- ✅ Copy all your data from SQLite to PostgreSQL
- ✅ Keep SQLite untouched (safe!)
- ✅ Verify everything worked

---

## PostgreSQL Quick Commands

**Connect as superuser:**
```bash
psql -U postgres
```

**Connect to specific database:**
```bash
psql -U postgres -d travel_agency
```

**List all databases:**
```sql
\l
```

**Switch to a database:**
```sql
\c travel_agency
```

**List all tables:**
```sql
\dt
```

**Show table structure:**
```sql
\d users
```

**Count rows:**
```sql
SELECT COUNT(*) FROM users;
```

**Exit PostgreSQL:**
```sql
\q
```

---

## Troubleshooting

### "Port 5432 already in use"
Another application is using that port. Check Task Manager or:
```bash
netstat -ano | findstr :5432
```

Then either:
- Stop the other application
- Use a different port (change in PostgreSQL setup)

### "PostgreSQL service won't start"
1. Check Services (services.msc)
2. Right-click postgresql-x64-15 → Properties
3. Make sure "Startup type" is set to "Automatic"
4. Click Start

### "psql command not found"
1. Add PostgreSQL `bin` folder to PATH (see Step 8)
2. Restart Command Prompt
3. Test: `psql --version`

### "Connection refused"
1. Check if PostgreSQL is running: `services.msc`
2. Check if port 5432 is correct in `.env`
3. Check firewall isn't blocking port 5432

### "password authentication failed"
1. Open pgAdmin
2. Right-click `postgres` user → Properties
3. Set new password
4. Update `.env` with new password

### "Database 'travel_agency' doesn't exist"
Create it:
```bash
psql -U postgres
# Then in PostgreSQL prompt:
CREATE DATABASE travel_agency;
\q
```

---

## Verify Complete Setup

Run this checklist:

```
✅ PostgreSQL installed (psql --version)
✅ Service running (services.msc)
✅ Database created (psql -l)
✅ .env file updated
✅ pip packages installed
✅ Test connection works
✅ Data migrated
```

When all are checked, you're ready! 🚀

---

## Next Steps

1. ✅ Install PostgreSQL (this guide)
2. ✅ Create database
3. ✅ Update `.env`
4. ⏭️ Migrate data: `python scripts/migrate_sqlite_to_postgres.py`
5. ⏭️ Test: `python scripts/test_postgres_connection.py`
6. ⏭️ Run Flask: `flask run`

---

## Need Help?

### Visual: Use pgAdmin
- Open pgAdmin 4 (should be in Start Menu)
- Browse databases, tables, data visually
- No command line needed

### Command Line: Use psql
- Open Command Prompt
- Run: `psql -U postgres -d travel_agency`
- Execute SQL queries directly

### Testing: Run test scripts
```bash
python scripts/test_postgres_connection.py
```

---

## That's It! 🎉

You now have:
- ✅ PostgreSQL installed
- ✅ Database created
- ✅ Connection configured
- ✅ Ready to migrate data

**Next: Follow [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) to migrate your data!**
