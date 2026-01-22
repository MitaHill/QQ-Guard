import os
import re
from typing import Optional

from src.AiCore.ai_utils import strip_think_tags
from src.AiCore.conversation_history_store import ConversationHistoryStore
from src.AiCore.prompt_loader import load_prompt
from src.AppConfig.app_config_store import APP_ROOT


class BaseAiClient:
    def __init__(self, info2ai_config):
        self.max_history = int(info2ai_config.get("max_history", 30))
        self.request_timeout = int(info2ai_config.get("request_timeout_seconds", 600))

        self.prompt_dir_env = info2ai_config.get("prompt_dir_env", "INFO2AI_PROMPT_DIR")
        self.prompt_file_env = info2ai_config.get("prompt_file_env", "INFO2AI_PROMPT_FILE")
        self.prompt_dir = os.getenv(self.prompt_dir_env)
        self.prompt_file = os.getenv(self.prompt_file_env)

        if not self.prompt_dir:
            print(f"❌ 未设置环境变量 {self.prompt_dir_env}")
        if not self.prompt_file:
            print(f"❌ 未设置环境变量 {self.prompt_file_env}")

        self.full_prompt = ""
        db_path = os.path.join(APP_ROOT, "db", "all.db")
        self.history_store = ConversationHistoryStore(db_path)
        self.history = []

    def load_knowledge_base(self):
        self.full_prompt = load_prompt(self.prompt_dir, self.prompt_file)

    def load_history(self):
        self.history = self.history_store.fetch_history(self.max_history)

    def build_messages(self, message: str):
        messages = [{"role": "system", "content": self.full_prompt}]
        for msg in self.history[-10:]:
            if isinstance(msg, dict) and "user" in msg and "assistant" in msg:
                messages.append({"role": "user", "content": msg["user"]})
                messages.append({"role": "assistant", "content": msg["assistant"]})
        messages.append({"role": "user", "content": message})
        return messages

    def add_history(self, message: str, ai_response: str):
        self.history_store.add_turn(message, ai_response, self.max_history)
        self.history = self.history_store.fetch_history(self.max_history)

    def chat(self, message: str) -> Optional[str]:
        raise NotImplementedError

    def judge(self, content: str) -> bool:
        response = self.chat(content)
        if not response:
            return False

        cleaned = strip_think_tags(response)
        match = re.search(r"```\s*(true|false)\s*```", cleaned, re.IGNORECASE)
        return match.group(1).lower() == "true" if match else False
