from __future__ import annotations
from typing import Any, List


class QdrantClientWrapper:
    def __init__(self, url: str, api_key: str | None = None) -> None:
        self.url = url
        self.api_key = api_key

    async def upsert(self, collection: str, vectors: List[Any]) -> None:
        # TODO: implement Qdrant upsert
        return None

    async def search(self, collection: str, query_vector: List[float], top_k: int = 10) -> list:
        return []
