"""
application/retrieval_service.py — Use case "truy vấn dữ liệu RAG".
Đây là phần mà MCP tools (search_profile, get_profile_detail) HOẶC bất
kỳ chatbot/service nào khác sẽ gọi vào để lấy dữ liệu đã ingest sẵn.
"""
from rag.domain.entities import RetrievedChunk, RetrievedProfile
from rag.ports.interfaces import EmbeddingProviderPort, VectorStorePort


class RetrievalService:
    def __init__(self, embedder: EmbeddingProviderPort, vector_store: VectorStorePort):
        self._embedder = embedder
        self._vector_store = vector_store

    def search_profiles(self, keyword: str, top_k: int = 20) -> list[RetrievedProfile]:
        """Tìm hồ sơ (archive) theo từ khóa tự do — tầng 'định danh hồ sơ'."""
        query_embedding = self._embedder.embed_text(keyword)
        return self._vector_store.search_profiles(query_embedding, top_k)

    def search_chunks_in_archive(self, archive_id: str, question: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Tìm đoạn text liên quan nhất bên TRONG 1 hồ sơ cụ thể — RAG thật sự."""
        query_embedding = self._embedder.embed_text(question)
        return self._vector_store.search_chunks(query_embedding, archive_id, top_k)