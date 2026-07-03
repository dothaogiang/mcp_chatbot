from __future__ import annotations
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from repositories.staff_profile_repository import StaffProfileRepository
from logger import get_logger

log = get_logger(__name__)


def schedule_refresh(repo: StaffProfileRepository, interval_seconds: int = 300) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def job():
        log.info("Refreshing staff profiles cache")
        await repo.refresh()

    scheduler.add_job(lambda: asyncio.create_task(job()), 'interval', seconds=interval_seconds)
    scheduler.start()
    return scheduler
