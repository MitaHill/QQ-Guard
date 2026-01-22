import os
from typing import Optional

import requests

from src.AiCore.base_ai_client import BaseAiClient


class OpenAiClient(BaseAiClient):
    def __init__(self, info2ai_config):
        super().__init__(info2ai_config)
        openai_config = info2ai_config.get("openai", {}) or {}

        self.base_url = openai_config.get("api_base_url", "https://api.openai.com/v1")
        self.model = openai_config.get("model_name", "gpt-4o-mini")
        self.api_key_env = openai_config.get("api_key_env", "OPENAI_API_KEY")

        self.api_key = os.getenv(self.api_key_env) or os.getenv("INFO2AI_API_KEY", "")
        if not self.api_key:
            print(f"❌ 未设置环境变量 {self.api_key_env}")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, message: str) -> Optional[str]:
        if not self.api_key:
            return None

        payload = {
            "model": self.model,
            "messages": self.build_messages(message),
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False,
        }

        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=self.request_timeout,
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if ai_response:
                    self.add_history(message, ai_response)
                    return ai_response
                return None
            print(f"OpenAI API 错误: {response.status_code} - {response.text}")
        except Exception as exc:
            print(f"请求错误: {exc}")

        return None
