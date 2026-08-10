import pymupdf

MIN_TEXT_LENGTH = 20  # below this, treat the PDF as having no usable text layer


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Direct text-layer extraction. Returns "" for a scanned/image-only PDF
    with no embedded text -- callers should fall back to OCR in that case."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        return "\n".join(page.get_text() for page in doc).strip()
    finally:
        doc.close()


def render_pdf_pages_to_images(pdf_bytes: bytes, max_pages: int = 5, dpi: int = 200) -> list:
    """Rasterize PDF pages to PNG bytes, for OCR fallback on scanned PDFs."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        images = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(dpi=dpi)
            images.append(pix.tobytes("png"))
        return images
    finally:
        doc.close()


def has_usable_text(text: str) -> bool:
    return len(text.strip()) >= MIN_TEXT_LENGTH
