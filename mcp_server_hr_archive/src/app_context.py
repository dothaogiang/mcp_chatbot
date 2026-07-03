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


_settings: Optional[Settings] = None
_client: Optional[ArchiveBackendClient] = None
_archive_repo: Optional[ArchiveRepository] = None
_staff_repo: Optional[StaffProfileRepository] = None
_archive_service: Optional[ArchiveService] = None
_staff_service: Optional[StaffProfileService] = None
_file_service: Optional[FileService] = None
_embedder: Optional[BGEM3Embedder] = None
_qdrant: Optional[QdrantClientWrapper] = None
_hybrid: Optional[HybridSearch] = None
_scheduler = None


def init_app(settings: Settings) -> None:
    global _settings, _client, _archive_repo, _staff_repo, _archive_service, _staff_service, _file_service, _embedder, _qdrant, _hybrid, _scheduler
    if _settings:
        return
    _settings = settings
    _client = ArchiveBackendClient(settings)
    _archive_repo = ArchiveRepository(_client)
    _staff_repo = StaffProfileRepository(_client)
    _archive_service = ArchiveService(_archive_repo)
    _staff_service = StaffProfileService(_staff_repo)
    _file_service = FileService(_client)
    _embedder = BGEM3Embedder(model=settings.EMBEDDING_MODEL)
    _qdrant = QdrantClientWrapper(settings.QDRANT_URL, settings.QDRANT_API_KEY)
    _hybrid = HybridSearch(_qdrant, _embedder)
    # schedule periodic staff profile refresh
    _scheduler = schedule_refresh(_staff_repo, interval_seconds=300)


def settings() -> Settings:
    return _settings


def archive_service() -> ArchiveService:
    return _archive_service


def staff_service() -> StaffProfileService:
    return _staff_service


def file_service() -> FileService:
    return _file_service


def hybrid_search() -> HybridSearch:
    return _hybrid


def close() -> None:
    # TODO: shutdown scheduler and close client
    return None
