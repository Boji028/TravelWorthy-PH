#!/usr/bin/env python
"""Delete corrupted accounts and show remaining users."""

import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="travel_agency_db",
    user="postgres",
    password="Enzo123"
)
cursor = conn.cursor()

# Delete the problematic accounts
print("Deleting corrupted account records...")
cursor.execute("DELETE FROM users WHERE email IN ('claude5.afk@gmail.com', 'claude6.afk@gmail.com')")
conn.commit()
print(f"✓ Deleted {cursor.rowcount} accounts")

# Show remaining users
cursor.execute("SELECT id, email, name FROM users ORDER BY id")
users = cursor.fetchall()

print("\n" + "="*60)
print("REMAINING USERS:")
print("="*60)
for uid, email, name in users:
    print(f"  ID {uid}: {email:40} ({name})")

cursor.close()
conn.close()
