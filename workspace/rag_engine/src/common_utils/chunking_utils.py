"""
Chunking theo câu (sentence-aware) thay vì cắt cứng ký tự, tránh cắt
ngang giữa 1 câu làm mất ngữ nghĩa (VD: cắt ngay giữa "tốt nghiệp năm
2015" thành 2 chunk khác nhau).
"""
import re
from config.configs import config_object

_SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list:
    text = text.strip()
    if not text:
        return []
    sentences = _SENTENCE_SPLIT_REGEX.split(text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_pages(pages: list, chunk_size: int = None, overlap_sentences: int = None) -> list:
    """
    pages: list[str] text theo từng trang PDF.
    Trả về: list[{"text": str, "page_number": int}]
    """
    chunk_size = chunk_size or config_object.CHUNK_SIZE_CHARS
    overlap_sentences = overlap_sentences if overlap_sentences is not None else config_object.CHUNK_OVERLAP_SENTENCES

    chunks = []
    current_sentences = []
    current_len = 0
    current_page = 1

    for page_no, page_text in enumerate(pages, start=1):
        for sentence in split_sentences(page_text):
            if current_sentences and current_len + len(sentence) > chunk_size:
                chunks.append({"text": " ".join(current_sentences), "page_number": current_page})
                current_sentences = current_sentences[-overlap_sentences:] if overlap_sentences > 0 else []
                current_len = sum(len(s) for s in current_sentences)
                current_page = page_no

            if not current_sentences:
                current_page = page_no

            current_sentences.append(sentence)
            current_len += len(sentence)

    if current_sentences:
        chunks.append({"text": " ".join(current_sentences), "page_number": current_page})

    return chunks
