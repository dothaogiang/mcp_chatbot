import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- Archive API (nguồn dữ liệu gốc) ---
    ARCHIVE_API_BASE_URL = os.getenv("ARCHIVE_API_BASE_URL", "http://192.168.1.46:4000")
    ARCHIVE_API_PATH = os.getenv("ARCHIVE_API_PATH", "/api/public/archives")
    ARCHIVE_API_PAGE_SIZE = int(os.getenv("ARCHIVE_API_PAGE_SIZE", "100"))

    # --- Qdrant ---
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None

    # --- Embedding models (fastembed, chạy local) ---
    DENSE_MODEL_NAME = os.getenv("DENSE_MODEL_NAME", "BAAI/bge-m3")
    SPARSE_MODEL_NAME = os.getenv("SPARSE_MODEL_NAME", "Qdrant/bm25")
    DENSE_VECTOR_SIZE = int(os.getenv("DENSE_VECTOR_SIZE", "1024"))

    # --- Reranker (cross-encoder sau hybrid search) ---
    RERANK_MODEL_NAME = os.getenv("RERANK_MODEL_NAME", "BAAI/bge-reranker-v2-m3")
    RERANK_POOL_SIZE = int(os.getenv("RERANK_POOL_SIZE", "20"))

    # --- OCR ---
    OCR_LANG = os.getenv("OCR_LANG", "vie")
    OCR_MIN_CHARS_PER_PAGE = int(os.getenv("OCR_MIN_CHARS_PER_PAGE", "50"))
    OCR_DPI = int(os.getenv("OCR_DPI", "200"))

    # --- Chunking (sentence-aware) ---
    CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "1200"))
    CHUNK_OVERLAP_SENTENCES = int(os.getenv("CHUNK_OVERLAP_SENTENCES", "2"))

    # --- Sync state ---
    SYNC_DB_PATH = os.getenv("SYNC_DB_PATH", "./data/sync_state.db")
    OCR_CONCURRENCY = int(os.getenv("OCR_CONCURRENCY", "4"))
    HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "60"))

    # --- HTTP API (FastAPI, để MCP gọi vào) ---
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8091"))


config_object = Config()
