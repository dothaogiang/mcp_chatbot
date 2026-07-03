from __future__ import annotations
from typing import Any, Dict, List
from repositories.staff_profile_repository import StaffProfileRepository
from rag.retrieval.hybrid_search import HybridSearch


class StaffProfileService:
    def __init__(self, repo: StaffProfileRepository, hybrid_search: HybridSearch) -> None:
        self.repo = repo
        self.hybrid_search = hybrid_search

    async def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Tìm qua Qdrant (đã index sẵn), KHÔNG gọi lại API + refresh mỗi lần hỏi."""
        return await self.hybrid_search.search(query, top_k=top_k)