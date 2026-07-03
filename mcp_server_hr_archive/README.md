# MCP Server HR Archive

## Giới thiệu

`mcp_server_hr_archive` là một MCP Server cấu trúc theo kiến trúc Clean Architecture và Configuration-Driven Tool Definition dành cho chatbot LangGraph. Dự án cung cấp một lớp trung gian giữa chatbot và Public Archives API, thực hiện:

- Đăng ký các công cụ MCP (`tools`) động từ `Resources/tools.yaml`
- Gọi các endpoint backend `GET /api/public/archives`, `GET /api/public/archives/{id}`, `GET /api/public/ho-so-can-bo`, `GET /api/public/files/proxy`
- Quản lý token `X-Chatbot-Token` và ánh xạ lỗi backend về exception nội bộ
- Tải và cache dữ liệu cán bộ tĩnh, chuẩn bị cho RAG/Hybrid Search
- Hỗ trợ metadata file và không trả binary trực tiếp trong tool result

## Tính năng chính

- `FastMCP` server entry point với `streamable-http`
- `Pydantic` settings và cấu hình `.env`
- `httpx` async cho backend client
- `APSscheduler` để polling tải lại dữ liệu `ho-so-can-bo`
- `Qdrant`/`bge-m3`/Hybrid Search stub cho pipeline RAG
- `Resources/tools.yaml` làm manifest để đăng ký tool động
- Docker + Docker Compose cho server và Qdrant
- Basic tests với `pytest`

## Cấu trúc thư mục

```
mcp_server_hr_archive/
├── src/
│   ├── server.py                 # Entry point, khởi tạo FastMCP + streamable-http
│   ├── logger.py
│   ├── app_context.py            # Khởi tạo singleton service/client để dùng chung
│   ├── config/settings.py        # Pydantic Settings, đọc .env
│   ├── common_utils/
│   │   ├── constants.py
│   │   └── exceptions.py
│   ├── clients/
│   │   └── archive_backend_client.py   # httpx async backend client + token + error handling
│   ├── repositories/
│   │   ├── archive_repository.py
│   │   └── staff_profile_repository.py # tải + cache ho-so-can-bo
│   ├── services/
│   │   ├── archive_service.py
│   │   ├── staff_profile_service.py
│   │   └── file_service.py
│   ├── schemas/
│   │   ├── archive.py
│   │   └── staff_profile.py
│   ├── tools/
│   │   ├── loader.py              # Load tool manifest từ Resources/tools.yaml
│   │   ├── manager.py             # Đăng ký tool với FastMCP
│   │   ├── registry.py
│   │   └── definitions/
│   │       ├── search_archive.py
│   │       ├── get_archive_detail.py
│   │       ├── search_staff_profile.py
│   │       └── get_archive_file.py
│   ├── rag/
│   │   ├── embeddings/bge_m3_embedder.py
│   │   ├── vectorstore/qdrant_client.py
│   │   ├── retrieval/hybrid_search.py
│   │   └── reranker/cross_encoder.py
│   └── scheduler/sync_staff_profiles.py
├── Resources/
│   ├── dev.yaml
│   └── tools.yaml                # Tool manifest YAML
├── tests/
│   ├── unit/
│   └── integration/
├── logs/
├── docker-compose.yaml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

## Hướng dẫn cài đặt

### 1. Chuẩn bị môi trường

- Python 3.12+
- Cài `uv` nếu chưa có

```bash
pip install uv
```

### 2. Cài dependencies

```bash
cd mcp_server_hr_archive
uv install --no-interaction
```

### 3. Sao chép file `.env`

```bash
cp .env.example .env
```

Điều chỉnh các giá trị:

- `BACKEND_BASE_URL`
- `QDRANT_URL`
- `CHATBOT_TOKEN_URL` / `CHATBOT_CLIENT_ID` / `CHATBOT_CLIENT_SECRET`

## Cách chạy

### Chạy trực tiếp

```bash
uv run python src/server.py
```

### Chạy với Docker Compose

```bash
docker compose up --build
```

Server sẽ kết nối với Qdrant nếu cấu hình `QDRANT_URL` đúng.

## `tools.yaml` và dynamic tool registration

`Resources/tools.yaml` là manifest công cụ MCP. Mỗi entry gồm:

- `category`: nhóm tool
- `name_tool`: tên tool đăng ký
- `module`: module Python chứa định nghĩa tool
- `attr`: hàm/đối tượng tool trong module
- `enabled`: bật/tắt tool
- `description`: mô tả tool
- `inputSchema`: JSON Schema để validate input

Ví dụ:

```yaml
- category: mcp
  name_tool: search_archive
  module: src.tools.definitions.search_archive
  attr: _impl
  enabled: true
  description: "Tìm kiếm hồ sơ lưu trữ theo từ khóa và bộ lọc"
  inputSchema:
    type: object
    properties:
      q:
        type: string
      page:
        type: integer
      size:
        type: integer
    required: []
```

## Test

```bash
pytest -q
```

## Ghi chú quan trọng

- Dự án hiện hỗ trợ dynamic registry từ YAML, nhưng các handler cần tồn tại dưới `src.tools.definitions`.
- `get_archive_file_info` trả metadata file, không trả binary trực tiếp.
- `GET /api/public/ho-so-can-bo` là dữ liệu JSON tĩnh và được cache.
- `ArchiveBackendClient` đã xử lý lỗi và map `404`/`500` không nhất quán thành `NotFoundError`.

## Hỗ trợ và mở rộng

- Thêm tool mới: chỉ cần cập nhật `Resources/tools.yaml` và thêm module tool trong `src.tools.definitions`
- Mở rộng schema: có thể mở rộng `inputSchema` trong YAML để gồm các trường bắt buộc/dạng mảng
- Tương lai: thêm endpoint reload manifest runtime hoặc mở rộng nhập tool theo factory
