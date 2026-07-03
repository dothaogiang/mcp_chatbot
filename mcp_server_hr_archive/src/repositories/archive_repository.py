from __future__ import annotations
from typing import Any, Dict, List, Optional
from clients.archive_backend_client import ArchiveBackendClient


class ArchiveRepository:
    def __init__(self, client: ArchiveBackendClient) -> None:
        self.client = client

    async def search(self, query: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        params = {"q": query, "page": page, "per_page": per_page}
        return await self.client.search_archives(params)

    async def get_by_id(self, archive_id: str) -> Dict[str, Any]:
        return await self.client.get_archive_detail(archive_id)
