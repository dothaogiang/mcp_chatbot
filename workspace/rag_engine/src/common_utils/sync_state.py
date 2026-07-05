"""
Lưu trạng thái đồng bộ (archive nào đã sync, file nào đã đổi) bằng SQLite
nhỏ gọn. Mục đích: cron chạy lại KHÔNG phải OCR/embedding lại toàn bộ dữ
liệu chưa thay đổi - OCR là bước đắt nhất trong pipeline.
"""
import sqlite3
import contextlib
import os
from config.configs import config_object

SCHEMA = """
CREATE TABLE IF NOT EXISTS archive_sync (
    archive_id TEXT PRIMARY KEY,
    last_updated_at TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS file_sync (
    archive_id TEXT NOT NULL,
    file_url TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    extraction_method TEXT,
    chunk_count INTEGER,
    synced_at TEXT NOT NULL,
    PRIMARY KEY (archive_id, file_url)
);

CREATE TABLE IF NOT EXISTS sync_checkpoint (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_page INTEGER DEFAULT 0
);
"""


@contextlib.contextmanager
def get_conn():
    os.makedirs(os.path.dirname(config_object.SYNC_DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(config_object.SYNC_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR IGNORE INTO sync_checkpoint (id, last_page) VALUES (1, 0)")


def get_archive_last_updated(archive_id: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT last_updated_at FROM archive_sync WHERE archive_id = ?", (archive_id,)
        ).fetchone()
        return row["last_updated_at"] if row else None


def set_archive_synced(archive_id: str, updated_at: str):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO archive_sync (archive_id, last_updated_at, synced_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(archive_id) DO UPDATE SET
                 last_updated_at = excluded.last_updated_at,
                 synced_at = excluded.synced_at""",
            (archive_id, updated_at),
        )


def get_file_hash(archive_id: str, file_url: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT content_hash FROM file_sync WHERE archive_id = ? AND file_url = ?",
            (archive_id, file_url),
        ).fetchone()
        return row["content_hash"] if row else None


def set_file_synced(archive_id: str, file_url: str, content_hash: str, extraction_method: str, chunk_count: int):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO file_sync (archive_id, file_url, content_hash, extraction_method, chunk_count, synced_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(archive_id, file_url) DO UPDATE SET
                 content_hash = excluded.content_hash,
                 extraction_method = excluded.extraction_method,
                 chunk_count = excluded.chunk_count,
                 synced_at = excluded.synced_at""",
            (archive_id, file_url, content_hash, extraction_method, chunk_count),
        )


def get_checkpoint_page() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT last_page FROM sync_checkpoint WHERE id = 1").fetchone()
        return row["last_page"] if row else 0


def set_checkpoint_page(page: int):
    with get_conn() as conn:
        conn.execute("UPDATE sync_checkpoint SET last_page = ? WHERE id = 1", (page,))


def reset_checkpoint():
    with get_conn() as conn:
        conn.execute("UPDATE sync_checkpoint SET last_page = 0 WHERE id = 1")
