import sqlite3
from db.setup import DB_PATH

def save_cve(discord_username, cve_id, description, url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO saved_cves (discord_username, cve_id, description, url) VALUES (?, ?, ?, ?)",
        (discord_username, cve_id, description, url)
    )
    conn.commit()
    conn.close()

def search_cve(discord_username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cve_id, description, url FROM saved_cves WHERE discord_username = ?",
        (discord_username,)
    )
    cves_user = cursor.fetchall()
    conn.close()
    return cves_user