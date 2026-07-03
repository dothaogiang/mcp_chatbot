from __future__ import annotations
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from repositories.staff_profile_repository import StaffProfileRepository
from rag.retrieval.hybrid_search import HybridSearch
from logger import get_logger

log = get_logger(__name__)


async def sync_once(repo: StaffProfileRepository, hybrid: HybridSearch) -> None:
    profiles = await repo.refresh()
    if not profiles:
        return

    texts = [_profile_to_text(p) for p in profiles]
    embeddings = await hybrid.embedder.embed(texts)

    points = [
        {
            "id": hybrid.qdrant.new_id(),
            "dense": emb["dense"],
            "sparse": emb["sparse"],
            "payload": {
                "archiveCode": profile.get("archiveCode"),
                "archiveName": profile.get("archiveName"),
                "metadata": profile.get("metadata", []),
            },
        }
        for profile, emb in zip(profiles, embeddings)
    ]
    await hybrid.qdrant.upsert(points)
    log.info("Đã đồng bộ + index %d hồ sơ cán bộ vào Qdrant", len(points))


def _profile_to_text(profile: dict) -> str:
    parts = [profile.get("archiveName", "")]
    for field in profile.get("metadata", []):
        if field.get("name") and field.get("value"):
            parts.append(f"{field['name']}: {field['value']}")
    return "\n".join(parts)


def schedule_refresh(
    repo: StaffProfileRepository, hybrid: HybridSearch, interval_seconds: int = 300,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def job() -> None:
        log.info("Đồng bộ định kỳ hồ sơ cán bộ...")
        try:
            await sync_once(repo, hybrid)
        except Exception:
            log.exception("Lỗi khi đồng bộ hồ sơ cán bộ")

    scheduler.add_job(lambda: asyncio.create_task(job()), "interval", seconds=interval_seconds)
    scheduler.start()
    asyncio.create_task(job())  # chạy ngay khi khởi động, không đợi interval đầu tiên
    return scheduler