from __future__ import annotations
from mcp import Tool

"""Tool: search_archive
Purpose: search public archives using backend API and return paginated results.
Input: { q: str, page: int, per_page: int }
Output: { items: list, total: int, page: int }
Call when user asks to find archives by keywords.
"""


async def _impl(params):
    # params: { q or keyword, page, per_page or size }
    from app_context import archive_service

    svc = archive_service()
    q = params.get("q") or params.get("keyword") or params.get("query")
    page = params.get("page", 0)
    size = params.get("per_page") or params.get("size") or 20
    res = await svc.search_archives(q, page=page, per_page=size)
    return res


tool = Tool(name="search_archive", description="Search archives", func=_impl)
