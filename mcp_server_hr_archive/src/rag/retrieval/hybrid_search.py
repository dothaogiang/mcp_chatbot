from __future__ import annotations
from typing import Any, Dict, List

from rag.embeddings.bge_m3_embedder import BGEM3Embedder
from rag.vectorstore.qdrant_client import QdrantClientWrapper

RRF_K = 60  # hằng số chuẩn của Reciprocal Rank Fusion


class HybridSearch:
    def __init__(self, qdrant: QdrantClientWrapper, embedder: BGEM3Embedder, staff_repo=None) -> None:
        self.qdrant = qdrant
        self.embedder = embedder
        self.staff_repo = staff_repo

    async def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        embedded = (await self.embedder.embed([query]))[0]
        dense_hits = await self.qdrant.search_dense(embedded["dense"], top_k=top_k * 2)
        sparse_hits = await self.qdrant.search_sparse(embedded["sparse"], top_k=top_k * 2)
        return self._reciprocal_rank_fusion(dense_hits, sparse_hits)[:top_k]

    @staticmethod
    def _reciprocal_rank_fusion(dense_hits, sparse_hits) -> List[Dict[str, Any]]:
        scores: Dict[Any, float] = {}
        payloads: Dict[Any, Any] = {}
        for rank, hit in enumerate(dense_hits):
            scores[hit.id] = scores.get(hit.id, 0.0) + 1.0 / (RRF_K + rank + 1)
            payloads[hit.id] = hit.payload
        for rank, hit in enumerate(sparse_hits):
            scores[hit.id] = scores.get(hit.id, 0.0) + 1.0 / (RRF_K + rank + 1)
            payloads[hit.id] = hit.payload
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return [{"id": _id, "score": score, **(payloads[_id] or {})} for _id, score in ranked]