from __future__ import annotations
from mcp import Tool

"""Tool: search_staff_profile
Purpose: run RAG/hybrid search against cached ho-so-can-bo dataset.
Input: { q: str, top_k: int }
Output: { hits: list }
"""


async def _impl(params):
    from config.settings import Settings
    from clients.archive_backend_client import ArchiveBackendClient
    from repositories.staff_profile_repository import StaffProfileRepository
    from src.rag.embeddings.bge_m3_embedder import BGEM3Embedder
    from src.rag.vectorstore.qdrant_client import QdrantClientWrapper
    from src.rag.retrieval.hybrid_search import HybridSearch

    from app_context import staff_service, hybrid_search

    svc = staff_service()
    # ensure cache is fresh
    hits = []
    q = params.get("q") or params.get("query")
    top_k = params.get("top_k", 10)
    hybrid = hybrid_search()
    if hybrid:
        hits = await hybrid.search(q, top_k=top_k)
    return {"hits": hits}


tool = Tool(name="search_staff_profile", description="Search staff profiles", func=_impl)
