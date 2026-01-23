import os
import sqlite3
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from src.AppConfig.app_config_store import APP_ROOT, AppConfigStore


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
        created_at = _now_shanghai()
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"""
                INSERT INTO {self.table_name}
                (group_id, user_id, username, message_id, message, raw_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(group_id),
                    str(user_id),
                    username or "",
                    str(message_id) if message_id is not None else None,
                    message or "",
                    raw_message or "",
                    created_at,
                ),
            )
            max_messages = _get_group_message_limit()
            if max_messages > 0:
                conn.execute(
                    f"""
                    DELETE FROM {self.table_name}
                    WHERE id IN (
                        SELECT id FROM {self.table_name}
                        WHERE group_id = ?
                        ORDER BY id DESC
                        LIMIT -1 OFFSET ?
                    )
                    """,
                    (str(group_id), int(max_messages)),
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

    def fetch_group_messages_for_export(self, group_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"""
                SELECT id, group_id, user_id, username, message_id, message, raw_message, created_at
                FROM {self.table_name}
                WHERE group_id = ?
                ORDER BY id ASC
                """,
                (str(group_id),),
            ).fetchall()
        return [dict(row) for row in rows]

    def fetch_all_messages_grouped(self):
        grouped = {}
        for group_id in self.list_groups():
            grouped[str(group_id)] = self.fetch_group_messages_for_export(group_id)
        return grouped


def _now_shanghai():
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")


def _get_group_message_limit():
    try:
        config = AppConfigStore.get()
        limit = config.get("app", {}).get("chat_history", {}).get("max_group_messages", 5000)
        return int(limit)
    except Exception:
        return 5000
