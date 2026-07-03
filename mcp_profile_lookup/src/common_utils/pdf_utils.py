"""
Trích xuất text từ PDF, TỰ ĐỘNG phát hiện PDF text thật vs PDF scan
(vì dữ liệu thực tế có cả hai loại lẫn lộn - xem projects[].fileUrls
trong Archive API).

Cách phát hiện: thử extract text trực tiếp trước (rẻ, nhanh). Nếu mật độ
ký tự/trang quá thấp (dấu hiệu PDF chỉ chứa ảnh scan) -> fallback OCR
tiếng Việt bằng pytesseract.
"""
import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from config.configs import config_object
from common_utils.constants import EXTRACTION_NATIVE, EXTRACTION_OCR
from logger import get_logger

logger = get_logger(__name__)


def _ocr_page(page: "fitz.Page") -> str:
    pix = page.get_pixmap(dpi=config_object.OCR_DPI)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img, lang=config_object.OCR_LANG)


def extract_text_from_pdf(pdf_bytes: bytes):
    """
    Trả về (danh_sach_text_theo_trang: list[str], extraction_method: str).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    native_pages = [page.get_text() for page in doc]
    total_chars = sum(len(p.strip()) for p in native_pages)
    avg_chars_per_page = total_chars / max(len(doc), 1)

    if avg_chars_per_page >= config_object.OCR_MIN_CHARS_PER_PAGE:
        logger.info(f"PDF text thật (avg {avg_chars_per_page:.0f} ký tự/trang) -> dùng native extract")
        return native_pages, EXTRACTION_NATIVE

    logger.info(f"PDF nghi là scan (avg {avg_chars_per_page:.0f} ký tự/trang) -> chạy OCR")
    ocr_pages = []
    for i, page in enumerate(doc):
        try:
            ocr_pages.append(_ocr_page(page))
        except Exception as e:
            logger.error(f"OCR lỗi tại trang {i}: {e}")
            ocr_pages.append("")
    return ocr_pages, EXTRACTION_OCR


def chunk_text(pages: list, chunk_size: int = None, overlap: int = None) -> list:
    """
    Gộp text các trang rồi chia chunk theo ký tự, có overlap để giữ ngữ
    cảnh ở ranh giới chunk. Mỗi chunk giữ lại page_number gần đúng để
    trích dẫn nguồn khi trả kết quả.
    """
    chunk_size = chunk_size or config_object.CHUNK_SIZE_CHARS
    overlap = overlap or config_object.CHUNK_OVERLAP_CHARS

    full_text = ""
    char_to_page = []
    for page_no, page_text in enumerate(pages, start=1):
        full_text += page_text
        char_to_page.extend([page_no] * len(page_text))

    full_text = full_text.strip()
    if not full_text:
        return []

    chunks = []
    start = 0
    while start < len(full_text):
        end = min(start + chunk_size, len(full_text))
        chunk_str = full_text[start:end].strip()
        if chunk_str:
            page_idx = min(start, len(char_to_page) - 1) if char_to_page else 0
            page_number = char_to_page[page_idx] if char_to_page else 1
            chunks.append({"text": chunk_str, "page_number": page_number})
        if end == len(full_text):
            break
        start = end - overlap
    return chunks
