"""
Cron job đồng bộ dữ liệu từ Archive API -> Qdrant.

Chạy thủ công: python src/ingestion/sync_job.py
Chạy định kỳ:  đặt trong crontab / APScheduler / k8s CronJob (VD: mỗi giờ).

Cơ chế incremental (tránh OCR/embedding lại toàn bộ mỗi lần chạy):
  - Archive: so sánh field `updatedAt` với lần sync trước -> bỏ qua nếu
    không đổi.
  - File PDF: hash nội dung tải về (MD5), so sánh với hash đã lưu -> bỏ
    qua OCR nếu file không đổi (OCR là bước đắt nhất trong pipeline).
  - Checkpoint theo page: nếu job bị crash giữa chừng (mất mạng, OCR
    timeout...), lần chạy sau resume từ page cuối cùng thành công thay
    vì chạy lại từ đầu toàn bộ.
"""
import asyncio
import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

from config.configs import config_object
from common_utils import sync_state, qdrant_utils
from common_utils.pdf_utils import extract_text_from_pdf, chunk_text
from common_utils.embedding_utils import embed_dense, embed_sparse, embed_dense_batch, embed_sparse_batch
from logger import get_logger

logger = get_logger(__name__)

# Giới hạn số file OCR chạy song song, tránh quá tải CPU/RAM khi volume lớn
ocr_semaphore = asyncio.Semaphore(config_object.OCR_CONCURRENCY)


async def fetch_archives_page(client: httpx.AsyncClient, page: int) -> dict:
    url = f"{config_object.ARCHIVE_API_BASE_URL}{config_object.ARCHIVE_API_PATH}"
    resp = await client.get(
        url,
        params={"page": page, "size": config_object.ARCHIVE_API_PAGE_SIZE},
        timeout=config_object.HTTP_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()


def build_archive_search_text(archive: dict) -> str:
    """Gộp field metadata thành 1 đoạn text tự nhiên để embed cho search_profile."""
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


async def sync_archive_metadata(archive: dict):
    """Upsert metadata của 1 archive vào collection 'archives' (tầng search_profile)."""
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


async def sync_file(client: httpx.AsyncClient, archive: dict, project: dict, file_url: str):
    """Xử lý 1 file PDF: kiểm tra thay đổi -> extract/OCR -> chunk -> embed -> upsert."""
    archive_id = archive["id"]

    async with ocr_semaphore:
        try:
            resp = await client.get(file_url, timeout=config_object.HTTP_TIMEOUT_SECONDS)
            resp.raise_for_status()
            pdf_bytes = resp.content
        except Exception as e:
            logger.error(f"Không tải được file {file_url}: {e}")
            return

        content_hash = hashlib.md5(pdf_bytes).hexdigest()
        old_hash = sync_state.get_file_hash(archive_id, file_url)
        if old_hash == content_hash:
            logger.info(f"File không đổi, bỏ qua: {file_url}")
            return

        logger.info(f"Đang extract: {file_url}")
        pages, method = extract_text_from_pdf(pdf_bytes)
        chunks = chunk_text(pages)

        if not chunks:
            logger.warning(f"Không trích được text từ: {file_url}")
            sync_state.set_file_synced(archive_id, file_url, content_hash, method, 0)
            return

        texts = [c["text"] for c in chunks]
        dense_vecs = embed_dense_batch(texts)
        sparse_vecs = embed_sparse_batch(texts)

        # Xóa chunk cũ trước khi upsert mới, tránh chunk rác nếu file rút gọn nội dung
        qdrant_utils.delete_chunks_by_file(archive_id, file_url)
        qdrant_utils.upsert_chunks(
            archive_id=archive_id,
            file_url=file_url,
            chunks=chunks,
            dense_vecs=dense_vecs,
            sparse_vecs=sparse_vecs,
            extra_payload={
                "project_name": project.get("name"),
                "extraction_method": method,
            },
        )
        sync_state.set_file_synced(archive_id, file_url, content_hash, method, len(chunks))
        logger.info(f"Đã đồng bộ {len(chunks)} chunk ({method}) từ: {file_url}")


async def sync_archive(client: httpx.AsyncClient, archive: dict):
    archive_id = archive["id"]
    updated_at = archive.get("updatedAt")

    last_synced = sync_state.get_archive_last_updated(archive_id)
    if last_synced == updated_at:
        logger.info(f"Archive không đổi, bỏ qua: {archive_id}")
        return

    await sync_archive_metadata(archive)

    for project in archive.get("projects") or []:
        for file_url in project.get("fileUrls") or []:
            await sync_file(client, archive, project, file_url)

    sync_state.set_archive_synced(archive_id, updated_at)


async def run_sync(resume: bool = True):
    sync_state.init_db()
    qdrant_utils.ensure_collections()

    start_page = sync_state.get_checkpoint_page() if resume else 0
    logger.info(f"Bắt đầu đồng bộ từ page {start_page}")

    async with httpx.AsyncClient() as client:
        page = start_page
        while True:
            data = await fetch_archives_page(client, page)
            archives = data.get("content", [])
            if not archives:
                break

            for archive in archives:
                try:
                    await sync_archive(client, archive)
                except Exception as e:
                    logger.error(f"Lỗi khi sync archive {archive.get('id')}: {e}")

            sync_state.set_checkpoint_page(page)

            if data.get("last", True):
                break
            page += 1

    sync_state.reset_checkpoint()
    logger.info("Đồng bộ hoàn tất.")


if __name__ == "__main__":
    asyncio.run(run_sync())
