import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, QRect, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from sinhala_ocr import app as app_module
from sinhala_ocr.app import MainWindow
from sinhala_ocr.core import Document, load_project, save_project
from sinhala_ocr.equation_ui import EquationEditor, RegionSelector
from sinhala_ocr.equations import Equation


def test_toggle_preference_and_document_mode(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(app_module, "QSettings", lambda *args: QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    window = MainWindow()
    assert not window.latex_toggle.isChecked()
    document = Document("image.png")
    window.display_document(document)
    window.latex_toggle.setChecked(True)
    equation = Equation(latex="x=2")
    window.attach_equation(equation)
    window.latex_toggle.setChecked(False)
    assert document.equations == [equation]
    assert equation.marker in document.text
    assert not document.latex_enabled
    window.latex_toggle.setChecked(True)
    second = MainWindow()
    assert second.latex_toggle.isChecked()
    second.display_document(Document("old.png", latex_enabled=False))
    assert not second.latex_toggle.isChecked()
    assert second.settings.value("latex_enabled", type=bool)
    save_project(document, tmp_path / "project.json")
    assert load_project(tmp_path / "project.json").latex_enabled
    app.processEvents()
    window.document = second.document = None
    window.close()
    second.close()


def test_live_preview_edit_accept_reject_undo_restore():
    app = QApplication.instance() or QApplication([])
    equation = Equation(latex="x=1", original_latex="x=1")
    editor = EquationEditor(equation)
    assert editor.preview.renderer().isValid()
    assert editor.preview.renderer().aspectRatioMode() == Qt.AspectRatioMode.KeepAspectRatio
    editor.source.selectAll()
    editor.source.insertPlainText(r"\frac{a}{b}")
    assert equation.status == "draft"
    assert editor.update_preview()
    editor.accept_equation()
    assert equation.status == "accepted"
    editor.source.undo()
    assert equation.latex == "x=1"
    assert equation.status == "draft"
    editor.source.redo()
    assert equation.latex == r"\frac{a}{b}"
    editor.restore_original()
    assert equation.latex == "x=1"
    editor.source.undo()
    assert equation.latex == r"\frac{a}{b}"
    editor.source.selectAll()
    editor.source.insertPlainText(r"\unsupported{x}")
    editor.accept_equation()
    assert equation.status == "draft"
    assert not editor.update_preview()
    assert "Unsupported" in editor.message.text()
    editor.reject_equation()
    assert equation.status == "rejected"
    assert equation.latex == r"\unsupported{x}"
    app.processEvents()
    editor.close()


def test_region_selection_maps_to_original_pixels():
    app = QApplication.instance() or QApplication([])
    pixmap = QPixmap(1800, 1200)
    selector = RegionSelector(pixmap)
    selector.selection = QRect(10, 20, 100, 50)
    assert selector.source_bbox() == (20, 40, 220, 140)
    app.processEvents()


def test_new_import_uses_preference_and_markers_preserve_selected_text(tmp_path, monkeypatch):
    from PIL import Image
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(app_module, "QSettings", lambda *args: QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    window = MainWindow()
    window.latex_toggle.setChecked(True)
    window.display_document(Document("old.png", latex_enabled=False))
    source = tmp_path / "new.png"
    Image.new("RGB", (20, 20)).save(source)
    monkeypatch.setattr(window, "safe_to_replace", lambda: True)
    monkeypatch.setattr(app_module.QFileDialog, "getOpenFileName", lambda *args: (str(source), ""))
    monkeypatch.setattr(window, "background", lambda operation, callback: callback(operation()))
    window.open_document()
    assert window.document.latex_enabled
    window.editor.setPlainText("සිංහල original")
    window.editor.selectAll()
    equation = Equation(latex="x")
    window.attach_equation(equation)
    assert window.document.text == "සිංහල original" + equation.marker
    window.document = None
    window.close()
    app.processEvents()
