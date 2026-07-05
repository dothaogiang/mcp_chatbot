"""
FeatureManager: chứa các hàm nghiệp vụ thực thi khi tool MCP được gọi.

QUAN TRỌNG: tên hàm PHẢI trùng chính xác với `name_tool` khai báo trong
Resources/tools.yaml. ToolRegistry (tools/registry.py) tự động match
theo tên -> đây là cơ chế cho phép thêm/sửa/xóa tool chỉ bằng cách sửa
file YAML, không cần đụng vào registry.py hay server.py.

Lưu ý: FeatureManager KHÔNG tự làm embedding/Qdrant nữa. Toàn bộ phần
đó nằm trong module rag/ (xem rag/README.md). Ở đây chỉ "dịch" kết quả
của RetrievalService sang đúng format tool trả về cho chatbot.
"""
from rag.retrieval_factory import get_retrieval_service
from logger import get_logger

logger = get_logger(__name__)


class FeatureManager:

    @staticmethod
    async def search_profile(keyword: str, top_k: int = 20) -> dict:
        service = get_retrieval_service()
        profiles = service.search_profiles(keyword=keyword, top_k=top_k)

        return {
            "keyword": keyword,
            "total_found": len(profiles),
            "profiles": [
                {
                    "archive_id": p.archive_id,
                    "title": p.title,
                    "arcFileCode": p.arc_file_code,
                    "boxCode": p.box_code,
                    "warehouseName": p.warehouse_name,
                    "startDate": p.start_date,
                    "endDate": p.end_date,
                    "staffMetadata": p.staff_metadata,
                    "score": p.score,
                }
                for p in profiles
            ],
        }

    @staticmethod
    async def get_profile_detail(archive_id: str, question: str, top_k: int = 5) -> dict:
        service = get_retrieval_service()
        chunks = service.search_chunks_in_archive(archive_id=archive_id, question=question, top_k=top_k)

        if not chunks:
            return {
                "archive_id": archive_id,
                "question": question,
                "found": False,
                "message": "Không tìm thấy nội dung liên quan trong hồ sơ này.",
                "chunks": [],
            }

        return {
            "archive_id": archive_id,
            "question": question,
            "found": True,
            "chunks": [
                {
                    "text": c.text,
                    "file_url": c.file_url,
                    "page_number": c.page_number,
                    "extraction_method": c.extraction_method,
                    "score": c.score,
                }
                for c in chunks
            ],
        }