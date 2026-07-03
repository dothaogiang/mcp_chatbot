# MCP Server: Tra cứu Hồ sơ Lưu trữ (Hybrid Search + RAG)

## Kiến trúc tổng quan

```
Chatbot (bên khác làm) --MCP protocol--> MCP Server (dự án này)
                                              │
                          ┌───────────────────┴───────────────────┐
                          │                                        │
                  search_profile                          get_profile_detail
              (tìm hồ sơ theo keyword)                (trả lời câu hỏi TRONG 1 hồ sơ)
                          │                                        │
                Qdrant collection                        Qdrant collection
                  "archives"                              "document_chunks"
              (metadata: title, mã hồ sơ,                (text trích/OCR từ PDF,
               staffMetadata...)                          filter theo archive_id)
                          ▲                                        ▲
                          └────────────────┬───────────────────────┘
                                            │
                              ingestion/sync_job.py (cron)
                                            │
                              Archive API thật (192.168.1.46:4000)
                              + tải PDF từ fileUrls + OCR nếu cần
```

Hai tool độc lập, dùng đúng lúc:
- `search_profile`: tìm ĐÚNG hồ sơ nào (trả về `archive_id`).
- `get_profile_detail`: dùng `archive_id` đó để hỏi sâu vào nội dung PDF bên trong hồ sơ.

## Cơ chế "sửa tool không cần sửa code"

Toàn bộ định nghĩa tool nằm ở `Resources/tools.yaml`. `ToolRegistry`
(`src/tools/registry.py`) tự động:
1. Đọc `tools.yaml` qua `CustomToolManager`.
2. Với mỗi `name_tool`, tìm method **cùng tên** trong `FeatureManager`
   (`src/feature_manager.py`) bằng `getattr`.
3. Build `Tool` object cho FastMCP.

**Muốn thêm tool mới**: viết 1 method `@staticmethod async def ten_tool(...)`
trong `FeatureManager`, thêm entry cùng tên trong `tools.yaml`. Không đụng
`registry.py`/`server.py`.

**Muốn sửa mô tả/tham số tool**: chỉ sửa `tools.yaml`.

**Muốn xóa tool**: xóa entry trong `tools.yaml` (có thể để nguyên method
trong FeatureManager, nó sẽ đơn giản không được đăng ký nữa).

---

## Bước 1 — Cài đặt môi trường local (không dùng Docker)

```bash
cd mcp_profile_lookup
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Cài Tesseract OCR tiếng Việt (bắt buộc cho PDF scan)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-vie
# macOS:
brew install tesseract tesseract-lang
```

## Bước 2 — Cấu hình

```bash
cp .env.example .env
# Mở .env, chỉnh lại ARCHIVE_API_BASE_URL nếu địa chỉ API thay đổi
```

## Bước 3 — Chạy Qdrant (vector database)

```bash
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

Kiểm tra Qdrant chạy OK: mở http://localhost:6333/dashboard

## Bước 4 — Chạy đồng bộ dữ liệu lần đầu (ingest)

```bash
cd src
python ingestion/sync_job.py
```

Lần chạy đầu sẽ:
- Tự tạo 2 collection `archives` và `document_chunks` trong Qdrant.
- Gọi Archive API phân trang, với mỗi hồ sơ: embed metadata, tải PDF,
  tự phát hiện PDF text thật hay scan, OCR nếu cần, chunk, embed, upsert.
- Lưu trạng thái vào `sync_state.db` (SQLite) để lần sau chỉ đồng bộ phần thay đổi.

⚠️ **Lưu ý quan trọng trước khi chạy full dataset**: vì chưa rõ tổng số
hồ sơ/PDF, nên **test thử với 1 page trước** để đo thời gian:

```bash
# Tạm sửa ARCHIVE_API_PAGE_SIZE=5 trong .env để chạy thử nhanh,
# đo thời gian trung bình/archive rồi ước tính tổng thời gian full run,
# đặc biệt phần OCR (bước tốn thời gian nhất).
```

Nếu job bị dừng giữa chừng (Ctrl+C, mất mạng...), chạy lại
`python ingestion/sync_job.py` sẽ **tự resume** từ page cuối cùng
thành công (nhờ checkpoint trong `sync_state.db`), không chạy lại từ đầu.

## Bước 5 — Chạy MCP server

```bash
python server.py
```

Server chạy ở `http://0.0.0.0:8090` (transport `streamable-http`), sẵn
sàng cho chatbot kết nối vào.

## Bước 6 — Đặt lịch đồng bộ định kỳ (cron)

**Cách A - crontab (Linux):**
```bash
crontab -e
# Chạy mỗi giờ:
0 * * * * cd /path/to/mcp_profile_lookup/src && /path/to/venv/bin/python ingestion/sync_job.py >> /var/log/sync_job.log 2>&1
```

**Cách B - Docker Compose (khuyến nghị, có sẵn service `sync_cron`):**
```bash
docker compose up -d
```
File `docker-compose.yaml` đã định nghĩa 3 service: `qdrant`, `mcp_server`,
`sync_cron` (tự lặp `sync_job.py` mỗi giờ — chỉnh `sleep 3600` nếu cần
tần suất khác).

---

## Test nhanh tool bằng tay (không cần chatbot)

```python
import asyncio
from feature_manager import FeatureManager

async def test():
    result = await FeatureManager.search_profile(keyword="Trần Xuân Sang")
    print(result)

    if result["profiles"]:
        archive_id = result["profiles"][0]["archive_id"]
        detail = await FeatureManager.get_profile_detail(
            archive_id=archive_id,
            question="tốt nghiệp năm nào"
        )
        print(detail)

asyncio.run(test())
```

## Các điểm cần lưu ý khi vận hành

| Vấn đề | Cách xử lý đã có sẵn |
|---|---|
| PDF vừa text thật vừa scan lẫn lộn | Auto-detect theo mật độ ký tự/trang, fallback OCR |
| Cron chạy lại nhiều lần | Idempotent (point ID xác định) + skip nếu `updatedAt`/hash file không đổi |
| Job bị crash giữa chừng | Checkpoint theo page, resume tự động |
| Volume dữ liệu chưa rõ | `OCR_CONCURRENCY` giới hạn số OCR chạy song song, tránh quá tải |
| Thêm/sửa/xóa tool | Chỉ sửa `Resources/tools.yaml` (+ method trong `feature_manager.py` nếu là tool mới) |

## Việc cần làm tiếp (chưa nằm trong phạm vi code này)

- **Access control**: MCP server hiện chưa có xác thực — cần trao đổi
  với lead về việc có giới hạn ai được gọi tool này hay không, vì dữ
  liệu chứa thông tin cá nhân.
- **Đo hiệu năng thật**: chạy pilot ingest với dữ liệu thật để biết
  tổng thời gian/OCR trước khi giao cho chatbot dùng production.
