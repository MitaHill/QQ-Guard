from typing import Optional

import os
import requests

from src.AiCore.ai_utils import strip_think_tags, to_bool
from src.AiCore.base_ai_client import BaseAiClient


class OllamaClient(BaseAiClient):
    def __init__(self, info2ai_config):
        super().__init__(info2ai_config)
        ollama_config = info2ai_config.get("ollama", {}) or {}
        self.base_url = ollama_config.get("base_url", "http://127.0.0.1:11434")
        self.model = ollama_config.get("model_name", "qwen2.5")
        self.thinking_enabled = to_bool(
            os.getenv("QQ_GUARD_OLLAMA_THINKING"),
            ollama_config.get("thinking_enabled", False),
        )

    def _chat_url(self):
        base = self.base_url.rstrip("/")
        if base.endswith("/api"):
            return f"{base}/chat"
        return f"{base}/api/chat"

    def chat(self, message: str) -> Optional[str]:
        payload = {
            "model": self.model,
            "messages": self.build_messages(message),
            "stream": False,
            "think": self.thinking_enabled,
        }

        try:
            response = requests.post(
                self._chat_url(),
                json=payload,
                timeout=self.request_timeout,
            )
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("message", {}).get("content", "").strip()
                if ai_response:
                    cleaned = strip_think_tags(ai_response)
                    self.add_history(message, cleaned)
                    return ai_response if self.thinking_enabled else cleaned
                return None
            print(f"Ollama API 错误: {response.status_code} - {response.text}")
        except Exception as exc:
            print(f"Ollama 请求错误: {exc}")

        return None
