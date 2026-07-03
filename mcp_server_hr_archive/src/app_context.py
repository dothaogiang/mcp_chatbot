from __future__ import annotations
from typing import Optional

from config.settings import Settings
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

_client: Optional[ArchiveBackendClient] = None
_archive_service: Optional[ArchiveService] = None
_staff_service: Optional[StaffProfileService] = None
_file_service: Optional[FileService] = None
_scheduler = None


def init_app(settings: Settings) -> None:
    global _client, _archive_service, _staff_service, _file_service, _scheduler
    if _client:
        return

    _client = ArchiveBackendClient(settings)
    archive_repo = ArchiveRepository(_client)
    staff_repo = StaffProfileRepository(_client)

    embedder = BGEM3Embedder(model_name=settings.EMBEDDING_MODEL)
    qdrant = QdrantClientWrapper(settings.QDRANT_URL, settings.QDRANT_API_KEY)
    hybrid = HybridSearch(qdrant, embedder, staff_repo)

    _archive_service = ArchiveService(archive_repo)
    _staff_service = StaffProfileService(staff_repo, hybrid)
    _file_service = FileService(_client)

    _scheduler = schedule_refresh(staff_repo, hybrid, settings.STAFF_SYNC_INTERVAL_SECONDS)


def archive_service() -> ArchiveService:
    return _archive_service


def staff_service() -> StaffProfileService:
    return _staff_service


def file_service() -> FileService:
    return _file_service


def close_app() -> None:
    if _scheduler:
        _scheduler.shutdown(wait=False)