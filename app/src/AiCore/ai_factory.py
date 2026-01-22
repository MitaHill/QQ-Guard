import os

from src.AiCore.ollama_client import OllamaClient
from src.AiCore.openai_client import OpenAiClient
from src.AppConfig.app_config_store import AppConfigStore


def create_ai_client():
    config = AppConfigStore.get()
    info2ai_config = config.get("info2ai", {}) or {}
    provider = os.getenv("QQ_GUARD_AI_PROVIDER") or info2ai_config.get("provider", "openai")
    provider = str(provider).strip().lower()

    if provider == "ollama":
        return OllamaClient(info2ai_config)
    return OpenAiClient(info2ai_config)
