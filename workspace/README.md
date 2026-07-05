# Profile Lookup: 2 project độc lập (rag_engine + mcp_profile_lookup)

## Vì sao 2 project riêng biệt, không phải 1 repo chia package

```
┌──────────────────────────┐          ┌──────────────────────────┐
│  rag_engine/              │          │  mcp_profile_lookup/      │
│  (project TỰ TRỊ riêng)   │          │  (giữ đúng khung mẫu sếp)  │
│                            │          │                            │
│  - Có requirements.txt     │          │  - Có requirements.txt     │
│    riêng                   │◄──HTTP──│    riêng                   │
│  - Có docker-compose        │          │  - Có docker-compose        │
│    riêng (Qdrant + API +    │          │    riêng (chỉ MCP server)   │
│    cron sync)                │          │                            │
│  - Expose port 8091          │          │  - Expose port 8090          │
│  - Có thể deploy/scale/       │          │  - Không biết gì về           │
│    update HOÀN TOÀN độc lập   │          │    Qdrant/embedding/rerank    │
└──────────────────────────┘          └──────────────────────────┘
```

Khác với lần tách trước (rag/ và mcp_server/ là 2 package Python trong
CÙNG 1 repo, share import), lần này 2 project là **2 codebase hoàn toàn
tách rời**, giao tiếp thuần qua HTTP (REST API). Điều này khớp đúng ý
"tự trị" (autonomous): mỗi project có thể:
- Clone/deploy riêng, không cần code của project kia.
- Đổi ngôn ngữ/framework bên trong (VD: RAG đổi sang Node.js) mà MCP
  không hề biết, miễn là API contract (`/search_profile`, `/profile_detail`)
  giữ nguyên.
- Scale độc lập (RAG cần nhiều CPU/RAM cho OCR+embedding, MCP thì nhẹ,
  chỉ forward request).

## `mcp_profile_lookup/` — giữ ĐÚNG khung mẫu sếp đưa

```
mcp_profile_lookup/
├── src/
│   ├── server.py
│   ├── feature_manager.py        # ProfileFeatureManager.search_profile()
│   ├── logger.py
│   ├── config/configs.py
│   ├── common_utils/
│   │   ├── constants.py
│   │   └── rag_client.py         # gọi HTTP sang rag_engine (thay cho search_utils.py)
│   └── tools/
│       ├── manager.py
│       └── registry.py
├── Resources/
│   └── tools.yaml
├── docker-compose.yaml
├── Dockerfile
└── requirements.txt
```

**Điểm khác duy nhất so với khung mẫu bạn đưa**: không còn
`ingestion/embed_profiles.py` + `ingest.py` (đã chuyển hết sang
`rag_engine/`), và `common_utils/search_utils.py` (embed_dense/embed_sparse)
đổi thành `common_utils/rag_client.py` (gọi HTTP) — vì bản chất MCP giờ
không tự làm search nữa, chỉ forward request sang RAG Engine.

## `rag_engine/` — project tự trị hoàn toàn

```
rag_engine/
├── src/
│   ├── main.py                    # FastAPI - expose /search_profile, /profile_detail
│   ├── retriever.py                # logic nghiệp vụ (hybrid search + rerank)
│   ├── logger.py
│   ├── config/configs.py
│   ├── common_utils/
│   │   ├── constants.py
│   │   ├── embedding_utils.py      # dense (BGE-M3) + sparse (BM25)
│   │   ├── reranker_utils.py       # cross-encoder rerank
│   │   ├── pdf_utils.py            # native extract + OCR tiếng Việt
│   │   ├── chunking_utils.py       # chunk theo câu (sentence-aware)
│   │   ├── qdrant_utils.py         # vector store wrapper
│   │   └── sync_state.py           # SQLite, incremental sync
│   └── ingestion/
│       ├── embed_profiles.py       # sinh vector cho từng hồ sơ (đúng như mẫu)
│       └── ingest.py               # điều phối chính: fetch API -> OCR -> chunk -> embed -> upsert
├── eval/                            # đánh giá offline chất lượng RAG
│   ├── test_questions.yaml
│   └── run_eval.py
├── docker-compose.yaml              # Qdrant + rag_api + rag_sync (đủ bộ, tự chạy được)
├── Dockerfile
└── requirements.txt
```

