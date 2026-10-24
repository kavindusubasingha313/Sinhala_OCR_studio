import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import QSettings, QThreadPool, Qt
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtWidgets import QApplication, QMessageBox

from sinhala_ocr import app as app_module
from sinhala_ocr.app import MainWindow
from sinhala_ocr.core import import_document, load_project, save_project
from sinhala_ocr.workspace_widgets import UnicodeEditor
from test_documents import colored_pdf


def make_window(tmp_path, monkeypatch):
    application = QApplication.instance() or QApplication([])
    monkeypatch.setattr(app_module, "QSettings", lambda *args: QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    window = MainWindow()
    errors = []
    monkeypatch.setattr(window, "error", errors.append)
    return application, window, errors


def drain(application):
    QThreadPool.globalInstance().waitForDone()
    application.processEvents()


def test_tabs_pages_preview_and_undo_keep_each_document(tmp_path, monkeypatch):
    application, window, errors = make_window(tmp_path, monkeypatch)
    source = colored_pdf(tmp_path / "pages.pdf")
    window.display_document(import_document(source))
    drain(application)
    assert not window.pixmap.isNull()
    window.editor.insertPlainText("වස්තුවක්")
    window.accept()
    window.pages.setCurrentRow(1)
    drain(application)
    assert window.document.active_page == 1
    assert window.pixmap.width() > window.pixmap.height()
    window.editor.insertPlainText("page two")
    photo = tmp_path / "photo.png"
    Image.new("RGB", (100, 100), "white").save(photo)
    window.display_document(import_document(photo))
    window.editor.insertPlainText("another photo")
    window.tabs.setCurrentIndex(0)
    assert window.editor.toPlainText() == "page two"
    window.pages.setCurrentRow(0)
    assert window.editor.toPlainText() == "වස්තුවක්"
    assert window.document.approved
    window.editor.undo()
    assert window.editor.toPlainText() == ""
    window.editor.redo()
    assert window.editor.toPlainText() == "වස්තුවක්"
    assert window.sessions[1].document.text == "another photo"
    drain(application)
    assert not errors
    window.document = None
    window.close()


def test_close_cancel_keeps_corrections_and_discard_closes_one_tab(tmp_path, monkeypatch):
    application, window, errors = make_window(tmp_path, monkeypatch)
    path = tmp_path / "photo.png"
    Image.new("RGB", (10, 10)).save(path)
    window.display_document(import_document(path))
    window.editor.insertPlainText("manual correction")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel)
    window.close_session(0)
    assert len(window.sessions) == 1
    assert window.document.text == "manual correction"
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard)
    window.close_session(0)
    assert not window.sessions
    assert window.editor.toPlainText() == ""
    drain(application)
    assert not errors
    window.close()


def test_candidate_replacement_retains_original_page_history(tmp_path, monkeypatch):
    application, window, _ = make_window(tmp_path, monkeypatch)
    source = colored_pdf(tmp_path / "pages.pdf")
    window.display_document(import_document(source))
    window.editor.insertPlainText("manually approved Sinhala වස්තුවක්")
    window.accept()
    session = window.session
    window.pages.setCurrentRow(1)
    window.apply_candidate(session, 0, "AI suggestion", [])
    assert window.document.active_page == 1
    assert session.document.pages[0].text == "AI suggestion"
    assert session.document.pages[0].history[-1]["text"] == "manually approved Sinhala වස්තුවක්"
    assert session.document.pages[0].history[-1]["approved"]
    project = tmp_path / "project.json"
    save_project(session.document, project)
    restored = load_project(project)
    assert restored.pages[0].history[-1]["approved"]
    assert restored.pages[0].text == "AI suggestion"
    drain(application)
    window.document = None
    window.close()


