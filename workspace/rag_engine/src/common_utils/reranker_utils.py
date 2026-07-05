"""
Rerank lại top-N kết quả từ hybrid search bằng cross-encoder, để tăng độ
chính xác trước khi trả về. Vì RRF fusion chỉ dựa vào thứ hạng dense/sparse
riêng lẻ, không thực sự "đọc hiểu" mức độ liên quan giữa câu hỏi và chunk.
"""
from functools import lru_cache
from fastembed.rerank.cross_encoder import TextCrossEncoder
from config.configs import config_object
from logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_reranker() -> TextCrossEncoder:
    logger.info(f"Loading reranker model: {config_object.RERANK_MODEL_NAME}")
    return TextCrossEncoder(model_name=config_object.RERANK_MODEL_NAME)


def rerank(query: str, documents: list, top_k: int) -> list:
    """Trả về list (index_trong_documents, score), sắp giảm dần, lấy top_k."""
    if not documents:
        return []
    model = get_reranker()
    scores = list(model.rerank(query, documents))
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
