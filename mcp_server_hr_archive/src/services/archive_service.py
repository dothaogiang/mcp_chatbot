from __future__ import annotations
from typing import Any, Dict, Optional
from repositories.archive_repository import ArchiveRepository
from common_utils.exceptions import NotFoundError


class ArchiveService:
    def __init__(self, repo: ArchiveRepository) -> None:
        self.repo = repo

    async def search_archives(self, **kwargs: Any) -> Dict[str, Any]:
        return await self.repo.search(**kwargs)

    async def get_archive(self, archive_id: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.repo.get_by_id(archive_id)
        except NotFoundError:
            return None