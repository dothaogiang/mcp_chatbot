from __future__ import annotations
from typing import Any, Dict, List
from clients.archive_backend_client import ArchiveBackendClient
from logger import get_logger

log = get_logger(__name__)


class StaffProfileRepository:
    """Tải + cache toàn bộ ho-so-can-bo (file JSON tĩnh, không phân trang, không filter)."""

    def __init__(self, client: ArchiveBackendClient) -> None:
        self.client = client
        self._cache: List[Dict[str, Any]] = []
        self._synced = False

    async def refresh(self) -> List[Dict[str, Any]]:
        data = await self.client.get_staff_profiles()
        if isinstance(data, list):
            self._cache = data
            self._synced = True
            log.info("Staff profile cache refreshed: %d records", len(data))
        else:
            log.warning("Unexpected staff profile shape; expected list, got %s", type(data))
        return self._cache

    async def all(self) -> List[Dict[str, Any]]:
        if not self._synced:
            await self.refresh()
        return self._cache

    @property
    def is_ready(self) -> bool:
        return self._synced