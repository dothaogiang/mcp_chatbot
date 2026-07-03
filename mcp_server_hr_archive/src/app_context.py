from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from config.settings import Settings, get_settings
from logger import setup_logging, get_logger
from clients.archive_backend_client import ArchiveBackendClient
from repositories.archive_repository import ArchiveRepository
from repositories.staff_profile_repository import StaffProfileRepository
from services.archive_service import ArchiveService
from services.staff_profile_service import StaffProfileService
from services.file_service import FileService
from rag.embeddings.bge_m3_embedder import BGEM3Embedder
from rag.vectorstore.qdrant_client import QdrantClientWrapper
from rag.retrieval.hybrid_search import HybridSearch
from scheduler.sync_staff_profiles import schedule_refresh

log = get_logger(__name__)

_client: Optional[ArchiveBackendClient] = None
_archive_service: Optional[ArchiveService] = None
_staff_service: Optional[StaffProfileService] = None
_file_service: Optional[FileService] = None
_scheduler = None


def _build_services(settings: Settings):
    """Chỉ tạo object, KHÔNG gọi coroutine nào -> an toàn để gọi trước khi có event loop."""
    global _client, _archive_service, _staff_service, _file_service

    _client = ArchiveBackendClient(settings)
    archive_repo = ArchiveRepository(_client)
    staff_repo = StaffProfileRepository(_client)

    embedder = BGEM3Embedder(model_name=settings.EMBEDDING_MODEL)
    qdrant = QdrantClientWrapper(settings.QDRANT_URL, settings.QDRANT_API_KEY)
    hybrid = HybridSearch(qdrant, embedder, staff_repo)

    _archive_service = ArchiveService(archive_repo)
    _staff_service = StaffProfileService(staff_repo, hybrid)
    _file_service = FileService(_client)

    return staff_repo, hybrid


@asynccontextmanager
async def lifespan(_mcp) -> AsyncIterator[dict]:
    """FastMCP gọi hàm này SAU KHI event loop đã chạy (bên trong mcp.run()).
    Đây là nơi DUY NHẤT được phép start scheduler / asyncio.create_task().
    """
    global _scheduler

    settings = get_settings()
    setup_logging(settings)
    staff_repo, hybrid = _build_services(settings)

    _scheduler = schedule_refresh(staff_repo, hybrid, settings.STAFF_SYNC_INTERVAL_SECONDS)
    log.info("App context initialized, scheduler started")

    try:
        yield {}
    finally:
        if _scheduler:
            _scheduler.shutdown(wait=False)
        if _client:
            await _client.aclose()
        log.info("App context shut down")


def archive_service() -> ArchiveService:
    return _archive_service


def staff_service() -> StaffProfileService:
    return _staff_service


def file_service() -> FileService:
    return _file_service