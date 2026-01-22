import os
import sqlite3
import threading

from src.AppConfig.app_config_store import APP_ROOT


class ChatHistoryStore:
    def __init__(self, db_path=None, table_name="chat_messages"):
        self.db_path = db_path or os.path.join(APP_ROOT, "db", "all.db")
        self.table_name = table_name
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    message_id TEXT,
                    message TEXT,
                    raw_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_group_created "
                f"ON {self.table_name}(group_id, created_at)"
            )

    def add_message(self, group_id, user_id, username, message_id, message, raw_message):
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"""
                INSERT INTO {self.table_name}
                (group_id, user_id, username, message_id, message, raw_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(group_id),
                    str(user_id),
                    username or "",
                    str(message_id) if message_id is not None else None,
                    message or "",
                    raw_message or "",
                ),
            )
            conn.commit()

    def list_groups(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                f"SELECT DISTINCT group_id FROM {self.table_name} ORDER BY group_id"
            ).fetchall()
        return [row[0] for row in rows]

    def fetch_group_messages(self, group_id, limit=100, offset=0):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"""
                SELECT id, group_id, user_id, username, message_id, message, raw_message, created_at
                FROM {self.table_name}
                WHERE group_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (str(group_id), int(limit), int(offset)),
            ).fetchall()
        return [dict(row) for row in rows]
