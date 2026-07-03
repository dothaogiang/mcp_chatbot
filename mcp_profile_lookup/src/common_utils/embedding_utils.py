"""
Sinh dense + sparse embedding dùng fastembed (chạy local, không cần gọi API
ngoài, không tốn phí theo request). Model được load 1 lần (singleton) vì
load model tốn vài giây - tránh load lại mỗi lần gọi tool.

- Dense (BAAI/bge-m3): bắt nghĩa (semantic) -> "làm nông" gần nghĩa với
  "nông dân", "nông nghiệp".
- Sparse (Qdrant/bm25): bắt từ khóa chính xác (lexical) -> tên riêng, số
  liệu, mã hồ sơ khớp chính xác.
Kết hợp cả hai qua RRF fusion trong qdrant_utils.hybrid_search().
"""
from functools import lru_cache
from fastembed import TextEmbedding, SparseTextEmbedding
from config.configs import config_object
from logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_dense_model() -> TextEmbedding:
    logger.info(f"Loading dense embedding model: {config_object.DENSE_MODEL_NAME}")
    return TextEmbedding(model_name=config_object.DENSE_MODEL_NAME)


@lru_cache(maxsize=1)
def get_sparse_model() -> SparseTextEmbedding:
    logger.info(f"Loading sparse embedding model: {config_object.SPARSE_MODEL_NAME}")
    return SparseTextEmbedding(model_name=config_object.SPARSE_MODEL_NAME)


def embed_dense(text: str) -> list:
    if not text or not text.strip():
        text = " "
    model = get_dense_model()
    return list(model.embed([text]))[0].tolist()


def embed_sparse(text: str) -> dict:
    if not text or not text.strip():
        text = " "
    model = get_sparse_model()
    result = list(model.embed([text]))[0]
    return {"indices": result.indices.tolist(), "values": result.values.tolist()}


def embed_dense_batch(texts: list) -> list:
    if not texts:
        return []
    model = get_dense_model()
    texts = [t if t and t.strip() else " " for t in texts]
    return [e.tolist() for e in model.embed(texts)]


def embed_sparse_batch(texts: list) -> list:
    if not texts:
        return []
    model = get_sparse_model()
    texts = [t if t and t.strip() else " " for t in texts]
    results = list(model.embed(texts))
    return [{"indices": r.indices.tolist(), "values": r.values.tolist()} for r in results]
