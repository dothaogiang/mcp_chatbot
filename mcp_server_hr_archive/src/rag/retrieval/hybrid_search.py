from __future__ import annotations
from typing import List, Dict, Any


class HybridSearch:
    def __init__(self, qdrant_client, embedder) -> None:
        self.qdrant = qdrant_client
        self.embedder = embedder

    async def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        vec = (await self.embedder.embed([query]))[0]
        hits = await self.qdrant.search("staff_profiles", vec, top_k=top_k)
        return hits
