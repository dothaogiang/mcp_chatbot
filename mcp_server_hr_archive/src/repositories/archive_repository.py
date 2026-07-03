from __future__ import annotations
from typing import Any, Dict, Optional
from clients.archive_backend_client import ArchiveBackendClient
from common_utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class ArchiveRepository:
    def __init__(self, client: ArchiveBackendClient) -> None:
        self.client = client

    async def search(
        self,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        language: Optional[str] = None,
        maintenance: Optional[str] = None,
        created_from: Optional[str] = None,
        created_to: Optional[str] = None,
        updated_from: Optional[str] = None,
        updated_to: Optional[str] = None,
        page: int = DEFAULT_PAGE,
        size: int = DEFAULT_PAGE_SIZE,
    ) -> Dict[str, Any]:
        params = {
            "keyword": keyword,
            "status": status,
            "warehouseId": warehouse_id,
            "language": language,
            "maintenance": maintenance,
            "createdFrom": created_from,
            "createdTo": created_to,
            "updatedFrom": updated_from,
            "updatedTo": updated_to,
            "page": page,
            "size": min(size, MAX_PAGE_SIZE),
        }
        params = {k: v for k, v in params.items() if v is not None}
        return await self.client.search_archives(params)

    async def get_by_id(self, archive_id: str) -> Dict[str, Any]:
        return await self.client.get_archive_detail(archive_id)