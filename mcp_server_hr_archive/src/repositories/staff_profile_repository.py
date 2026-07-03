from __future__ import annotations
from typing import Any, Dict, List
from clients.archive_backend_client import ArchiveBackendClient
from logger import get_logger

log = get_logger(__name__)


class StaffProfileRepository:
    """Loads and caches the static ho-so-can-bo JSON and exposes it for indexing/searching."""

    def __init__(self, client: ArchiveBackendClient) -> None:
        self.client = client
        self._cache: List[Dict[str, Any]] = []

    async def refresh(self) -> None:
        data = await self.client.get_staff_profiles()
        if isinstance(data, list):
            self._cache = data
        else:
            log.warning("Unexpected staff profile shape; expected list")

    async def all(self) -> List[Dict[str, Any]]:
        return self._cache
