import asyncio
import sys
import os

# ensure project src is importable when tests run from nested package

# ensure project root and src dir are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from src.clients.archive_backend_client import ArchiveBackendClient
from src.config.settings import Settings


def test_client_init(monkeypatch):
    settings = Settings(BACKEND_BASE_URL="http://example.local", QDRANT_URL="http://q")
    client = ArchiveBackendClient(settings)
    asyncio.run(client.close())
