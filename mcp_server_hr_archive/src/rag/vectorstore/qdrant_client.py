from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid

from qdrant_client import AsyncQdrantClient, models
from logger import get_logger

log = get_logger(__name__)

COLLECTION = "staff_profiles"
DENSE_DIM = 1024  # đúng chiều output dense của bge-m3


class QdrantClientWrapper:
    def __init__(self, url: str, api_key: Optional[str] = None) -> None:
        self._client = AsyncQdrantClient(url=url, api_key=api_key)
        self._ensured = False

    async def ensure_collection(self) -> None:
        if self._ensured:
            return
        collections = await self._client.get_collections()
        if COLLECTION not in {c.name for c in collections.collections}:
            await self._client.create_collection(
                collection_name=COLLECTION,
                vectors_config={"dense": models.VectorParams(size=DENSE_DIM, distance=models.Distance.COSINE)},
                sparse_vectors_config={"sparse": models.SparseVectorParams()},
            )
        self._ensured = True

    async def upsert(self, points: List[Dict[str, Any]]) -> None:
        await self.ensure_collection()
        qdrant_points = [
            models.PointStruct(
                id=p["id"],
                vector={
                    "dense": p["dense"],
                    "sparse": models.SparseVector(
                        indices=list(p["sparse"].keys()), values=list(p["sparse"].values()),
                    ),
                },
                payload=p["payload"],
            )
            for p in points
        ]
        await self._client.upsert(collection_name=COLLECTION, points=qdrant_points)

    async def search_dense(self, dense_vector: List[float], top_k: int = 20):
        await self.ensure_collection()
        res = await self._client.query_points(
            collection_name=COLLECTION, query=dense_vector, using="dense", limit=top_k, with_payload=True,
        )
        return res.points

    async def search_sparse(self, sparse: Dict[int, float], top_k: int = 20):
        await self.ensure_collection()
        res = await self._client.query_points(
            collection_name=COLLECTION,
            query=models.SparseVector(indices=list(sparse.keys()), values=list(sparse.values())),
            using="sparse", limit=top_k, with_payload=True,
        )
        return res.points

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())