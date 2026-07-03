import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from src.services.archive_service import ArchiveService


class DummyRepo:
    async def search(self, **kwargs):
        return {"items": [], "total": 0, "page": kwargs.get("page", 0)}

    async def get_by_id(self, archive_id):
        return {"id": archive_id}


def test_search_and_get():
    repo = DummyRepo()
    svc = ArchiveService(repo)

    # search_archives(**kwargs) chỉ nhận keyword args, không phải positional
    res = asyncio.run(svc.search_archives(keyword="x", page=1, size=10))
    assert res["page"] == 1

    detail = asyncio.run(svc.get_archive("abc"))
    assert detail["id"] == "abc"