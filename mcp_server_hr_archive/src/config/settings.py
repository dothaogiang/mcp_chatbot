from __future__ import annotations
from pathlib import Path
from typing import Optional
import os

import yaml


def _load_dev_yaml() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    yaml_path = root / "Resources" / "dev.yaml"
    if not yaml_path.exists():
        return {}

    try:
        content = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

    env_values: dict[str, str] = {}
    for key, value in content.items():
        if not isinstance(key, str):
            continue
        env_key = key.strip().upper().replace("-", "_")
        env_values[env_key] = str(value)
    return env_values


# pydantic v2.13 removed BaseSettings into pydantic-settings. Provide a lightweight
# fallback Settings implementation so tests/imports work in diverse environments.
try:
    from pydantic import BaseSettings, Field, AnyHttpUrl


    class Settings(BaseSettings):
        ENV: str = Field("development", env="ENV")
        BACKEND_BASE_URL: AnyHttpUrl = Field(..., env="BACKEND_BASE_URL")
        CHATBOT_TOKEN_URL: Optional[AnyHttpUrl] = Field(None, env="CHATBOT_TOKEN_URL")
        CHATBOT_CLIENT_ID: Optional[str] = Field(None, env="CHATBOT_CLIENT_ID")
        CHATBOT_CLIENT_SECRET: Optional[str] = Field(None, env="CHATBOT_CLIENT_SECRET")
        QDRANT_URL: str = Field(..., env="QDRANT_URL")
        QDRANT_API_KEY: Optional[str] = Field(None, env="QDRANT_API_KEY")
        EMBEDDING_MODEL: str = Field("bge-m3-small", env="EMBEDDING_MODEL")

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"


    def get_settings() -> Settings:
        for key, value in _load_dev_yaml().items():
            if os.getenv(key) is None:
                os.environ[key] = value
        return Settings()
except Exception:
    # Minimal fallback Settings class
    class Settings:
        def __init__(self, **overrides) -> None:
            self.ENV = overrides.get("ENV", os.getenv("ENV", "development"))
            self.BACKEND_BASE_URL = overrides.get("BACKEND_BASE_URL", os.getenv("BACKEND_BASE_URL", "http://localhost:4000"))
            self.CHATBOT_TOKEN_URL = overrides.get("CHATBOT_TOKEN_URL", os.getenv("CHATBOT_TOKEN_URL"))
            self.CHATBOT_CLIENT_ID = overrides.get("CHATBOT_CLIENT_ID", os.getenv("CHATBOT_CLIENT_ID"))
            self.CHATBOT_CLIENT_SECRET = overrides.get("CHATBOT_CLIENT_SECRET", os.getenv("CHATBOT_CLIENT_SECRET"))
            self.QDRANT_URL = overrides.get("QDRANT_URL", os.getenv("QDRANT_URL", "http://localhost:6333"))
            self.QDRANT_API_KEY = overrides.get("QDRANT_API_KEY", os.getenv("QDRANT_API_KEY"))
            self.EMBEDDING_MODEL = overrides.get("EMBEDDING_MODEL", os.getenv("EMBEDDING_MODEL", "bge-m3-small"))


    def get_settings() -> Settings:
        for key, value in _load_dev_yaml().items():
            if os.getenv(key) is None:
                os.environ[key] = value
        return Settings()
