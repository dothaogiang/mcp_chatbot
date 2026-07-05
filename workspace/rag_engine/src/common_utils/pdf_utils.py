"""
Trích xuất text từ PDF, TỰ ĐỘNG phát hiện PDF text thật vs PDF scan. Nếu
mật độ ký tự/trang quá thấp -> fallback OCR tiếng Việt.
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
    """Trả về (danh_sach_text_theo_trang: list[str], extraction_method: str)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    native_pages = [page.get_text() for page in doc]
    total_chars = sum(len(p.strip()) for p in native_pages)
    avg_chars_per_page = total_chars / max(len(doc), 1)

    if avg_chars_per_page >= config_object.OCR_MIN_CHARS_PER_PAGE:
        logger.info(f"PDF text thật (avg {avg_chars_per_page:.0f} ký tự/trang) -> native extract")
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
