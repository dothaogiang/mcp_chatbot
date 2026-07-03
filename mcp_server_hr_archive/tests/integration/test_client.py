import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from src.clients.archive_backend_client import ArchiveBackendClient
from src.config.settings import Settings


def test_client_init():
    settings = Settings(BACKEND_BASE_URL="http://example.local", QDRANT_URL="http://q")
    client = ArchiveBackendClient(settings)
    asyncio.run(client.aclose())  # đúng tên method thật là aclose(), không phải close()