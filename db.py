"""
db.py — Neon Postgres connection and schema initialisation.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Create tables if they don't already exist."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS society_members (
            id          SERIAL PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,          -- bcrypt hash
            joined_at   TIMESTAMPTZ DEFAULT NOW(),
            is_institute_member BOOLEAN DEFAULT FALSE,
            is_app_subscriber BOOLEAN DEFAULT FALSE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_manifestations (
            email TEXT NOT NULL,
            date TEXT NOT NULL,
            gratitude_1 TEXT,
            gratitude_2 TEXT,
            gratitude_3 TEXT,
            gratitude_done BOOLEAN DEFAULT FALSE,
            morning_vis TEXT,
            vis_done BOOLEAN DEFAULT FALSE,
            inspired_action TEXT,
            action_taken BOOLEAN DEFAULT FALSE,
            evening_vis TEXT,
            evening_done BOOLEAN DEFAULT FALSE,
            encouragement_received BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (email, date)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_encouragements (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL
        );
    """)
    conn.commit()

    # Handle schema migrations for society_members
    try:
        cur.execute("ALTER TABLE society_members ADD COLUMN is_institute_member BOOLEAN DEFAULT FALSE")
        conn.commit()
    except Exception:
        conn.rollback()

    try:
        cur.execute("ALTER TABLE society_members ADD COLUMN is_app_subscriber BOOLEAN DEFAULT FALSE")
        conn.commit()
    except Exception:
        conn.rollback()

    cur.close()
    conn.close()
    print("DB initialised.")
