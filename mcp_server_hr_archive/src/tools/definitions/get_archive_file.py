from __future__ import annotations
from typing import Optional
from app_context import file_service, archive_service


async def get_archive_file_info(
    archive_id: Optional[str] = None,
    file_index: int = 0,
    key: Optional[str] = None,
) -> dict:
    """Lấy metadata của 1 file gốc (tên file, kích thước, content-type) — KHÔNG trả nội
    dung binary. Khuyến nghị truyền `archive_id` (lấy từ `get_archive_detail`) +
    `file_index`; tool tự tra `fileUrls` và tính `key`. Chỉ truyền thẳng `key` nếu đã
    biết chính xác object path.
    """
    file_svc = file_service()
    if not key:
        if not archive_id:
            return {"found": False, "message": "Cần archive_id hoặc key"}
        key = await file_svc.resolve_key_from_archive(archive_service(), archive_id, file_index)
        if not key:
            return {"found": False, "message": "Không tìm thấy file trong hồ sơ này"}

    info = await file_svc.get_file_info(key)
    return {"found": True, "file": info}