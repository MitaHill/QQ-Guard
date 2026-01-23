import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from src.AppConfig.app_config_store import APP_ROOT


class ConversationHistoryStore:
    def __init__(self, db_path: str, table_name: str = "conversation_history"):
        self.db_path = db_path
        self.table_name = table_name
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_content TEXT NOT NULL,
                    assistant_content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created "
                f"ON {self.table_name}(created_at)"
            )

    def fetch_history(self, limit: int):
        if limit <= 0:
            return []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute(
                f"SELECT COUNT(*) FROM {self.table_name}"
            ).fetchone()[0]
            if total == 0:
                return []
            if total <= limit:
                rows = conn.execute(
                    f"SELECT user_content, assistant_content "
                    f"FROM {self.table_name} ORDER BY id ASC"
                ).fetchall()
                return [{"user": r["user_content"], "assistant": r["assistant_content"]} for r in rows]

            first_row = conn.execute(
                f"SELECT id, user_content, assistant_content "
                f"FROM {self.table_name} ORDER BY id ASC LIMIT 1"
            ).fetchone()
            recent_rows = conn.execute(
                f"SELECT id, user_content, assistant_content "
                f"FROM {self.table_name} ORDER BY id DESC LIMIT ?",
                (limit - 1,),
            ).fetchall()
            recent_rows = list(reversed(recent_rows))

        history = []
        if first_row:
            history.append({"user": first_row["user_content"], "assistant": first_row["assistant_content"]})
        history.extend(
            {"user": r["user_content"], "assistant": r["assistant_content"]} for r in recent_rows
        )
        return history

    def add_turn(self, user_content: str, assistant_content: str, max_history: int):
        created_at = _now_shanghai()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"""
                INSERT INTO {self.table_name} (user_content, assistant_content, created_at)
                VALUES (?, ?, ?)
                """,
                (user_content, assistant_content, created_at),
            )
            conn.commit()
        self.trim_history(max_history)

    def trim_history(self, max_history: int):
        if max_history <= 0:
            return
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM {self.table_name}"
            ).fetchone()[0]
            if total <= max_history:
                return

            first_row = conn.execute(
                f"SELECT id FROM {self.table_name} ORDER BY id ASC LIMIT 1"
            ).fetchone()
            if not first_row:
                return

            keep_ids = [first_row[0]]
            if max_history > 1:
                recent_rows = conn.execute(
                    f"SELECT id FROM {self.table_name} ORDER BY id DESC LIMIT ?",
                    (max_history - 1,),
                ).fetchall()
                keep_ids.extend(row[0] for row in recent_rows)

            placeholders = ",".join("?" for _ in keep_ids)
            conn.execute(
                f"DELETE FROM {self.table_name} WHERE id NOT IN ({placeholders})",
                keep_ids,
            )
            conn.commit()


def _now_shanghai():
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
