"""
FastAPI app - đây là RANH GIỚI DUY NHẤT giữa rag_engine và mcp_profile_lookup.
mcp_profile_lookup KHÔNG import bất kỳ module Python nào của rag_engine,
chỉ gọi HTTP vào 2 endpoint dưới đây.

Chạy: uvicorn main:app --host 0.0.0.0 --port 8091 --app-dir src
"""
from fastapi import FastAPI
from pydantic import BaseModel
import retriever
from logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="RAG Engine - Profile Lookup", version="1.0.0")


class SearchProfileRequest(BaseModel):
    keyword: str
    top_k: int = 20


class ProfileDetailRequest(BaseModel):
    archive_id: str
    question: str
    top_k: int = 5


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/search_profile")
def search_profile_endpoint(req: SearchProfileRequest):
    return retriever.search_profile(keyword=req.keyword, top_k=req.top_k)


@app.post("/profile_detail")
def profile_detail_endpoint(req: ProfileDetailRequest):
    return retriever.search_profile_detail(
        archive_id=req.archive_id, question=req.question, top_k=req.top_k
    )
