from __future__ import annotations
from typing import Any, Dict, List
from repositories.staff_profile_repository import StaffProfileRepository


class StaffProfileService:
    def __init__(self, repo: StaffProfileRepository) -> None:
        self.repo = repo

    async def refresh_and_list(self) -> List[Dict[str, Any]]:
        await self.repo.refresh()
        return await self.repo.all()
