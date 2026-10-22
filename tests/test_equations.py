import base64
import json
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from PIL import Image
import pytest

from sinhala_ocr.core import Document, Recognition, export_document, load_project, save_project
from sinhala_ocr.equations import (Equation, EquationDetection, EquationError, equation_crop,
                                  equation_omml, mathml, recognize_document, render_equation)

FIXTURES = json.loads((Path(__file__).parent / "regression/equations/physics.json").read_text(encoding="utf-8"))
NS = {"m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
      "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda x: x["category"])
def test_physics_render_and_native_word_structure(tmp_path, fixture):
    equation = Equation(latex=fixture["latex"])
    equation.accept()
    assert render_equation(equation.latex).startswith(b"<svg")
    assert equation_omml(equation).xpath(".//m:" + fixture["omml"], namespaces=NS)
    document = Document("original.png", fixture["context"] + equation.marker, equations=[equation])
    output = tmp_path / "physics.docx"
    export_document(document, output)
    with ZipFile(output) as archive:
        xml = etree.fromstring(archive.read("word/document.xml"))
    assert xml.xpath("count(//m:oMathPara/m:oMath)", namespaces=NS) == 1
    assert xml.xpath("//m:" + fixture["omml"], namespaces=NS)
    assert fixture["context"] in "".join(xml.xpath("//w:t/text()", namespaces=NS))
    assert not xml.xpath("//w:txbxContent", namespaces=NS)


@pytest.mark.parametrize("source", [r"\unknown{x}", r"\frac{1}", r"\sqrt", "x^^2", "{x", "x}",
                                    r"\begin{matrix}a\end{pmatrix}", r"\input{private}", "$x$", "x" * 4001])
def test_invalid_equation_never_accepted(source):
    equation = Equation(latex=source)
    with pytest.raises(EquationError):
        equation.accept()
    assert equation.status == "draft"


def test_off_never_constructs_equation_engine(tmp_path):
    class TextEngine:
        def recognize(self, source):
            return Recognition("සිංහල පමණි", "test")
    def forbidden_factory():
        pytest.fail("Equation model must not load when OFF")
    result = recognize_document(tmp_path / "page.png", TextEngine(), False, forbidden_factory)
    assert result.text_result.text == "සිංහල පමණි"
    assert not result.equations


def test_on_calls_optional_engine_and_keeps_crop(tmp_path):
    source = tmp_path / "page.png"
    Image.new("RGB", (100, 100), "white").save(source)
    calls = []
    class TextEngine:
        def recognize(self, source):
            return Recognition("සිංහල", "test")
    class EquationEngine:
        def detect_and_recognize(self, source):
            calls.append(source)
            return [EquationDetection((10, 20, 80, 60), r"E=mc^2", "inline")]
    result = recognize_document(source, TextEngine(), True, EquationEngine)
    assert calls == [source]
    assert result.equations[0].original_latex == r"E=mc^2"
    assert result.equations[0].bbox == [10, 20, 80, 60]
    assert result.equations[0].image_png
    assert result.equations[0].placement == "inline"
    missing = recognize_document(source, TextEngine(), True)
    assert "not installed" in missing.notice


def test_project_backward_compatibility_and_mode_off_preservation(tmp_path):
    source = tmp_path / "page.png"
    Image.new("RGB", (100, 80), "white").save(source)
    equation = equation_crop(source, (1, 2, 50, 60))
    equation.original_latex = "x=1"
    equation.edit("x=2")
    equation.accept()
    document = Document(str(source), "සිංහල " + equation.marker, latex_enabled=True, equations=[equation])
    document.latex_enabled = False
    project = tmp_path / "test.json"
    save_project(document, project)
    source.unlink()
    restored = load_project(project)
    assert restored == document
    assert restored.equations[0].status == "accepted"
    assert base64.b64decode(restored.equations[0].image_png).startswith(b"\x89PNG")
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"source": "image.png", "text": "old", "approved": True}))
    assert load_project(old) == Document("image.png", "old", True)


