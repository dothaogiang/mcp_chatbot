from __future__ import annotations
from mcp import Tool

"""Tool: get_archive_detail
Purpose: fetch brief detail for an archive id.
Input: { id: str }
Output: { archive: { ... } }
Note: backend may return inconsistent not-found errors; client maps to exceptions.
"""


async def _impl(params):
    from config.settings import Settings
    from clients.archive_backend_client import ArchiveBackendClient
    from common_utils.exceptions import NotFoundError

    from app_context import archive_service
    svc = archive_service()
    archive_id = params.get("id") or params.get("archive_id")
    if not archive_id:
        raise ValueError("missing archive id")
    try:
        data = await svc.get_archive(archive_id)
    except NotFoundError:
        return {"archive": None}
    return {"archive": data}


tool = Tool(name="get_archive_detail", description="Get archive detail", func=_impl)
