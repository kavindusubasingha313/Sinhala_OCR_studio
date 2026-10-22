"""Qt desktop shell. Native text editing preserves IME composition handling."""
import sys
import os
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QSettings, QThreadPool, QTimer, Signal, Qt
from PySide6.QtGui import QAction, QFont, QFontDatabase, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QScrollArea,
    QSplitter, QTextEdit, QToolBar, QVBoxLayout, QWidget,
)

from .diagnostics import Diagnostics

from .core import (Document, TesseractEngine, export_document, import_document,
                   load_project, save_project)


class Signals(QObject):
    completed = Signal(object)
    failed = Signal(str)


class Task(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.signals = Signals()

    def run(self):
        try:
            self.signals.completed.emit(self.operation())
        except Exception as error:
            self.signals.failed.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.diagnostics = Diagnostics()
        self.settings = QSettings("SinhalaOCRStudio", "Desktop")
        self.document = None
        self.busy = False
        self.zoom = 1.0
        self.pixmap = QPixmap()
        self.setWindowTitle("Sinhala OCR Studio · Document workspace")
        self.resize(1200, 780)
        toolbar = QToolBar("Document actions")
        self.addToolBar(toolbar)
        for title, callback, shortcut in [
            ("Import", self.open_document, "Ctrl+O"),
            ("Open project", self.open_project, "Ctrl+Shift+O"),
            ("Save project", self.save, "Ctrl+S"),
            ("Export", self.export, "Ctrl+E"),
            ("Recognize", self.recognize, "Ctrl+R"),
            ("Accept", self.accept, "Ctrl+Return"),
        ]:
            action = QAction(title, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            toolbar.addAction(action)
        diagnostic_action = QAction("Diagnostic logging", self)
        diagnostic_action.setCheckable(True)
        diagnostic_action.toggled.connect(self.enable_diagnostics)
        toolbar.addAction(diagnostic_action)
        report_action = QAction("Export bug report", self)
        report_action.triggered.connect(self.export_report)
        toolbar.addAction(report_action)
        toolbar.addSeparator()
        self.theme = QComboBox()
        self.theme.addItems(["System", "Light", "Dark"])
        self.theme.setCurrentText(self.settings.value("theme", "System"))
        self.theme.currentTextChanged.connect(self.set_theme)
        toolbar.addWidget(self.theme)
        root = QWidget()
        layout = QVBoxLayout(root)
        heading = QLabel("DOCUMENT WORKSPACE   /   Offline · Sinhala + English")
        layout.addWidget(heading)
        split = QSplitter()
        self.pages = QListWidget()
        self.pages.setMaximumWidth(210)
        self.pages.addItem("Import a document to begin")
        split.addWidget(self.pages)
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        controls = QHBoxLayout()
        for title, factor in [("Zoom −", 0.8), ("Zoom +", 1.25)]:
            button = QPushButton(title)
            button.clicked.connect(lambda checked=False, f=factor: self.change_zoom(f))
            controls.addWidget(button)
        preview_layout.addLayout(controls)
        self.preview = QLabel("Original document preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.preview)
        preview_layout.addWidget(scroll)
        split.addWidget(preview_panel)
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText("Recognized or selectable PDF text appears here. You can edit every character.")
        self.editor.textChanged.connect(self.edited)
        split.addWidget(self.editor)
        split.setSizes([180, 500, 500])
        layout.addWidget(split)
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        self.setCentralWidget(root)
        self.statusBar().showMessage("Ready · Cloud uploads disabled · Stage 1 foundation")
        self.set_theme(self.theme.currentText())
        QApplication.styleHints().colorSchemeChanged.connect(lambda _: self.set_theme(self.theme.currentText()))

    def set_theme(self, theme):
        self.settings.setValue("theme", theme)
        dark = theme == "Dark" or (theme == "System" and QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark)
        bg, fg, panel = ("#171b24", "#edf0f7", "#252c39") if dark else ("#f2f4f8", "#202735", "#ffffff")
        self.setStyleSheet(f"QWidget {{ background: {bg}; color: {fg}; font-size: 13px; }} "
                          f"QTextEdit, QListWidget, QComboBox {{ background: {panel}; padding: 10px; border: 1px solid #6b7890; border-radius: 6px; }} "
                          "QToolBar { spacing: 10px; padding: 10px; } QPushButton { padding: 8px; }")

    def enable_diagnostics(self, enabled):
        self.diagnostics.enabled = enabled
        self.diagnostics.record("startup")

    def export_report(self):
        name, _ = QFileDialog.getSaveFileName(self, "Export diagnostic report (no document content)", "sinhala-ocr-report.zip", "ZIP (*.zip)")
        if name:
            try:
                if self.document and Path(name).resolve() == Path(self.document.source).resolve():
                    raise ValueError("Cannot overwrite original source.")
                self.diagnostics.record("export_report")
                self.diagnostics.export(Path(name))
            except Exception as error:
                self.error(str(error))

    def error(self, message):
        self.diagnostics.record("operation_failed")
        QMessageBox.warning(self, "Operation could not complete", message)

    def safe_to_replace(self):
        if self.busy:
            self.error("Wait for the current operation to finish.")
            return False
        if self.document:
            return QMessageBox.question(self, "Close current document?", "Save your project first to preserve changes. Close this document?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
        return True

    def background(self, operation, callback):
        self.busy = True
        self.progress.setRange(0, 0)
        self.progress.show()
        task = Task(operation)
        self.active_task = task
        def finish(result=None, error=None):
            self.busy = False
            self.progress.hide()
            if error:
                self.error(error)
            else:
                callback(result)
        task.signals.completed.connect(lambda result: finish(result=result))
        task.signals.failed.connect(lambda message: finish(error=message))
        QThreadPool.globalInstance().start(task)

    def open_document(self):
        if not self.safe_to_replace():
            return
        name, _ = QFileDialog.getOpenFileName(self, "Import document", "", "Documents (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.pdf)")
        if name:
            self.background(lambda: import_document(Path(name)), self.display_document)

    def display_document(self, document):
        approved = document.approved
        self.document = document
        self.editor.setPlainText(document.text)
        self.document.approved = approved
        self.pages.clear()
        self.pages.addItem(Path(document.source).name)
        self.zoom = 1.0
        reader = QImageReader(document.source)
        reader.setAutoTransform(True)
        self.pixmap = QPixmap.fromImage(reader.read())
        if self.pixmap.isNull():
            self.preview.setText("PDF text imported directly.\nPDF page rendering is planned for Stage 2.")
        else:
            self.change_zoom(1)
        self.statusBar().showMessage("Imported · Review text before accepting · Confidence unavailable")

    def change_zoom(self, factor):
        self.zoom = max(0.1, min(4.0, self.zoom * factor))
        if not self.pixmap.isNull():
            self.preview.setPixmap(self.pixmap.scaledToWidth(int(600 * self.zoom), Qt.TransformationMode.SmoothTransformation))

    def edited(self):
        if self.document:
            self.document.text = self.editor.toPlainText()
            self.document.approved = False

    def recognize(self):
        if not self.document or self.busy:
            return
        if self.document.text or self.document.approved:
            self.error("Existing text is protected. Import a fresh document to rerun OCR.")
            return
        if Path(self.document.source).suffix.lower() == ".pdf":
            self.error("Scanned PDF OCR is planned for Stage 2; selectable text is imported directly.")
            return
        def complete(result):
            self.document.apply_recognition(result)
            self.editor.setPlainText(self.document.text)
            self.statusBar().showMessage("OCR complete · All text requires review; confidence unavailable")
        source = Path(self.document.source)
        self.background(lambda: TesseractEngine().recognize(source), complete)

    def accept(self):
        if self.document:
            self.document.approved = True
            self.statusBar().showMessage("Text approved · Save project to persist approval")

    def save(self):
        if not self.document:
            return
        name, _ = QFileDialog.getSaveFileName(self, "Save editable project", "document.sos.json", "Studio project (*.sos.json)")
        if name:
            try:
                if Path(name).resolve() == Path(self.document.source).resolve():
                    raise ValueError("Cannot overwrite the original source.")
                save_project(self.document, Path(name))
            except Exception as error:
                self.error(str(error))

    def open_project(self):
        if not self.safe_to_replace():
            return
        name, _ = QFileDialog.getOpenFileName(self, "Open project", "", "Studio project (*.sos.json)")
        if name:
            try:
                self.display_document(load_project(Path(name)))
            except Exception as error:
                self.error(str(error))

    def export(self):
        if not self.document:
            return
        name, _ = QFileDialog.getSaveFileName(self, "Export text", "document.docx", "Word (*.docx);;Unicode text (*.txt)")
        if name:
            snapshot = Document(self.document.source, self.document.text, self.document.approved)
            self.background(lambda: export_document(snapshot, Path(name)), lambda _: self.statusBar().showMessage("Export validated and saved"))

    def closeEvent(self, event):
        if self.safe_to_replace():
            event.accept()
        else:
            event.ignore()


def main():
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "tesseract"
        os.environ["PATH"] = str(bundled) + os.pathsep + os.environ.get("PATH", "")
        os.environ["TESSDATA_PREFIX"] = str(bundled / "tessdata")
    app = QApplication(sys.argv)
    font_path = Path(__file__).parent / "assets" / "NotoSansSinhala.ttf"
    QFontDatabase.addApplicationFont(str(font_path))
    font = QFont()
    font.setFamilies(["Nirmala UI", "Iskoola Pota", "Noto Sans Sinhala", "Segoe UI"])
    app.setFont(font)
    window = MainWindow()
    window.show()
    if "--smoke-test" in sys.argv:
        def smoke():
            import tempfile
            from PIL import Image
            try:
                with tempfile.TemporaryDirectory() as folder:
                    image = Path(folder) / "blank.png"
                    Image.new("RGB", (500, 200), "white").save(image)
                    result = TesseractEngine().recognize(image)
                    assert not result.text.strip()
                    window.display_document(Document(str(image), "සිංහල English x² = ½"))
                    assert window.editor.toPlainText() == "සිංහල English x² = ½"
                    for theme in ["Dark", "Light"]:
                        window.theme.setCurrentText(theme)
                    export_document(window.document, Path(folder) / "smoke.docx")
                window.diagnostics.record("smoke_passed")
                Path("packaged-smoke.json").write_text('{"status": "passed"}', encoding="utf-8")
                app.exit(0)
            except Exception as error:
                import json
                Path("packaged-smoke.json").write_text(json.dumps({"status": "failed", "error_type": type(error).__name__}), encoding="utf-8")
                app.exit(1)
        QTimer.singleShot(200, smoke)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