def test_sinhala_preedit_and_commit_are_not_duplicated_or_normalized():
    application = QApplication.instance() or QApplication([])
    editor = UnicodeEditor()
    editor.show()
    editor.setFocus()
    for preedit in ["ව", "වස්", "වස්තු", "වස්තුවක්"]:
        application.sendEvent(editor, QInputMethodEvent(preedit, []))
        assert editor.toPlainText() == ""
    commit = QInputMethodEvent()
    commit.setCommitString("වස්තුවක්")
    application.sendEvent(editor, commit)
    assert editor.toPlainText() == "වස්තුවක්"
    assert editor.testAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled)
    editor.undo()
    assert editor.toPlainText() == ""
    editor.redo()
    assert editor.toPlainText() == "වස්තුවක්"
    editor.close()


def test_ai_consent_and_daily_limit_block_requests(tmp_path, monkeypatch):
    from sinhala_ocr import advanced_ocr
    from PySide6.QtCore import QDate
    application, window, errors = make_window(tmp_path, monkeypatch)
    path = tmp_path / "photo.png"
    Image.new("RGB", (10, 10)).save(path)
    window.display_document(import_document(path))
    drain(application)
    monkeypatch.setattr(advanced_ocr.CredentialStore, "get", lambda _: "test-key")
    requests = []
    monkeypatch.setattr(advanced_ocr, "recognize_with_ai", lambda *args, **kwargs: requests.append(args))
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    window.advanced_ocr()
    assert not requests
    assert window.settings.value("ai/requests", 0, type=int) == 0
    window.settings.setValue("ai/day", QDate.currentDate().toString(Qt.DateFormat.ISODate))
    window.settings.setValue("ai/requests", 10)
    window.settings.setValue("ai/daily_limit", 10)
    window.advanced_ocr()
    assert not requests
    assert "limit" in errors[-1]
    window.document = None
    window.close()


def test_equation_references_are_readable_without_changing_project_ids(tmp_path, monkeypatch):
    from sinhala_ocr.equations import Equation
    application, window, _ = make_window(tmp_path, monkeypatch)
    path = tmp_path / "photo.png"
    Image.new("RGB", (10, 10)).save(path)
    window.display_document(import_document(path))
    equation = Equation(latex="x^2")
    window.attach_equation(equation)
    assert window.editor.toPlainText() == "⟦Equation 1⟧"
    assert window.document.text == equation.marker
    window.editor.undo()
    assert window.document.text == ""
    window.editor.redo()
    assert window.document.text == equation.marker
    drain(application)
    window.document = None
    window.close()


def test_preview_is_actually_painted_in_both_themes(tmp_path, monkeypatch):
    application, window, errors = make_window(tmp_path, monkeypatch)
    window.show()
    window.display_document(import_document(colored_pdf(tmp_path / "painted.pdf")))
    drain(application)
    for theme in ["Light", "Dark"]:
        window.theme.setCurrentText(theme)
        application.processEvents()
        center = window.viewer.mapFromScene(window.viewer.image_item.boundingRect().center())
        pixel = window.viewer.viewport().grab().toImage().pixelColor(center)
        assert (pixel.red(), pixel.green(), pixel.blue()) == (255, 0, 0)
    window.pages.setCurrentRow(1)
    drain(application)
    center = window.viewer.mapFromScene(window.viewer.image_item.boundingRect().center())
    pixel = window.viewer.viewport().grab().toImage().pixelColor(center)
    assert (pixel.red(), pixel.green(), pixel.blue()) == (0, 0, 255)
    assert not errors
    window.document = None
    window.close()


