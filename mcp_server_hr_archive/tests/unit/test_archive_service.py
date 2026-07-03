import asyncio
import sys
import os

# ensure project src is importable when tests run from nested package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# also add src directory so imports like `from logger import ...` resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from src.services.archive_service import ArchiveService


class DummyRepo:
    async def search(self, q, page, per_page):
        return {"items": [], "total": 0, "page": page}

    async def get_by_id(self, _id):
        return {"id": _id}


def test_search_and_get():
    repo = DummyRepo()
    svc = ArchiveService(repo)
    res = asyncio.run(svc.search_archives("x", 1, 10))
    assert res["page"] == 1
    detail = asyncio.run(svc.get_archive("abc"))
    assert detail["id"] == "abc"
