from __future__ import annotations
from typing import List


class BGEM3Embedder:
    def __init__(self, model: str = "bge-m3-small") -> None:
        self.model = model

    async def embed(self, texts: List[str]) -> List[List[float]]:
        # Placeholder: call real bge-m3 client here
        return [[0.0] * 1536 for _ in texts]
