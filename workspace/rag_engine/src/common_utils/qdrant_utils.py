"""
Wrapper thao tác Qdrant cho 2 collection:
  - "archives"        : 1 point = 1 hồ sơ (metadata)
  - "document_chunks" : 1 point = 1 đoạn text trích từ PDF (filter theo archive_id)
"""
import hashlib
from qdrant_client import QdrantClient, models
from config.configs import config_object
from common_utils.constants import DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME, COLLECTION_ARCHIVES, COLLECTION_CHUNKS
from logger import get_logger

logger = get_logger(__name__)

_client = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=config_object.QDRANT_URL, api_key=config_object.QDRANT_API_KEY)
    return _client


def ensure_collections():
    client = get_client()
    vectors_config = {
        DENSE_VECTOR_NAME: models.VectorParams(size=config_object.DENSE_VECTOR_SIZE, distance=models.Distance.COSINE)
    }
    sparse_vectors_config = {SPARSE_VECTOR_NAME: models.SparseVectorParams()}

    for collection in (COLLECTION_ARCHIVES, COLLECTION_CHUNKS):
        if not client.collection_exists(collection):
            logger.info(f"Tạo collection: {collection}")
            client.create_collection(
                collection_name=collection,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
            )
        else:
            logger.info(f"Collection đã tồn tại: {collection}")


def make_point_id(*parts: str) -> str:
    raw = ":".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def upsert_archive(archive_id: str, dense_vec: list, sparse_vec: dict, payload: dict):
    client = get_client()
    client.upsert(
        collection_name=COLLECTION_ARCHIVES,
        points=[
            models.PointStruct(
                id=make_point_id("archive", archive_id),
                vector={
                    DENSE_VECTOR_NAME: dense_vec,
                    SPARSE_VECTOR_NAME: models.SparseVector(**sparse_vec),
                },
                payload=payload,
            )
        ],
    )


def upsert_chunks(archive_id: str, file_url: str, chunks: list, dense_vecs: list, sparse_vecs: list, extra_payload: dict):
    client = get_client()
    points = []
    for i, (chunk, dvec, svec) in enumerate(zip(chunks, dense_vecs, sparse_vecs)):
        payload = {
            "archive_id": archive_id,
            "file_url": file_url,
            "page_number": chunk["page_number"],
            "chunk_index": i,
            "text": chunk["text"],
            **extra_payload,
        }
        points.append(
            models.PointStruct(
                id=make_point_id("chunk", archive_id, file_url, str(i)),
                vector={
                    DENSE_VECTOR_NAME: dvec,
                    SPARSE_VECTOR_NAME: models.SparseVector(**svec),
                },
                payload=payload,
            )
        )
    if points:
        client.upsert(collection_name=COLLECTION_CHUNKS, points=points)


def delete_chunks_by_file(archive_id: str, file_url: str):
    client = get_client()
    client.delete(
        collection_name=COLLECTION_CHUNKS,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(key="archive_id", match=models.MatchValue(value=archive_id)),
                    models.FieldCondition(key="file_url", match=models.MatchValue(value=file_url)),
                ]
            )
        ),
    )


def hybrid_search(collection: str, dense_vec: list, sparse_vec: dict, limit: int, query_filter=None):
    client = get_client()
    result = client.query_points(
        collection_name=collection,
        prefetch=[
            models.Prefetch(query=dense_vec, using=DENSE_VECTOR_NAME, limit=limit * 3, filter=query_filter),
            models.Prefetch(
                query=models.SparseVector(**sparse_vec), using=SPARSE_VECTOR_NAME, limit=limit * 3, filter=query_filter
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit,
        with_payload=True,
    )
    return result.points
