from __future__ import annotations
from pathlib import Path
from typing import Optional
import os
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_dev_yaml() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    yaml_path = root / "Resources" / "dev.yaml"
    if not yaml_path.exists():
        return {}
    content = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    return {str(k).strip().upper().replace("-", "_"): str(v) for k, v in content.items()}


# Nạp Resources/dev.yaml vào env trước khi Settings() khởi tạo (chỉ set nếu chưa có
# trong môi trường, để .env / biến hệ thống luôn được ưu tiên hơn)
for _k, _v in _load_dev_yaml().items():
    os.environ.setdefault(_k, _v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENV: str = "development"
    BACKEND_BASE_URL: str
    CHATBOT_TOKEN_URL: Optional[str] = None
    CHATBOT_CLIENT_ID: Optional[str] = None
    CHATBOT_CLIENT_SECRET: Optional[str] = None
    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    STAFF_SYNC_INTERVAL_SECONDS: int = 300


def get_settings() -> Settings:
    return Settings()