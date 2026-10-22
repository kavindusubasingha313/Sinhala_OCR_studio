"""Document storage and engine contracts, independent of the interface."""
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol
import json
import os
import tempfile

from docx import Document as WordDocument
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pypdf import PdfReader
from PIL import Image


@dataclass
class Recognition:
    text: str
    engine: str
    # Unknown confidence is distinct from high confidence.
    confidence: float | None = None


class OcrEngine(Protocol):
    def recognize(self, image: Path) -> Recognition: ...


class TesseractEngine:
    def recognize(self, image: Path) -> Recognition:
        import pytesseract
        available = set(pytesseract.get_languages())
        if not {"sin", "eng"} <= available:
            raise RuntimeError("Install Tesseract Sinhala (sin) and English (eng) language data.")
        with Image.open(image) as source:
            return Recognition(pytesseract.image_to_string(source, lang="sin+eng"), "tesseract")


@dataclass
class Document:
    source: str
    text: str = ""
    approved: bool = False

    def apply_recognition(self, result: Recognition) -> None:
        # Every edit is protected, even before explicit approval.
        if self.text or self.approved:
            raise ValueError("Existing text is protected. Open a new document to rerun OCR.")
        self.text = result.text


def import_document(path: Path) -> Document:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(path)
        return Document(str(path), "\n\n".join(page.extract_text() or "" for page in reader.pages))
    with Image.open(path) as image:
        image.verify()
    return Document(str(path))


def atomic_write(destination: Path, writer, validator) -> None:
    handle, temporary = tempfile.mkstemp(dir=destination.parent, suffix=destination.suffix)
    os.close(handle)
    path = Path(temporary)
    try:
        writer(path)
        validator(path)
        with path.open("rb") as stream:
            os.fsync(stream.fileno())
        os.replace(path, destination)
    finally:
        path.unlink(missing_ok=True)


def save_project(document: Document, destination: Path) -> None:
    atomic_write(destination,
                 lambda p: p.write_text(json.dumps(asdict(document), ensure_ascii=False), encoding="utf-8"),
                 lambda p: Document(**json.loads(p.read_text(encoding="utf-8"))))


def load_project(path: Path) -> Document:
    return Document(**json.loads(path.read_text(encoding="utf-8")))


def export_document(document: Document, destination: Path) -> None:
    if Path(document.source).resolve() == destination.resolve():
        raise ValueError("Export cannot overwrite the source document.")
    if destination.suffix.lower() == ".txt":
        def validate(path):
            if path.read_text(encoding="utf-8") != document.text:
                raise ValueError("Text integrity check failed")
        atomic_write(destination, lambda p: p.write_text(document.text, encoding="utf-8"), validate)
    elif destination.suffix.lower() == ".docx":
        def write(path):
            word = WordDocument()
            for line in document.text.split("\n"):
                run = word.add_paragraph().add_run(line)
                run.font.name = "Nirmala UI"
                fonts = run._element.get_or_add_rPr().rFonts
                fonts.set(qn("w:cs"), "Nirmala UI")
                language = OxmlElement("w:lang")
                language.set(qn("w:bidi"), "si-LK")
                run._element.get_or_add_rPr().append(language)
            word.save(path)
        def validate(path):
            word = WordDocument(path)
            if "\n".join(p.text for p in word.paragraphs) != document.text:
                raise ValueError("DOCX text integrity check failed")
        atomic_write(destination, write, validate)
    else:
        raise ValueError("Stage 1 supports TXT and DOCX exports only.")