def test_equation_crop_recognition_requires_review_and_is_undoable(tmp_path, monkeypatch):
    from sinhala_ocr import advanced_ocr
    from sinhala_ocr.equations import Equation, equation_crop
    from sinhala_ocr.equation_ui import EquationEditor
    import base64
    application, window, errors = make_window(tmp_path, monkeypatch)
    path = tmp_path / 'formula.png'
    Image.new('RGB', (100, 100), 'white').save(path)
    window.display_document(import_document(path))
    drain(application)
    equation = equation_crop(path, (10, 10, 50, 50))
    equation.edit('x')
    dialog = EquationEditor(equation, window)
    dialog.show()
    monkeypatch.setattr(advanced_ocr.CredentialStore, 'get', lambda _: 'test-key')
    calls = []
    def recognize(data, **kwargs):
        calls.append((data, kwargs))
        return advanced_ocr.AiResult('', [Equation(latex=r'm=\sqrt{100^2+200^2+2\times100\times200\times\frac{1}{2}}')])
    monkeypatch.setattr(advanced_ocr, 'recognize_with_ai', recognize)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.No)
    window.advanced_ocr(equation_editor=dialog)
    assert not calls
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Yes)
    window.advanced_ocr(equation_editor=dialog)
    drain(application)
    assert calls[0][0] == base64.b64decode(equation.image_png)
    assert calls[0][1]['latex_enabled'] is True
    assert equation.latex.startswith(r'm=\sqrt')
    assert equation.status == 'draft'
    dialog.source.undo()
    assert equation.latex == 'x'
    assert not errors
    dialog.close()
    window.document = None
    window.close()


def test_pasted_sinhala_is_preserved_exactly():
    application = QApplication.instance() or QApplication([])
    editor = UnicodeEditor()
    text = 'වස්තුවක් සිංහල වවවව'
    application.clipboard().setText(text)
    editor.paste()
    assert editor.toPlainText() == text
    editor.undo()
    assert editor.toPlainText() == ''
    editor.close()


def test_native_input_apply_is_undoable_and_cancel_preserves_page(tmp_path, monkeypatch):
    from sinhala_ocr import windows_input
    from PySide6.QtWidgets import QDialog
    application, window, errors = make_window(tmp_path, monkeypatch)
    path = tmp_path / 'input.png'
    Image.new('RGB', (10, 10)).save(path)
    window.display_document(import_document(path))
    drain(application)
    window.editor.insertPlainText('original වවවව')
    window.accept()
    class FakeDialog:
        result_text = 'වස්තුවක් ශ්‍රී'
        outcome = QDialog.DialogCode.Rejected
        def __init__(self, text, parent):
            assert text == 'original වවවව'
        def exec(self):
            return self.outcome
    monkeypatch.setattr(windows_input, 'WindowsInputDialog', FakeDialog)
    window.windows_sinhala_editor()
    assert window.document.text == 'original වවවව'
    assert window.document.approved
    FakeDialog.outcome = QDialog.DialogCode.Accepted
    window.windows_sinhala_editor()
    assert window.document.text == 'වස්තුවක් ශ්‍රී'
    assert not window.document.approved
    window.editor.undo()
    assert window.document.text == 'original වවවව'
    window.editor.redo()
    assert window.document.text == 'වස්තුවක් ශ්‍රී'
    save_project(window.document, tmp_path / 'typed.sos.json')
    assert load_project(tmp_path / 'typed.sos.json').text == 'වස්තුවක් ශ්‍රී'
    assert not errors
    window.document = None
    window.close()


def test_saved_word_replaces_only_selection_with_undo(tmp_path, monkeypatch):
    from sinhala_ocr import word_memory
    from PySide6.QtWidgets import QDialog
    application, window, errors = make_window(tmp_path, monkeypatch)
    path = tmp_path / 'input.png'
    Image.new('RGB', (10, 10)).save(path)
    window.display_document(import_document(path))
    drain(application)
    window.editor.insertPlainText('bad English')
    cursor = window.editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(3, cursor.MoveMode.KeepAnchor)
    window.editor.setTextCursor(cursor)
    monkeypatch.setattr(word_memory, 'WordMemory', lambda: None)
    class FakeDialog:
        chosen = 'වස්තුවක්'
        def __init__(self, memory, selection, parent):
            assert selection == 'bad'
        def exec(self):
            return QDialog.DialogCode.Accepted
    monkeypatch.setattr(word_memory, 'WordMemoryDialog', FakeDialog)
    window.saved_words()
    assert window.document.text == 'වස්තුවක් English'
    window.editor.undo()
    assert window.document.text == 'bad English'
    assert not errors
    window.document = None
    window.close()
