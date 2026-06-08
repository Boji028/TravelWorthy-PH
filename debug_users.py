#!/usr/bin/env python
"""Debug script to check user accounts in database."""

import psycopg2
from werkzeug.security import check_password_hash

# Direct database connection
conn = psycopg2.connect(
    host="localhost",
    database="travel_agency_db",
    user="postgres",
    password="Enzo123"
)
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT id, email, name, is_admin, email_verified, password FROM users ORDER BY created_at DESC")
users = cursor.fetchall()

print("\n" + "=" * 80)
print("REGISTERED USERS IN DATABASE")
print("=" * 80)

for user_id, email, name, is_admin, verified, password_hash in users:
    print(f"\nID: {user_id}")
    print(f"Email: {email}")
    print(f"Name: {name}")
    print(f"Admin: {is_admin}")
    print(f"Verified: {verified}")
    print(f"Password Hash: {password_hash[:40]}...")

# Test password verification for each account
print("\n" + "=" * 80)
print("PASSWORD VERIFICATION TEST")
print("=" * 80)

test_passwords = {
    "ragingsanford1@gmail.com": "TestPass123",
    "claude5.afk@gmail.com": "Claude5Pass123",
    "claude6.afk@gmail.com": "Claude6Pass123"
}

for email, test_pwd in test_passwords.items():
    cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    if result:
        hash_stored = result[0]
        matches = check_password_hash(hash_stored, test_pwd)
        print(f"\n{email} with password '{test_pwd}': {matches}")
    else:
        print(f"\n{email}: NOT FOUND IN DATABASE")

cursor.close()
conn.close()

print("\n" + "=" * 80)