## Chạy cả 2 project cùng lúc (local dev)

**Bước 1 - Chạy rag_engine trước (nó phải sẵn sàng trước khi MCP gọi vào):**

```bash
cd rag_engine
cp .env.example .env
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
sudo apt-get install tesseract-ocr tesseract-ocr-vie   # OCR tiếng Việt

# Chạy Qdrant
docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant:latest

# Ingest dữ liệu lần đầu (test với page nhỏ trước, xem README riêng)
cd src && python ingestion/ingest.py

# Chạy HTTP API
uvicorn main:app --host 0.0.0.0 --port 8091
```

Kiểm tra RAG Engine sống: `curl http://localhost:8091/health` → `{"status": "ok"}`

**Bước 2 - Chạy mcp_profile_lookup (project khác, terminal khác):**

```bash
cd mcp_profile_lookup
cp .env.example .env    # RAG_SERVICE_URL=http://localhost:8091 (mặc định đã đúng)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cd src && python server.py
```

MCP server chạy port 8090, sẵn sàng cho chatbot kết nối vào — mọi request
tool sẽ được forward sang `rag_engine` qua HTTP.

## Chạy bằng Docker (mỗi project tự `docker compose up -d` riêng)

```bash
# Terminal 1
cd rag_engine && docker compose up -d

# Terminal 2 (sau khi rag_engine đã chạy)
cd mcp_profile_lookup && docker compose up -d
```

`mcp_profile_lookup/docker-compose.yaml` dùng `host.docker.internal:8091`
để gọi sang container của `rag_engine` — nếu deploy lên server thật
(không phải Docker Desktop), sửa `RAG_SERVICE_URL` thành IP/domain thật
của RAG Engine.

## Test nhanh RAG Engine độc lập, không cần MCP

```bash
curl -X POST http://localhost:8091/search_profile \
  -H "Content-Type: application/json" \
  -d '{"keyword": "Trần Xuân Sang", "top_k": 10}'

curl -X POST http://localhost:8091/profile_detail \
  -H "Content-Type: application/json" \
  -d '{"archive_id": "50000000-0000-0000-0000-000000000002", "question": "tốt nghiệp năm nào"}'
```

## Chạy eval (đo chất lượng RAG)

```bash
cd rag_engine
python eval/run_eval.py
```

Cần điền `archive_id` thật + đáp án kỳ vọng vào `eval/test_questions.yaml`
sau khi đã ingest dữ liệu thật.

## Cách thêm/sửa/xóa tool MCP

1. Sửa `mcp_profile_lookup/Resources/tools.yaml`.
2. Nếu tool mới cần logic RAG mới: thêm hàm trong `rag_engine/src/retriever.py`
   + endpoint mới trong `rag_engine/src/main.py`, rồi thêm method gọi HTTP
   tương ứng trong `mcp_profile_lookup/src/common_utils/rag_client.py` +
   `feature_manager.py`.
3. Không đụng `registry.py`, `manager.py`, `server.py` của MCP.

## Việc cần làm tiếp

- Chạy pilot ingest với dữ liệu thật để đo thời gian OCR trước khi chạy full.
- Điền `eval/test_questions.yaml` với dữ liệu thật, chạy định kỳ khi đổi
  model embedding/rerank/chunking.
- Trao đổi với lead về access control giữa 2 service (RAG Engine hiện
  không có xác thực — nếu expose ra ngoài mạng nội bộ cần thêm API key
  hoặc giới hạn network để chỉ MCP server gọi được vào).
