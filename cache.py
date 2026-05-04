import sqlite3
import json

class SQLiteCache:
    def __init__(self, db_path="cache.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

    def get(self, key):
        cur = self.conn.execute("SELECT value FROM cache WHERE key=?", (key,))
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def set(self, key, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
            (key, json.dumps(value))
        )
        self.conn.commit()