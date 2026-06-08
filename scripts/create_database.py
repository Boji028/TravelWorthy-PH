#!/usr/bin/env python3
"""Create travel_agency database"""
import psycopg2
from psycopg2 import sql

try:
    # Connect to default postgres database
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Enzo123",
        database="postgres"
    )
    
    # Create database
    conn.autocommit = True
    cursor = conn.cursor()
    
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(
        sql.Identifier("travel_agency")
    ))
    
    cursor.close()
    conn.close()
    print("✅ Database 'travel_agency' created successfully!")
    
except psycopg2.Error as e:
    # Database might already exist, which is fine
    if "already exists" in str(e):
        print("✅ Database 'travel_agency' already exists!")
    else:
        print(f"❌ Error: {e}")
        exit(1)

