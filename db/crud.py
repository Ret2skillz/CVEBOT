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

def delete_cve(discord_username, cve_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM saved_cves WHERE discord_username = ? AND cve_id = ?",
        (discord_username, cve_id)
    )
    conn.commit()
    conn.close()

def save_audit_repo(discord_username, repo_name, repo_url, repo_desc, stars, language):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT OR IGNORE INTO saved_audit_repos 
               (discord_username, repo_name, repo_url, repo_desc, stars, language) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (discord_username, repo_name, repo_url, repo_desc, stars, language)
        )
        conn.commit()
    except Exception as e:
        print(f"Error saving audit repo: {e}")
    finally:
        conn.close()

def get_saved_audit_repos(discord_username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT repo_name, repo_url, repo_desc, stars, language 
           FROM saved_audit_repos 
           WHERE discord_username = ? 
           ORDER BY saved_at DESC""",
        (discord_username,)
    )
    repos = []
    for row in cursor.fetchall():
        repos.append({
            "name": row[0],
            "url": row[1],
            "description": row[2],
            "stars": row[3],
            "language": row[4]
        })
    conn.close()
    return repos

def delete_audit_repo(discord_username, repo_url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM saved_audit_repos WHERE discord_username = ? AND repo_url = ?",
        (discord_username, repo_url)
    )
    conn.commit()
    conn.close()

