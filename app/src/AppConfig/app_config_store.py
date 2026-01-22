import os
import threading

import yaml

APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(APP_ROOT, "config", "AppConfig.Yaml")


class AppConfigStore:
    _lock = threading.Lock()
    _data = None
    _mtime = None
    _version = 0

    @classmethod
    def _load(cls):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        cls._data = data
        cls._mtime = os.path.getmtime(CONFIG_PATH)
        cls._version += 1
        return data

    @classmethod
    def get(cls):
        with cls._lock:
            if cls._data is None:
                return cls._load()
            try:
                mtime = os.path.getmtime(CONFIG_PATH)
            except FileNotFoundError:
                return cls._data
            if cls._mtime != mtime:
                return cls._load()
            return cls._data

    @classmethod
    def save(cls, data):
        with cls._lock:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    data,
                    f,
                    sort_keys=False,
                    allow_unicode=True,
                    default_flow_style=False,
                )
            cls._data = data
            cls._mtime = os.path.getmtime(CONFIG_PATH)
            cls._version += 1

    @classmethod
    def version(cls):
        return cls._version
