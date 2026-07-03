from __future__ import annotations
from typing import List


class CrossEncoderReranker:
    def __init__(self, model: str | None = None) -> None:
        self.model = model

    async def rerank(self, query: str, candidates: List[dict]) -> List[dict]:
        # Placeholder — return candidates as-is
        return candidates
