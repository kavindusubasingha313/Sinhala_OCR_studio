"""Qt desktop shell. Native text editing preserves IME composition handling."""
import sys
import os
from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QSettings, QThreadPool, QTimer, Signal, Qt
from PySide6.QtGui import QAction, QFont, QFontDatabase, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QScrollArea,
    QSplitter, QTextEdit, QToolBar, QVBoxLayout, QWidget,
)

from .diagnostics import Diagnostics
from .equations import Equation, EquationError, equation_crop, recognize_document
from .equation_ui import EquationEditor, RegionDialog

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
        equation_controls = QHBoxLayout()
        self.latex_toggle = QCheckBox("LaTeX OFF")
        self.latex_toggle.setChecked(self.settings.value("latex_enabled", False, type=bool))
        self.latex_toggle.setText("LaTeX ON" if self.latex_toggle.isChecked() else "LaTeX OFF")
        self.latex_toggle.setToolTip("Enable equation workflows for this document. Turning OFF preserves saved equations. Automatic equation OCR is not yet installed.")
        self.latex_toggle.toggled.connect(self.set_latex_mode)
        equation_controls.addWidget(self.latex_toggle)
        for title, callback in [("Add equation", self.add_equation), ("Mark equation region", self.mark_equation), ("Edit selected equation", self.edit_equation), ("Insert equation marker", self.insert_equation_marker)]:
            button = QPushButton(title)
            button.clicked.connect(callback)
            equation_controls.addWidget(button)
        layout.addLayout(equation_controls)
        split = QSplitter()
        self.pages = QListWidget()
        self.pages.setMaximumWidth(210)
        self.pages.addItem("Import a document to begin")
        navigation = QWidget()
        navigation_layout = QVBoxLayout(navigation)
        navigation_layout.addWidget(self.pages)
        navigation_layout.addWidget(QLabel("Equations — double-click to edit"))
        self.equation_list = QListWidget()
        self.equation_list.itemDoubleClicked.connect(lambda _: self.edit_equation())
        navigation_layout.addWidget(self.equation_list)
        split.addWidget(navigation)
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

    def set_latex_mode(self, enabled):
        self.settings.setValue("latex_enabled", enabled)
        self.latex_toggle.setText("LaTeX ON" if enabled else "LaTeX OFF")
        if self.document:
            self.document.latex_enabled = enabled
        self.statusBar().showMessage("LaTeX ON · Manual equation editing available; automatic equation recognition not installed" if enabled else "LaTeX OFF · Standard OCR; existing equations preserved")

    def refresh_equations(self):
        self.equation_list.clear()
        if self.document:
            for index, equation in enumerate(self.document.equations, 1):
                self.equation_list.addItem(f"{index}. {equation.placement} · {equation.status}")

    def attach_equation(self, equation):
        self.document.equations.append(equation)
        self.insert_marker_at_cursor(equation.marker)
        self.refresh_equations()
        self.equation_list.setCurrentRow(len(self.document.equations) - 1)

    def insert_marker_at_cursor(self, marker):
        cursor = self.editor.textCursor()
        cursor.setPosition(cursor.selectionEnd())
        self.editor.setTextCursor(cursor)
        self.editor.insertPlainText(marker)

    def add_equation(self):
        if not self.document or self.busy:
            return
        if not self.document.latex_enabled:
            self.error("Turn LaTeX ON to add an equation. Existing equations remain editable when OFF.")
            return
        self.attach_equation(Equation())
        self.edit_equation()

    def mark_equation(self):
        if not self.document or self.busy:
            return
        if not self.document.latex_enabled or self.pixmap.isNull():
            self.error("Turn LaTeX ON and import an image to mark an equation. PDF region selection is not yet available.")
            return
        dialog = RegionDialog(self.pixmap, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                equation = equation_crop(Path(self.document.source), dialog.selector.source_bbox())
                self.attach_equation(equation)
                self.edit_equation()
            except (OSError, ValueError) as error:
                self.error(str(error))

    def edit_equation(self):
        row = self.equation_list.currentRow()
        if self.document and 0 <= row < len(self.document.equations):
            EquationEditor(self.document.equations[row], self).exec()
            self.document.approved = False
            self.refresh_equations()
            self.equation_list.setCurrentRow(row)

    def insert_equation_marker(self):
        row = self.equation_list.currentRow()
        if self.document and 0 <= row < len(self.document.equations):
            marker = self.document.equations[row].marker
            if marker in self.editor.toPlainText():
                self.error("This equation already has a marker. Move that marker to change its position.")
            else:
                self.insert_marker_at_cursor(marker)

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
            preferred_mode = self.settings.value("latex_enabled", False, type=bool)
            def imported(document):
                document.latex_enabled = preferred_mode
                self.display_document(document)
            self.background(lambda: import_document(Path(name)), imported)

    def display_document(self, document):
        approved = document.approved
        self.document = document
        self.editor.setPlainText(document.text)
        self.document.approved = approved
        self.latex_toggle.blockSignals(True)
        self.latex_toggle.setChecked(document.latex_enabled)
        self.latex_toggle.setText("LaTeX ON" if document.latex_enabled else "LaTeX OFF")
        self.latex_toggle.blockSignals(False)
        self.refresh_equations()
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
            try:
                self.document.apply_recognition(result.text_result)
            except ValueError as error:
                self.error(str(error))
                return
            self.editor.setPlainText(self.document.text)
            for equation in result.equations:
                self.attach_equation(equation)
            self.statusBar().showMessage(result.notice or "OCR complete · All text requires review; confidence unavailable")
        source = Path(self.document.source)
        latex_enabled = self.document.latex_enabled
        self.background(lambda: recognize_document(source, TesseractEngine(), latex_enabled), complete)

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
        if not self.document or self.busy:
            return
        name, _ = QFileDialog.getSaveFileName(self, "Export document", "document.docx", "Word (*.docx);;Unicode text (*.txt);;Markdown with equations (*.md);;LaTeX source fragment (*.tex)")
        if name:
            snapshot = deepcopy(self.document)
            image_fallback = False
            if snapshot.equations and Path(name).suffix.lower() == ".docx":
                from .equation_export import editable_equation_errors
                try:
                    errors = editable_equation_errors(snapshot)
                except EquationError as error:
                    self.error(str(error))
                    return
                if errors:
                    detail = "\n".join(message for _, message in errors)
                    if not all(eq.image_png for eq, _ in errors):
                        self.error(detail + "\nCorrect and Accept the equations or export LaTeX/Markdown source.")
                        return
                    image_fallback = QMessageBox.question(self, "Equation export needs review", detail + "\nUse original equation crops as clearly labelled non-editable images for unsupported conversions? Supported equations must still be Accepted.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
                    if not image_fallback:
                        return
            self.background(lambda: export_document(snapshot, Path(name), image_fallback=image_fallback), lambda _: self.statusBar().showMessage("Export validated and saved"))

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
    smoke_settings = None
    if "--smoke-test" in sys.argv:
        import tempfile
        smoke_settings = tempfile.TemporaryDirectory()
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, smoke_settings.name)
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
                    window.latex_toggle.setChecked(True)
                    equation = Equation(latex=r"E=\frac{1}{2}mv^2", placement="inline")
                    equation.accept()
                    window.attach_equation(equation)
                    preview = EquationEditor(equation, window)
                    assert preview.update_preview()
                    export_document(window.document, Path(folder) / "smoke.docx")
                window.diagnostics.record("smoke_passed")
                Path("packaged-smoke.json").write_text('{"status": "passed"}', encoding="utf-8")
                app.exit(0)
            except Exception as error:
                import json
                Path("packaged-smoke.json").write_text(json.dumps({"status": "failed", "error_type": type(error).__name__}), encoding="utf-8")
                app.exit(1)
        QTimer.singleShot(200, smoke)
    result = app.exec()
    if smoke_settings:
        smoke_settings.cleanup()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
