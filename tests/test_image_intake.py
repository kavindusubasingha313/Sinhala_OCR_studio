from pathlib import Path

from PySide6.QtCore import QMimeData, QUrl, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QDialogButtonBox

from sinhala_ocr.image_intake import ImageIntakeDialog, persist_image, read_image
from sinhala_ocr.core import Document, export_document, load_project, save_project


def test_paste_drop_file_and_invalid_input_preserves_preview(tmp_path):
    app = QApplication.instance() or QApplication([])
    dialog = ImageIntakeDialog()
    image = QImage(80, 60, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.white)
    mime = QMimeData()
    mime.setImageData(image)
    assert dialog.consume(mime)
    assert dialog.buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled()
    file = tmp_path / 'image.png'
    image.save(str(file))
    urls = QMimeData()
    urls.setUrls([QUrl.fromLocalFile(str(file))])
    assert dialog.consume(urls)
    urls.setUrls([QUrl('https://example.com/private.png')])
    assert not dialog.consume(urls)
    assert dialog.image.size() == image.size()
    assert 'web links' in dialog.message.text()
    dialog.close()
    app.processEvents()


def test_capture_transparency_and_project_reopen_and_unicode_export(tmp_path):
    app = QApplication.instance() or QApplication([])
    image = QImage(80, 60, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    image.setPixelColor(20, 20, Qt.GlobalColor.black)
    path = persist_image(image, tmp_path / 'local captures')
    restored = read_image(path)
    assert restored.pixelColor(0, 0) == Qt.GlobalColor.white
    assert restored.pixelColor(20, 20) == Qt.GlobalColor.black
    document = Document(str(path), 'වස්තුවක් සිංහල English x² = ½')
    project = tmp_path / 'capture.json'
    save_project(document, project)
    reopened = load_project(project)
    assert Path(reopened.source).is_file()
    destination = tmp_path / 'recognized.txt'
    export_document(reopened, destination)
    assert destination.read_text(encoding='utf-8') == document.text
    app.processEvents()


def test_quick_text_and_equation_routes_preserve_existing_tab(tmp_path, monkeypatch):
    from test_workspace import make_window
    from sinhala_ocr import image_intake
    app, window, errors = make_window(tmp_path, monkeypatch)
    monkeypatch.setattr(window, 'request_preview', lambda: None)
    monkeypatch.setattr(window, 'start_thumbnails', lambda _: None)
    original_persist = image_intake.persist_image
    monkeypatch.setattr(image_intake, 'persist_image', lambda img: original_persist(img, tmp_path))
    window.display_document(Document('original.png', 'approved original', approved=True))
    calls = []
    monkeypatch.setattr(window, 'recognize', lambda force_image=False: calls.append(('text', force_image)))
    monkeypatch.setattr(window, 'edit_equation', lambda auto_recognize=False: calls.append(('equation', auto_recognize)))
    image = QImage(100, 50, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.white)
    window.open_captured_image(image)
    assert calls == [('text', True)]
    assert not window.document.latex_enabled
    window.open_captured_image(image, equation=True)
    assert calls[-1] == ('equation', True)
    assert window.document.latex_enabled
    assert window.document.equations[0].image_png
    assert window.document.equations[0].marker in window.document.text
    assert window.sessions[0].document.text == 'approved original'
    assert window.sessions[0].document.approved
    assert len(window.sessions) == 3
    window.document = None
    window.close()
    app.processEvents()
