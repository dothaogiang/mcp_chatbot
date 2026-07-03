from __future__ import annotations
from app_context import staff_service


async def search_staff_profile(query: str, top_k: int = 5) -> dict:
    """Tìm hồ sơ cán bộ theo tên, mã nhân viên, hoặc thông tin cá nhân/nghiệp vụ
    (hợp đồng, bảo hiểm, khen thưởng, kỷ luật...). Dữ liệu đã được index sẵn định kỳ.
    """
    svc = staff_service()
    hits = await svc.search(query, top_k=top_k)
    return {"results": hits}