"""
FeatureManager: chứa các hàm nghiệp vụ thực thi khi tool được gọi.

QUAN TRỌNG: tên hàm PHẢI trùng chính xác với `name_tool` khai báo trong
Resources/tools.yaml. ToolRegistry (tools/registry.py) sẽ tự động match
theo tên -> đây là cơ chế cho phép thêm/sửa/xóa tool chỉ bằng cách sửa
file YAML, không cần đụng vào registry.py hay server.py.

Khi cần thêm tool mới:
  1. Viết 1 method @staticmethod async cùng tên trong class này.
  2. Thêm entry tương ứng trong Resources/tools.yaml.
  Xong - không cần sửa gì thêm.
"""
from qdrant_client import models
from config.configs import config_object
from common_utils.embedding_utils import embed_dense, embed_sparse
from common_utils import qdrant_utils
from logger import get_logger

logger = get_logger(__name__)


class FeatureManager:

    @staticmethod
    async def search_profile(keyword: str, top_k: int = 20) -> dict:
        """
        Tìm hồ sơ (archive) theo từ khóa tự do, hybrid search (dense+sparse).
        Keyword mơ hồ -> điểm relevance dàn trải -> nhiều hồ sơ được trả về.
        Keyword cụ thể -> điểm relevance cô đặc vào ít hồ sơ hơn, chính xác hơn.
        Đây là tầng "định danh hồ sơ" - dùng archive_id trả về để gọi tiếp
        get_profile_detail nếu cần hỏi sâu vào nội dung.
        """
        dense_vec = embed_dense(keyword)
        sparse_vec = embed_sparse(keyword)

        points = qdrant_utils.hybrid_search(
            collection=config_object.COLLECTION_ARCHIVES,
            dense_vec=dense_vec,
            sparse_vec=sparse_vec,
            limit=top_k,
        )

        profiles = [
            {
                "archive_id": p.payload.get("archive_id"),
                "title": p.payload.get("title"),
                "arcFileCode": p.payload.get("arcFileCode"),
                "boxCode": p.payload.get("boxCode"),
                "warehouseName": p.payload.get("warehouseName"),
                "startDate": p.payload.get("startDate"),
                "endDate": p.payload.get("endDate"),
                "staffMetadata": p.payload.get("staffMetadata"),
                "score": round(p.score, 4),
            }
            for p in points
        ]

        return {
            "keyword": keyword,
            "total_found": len(profiles),
            "profiles": profiles,
        }

    @staticmethod
    async def get_profile_detail(archive_id: str, question: str, top_k: int = 5) -> dict:
        """
        Trả lời câu hỏi chi tiết TRONG PHẠM VI 1 hồ sơ cụ thể (VD: "tốt
        nghiệp năm nào"). Search trên các chunk nội dung PDF đã được
        extract/OCR sẵn, filter CỨNG theo archive_id -> không lẫn thông
        tin giữa các hồ sơ khác nhau.

        Lưu ý: MCP chỉ làm nhiệm vụ RETRIEVAL - trả về các đoạn văn bản
        liên quan nhất kèm nguồn (file_url, page_number). Việc tổng hợp
        thành câu trả lời tự nhiên ("Năm 2015") là do LLM phía chatbot
        đảm nhận (tầng Generation của RAG), không phải việc của MCP server.
        """
        dense_vec = embed_dense(question)
        sparse_vec = embed_sparse(question)

        archive_filter = models.Filter(
            must=[models.FieldCondition(key="archive_id", match=models.MatchValue(value=archive_id))]
        )

        points = qdrant_utils.hybrid_search(
            collection=config_object.COLLECTION_CHUNKS,
            dense_vec=dense_vec,
            sparse_vec=sparse_vec,
            limit=top_k,
            query_filter=archive_filter,
        )

        if not points:
            return {
                "archive_id": archive_id,
                "question": question,
                "found": False,
                "message": "Không tìm thấy nội dung liên quan trong hồ sơ này.",
                "chunks": [],
            }

        chunks = [
            {
                "text": p.payload.get("text"),
                "file_url": p.payload.get("file_url"),
                "page_number": p.payload.get("page_number"),
                "extraction_method": p.payload.get("extraction_method"),
                "score": round(p.score, 4),
            }
            for p in points
        ]

        return {
            "archive_id": archive_id,
            "question": question,
            "found": True,
            "chunks": chunks,
        }
