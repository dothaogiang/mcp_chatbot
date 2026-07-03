from __future__ import annotations
from mcp import Tool

"""Tool: get_archive_file_info
Purpose: return metadata for a file (including `key` to pass to file proxy).
Input: { archive_id: str, file_index: int }
Output: { file: { name, size, key } }
Note: This tool returns metadata only; callers must not embed binary into MCP outputs.
"""


async def _impl(params):
    from config.settings import Settings
    from clients.archive_backend_client import ArchiveBackendClient
    from urllib.parse import urlparse

    from app_context import file_service, archive_service

    file_svc = file_service()
    archive_svc = archive_service()

    key = params.get("key")
    if not key:
        archive_id = params.get("archive_id") or params.get("id")
        file_index = int(params.get("file_index", 0))
        if not archive_id:
            raise ValueError("missing archive_id or key")
        archive = await archive_svc.get_archive(archive_id)
        projects = archive.get("projects") or []
        file_url = None
        for p in projects:
            furls = p.get("fileUrls") or []
            if furls:
                if file_index < len(furls):
                    file_url = furls[file_index]
                    break
                else:
                    file_url = furls[0]
                    break
        if not file_url:
            return {"file": None}
        from clients.archive_backend_client import ArchiveBackendClient
        key = ArchiveBackendClient.extract_key_from_url(file_url)

    # Ask archive backend for headers/metadata only
    meta = await file_svc.client.get_file_metadata(key)
    return {"file": meta}


tool = Tool(name="get_archive_file_info", description="Get archive file metadata", func=_impl)
