import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import urllib.parse

print("--- DIAGNOSTIC START ---")

# 1. Inspect .env
load_dotenv()
url = os.getenv("DATABASE_URL")
if url:
    print(f"DATABASE_URL found in env: {url}")
else:
    print("DATABASE_URL NOT found in env.")

# 2. Test SQLAlchemy Connection
if url:
    print("\nAttempting SQLAlchemy connection...")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            print(">> SUCCESS: SQLAlchemy connected using .env URL.")
    except Exception as e:
        print(f">> FAILED: SQLAlchemy connection error: {e}")

# 3. Test Direct Psycopg2 with likely passwords
print("\nAttempting direct psycopg2 connections...")
try:
    import psycopg2
    
    # Test 1: README password
    try:
        conn = psycopg2.connect(
            dbname="MediMind",
            user="auth_user",
            password="Medimind@123",
            host="localhost",
            port="5432"
        )
        print(">> SUCCESS: Connected with password 'Medimind@123'")
        conn.close()
    except Exception as e:
        print(f">> FAILED: Could not connect with 'Medimind@123'. Error: {e}")

    # Test 2: Simple password (from logs)
    try:
        conn = psycopg2.connect(
            dbname="MediMind",
            user="auth_user",
            password="MediMind",
            host="localhost",
            port="5432"
        )
        print(">> SUCCESS: Connected with password 'MediMind'")
        conn.close()
    except Exception as e:
        print(f">> FAILED: Could not connect with 'MediMind'. Error: {e}")

except ImportError:
    print("psycopg2 NOT installed, skipping direct tests.")

print("--- DIAGNOSTIC END ---")
