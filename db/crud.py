import sqlite3
from setup import DB_PATH

def save_cve(discord_username, cve_id, description, url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO saved_cves (discord_username, cve_id, description, url) VALUES (?, ?, ?, ?)",
        (discord_username, cve_id, description, url)
    )
    conn.commit()
    conn.close()