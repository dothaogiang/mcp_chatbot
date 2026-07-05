"""
embed_profiles.py: chịu trách nhiệm sinh vector cho METADATA của từng hồ
sơ (archive), tách riêng khỏi ingest.py để dễ đọc - ingest.py lo việc
fetch/vòng lặp/điều phối, embed_profiles.py lo việc "biến 1 archive thành
vector".
"""
from common_utils.embedding_utils import embed_dense, embed_sparse
from common_utils import qdrant_utils


def build_archive_search_text(archive: dict) -> str:
    """Gộp field metadata thành 1 đoạn text tự nhiên để embed."""
    staff_lines = "; ".join(
        f"{m.get('fieldName', '')}: {m.get('value', '')}" for m in (archive.get("staffMetadata") or [])
    )
    project_names = "; ".join(p.get("name", "") for p in (archive.get("projects") or []))
    parts = [
        f"Tiêu đề: {archive.get('title', '')}",
        f"Mã hồ sơ: {archive.get('arcFileCode', '')}",
        f"Kho: {archive.get('warehouseName', '')}",
        f"Thời gian: {archive.get('startDate', '')} - {archive.get('endDate', '')}",
        f"Thông tin cán bộ: {staff_lines}" if staff_lines else "",
        f"Tài liệu: {project_names}" if project_names else "",
    ]
    return ". ".join(p for p in parts if p)


def embed_and_upsert_archive(archive: dict):
    """Sinh dense+sparse vector cho 1 archive rồi upsert vào collection 'archives'."""
    search_text = build_archive_search_text(archive)
    dense_vec = embed_dense(search_text)
    sparse_vec = embed_sparse(search_text)

    payload = {
        "archive_id": archive["id"],
        "title": archive.get("title"),
        "arcFileCode": archive.get("arcFileCode"),
        "boxCode": archive.get("boxCode"),
        "warehouseName": archive.get("warehouseName"),
        "startDate": archive.get("startDate"),
        "endDate": archive.get("endDate"),
        "status": archive.get("status"),
        "staffMetadata": archive.get("staffMetadata"),
    }
    qdrant_utils.upsert_archive(archive["id"], dense_vec, sparse_vec, payload)
