#!/usr/bin/env python
"""Reset admin account password."""

import psycopg2
from werkzeug.security import generate_password_hash

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="travel_agency_db",
    user="postgres",
    password="Enzo123"
)
cursor = conn.cursor()

# New admin password
new_password = "Admin12345"
password_hash = generate_password_hash(new_password)

# Update admin account
cursor.execute(
    "UPDATE users SET password = %s WHERE email = %s",
    (password_hash, "admin@travelworthyph.com")
)
conn.commit()

print("=" * 70)
print("✓ ADMIN PASSWORD RESET")
print("=" * 70)
print(f"Email:    admin@travelworthyph.com")
print(f"Password: {new_password}")
print("=" * 70)
print("\nUse these credentials to log in to your admin account!")

cursor.close()
conn.close()
