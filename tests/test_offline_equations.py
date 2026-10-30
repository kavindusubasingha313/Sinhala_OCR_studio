from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import sys

from PIL import Image
import pytest

from sinhala_ocr import offline_equations as offline
from sinhala_ocr.core import Document, export_document
from sinhala_ocr.equations import Equation, EquationError

FIXTURE = Path(offline.__file__).parent / 'assets' / 'equation_smoke.png'


def test_off_does_not_load_model_or_decode_image(monkeypatch):
    def forbidden(*args):
        pytest.fail('Disabled recognition loaded a model')
    monkeypatch.setattr(offline, 'load_engine', forbidden)
    with pytest.raises(EquationError, match='Turn LaTeX ON'):
        offline.recognize_equation(b'not an image', enabled=False)


def test_missing_models_fail_before_import_or_download(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, 'rapid_latex_ocr', None)
    offline.load_engine.cache_clear()
    with pytest.raises(EquationError, match='models are missing'):
        offline.load_engine(tmp_path)


def test_corrupted_model_rejected(tmp_path):
    (tmp_path / 'encoder.onnx').write_bytes(b'corrupt')
    with pytest.raises(EquationError, match='integrity check failed'):
        offline.validate_models(tmp_path)


def test_blank_crop_does_not_load_engine(monkeypatch):
    data = BytesIO()
    Image.new('RGB', (100, 100), 'white').save(data, 'PNG')
    monkeypatch.setattr(offline, 'load_engine', lambda _: pytest.fail('blank crop loaded model'))
    with pytest.raises(EquationError, match='blank'):
        offline.recognize_equation(data.getvalue(), enabled=True)


def test_real_cpu_recognition_and_editable_word_export(tmp_path, monkeypatch):
    if not (offline.model_directory() / 'encoder.onnx').is_file():
        pytest.skip('Offline model files not installed; CI downloads before tests')
    # Any implicit download is a test failure: all recognition must be local.
    import requests
    monkeypatch.setattr(requests, 'get', lambda *a, **k: pytest.fail('Inference attempted network access'))
    source = offline.recognize_equation(FIXTURE.read_bytes(), enabled=True)
    assert source.replace(r'\,', '').replace(' ', '') == 'x=1'
    equation = Equation(latex=source, original_latex=source)
    equation.accept()
    document = Document('synthetic.png', text='සිංහල ' + equation.marker, equations=[equation])
    destination = tmp_path / 'recognized.docx'
    export_document(document, destination)
    with ZipFile(destination) as archive:
        xml = archive.read('word/document.xml').decode()
    assert '<m:oMath' in xml
    assert 'සිංහල' in xml
    assert 'txbxContent' not in xml and '<w:drawing' not in xml


def test_offline_ui_review_undo_and_changed_source_protection(tmp_path, monkeypatch):
    import base64
    from PySide6.QtWidgets import QMessageBox
    from sinhala_ocr.equation_ui import EquationEditor
    from test_workspace import make_window
    application, window, errors = make_window(tmp_path, monkeypatch)
    monkeypatch.setattr(window, 'request_preview', lambda: None)
    monkeypatch.setattr(window, 'start_thumbnails', lambda _: None)
    window.display_document(Document('synthetic.png', latex_enabled=True))
    equation = Equation(latex='x=0', image_png=base64.b64encode(FIXTURE.read_bytes()).decode())
    window.attach_equation(equation)
    editor = EquationEditor(equation, window)
    editor.show()
    pending = []
    monkeypatch.setattr(window, 'background', lambda operation, complete, **kwargs: pending.append(complete))
    monkeypatch.setattr(QMessageBox, 'question', lambda *a: QMessageBox.StandardButton.Yes)
    window.offline_equation(editor)
    assert equation.latex == 'x=0'
    pending.pop()('x=1')
    assert equation.latex == 'x=1' and equation.status == 'draft'
    editor.source.undo()
    assert equation.latex == 'x=0'
    window.offline_equation(editor)
    editor.source.insertPlainText('edited')
    before = editor.source.toPlainText()
    pending.pop()('x=2')
    assert editor.source.toPlainText() == before
    assert 'preserved' in editor.message.text()
    window.offline_equation(editor)
    editor.close()
    pending.pop()('x=3')
    assert equation.latex == before
    assert not errors
    window.document = None
    window.close()
    application.processEvents()


def test_transparent_equation_is_composited_and_padded(monkeypatch):
    image = Image.new('RGBA', (60, 40), (0, 0, 0, 0))
    image.putpixel((20, 20), (0, 0, 0, 255))
    data = BytesIO()
    image.save(data, 'PNG')
    def engine(png):
        with Image.open(BytesIO(png)) as crop:
            assert crop.size == (84, 64)
            assert crop.convert('RGB').getpixel((0, 0)) == (255, 255, 255)
            assert crop.convert('RGB').getpixel((32, 32)) == (0, 0, 0)
        return 'x=1', 0
    monkeypatch.setattr(offline, 'load_engine', lambda _: engine)
    assert offline.recognize_equation(data.getvalue(), enabled=True) == 'x=1'


def test_equation_action_explains_missing_selection_and_busy_state(tmp_path, monkeypatch):
    from test_workspace import make_window
    app, window, errors = make_window(tmp_path, monkeypatch)
    window.recognize_selected_equation()
    assert 'First select' in errors[-1]
    window.busy = True
    window.recognize_selected_equation()
    assert 'Another operation' in errors[-1]
    window.busy = False
    window.close()
    app.processEvents()
