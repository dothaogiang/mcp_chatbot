"""
ingest.py: điều phối chính của pipeline ingestion, chạy 1 lần hoặc định kỳ.

Chạy thủ công: cd src && python ingestion/ingest.py
Chạy định kỳ:  crontab / docker-compose service "rag_sync".

Cơ chế incremental (tránh OCR/embedding lại toàn bộ mỗi lần chạy):
  - Archive: so sánh `updatedAt` với lần sync trước -> bỏ qua nếu không đổi.
  - File PDF: hash nội dung tải về (MD5) -> bỏ qua OCR nếu file không đổi.
  - Checkpoint theo page: job bị crash giữa chừng -> resume từ page cuối cùng.
"""
import asyncio
import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

from config.configs import config_object
from common_utils import sync_state, qdrant_utils
from common_utils.pdf_utils import extract_text_from_pdf
from common_utils.chunking_utils import chunk_pages
from common_utils.embedding_utils import embed_dense_batch, embed_sparse_batch
from ingestion.embed_profiles import embed_and_upsert_archive
from logger import get_logger

logger = get_logger(__name__)

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


async def sync_file(client: httpx.AsyncClient, archive: dict, project: dict, file_url: str):
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
        chunks = chunk_pages(pages)

        if not chunks:
            logger.warning(f"Không trích được text từ: {file_url}")
            sync_state.set_file_synced(archive_id, file_url, content_hash, method, 0)
            return

        texts = [c["text"] for c in chunks]
        dense_vecs = embed_dense_batch(texts)
        sparse_vecs = embed_sparse_batch(texts)

        qdrant_utils.delete_chunks_by_file(archive_id, file_url)
        qdrant_utils.upsert_chunks(
            archive_id=archive_id,
            file_url=file_url,
            chunks=chunks,
            dense_vecs=dense_vecs,
            sparse_vecs=sparse_vecs,
            extra_payload={"project_name": project.get("name"), "extraction_method": method},
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

    embed_and_upsert_archive(archive)

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
