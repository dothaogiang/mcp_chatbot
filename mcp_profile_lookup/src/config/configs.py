import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    # --- MCP server ---
    SERVER_NAME = os.getenv("SERVER_NAME", "profile_lookup")
    URL_HOST_SERVER = os.getenv("URL_HOST_SERVER", "0.0.0.0")
    PORT_SERVER = int(os.getenv("PORT_SERVER", "8090"))

    # --- Resources (nơi chứa tools.yaml) ---
    RESOURCES_DIR = os.path.join(BASE_DIR, "..", "Resources")

    # --- Archive API (nguồn dữ liệu gốc) ---
    ARCHIVE_API_BASE_URL = os.getenv("ARCHIVE_API_BASE_URL", "http://192.168.1.46:4000")
    ARCHIVE_API_PATH = os.getenv("ARCHIVE_API_PATH", "/api/public/archives")
    ARCHIVE_API_PAGE_SIZE = int(os.getenv("ARCHIVE_API_PAGE_SIZE", "100"))

    # --- Qdrant ---
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
    COLLECTION_ARCHIVES = "archives"
    COLLECTION_CHUNKS = "document_chunks"

    # --- Embedding models (fastembed, chạy local) ---
    DENSE_MODEL_NAME = os.getenv("DENSE_MODEL_NAME", "BAAI/bge-m3")
    SPARSE_MODEL_NAME = os.getenv("SPARSE_MODEL_NAME", "Qdrant/bm25")
    DENSE_VECTOR_SIZE = int(os.getenv("DENSE_VECTOR_SIZE", "1024"))  # bge-m3 output dim

    # --- OCR ---
    OCR_LANG = os.getenv("OCR_LANG", "vie")
    OCR_MIN_CHARS_PER_PAGE = int(os.getenv("OCR_MIN_CHARS_PER_PAGE", "50"))
    OCR_DPI = int(os.getenv("OCR_DPI", "200"))

    # --- Chunking ---
    CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "1200"))
    CHUNK_OVERLAP_CHARS = int(os.getenv("CHUNK_OVERLAP_CHARS", "200"))

    # --- Sync state (trạng thái đồng bộ, để cron chạy incremental) ---
    SYNC_DB_PATH = os.getenv("SYNC_DB_PATH", os.path.join(BASE_DIR, "..", "sync_state.db"))
    OCR_CONCURRENCY = int(os.getenv("OCR_CONCURRENCY", "4"))
    HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "60"))


config_object = Config()
