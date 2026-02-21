import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "cves.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_cves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_username TEXT NOT NULL,
        cve_id TEXT NOT NULL,
        description TEXT,
        url TEXT,
        tag TEXT,
        type_vuln TEXT
    )
    """)
    conn.commit()
    conn.close()
