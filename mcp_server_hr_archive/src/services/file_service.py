from __future__ import annotations
from typing import Any
from clients.archive_backend_client import ArchiveBackendClient


class FileService:
    def __init__(self, client: ArchiveBackendClient) -> None:
        self.client = client

    async def get_file_bytes(self, key: str) -> bytes:
        return await self.client.get_file_proxy(key)
