from __future__ import annotations
from typing import Any, Dict
from repositories.archive_repository import ArchiveRepository


class ArchiveService:
    def __init__(self, repo: ArchiveRepository) -> None:
        self.repo = repo

    async def search_archives(self, q: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        return await self.repo.search(q, page, per_page)

    async def get_archive(self, archive_id: str) -> Dict[str, Any]:
        return await self.repo.get_by_id(archive_id)
