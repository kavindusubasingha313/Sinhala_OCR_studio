from io import BytesIO
from zipfile import ZipFile

from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject
from lxml import etree

from sinhala_ocr.core import import_document, export_document, save_project, load_project
from sinhala_ocr.documents import render_page
from sinhala_ocr.equations import Equation


def colored_pdf(path):
    writer = PdfWriter()
    for width, height, color in [(300, 400, b"1 0 0"), (400, 300, b"0 0 1")]:
        page = writer.add_blank_page(width, height)
        stream = DecodedStreamObject()
        stream.set_data(color + f" rg 0 0 {width} {height} re f".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
    writer.write(path)
    return path


def test_pdf_pages_render_independently(tmp_path):
    source = colored_pdf(tmp_path / "pages.pdf")
    document = import_document(source)
    assert len(document.pages) == 2
    first = Image.open(BytesIO(render_page(source, 0, 400)))
    second = Image.open(BytesIO(render_page(source, 1, 400)))
    assert first.height > first.width
    assert second.width > second.height
    assert first.getpixel((10, 10))[:3] == (255, 0, 0)
    assert second.getpixel((10, 10))[:3] == (0, 0, 255)


def test_tiff_frames_and_page_corrections_survive_project(tmp_path):
    source = tmp_path / "frames.tiff"
    Image.new("RGB", (100, 80), "red").save(source, save_all=True, append_images=[Image.new("RGB", (100, 80), "blue")])
    document = import_document(source)
    assert len(document.pages) == 2
    assert Image.open(BytesIO(render_page(source, 1))).getpixel((1, 1)) == (0, 0, 255)
    document.text = "පළමු පිටුව"
    document.approved = True
    document.activate_page(1)
    equation = Equation(latex=r"E=\frac{1}{2}mv^2", placement="inline")
    equation.accept()
    document.text = "දෙවන පිටුව " + equation.marker
    document.equations.append(equation)
    project = tmp_path / "pages.json"
    save_project(document, project)
    restored = load_project(project)
    assert restored.active_page == 1
    assert restored.equations[0].latex == equation.latex
    restored.activate_page(0)
    assert restored.text == "පළමු පිටුව"
    assert restored.approved
    output = tmp_path / "all-pages.docx"
    export_document(restored, output)
    with ZipFile(output) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
        settings = etree.fromstring(archive.read("word/settings.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main", "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
    text = "".join(root.xpath("//w:t/text()", namespaces=ns))
    assert "පළමු පිටුව" in text and "දෙවන පිටුව" in text
    assert len(root.xpath("//m:oMath", namespaces=ns)) == 1
    assert root.xpath("//m:f", namespaces=ns)
    assert not root.xpath("//w:drawing | //w:txbxContent", namespaces=ns)
    assert settings.xpath("//m:mathFont/@m:val", namespaces=ns) == ["Cambria Math"]
    tags = [child.tag for child in settings]
    assert tags.index("{" + ns["m"] + "}mathPr") < tags.index("{" + ns["w"] + "}themeFontLang")


def test_forced_visual_ocr_uses_selected_pdf_page(tmp_path, monkeypatch):
    from sinhala_ocr.core import Recognition, TesseractEngine
    from sinhala_ocr.documents import recognize_page
    source = colored_pdf(tmp_path / "pages.pdf")
    document = import_document(source)
    colors = []
    def recognize(_self, image):
        colors.append(Image.open(image).getpixel((10, 10))[:3])
        return Recognition("scanned", "test")
    monkeypatch.setattr(TesseractEngine, "recognize", recognize)
    assert recognize_page(document, 1, force_image=True).text == "scanned"
    assert colors == [(0, 0, 255)]
