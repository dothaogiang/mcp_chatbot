"""
Logic nghiệp vụ chính của RAG engine. src/main.py (FastAPI) gọi vào đây.
"""
from qdrant_client import models
from config.configs import config_object
from common_utils.constants import COLLECTION_ARCHIVES, COLLECTION_CHUNKS
from common_utils import embedding_utils, qdrant_utils, reranker_utils
from logger import get_logger

logger = get_logger(__name__)


def search_profile(keyword: str, top_k: int = 20) -> dict:
    """
    Tìm hồ sơ theo từ khóa tự do, hybrid search (dense + sparse, fusion RRF).
    Keyword mơ hồ -> điểm relevance dàn trải -> nhiều hồ sơ được trả về.
    Keyword cụ thể -> điểm relevance cô đặc vào ít hồ sơ hơn, chính xác hơn.
    """
    dense_vec = embedding_utils.embed_dense(keyword)
    sparse_vec = embedding_utils.embed_sparse(keyword)

    points = qdrant_utils.hybrid_search(
        collection=COLLECTION_ARCHIVES,
        dense_vec=dense_vec,
        sparse_vec=sparse_vec,
        limit=top_k,
    )

    profiles = [_point_to_profile(p) for p in points]
    return {"keyword": keyword, "total_found": len(profiles), "profiles": profiles}


def search_profile_detail(archive_id: str, question: str, top_k: int = 5) -> dict:
    """
    Trả lời câu hỏi chi tiết TRONG PHẠM VI 1 hồ sơ cụ thể:
      1. Hybrid search trên document_chunks, filter cứng theo archive_id,
         lấy pool rộng (RERANK_POOL_SIZE).
      2. Rerank pool đó bằng cross-encoder, chọn top_k chính xác nhất.
    Trả về đoạn text liên quan nhất kèm nguồn (file_url, page_number).
    """
    dense_vec = embedding_utils.embed_dense(question)
    sparse_vec = embedding_utils.embed_sparse(question)

    archive_filter = models.Filter(
        must=[models.FieldCondition(key="archive_id", match=models.MatchValue(value=archive_id))]
    )

    pool = qdrant_utils.hybrid_search(
        collection=COLLECTION_CHUNKS,
        dense_vec=dense_vec,
        sparse_vec=sparse_vec,
        limit=config_object.RERANK_POOL_SIZE,
        query_filter=archive_filter,
    )

    if not pool:
        return {
            "archive_id": archive_id,
            "question": question,
            "found": False,
            "message": "Không tìm thấy nội dung liên quan trong hồ sơ này.",
            "chunks": [],
        }

    texts = [p.payload.get("text", "") for p in pool]
    ranked = reranker_utils.rerank(question, texts, top_k=top_k)

    chunks = []
    for idx, score in ranked:
        p = pool[idx]
        chunks.append(
            {
                "text": p.payload.get("text"),
                "file_url": p.payload.get("file_url"),
                "page_number": p.payload.get("page_number"),
                "extraction_method": p.payload.get("extraction_method"),
                "rerank_score": round(float(score), 4),
                "retrieval_score": round(p.score, 4),
            }
        )

    return {"archive_id": archive_id, "question": question, "found": True, "chunks": chunks}


def _point_to_profile(p) -> dict:
    return {
        "archive_id": p.payload.get("archive_id"),
        "title": p.payload.get("title"),
        "arcFileCode": p.payload.get("arcFileCode"),
        "boxCode": p.payload.get("boxCode"),
        "warehouseName": p.payload.get("warehouseName"),
        "startDate": p.payload.get("startDate"),
        "endDate": p.payload.get("endDate"),
        "staffMetadata": p.payload.get("staffMetadata"),
        "score": round(p.score, 4),
    }
