from __future__ import annotations
from app_context import archive_service


async def get_archive_detail(id: str) -> dict:
    """Lấy chi tiết đầy đủ 1 hồ sơ lưu trữ theo UUID.

    CHỈ gọi khi đã có UUID hợp lệ — thường lấy từ kết quả `search_archive`.
    Không tự đoán UUID.
    """
    svc = archive_service()
    archive = await svc.get_archive(id)
    if archive is None:
        return {"found": False, "message": "Không tìm thấy hồ sơ với ID này"}
    return {"found": True, "archive": archive}