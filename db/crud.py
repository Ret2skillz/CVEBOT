import sqlite3
from db.setup import DB_PATH

def save_cve(discord_username, cve_id, description, url, tag, type_vuln):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO saved_cves (discord_username, cve_id, description, url, tag, type_vuln) VALUES (?, ?, ?, ?, ?, ?)",
        (discord_username, cve_id, description, url, tag, type_vuln)
    )
    conn.commit()
    conn.close()

def search_cve(discord_username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cve_id, description, url, tag, type_vuln FROM saved_cves WHERE discord_username = ?",
        (discord_username,)
    )
    cves_user = cursor.fetchall()
    conn.close()
    return cves_user

def search_by_tag(discord_username, tag):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cve_id, description, url, type_vuln FROM saved_cves WHERE discord_username = ? AND tag = ?",
        (discord_username, tag)
    )
    cves_tag = cursor.fetchall()
    conn.close()
    return cves_tag

def search_by_type(discord_username, type_vuln):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cve_id, description, url, tag FROM saved_cves WHERE discord_username = ? AND type_vuln = ?",
        (discord_username, type_vuln)
    )
    cves_type = cursor.fetchall()
    conn.close()
    return cves_type

def delete_cve(discord_username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM saved_cves WHERE discord_username = ?",
        (discord_username,)
    )
    conn.commit()
    conn.close()

