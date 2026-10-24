"""Bounded PDF/image page access. PDFium calls are serialized across workers."""
from io import BytesIO
from pathlib import Path
from threading import RLock

from PIL import Image, ImageOps
from pypdf import PdfReader

PDF_LOCK = RLock()
MAX_PAGES = 500


def import_pages(path):
    from .core import Document, DocumentPage
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        with PDF_LOCK:
            reader = PdfReader(path)
            if reader.is_encrypted and not reader.decrypt(""):
                raise ValueError("This PDF is password-protected. Open an unlocked copy.")
            if not 0 < len(reader.pages) <= MAX_PAGES:
                raise ValueError(f"Import supports 1–{MAX_PAGES} pages per document.")
            pages = [DocumentPage(index, page.extract_text() or "") for index, page in enumerate(reader.pages)]
    else:
        with Image.open(path) as image:
            count = getattr(image, "n_frames", 1)
            if count > MAX_PAGES:
                raise ValueError(f"Import supports at most {MAX_PAGES} image frames.")
            image.seek(0)
            image.load()
        pages = [DocumentPage(index) for index in range(count)]
    document = Document(str(path), pages=pages)
    document.activate_page(0)
    return document


def render_page(source, index=0, max_edge=1800):
    """PNG pixels for the selected page/frame, independent of any GUI objects."""
    source = Path(source)
    max_edge = max(100, min(3500, int(max_edge)))
    if source.suffix.lower() == ".pdf":
        import pypdfium2 as pdfium
        with PDF_LOCK:
            pdf = pdfium.PdfDocument(str(source))
            try:
                page = pdf[index]
                try:
                    width, height = page.get_size()
                    bitmap = page.render(scale=max_edge / max(width, height))
                    try:
                        image = bitmap.to_pil().convert("RGB")
                    finally:
                        bitmap.close()
                finally:
                    page.close()
            finally:
                pdf.close()
    else:
        with Image.open(source) as raw:
            raw.seek(index)
            image = ImageOps.exif_transpose(raw).convert("RGB")
            image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
    output = BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


def recognize_page(document, page_index, force_image=False):
    """Use direct PDF text when present; OCR only the selected scanned page."""
    from .core import Recognition, TesseractEngine
    page = document.pages[page_index] if document.pages else None
    source_index = page.source_index if page else 0
    if Path(document.source).suffix.lower() == ".pdf" and not force_image:
        with PDF_LOCK:
            text = PdfReader(document.source).pages[source_index].extract_text() or ""
        if text.strip():
            return Recognition(text, "PDF selectable text")
    data = render_page(document.source, source_index, 3000)
    return TesseractEngine().recognize(BytesIO(data))
