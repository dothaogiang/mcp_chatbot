from __future__ import annotations
from typing import Any, Dict, Optional
from clients.archive_backend_client import ArchiveBackendClient
from services.archive_service import ArchiveService


class FileService:
    def __init__(self, client: ArchiveBackendClient) -> None:
        self.client = client

    async def get_file_info(self, key: str) -> Dict[str, Any]:
        return await self.client.get_file_metadata(key)

    async def resolve_key_from_archive(
        self, archive_service: ArchiveService, archive_id: str, file_index: int = 0,
    ) -> Optional[str]:
        archive = await archive_service.get_archive(archive_id)
        if not archive:
            return None
        for project in archive.get("projects") or []:
            file_urls = project.get("fileUrls") or []
            if file_urls and file_index < len(file_urls):
                return self.client.extract_key_from_url(file_urls[file_index])
        return None