import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QSettings, QTimer
from PySide6.QtWidgets import QApplication
from sinhala_ocr.app import MainWindow
from sinhala_ocr.core import Document


def test_workspace_launch_edit_theme_and_worker(tmp_path):
    app = QApplication.instance() or QApplication([])
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    window = MainWindow()
    window.show()
    app.processEvents()
    window.display_document(Document("missing.png", "සිංහල English", True))
    assert window.document.approved
    window.editor.insertPlainText("edited ")
    assert not window.document.approved
    window.editor.undo()
    assert window.editor.toPlainText() == "සිංහල English"
    window.editor.redo()
    assert "edited" in window.document.text
    window.theme.setCurrentText("Dark")
    assert window.settings.value("theme") == "Dark"
    window.accept()
    assert window.document.approved
    loop = QEventLoop()
    results = []
    window.background(lambda: "worker result", lambda value: (results.append(value), loop.quit()))
    QTimer.singleShot(5000, loop.quit)
    loop.exec()
    assert results == ["worker result"]
    assert not window.busy
    window.document = None
    window.close()
