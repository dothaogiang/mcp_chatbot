"""
ProfileFeatureManager: chứa các hàm nghiệp vụ thực thi khi tool được gọi.

QUAN TRỌNG: tên hàm PHẢI trùng chính xác với `name_tool` khai báo trong
Resources/tools.yaml, để ToolRegistry tự động match (xem tools/registry.py).

Class này KHÔNG chứa logic embedding/Qdrant/rerank - toàn bộ nằm ở project
rag_engine/ (chạy độc lập). Ở đây chỉ gọi HTTP qua common_utils/rag_client.py.
"""
from common_utils import rag_client
from logger import get_logger

logger = get_logger(__name__)


class ProfileFeatureManager:

    @staticmethod
    async def search_profile(keyword: str, top_k: int = 20) -> dict:
        """Tìm hồ sơ theo từ khóa tự do - gọi sang RAG Engine (rag_engine/src/main.py)."""
        return await rag_client.call_search_profile(keyword=keyword, top_k=top_k)

    @staticmethod
    async def get_profile_detail(archive_id: str, question: str, top_k: int = 5) -> dict:
        """Trả lời câu hỏi chi tiết trong 1 hồ sơ - gọi sang RAG Engine."""
        return await rag_client.call_profile_detail(archive_id=archive_id, question=question, top_k=top_k)
