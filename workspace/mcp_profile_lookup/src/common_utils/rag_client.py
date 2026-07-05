"""
rag_client.py: client HTTP gọi sang RAG Engine (project rag_engine/, chạy
độc lập, thường ở port 8091).

LƯU Ý: đây là điểm khác so với cấu trúc `common_utils/search_utils.py`
(chứa embed_dense/embed_sparse/build_filter) - vì giờ RAG đã tách thành
project tự trị riêng, MCP KHÔNG còn tự làm embedding/search nữa, chỉ gọi
HTTP vào RAG Engine. File này đóng vai trò tương đương nhưng bản chất là
1 HTTP client mỏng, không chứa logic search.
"""
import httpx
from config.configs import config_object
from logger import get_logger

logger = get_logger(__name__)


async def call_search_profile(keyword: str, top_k: int = 20) -> dict:
    async with httpx.AsyncClient(timeout=config_object.RAG_REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            f"{config_object.RAG_SERVICE_URL}/search_profile",
            json={"keyword": keyword, "top_k": top_k},
        )
        resp.raise_for_status()
        return resp.json()


async def call_profile_detail(archive_id: str, question: str, top_k: int = 5) -> dict:
    async with httpx.AsyncClient(timeout=config_object.RAG_REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            f"{config_object.RAG_SERVICE_URL}/profile_detail",
            json={"archive_id": archive_id, "question": question, "top_k": top_k},
        )
        resp.raise_for_status()
        return resp.json()