def test_word_inline_and_display_placement(tmp_path):
    inline = Equation(latex="x^2", placement="inline")
    display = Equation(latex=r"\frac{a}{b}", placement="display")
    inline.accept()
    display.accept()
    document = Document("original", "පෙර " + inline.marker + " පසු\n" + display.marker,
                        equations=[inline, display])
    path = tmp_path / "output.docx"
    export_document(document, path)
    with ZipFile(path) as archive:
        xml = etree.fromstring(archive.read("word/document.xml"))
    assert xml.xpath("count(//w:p/m:oMath)", namespaces=NS) == 1
    assert xml.xpath("count(//w:p/m:oMathPara/m:oMath)", namespaces=NS) == 1
    paragraph = xml.xpath("//w:p[m:oMath]", namespaces=NS)[0]
    assert paragraph[0].tag.endswith("}r")
    assert paragraph[1].tag.endswith("}oMath")
    assert paragraph[2].tag.endswith("}r")


def test_unsupported_export_requires_explicit_original_crop_fallback(tmp_path):
    source = tmp_path / "page.png"
    Image.new("RGB", (100, 80), "white").save(source)
    equation = equation_crop(source, (1, 1, 80, 60))
    equation.latex = r"\unsupported{x}"
    document = Document(str(source), equation.marker, equations=[equation])
    path = tmp_path / "out.docx"
    path.write_bytes(b"existing")
    with pytest.raises(EquationError):
        export_document(document, path)
    assert path.read_bytes() == b"existing"
    export_document(document, path, image_fallback=True)
    with ZipFile(path) as archive:
        xml = etree.fromstring(archive.read("word/document.xml"))
    assert xml.xpath("//w:drawing", namespaces=NS)
    assert "not editable" in "".join(xml.xpath("//w:t/text()", namespaces=NS))
    assert not xml.xpath("//m:oMath | //w:txbxContent", namespaces=NS)


@pytest.mark.parametrize("extension", [".md", ".tex"])
def test_source_export_preserves_latex_and_sinhala(tmp_path, extension):
    equation = Equation(latex=r"\frac{1}{2}", placement="inline")
    document = Document("image.png", "සිංහල " + equation.marker, equations=[equation])
    path = tmp_path / ("source" + extension)
    export_document(document, path)
    content = path.read_text(encoding="utf-8")
    assert "සිංහල" in content
    assert equation.latex in content
    assert "[[eq:" not in content


@pytest.mark.parametrize("change", ["duplicate", "missing", "malformed", "rejected", "draft", "txt"])
def test_no_silent_equation_loss(tmp_path, change):
    equation = Equation(latex="x")
    equation.accept()
    document = Document("image.png", equation.marker, equations=[equation])
    if change == "duplicate":
        document.text *= 2
    elif change == "missing":
        document.text = "plain text"
    elif change == "malformed":
        document.text = "[[eq:bad]]"
    elif change in {"rejected", "draft"}:
        equation.status = change
    path = tmp_path / ("out.txt" if change == "txt" else "out.docx")
    with pytest.raises(EquationError):
        export_document(document, path)
    assert not path.exists()


def test_crop_bounds(tmp_path):
    path = tmp_path / "source.png"
    Image.new("RGB", (100, 100), "white").save(path)
    with pytest.raises(EquationError):
        equation_crop(path, (-1, 0, 50, 50))


def test_empty_fraction_argument_rejected():
    with pytest.raises(EquationError):
        mathml(r"\frac{}{2}")


def test_supported_draft_is_not_offered_as_conversion_fallback():
    from sinhala_ocr.equation_export import editable_equation_errors
    equation = Equation(latex="x", image_png="source-crop-placeholder")
    document = Document("original", equation.marker, equations=[equation])
    with pytest.raises(EquationError, match="Accept"):
        editable_equation_errors(document)
