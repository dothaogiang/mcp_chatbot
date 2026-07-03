from __future__ import annotations
from typing import Optional
from app_context import archive_service


async def search_archive(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    language: Optional[str] = None,
    maintenance: Optional[str] = None,
    created_from: Optional[str] = None,
    created_to: Optional[str] = None,
    page: int = 0,
    size: int = 20,
) -> dict:
    """Tìm kiếm hồ sơ lưu trữ theo từ khóa và bộ lọc.

    Gọi khi người dùng muốn tìm/liệt kê hồ sơ theo tiêu đề, mã hồ sơ, mã hộp, trạng thái,
    kho, ngôn ngữ, thời hạn bảo quản, khoảng ngày tạo. Trả về danh sách tóm tắt — dùng
    `get_archive_detail` với `id` lấy từ đây nếu cần xem đầy đủ 1 hồ sơ.
    """
    svc = archive_service()
    return await svc.search_archives(
        keyword=keyword, status=status, warehouse_id=warehouse_id,
        language=language, maintenance=maintenance,
        created_from=created_from, created_to=created_to,
        page=page, size=size,
    )