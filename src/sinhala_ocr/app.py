"""Tabbed, page-aware Qt workspace with native Unicode input and reviewed OCR."""
import os
import sys
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QObject, QRunnable, QSettings, QThreadPool, QTimer, Signal, Slot, Qt, QSize, QDate
from PySide6.QtGui import QAction, QFontDatabase, QIcon, QPixmap, QTextDocument, QKeySequence
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QFileDialog,
                               QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QMainWindow, QMenu, QMessageBox, QPlainTextDocumentLayout,
                               QProgressBar, QSplitter, QTabBar, QTabWidget, QVBoxLayout, QWidget)

from . import __version__
from .core import Document, DocumentPage, TesseractEngine, export_document, import_document, load_project, save_project
from .diagnostics import Diagnostics
from .documents import recognize_page, render_page
from .equations import Equation, EquationError, equation_crop, render_equation
from .equation_ui import EquationEditor, RegionDialog
from .themes import stylesheet
from .workspace_widgets import (AiSettingsDialog, CandidateDialog, KeyboardDialog, PageViewer,
                                UnicodeEditor, button, row, sinhala_font, display_text, model_text)


@dataclass(eq=False)
class Session:
    document: Document
    project_path: Path | None = None
    dirty: bool = False
    text_documents: dict = field(default_factory=dict)
    thumbnails: dict = field(default_factory=dict)
    preview_cache: dict = field(default_factory=dict)


class Signals(QObject):
    completed = Signal(object)


class Task(QRunnable):
    def __init__(self, identity, operation):
        super().__init__()
        self.identity, self.operation = identity, operation
        self.signals = Signals()

    def run(self):
        try:
            result = {"id": self.identity, "result": self.operation(), "error": None}
        except Exception as error:
            result = {"id": self.identity, "result": None, "error": str(error)}
        self.signals.completed.emit(result)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        if "Noto Sans Sinhala" not in QFontDatabase.families():
            QFontDatabase.addApplicationFont(str(Path(__file__).parent / "assets" / "NotoSansSinhala.ttf"))
        self.settings = QSettings("SinhalaOCRStudio", "Desktop")
        self.diagnostics = Diagnostics()
        self.sessions = []
        self.session = None
        self.document = None
        self.busy = False
        self.jobs = {}
        self.loading = False
        self.closing = False
        self.preview_generation = 0
        self.preview_png = b""
        self.pixmap = QPixmap()
        self.zoom = 1.0
        self.setWindowTitle(f"Sinhala OCR Studio {__version__}")
        self.resize(1380, 900)
        self.setMinimumSize(980, 640)
        self.build_ui()
        self.set_theme(self.theme.currentText())
        QApplication.styleHints().colorSchemeChanged.connect(lambda _: self.set_theme(self.theme.currentText()))
        self.statusBar().showMessage("Ready · Import multiple PDFs or photos to begin")

    def build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 18, 22, 12)
        layout.setSpacing(12)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        brand = QLabel("Sinhala OCR Studio")
        brand.setObjectName("brand")
        subtitle = QLabel(f"Read. Refine. Create.  ·  v{__version__}")
        subtitle.setObjectName("subtitle")
        titles.addWidget(brand)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch()
        badge = QLabel("LOCAL WORKSPACE")
        badge.setObjectName("section")
        header.addWidget(badge)
        self.theme = QComboBox()
        self.theme.addItems(["System", "Light", "Dark"])
        self.theme.setCurrentText(self.settings.value("theme", "System"))
        self.theme.currentTextChanged.connect(self.set_theme)
        header.addWidget(self.theme)
        layout.addLayout(header)
        actions = row(button("＋ Import files", self.open_document, "primary"),
                      button("Recognize page", self.recognize),
                      button("✦ Advanced OCR", self.advanced_ocr, "ai"))
        actions.addStretch()
        actions.addWidget(button("Save project", self.save))
        actions.addWidget(button("Export document", self.export))
        more = button("More  ▾", lambda: None)
        menu = QMenu(more)
        for label, callback in [("Open saved project", self.open_project), ("Recognize visual page (ignore PDF text)", lambda: self.recognize(force_image=True)), ("Keyboard & Sinhala font", self.keyboard_settings),
                                ("AI provider settings", self.ai_settings), ("Restore previous OCR result", self.restore_result),
                                ("Export bug report", self.export_report)]:
            menu.addAction(label, callback)
        diagnostics = menu.addAction("Diagnostic logging")
        diagnostics.setCheckable(True)
        diagnostics.toggled.connect(self.enable_diagnostics)
        more.setMenu(menu)
        actions.addWidget(more)
        layout.addLayout(actions)
        self.tabs = QTabBar()
        self.tabs.setExpanding(False)
        self.tabs.setTabsClosable(True)
        self.tabs.setDrawBase(False)
        self.tabs.currentChanged.connect(self.switch_session)
        self.tabs.tabCloseRequested.connect(self.close_session)
        layout.addWidget(self.tabs)
        self.split = QSplitter()
        sidebar, side = self.card()
        side.addWidget(self.section("PAGES"))
        self.pages = QListWidget()
        self.pages.setIconSize(QSize(76, 104))
        self.pages.currentRowChanged.connect(self.switch_page)
        side.addWidget(self.pages)
        self.page_count = QLabel("No document open")
        self.page_count.setObjectName("muted")
        side.addWidget(self.page_count)
        sidebar.setMinimumWidth(155)
        sidebar.setMaximumWidth(240)
        self.split.addWidget(sidebar)
        source_card, source_layout = self.card()
        source_header = row(self.section("ORIGINAL DOCUMENT"))
        source_header.addStretch()
        source_header.addWidget(button("−", lambda: self.change_zoom(0.8)))
        source_header.addWidget(button("Fit", lambda: self.viewer.fit_page()))
        source_header.addWidget(button("＋", lambda: self.change_zoom(1.25)))
        source_layout.addLayout(source_header)
        self.viewer = PageViewer()
        self.preview = self.viewer  # compatibility name for integrations
        source_layout.addWidget(self.viewer, 1)
        navigation = row(button("‹ Previous", lambda: self.navigate_page(-1)))
        self.page_label = QLabel("Original page")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        navigation.addWidget(self.page_label, 1)
        navigation.addWidget(button("Next ›", lambda: self.navigate_page(1)))
        source_layout.addLayout(navigation)
        self.split.addWidget(source_card)
        output_card, output_layout = self.card()
        output_header = row(self.section("EDITABLE OUTPUT"))
        output_header.addStretch()
        self.latex_toggle = QCheckBox("LaTeX OFF")
        self.latex_toggle.setChecked(self.settings.value("latex_enabled", False, type=bool))
        self.latex_toggle.setText("LaTeX ON" if self.latex_toggle.isChecked() else "LaTeX OFF")
        self.latex_toggle.setToolTip("Enable equation extraction in Advanced OCR. Standard offline OCR remains text-only. Existing equations are preserved when OFF.")
        self.latex_toggle.toggled.connect(self.set_latex_mode)
        output_header.addWidget(self.latex_toggle)
        output_layout.addLayout(output_header)
        self.output_tabs = QTabWidget()
        text_panel = QWidget()
        text_panel.setObjectName("outputPanel")
        text_layout = QVBoxLayout(text_panel)
        text_layout.setContentsMargins(0, 8, 0, 0)
        editing = row(button("Undo", lambda: self.editor.undo()), button("Redo", lambda: self.editor.redo()),
                      button("Keyboard check", self.keyboard_settings),
                      button("Saved words", self.saved_words))
        editing.addStretch()
        text_layout.addLayout(editing)
        if sys.platform == "win32":
            text_layout.addWidget(button("Sinhala typing pad · Helakuru", self.windows_sinhala_editor, "primary"))
        self.editor = UnicodeEditor()
        self.editor.textChanged.connect(self.edited)
        text_layout.addWidget(self.editor, 1)
        text_layout.addWidget(button("✓ Accept this page", self.accept, "primary"))
        self.output_tabs.addTab(text_panel, "Text editor")
        equations_panel = QWidget()
        equations_panel.setObjectName("outputPanel")
        eq_layout = QVBoxLayout(equations_panel)
        equation_hint = QLabel("Equations have editable LaTeX source. Word export uses native equation objects by default.")
        equation_hint.setWordWrap(True)
        equation_hint.setObjectName("muted")
        eq_layout.addWidget(equation_hint)
        eq_layout.addLayout(row(button("Add equation", self.add_equation), button("Mark region", self.mark_equation)))
        self.equation_list = QListWidget()
        self.equation_list.itemDoubleClicked.connect(lambda _: self.edit_equation())
        eq_layout.addWidget(self.equation_list, 1)
        eq_layout.addLayout(row(button("Edit source & preview", self.edit_equation), button("Insert in text", self.insert_equation_marker)))
        eq_layout.addWidget(button("Convert selected LaTeX to equation", self.convert_selected_latex))
        self.output_tabs.addTab(equations_panel, "Equations")
        output_layout.addWidget(self.output_tabs)
        self.split.addWidget(output_card)
        self.split.setSizes([180, 600, 560])
        self.split.setStretchFactor(1, 1)
        self.split.setStretchFactor(2, 1)
        layout.addWidget(self.split, 1)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.setCentralWidget(root)
        # Keep OCR/approval shortcuts away from IME composition. Only conventional
        # file actions are application-wide; text editing shortcuts remain native.
        for shortcut, callback in [(QKeySequence.StandardKey.Open, self.open_document), (QKeySequence.StandardKey.Save, self.save)]:
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            self.addAction(action)

    @staticmethod
    def card():
        widget = QFrame()
        widget.setObjectName("card")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        return widget, layout

    @staticmethod
    def section(text):
        label = QLabel(text)
        label.setObjectName("section")
        return label

    def set_theme(self, theme):
        self.settings.setValue("theme", theme)
        dark = theme == "Dark" or (theme == "System" and QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark)
        self.setStyleSheet(stylesheet(dark))
        if hasattr(self, "viewer"):
            self.viewer.scene().invalidate()
            self.viewer.viewport().update()

    def apply_editor_font(self):
        font = sinhala_font(self.settings.value("editor/font", "Noto Sans Sinhala"))
        self.editor.setFont(font)
        for session in self.sessions:
            for text_document in session.text_documents.values():
                text_document.setDefaultFont(font)

    def keyboard_settings(self):
        KeyboardDialog(self.settings, self.apply_editor_font, self).exec()
        self.editor.setFocus()

    def windows_sinhala_editor(self):
        if not self.document or self.busy:
            return
        self.commit_input()
        from .windows_input import WindowsInputDialog
        original = self.editor.toPlainText()
        cursor = self.editor.textCursor()
        session, page = self.session, self.document.active_page
        try:
            dialog = WindowsInputDialog(cursor.selectedText(), self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # One Qt undo command; approved text changes only after Apply.
                if self.session is not session or self.document.active_page != page or self.editor.toPlainText() != original:
                    self.error("The page changed while typing. Your native editor result was not applied.")
                    return
                if dialog.result_text:
                    cursor.beginEditBlock()
                    cursor.insertText(dialog.result_text)
                    cursor.endEditBlock()
                    self.editor.setTextCursor(cursor)
        except (ValueError, RuntimeError, OSError) as error:
            self.error(str(error))
        self.editor.setFocus()

    def saved_words(self):
        from .word_memory import WordMemory, WordMemoryDialog
        if self.busy:
            return
        self.commit_input()
        cursor = self.editor.textCursor()
        try:
            dialog = WordMemoryDialog(WordMemory(), cursor.selectedText(), self)
            if dialog.exec() == QDialog.DialogCode.Accepted and self.document:
                cursor.insertText(dialog.chosen)
                self.editor.setTextCursor(cursor)
        except (ValueError, OSError) as error:
            self.error("Personal words could not be loaded. Existing files were preserved. " + str(error))
        self.editor.setFocus()

    def set_latex_mode(self, enabled):
        self.settings.setValue("latex_enabled", enabled)
        self.latex_toggle.setText("LaTeX ON" if enabled else "LaTeX OFF")
        if self.document:
            self.document.latex_enabled = enabled
            self.mark_dirty()
        self.statusBar().showMessage("LaTeX ON · Advanced OCR can suggest editable equations; manual source editing is also available" if enabled else "LaTeX OFF · Existing equation sources and edits are preserved")

    def mark_dirty(self):
        if self.session:
            self.session.dirty = True
            self.update_tab_titles()

    def update_tab_titles(self):
        for index, session in enumerate(self.sessions):
            self.tabs.setTabText(index, ("● " if session.dirty else "") + Path(session.document.source).name)

    def display_document(self, document, project_path=None):
        if not document.pages:
            document.pages = [DocumentPage(0, document.text, document.approved, document.equations)]
        session = Session(document, Path(project_path) if project_path else None)
        self.sessions.append(session)
        self.tabs.blockSignals(True)
        self.tabs.addTab(Path(document.source).name)
        self.tabs.setCurrentIndex(len(self.sessions) - 1)
        self.tabs.blockSignals(False)
        self.switch_session(len(self.sessions) - 1)
        self.start_thumbnails(session)

    def commit_input(self):
        QApplication.inputMethod().commit()
        if self.document:
            self.document.capture_page()

    def switch_session(self, index):
        if not 0 <= index < len(self.sessions):
            return
        self.commit_input()
        self.session = self.sessions[index]
        self.document = self.session.document
        self.loading = True
        self.latex_toggle.blockSignals(True)
        self.latex_toggle.setChecked(self.document.latex_enabled)
        self.latex_toggle.setText("LaTeX ON" if self.document.latex_enabled else "LaTeX OFF")
        self.latex_toggle.blockSignals(False)
        self.pages.blockSignals(True)
        self.pages.clear()
        for page_index, page in enumerate(self.document.pages):
            item = QListWidgetItem(f"Page {page_index + 1}")
            if page_index in self.session.thumbnails:
                pixmap = QPixmap()
                pixmap.loadFromData(self.session.thumbnails[page_index])
                item.setIcon(QIcon(pixmap))
            self.pages.addItem(item)
        self.pages.setCurrentRow(self.document.active_page)
        self.pages.blockSignals(False)
        self.page_count.setText(f"{len(self.document.pages)} page(s) · {len(self.sessions)} document(s)")
        self.loading = False
        self.show_active_page()

    def switch_page(self, index):
        if not self.document or self.loading or not 0 <= index < len(self.document.pages):
            return
        self.commit_input()
        self.document.activate_page(index)
        self.show_active_page()

    def navigate_page(self, delta):
        if self.document:
            index = self.document.active_page + delta
            if 0 <= index < len(self.document.pages):
                self.pages.setCurrentRow(index)

    def show_active_page(self):
        self.loading = True
        index = self.document.active_page
        if index not in self.session.text_documents:
            text_document = QTextDocument(self)
            text_document.setDocumentLayout(QPlainTextDocumentLayout(text_document))
            text_document.setDefaultFont(sinhala_font(self.settings.value("editor/font", "Noto Sans Sinhala")))
            text_document.setPlainText(display_text(self.document.text, self.document.equations))
            self.session.text_documents[index] = text_document
        self.editor.setDocument(self.session.text_documents[index])
        self.apply_editor_font()
        self.refresh_equations()
        self.loading = False
        self.page_label.setText(f"Page {index + 1} of {len(self.document.pages)}")
        self.request_preview()
        self.editor.setFocus()

    def request_preview(self):
        self.preview_generation += 1
        generation = self.preview_generation
        session, index = self.session, self.document.active_page
        self.preview_png = b""
        self.pixmap = QPixmap()
        self.viewer.set_message("Loading page…")
        def complete(data):
            if session not in self.sessions:
                return
            session.preview_cache[index] = data
            while len(session.preview_cache) > 3:
                del session.preview_cache[next(iter(session.preview_cache))]
            if self.session is session and self.document.active_page == index and generation == self.preview_generation:
                self.preview_png = data
                self.pixmap.loadFromData(data)
                if self.pixmap.isNull():
                    self.viewer.set_message("This page could not be displayed.")
                    return
                self.viewer.set_page(self.pixmap)
                self.pages.item(index).setIcon(QIcon(self.pixmap.scaled(76, 104, Qt.AspectRatioMode.KeepAspectRatio)))
        def failed(message):
            if generation == self.preview_generation:
                self.viewer.set_message("Preview unavailable\n" + message)
        if index in session.preview_cache:
            complete(session.preview_cache[index])
        else:
            self.background(lambda: render_page(session.document.source, session.document.pages[index].source_index), complete, exclusive=False, on_error=failed)

    def start_thumbnails(self, session):
        if not Path(session.document.source).exists():
            return
        def render():
            result = {}
            for index, page in enumerate(session.document.pages[:60]):
                result[index] = render_page(session.document.source, page.source_index, 150)
            return result
        def complete(result):
            session.thumbnails.update(result)
            if self.session is session:
                for index, data in result.items():
                    pixmap = QPixmap()
                    pixmap.loadFromData(data)
                    self.pages.item(index).setIcon(QIcon(pixmap))
        self.background(render, complete, exclusive=False, on_error=lambda message: self.statusBar().showMessage("Some thumbnails could not load: " + message))

    def change_zoom(self, factor):
        self.viewer.zoom_by(factor)

    def edited(self):
        if self.document and not self.loading:
            self.document.text = model_text(self.editor.toPlainText(), self.document.equations)
            self.document.approved = False
            self.document.capture_page()
            self.mark_dirty()

    def open_document(self):
        if self.busy:
            return
        names, _ = QFileDialog.getOpenFileNames(self, "Import PDFs and photos", "", "Documents (*.pdf *.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp)")
        if not names:
            return
        preferred = self.settings.value("latex_enabled", False, type=bool)
        def operation():
            documents, errors = [], []
            for name in names:
                try:
                    document = import_document(Path(name))
                    document.latex_enabled = preferred
                    documents.append(document)
                except Exception as error:
                    errors.append(f"{Path(name).name}: {error}")
            return documents, errors
        def complete(result):
            documents, errors = result
            for document in documents:
                existing = next((i for i, session in enumerate(self.sessions) if Path(session.document.source).resolve() == Path(document.source).resolve()), None)
                if existing is None:
                    self.display_document(document)
                else:
                    self.tabs.setCurrentIndex(existing)
            if errors:
                self.error("\n".join(errors))
            else:
                self.statusBar().showMessage(f"{len(documents)} document(s) opened · Switch tabs or select page thumbnails")
        self.background(operation, complete)

    def open_project(self):
        if self.busy:
            return
        name, _ = QFileDialog.getOpenFileName(self, "Open saved project", "", "Studio project (*.sos.json)")
        if name:
            try:
                self.display_document(load_project(Path(name)), Path(name))
            except Exception as error:
                self.error(str(error))

    def save(self):
        return self.save_session(self.session) if self.session else False

    def save_session(self, session):
        self.commit_input()
        path = session.project_path
        if not path:
            name, _ = QFileDialog.getSaveFileName(self, "Save all pages in this project", Path(session.document.source).stem + ".sos.json", "Studio project (*.sos.json)")
            if not name:
                return False
            path = Path(name)
        try:
            save_project(session.document, path)
            session.project_path = path
            session.dirty = False
            self.update_tab_titles()
            self.statusBar().showMessage("Project saved · All pages, equations and corrections preserved")
            return True
        except Exception as error:
            self.error(str(error))
            return False

    def confirm_close(self, session):
        if not session.dirty:
            return True
        answer = QMessageBox.question(self, "Save changes before closing?", f"Save changes to {Path(session.document.source).name}?",
                                      QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                      QMessageBox.StandardButton.Save)
        if answer == QMessageBox.StandardButton.Save:
            return self.save_session(session)
        return answer == QMessageBox.StandardButton.Discard

    def safe_to_replace(self):
        return not self.busy and (not self.session or self.confirm_close(self.session))

    def close_session(self, index):
        if self.busy or not 0 <= index < len(self.sessions):
            return
        self.commit_input()
        session = self.sessions[index]
        if not self.confirm_close(session):
            return
        self.tabs.blockSignals(True)
        self.tabs.removeTab(index)
        self.tabs.blockSignals(False)
        self.sessions.pop(index)
        if self.sessions:
            target = min(index, len(self.sessions) - 1)
            self.tabs.setCurrentIndex(target)
            self.switch_session(target)
        else:
            self.document = self.session = None
            self.preview_generation += 1
            self.pages.clear()
            self.equation_list.clear()
            self.loading = True
            blank = QTextDocument(self)
            blank.setDocumentLayout(QPlainTextDocumentLayout(blank))
            self.editor.setDocument(blank)
            self.loading = False
            self.viewer.set_message("Import a PDF or photo to start")
            self.page_label.setText("No document open")
            self.page_count.setText("No document open")
        for text_document in session.text_documents.values():
            text_document.deleteLater()

    def refresh_equations(self):
        self.equation_list.clear()
        if self.document:
            for index, equation in enumerate(self.document.equations, 1):
                self.equation_list.addItem(f"Equation {index}  ·  {equation.placement}  ·  {equation.status}\n{equation.latex[:65] or 'Enter LaTeX source…'}")

    def insert_marker_at_cursor(self, marker):
        self.commit_input()
        cursor = self.editor.textCursor()
        cursor.setPosition(cursor.selectionEnd())
        self.editor.setTextCursor(cursor)
        self.editor.insertPlainText(display_text(marker, self.document.equations))

    def attach_equation(self, equation):
        self.document.equations.append(equation)
        self.insert_marker_at_cursor(equation.marker)
        self.refresh_equations()
        self.equation_list.setCurrentRow(len(self.document.equations) - 1)

    def add_equation(self):
        if self.document and not self.busy:
            self.attach_equation(Equation())
            self.edit_equation()

    def mark_equation(self):
        if not self.document or not self.preview_png:
            return
        dialog = RegionDialog(self.pixmap, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            equation = equation_crop(BytesIO(self.preview_png), dialog.selector.source_bbox())
            self.attach_equation(equation)
            self.edit_equation()

    def edit_equation(self):
        index = self.equation_list.currentRow()
        if self.document and 0 <= index < len(self.document.equations):
            EquationEditor(self.document.equations[index], self).exec()
            self.document.approved = False
            self.document.capture_page()
            self.refresh_equations()
            self.equation_list.setCurrentRow(index)
            self.mark_dirty()

    def insert_equation_marker(self):
        index = self.equation_list.currentRow()
        if self.document and 0 <= index < len(self.document.equations):
            marker = self.document.equations[index].marker
            if marker in self.document.text:
                self.error("This equation is already in the text. Move its equation reference to change its position.")
            else:
                self.insert_marker_at_cursor(marker)

    def convert_selected_latex(self):
        if not self.document:
            return
        cursor = self.editor.textCursor()
        source = cursor.selectedText().replace("\u2029", "\n").strip()
        if not source:
            self.error("Select LaTeX source in the text editor first, such as E=\\frac{1}{2}mv^2.")
            return
        for left, right in [("$$", "$$"), ("\\[", "\\]"), ("\\(", "\\)"), ("$", "$")]:
            if source.startswith(left) and source.endswith(right):
                source = source[len(left):-len(right)]
                break
        try:
            render_equation(source)
        except EquationError as error:
            self.error(str(error))
            return
        equation = Equation(latex=source, original_latex=source)
        self.document.equations.append(equation)
        cursor.insertText(display_text(equation.marker, self.document.equations))
        self.refresh_equations()
        self.equation_list.setCurrentRow(len(self.document.equations) - 1)
        self.edit_equation()

    def accept(self):
        if self.document:
            self.document.approved = True
            self.document.capture_page()
            self.mark_dirty()
            self.statusBar().showMessage("Page accepted · Save project to keep the approval")

    def apply_candidate(self, session, index, text, equations):
        from .equation_export import document_parts
        document_parts(Document(session.document.source, text, equations=equations))
        page = session.document.pages[index]
        page.history.append({"text": page.text, "approved": page.approved, "equations": [asdict(eq) for eq in page.equations]})
        page.text, page.approved, page.equations = text, False, equations
        if session.document.active_page == index:
            session.document.text, session.document.approved, session.document.equations = text, False, equations
        self.replace_page_text_document(session, index)
        session.dirty = True
        self.update_tab_titles()
        if self.session is session and self.document.active_page == index:
            self.show_active_page()

    def replace_page_text_document(self, session, index):
        # Keep native undo for manual edits on each page; replacing a result has
        # its own persisted page history including equation states.
        if index in session.text_documents:
            was_loading = self.loading
            self.loading = True
            session.text_documents[index].setPlainText(display_text(session.document.pages[index].text, session.document.pages[index].equations))
            self.loading = was_loading

    def review_candidate(self, session, index, text, equations=None, ai=False):
        if session not in self.sessions:
            return
        self.tabs.setCurrentIndex(self.sessions.index(session))
        self.pages.setCurrentRow(index)
        equations = equations or []
        dialog = CandidateDialog(display_text(text, equations), len(equations), ai, self)
        dialog.setWindowTitle(f"Review suggestion · {Path(session.document.source).name} · Page {index + 1}")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_candidate(session, index, text, equations)
            self.statusBar().showMessage("Suggestion applied · Review equations, then Save project")

    def restore_result(self):
        if not self.document:
            return
        page = self.document.pages[self.document.active_page]
        if not page.history:
            self.error("No earlier OCR result is stored for this page.")
            return
        if QMessageBox.question(self, "Restore previous page?", "Replace the current page with its previous saved result? Current text is retained in page history.") != QMessageBox.StandardButton.Yes:
            return
        previous = page.history.pop()
        self.apply_candidate(self.session, self.document.active_page, previous["text"], [Equation(**eq) for eq in previous["equations"]])
        self.document.approved = previous["approved"]
        self.document.capture_page()

    def recognize(self, force_image=False):
        if not self.document or self.busy:
            return
        self.commit_input()
        session, index = self.session, self.document.active_page
        snapshot = deepcopy(self.document)
        self.background(lambda: recognize_page(snapshot, index, force_image), lambda result: self.review_candidate(session, index, result.text))

    def ai_settings(self):
        return AiSettingsDialog(self.settings, self).exec()

    def advanced_ocr(self, equation_editor=None):
        if not self.document or self.busy:
            return
        from .advanced_ocr import CredentialStore, DEFAULT_MODEL, recognize_with_ai
        try:
            key = CredentialStore().get()
            if not key:
                if self.ai_settings() != QDialog.DialogCode.Accepted:
                    return
                key = CredentialStore().get()
            if not key:
                self.error("An API key is required. Enter it under More → AI provider settings.")
                return
        except ValueError as error:
            self.error(str(error))
            return
        today = QDate.currentDate().toString(Qt.DateFormat.ISODate)
        used = self.settings.value("ai/requests", 0, type=int) if self.settings.value("ai/day", "") == today else 0
        limit = self.settings.value("ai/daily_limit", 10, type=int)
        if used >= limit:
            self.error("Daily AI request limit reached. Review your usage and provider spending limit before increasing it in AI settings.")
            return
        session, index = self.session, self.document.active_page
        model = self.settings.value("ai/model", DEFAULT_MODEL)
        target = "the selected equation crop" if equation_editor else f"page {index + 1} of {Path(self.document.source).name}"
        answer = QMessageBox.question(self, "Send image to OpenAI?",
                                      f"Upload {target} to OpenAI for AI transcription?\n\nModel: {model}\nRequests today: {used}/{limit}\nMaximum output: 4,096 tokens. API charges may apply. Set a spending limit in your provider account.\n\nOnly the selected image is sent. The suggestion will be shown for review; your current text will not change automatically.",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.commit_input()
        self.settings.setValue("ai/day", today)
        self.settings.setValue("ai/requests", used + 1)
        self.settings.sync()
        source, source_index, latex = self.document.source, self.document.pages[index].source_index, self.document.latex_enabled
        crop = equation_editor.equation.image_png if equation_editor else None
        initial_source = equation_editor.source.toPlainText() if equation_editor else None
        def operation():
            if crop:
                import base64
                data = base64.b64decode(crop)
            else:
                data = render_page(source, source_index, 2000)
            return recognize_with_ai(data, consent=True, api_key=key, latex_enabled=True if crop else latex, model=model)
        def complete(result):
            self.statusBar().showMessage(f"AI suggestion received · {result.input_tokens} input / {result.output_tokens} output tokens")
            if equation_editor:
                if not equation_editor.isVisible():
                    return
                if len(result.equations) != 1:
                    self.error("The crop did not produce exactly one equation. Select a tighter region and try again; existing source was preserved.")
                    return
                if equation_editor.source.toPlainText() != initial_source:
                    self.error("Equation source changed during recognition; it was preserved. Try again when editing is complete.")
                    return
                if QMessageBox.question(equation_editor, "Review recognized equation",
                                        "Replace the source with this AI suggestion? Compare it with the crop before accepting.\n\n" + result.equations[0].latex,
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                    return
                equation_editor.source.selectAll()
                equation_editor.source.insertPlainText(result.equations[0].latex)
                equation_editor.update_preview()
            else:
                self.review_candidate(session, index, result.text, result.equations, ai=True)
        self.background(operation, complete)

    def export(self):
        if not self.document or self.busy:
            return
        self.commit_input()
        name, _ = QFileDialog.getSaveFileName(self, "Export all pages · editable Word equations", Path(self.document.source).stem + ".docx", "Word with editable equations (*.docx);;Unicode text (*.txt);;Markdown (*.md);;LaTeX source (*.tex)")
        if not name:
            return
        snapshot = self.document.for_export()
        image_fallback = False
        if snapshot.equations and Path(name).suffix.lower() == ".docx":
            from .equation_export import editable_equation_errors
            try:
                errors = editable_equation_errors(snapshot)
            except EquationError as error:
                self.error(str(error) + " Open the Equations tab to review the source.")
                return
            if errors:
                if not all(eq.image_png for eq, _ in errors):
                    self.error("An equation cannot be converted to an editable Word object. Edit its LaTeX source; no image replacement was made.")
                    return
                image_fallback = QMessageBox.question(self, "Editable conversion unavailable", "Some equations cannot be exported as editable Word objects. Export those original crops as labelled non-editable images instead? Choose No to edit the LaTeX source.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
                if not image_fallback:
                    return
        def complete(_):
            self.statusBar().showMessage("Export saved · Explicit image fallback included" if image_fallback else f"Export saved · {len(snapshot.equations)} editable equation(s) · All pages included")
        self.background(lambda: export_document(snapshot, Path(name), image_fallback=image_fallback), complete)

    def background(self, operation, callback, *, exclusive=True, on_error=None):
        identity = uuid4().hex
        task = Task(identity, operation)
        self.jobs[identity] = (task, callback, exclusive, on_error)
        if exclusive:
            self.busy = True
            self.progress.setRange(0, 0)
            self.progress.show()
            self.statusBar().showMessage("Working… You can browse your documents while this completes.")
        task.signals.completed.connect(self.job_finished)
        QThreadPool.globalInstance().start(task)

    @Slot(object)
    def job_finished(self, result):
        _, callback, _, on_error = self.jobs.pop(result["id"])
        self.busy = any(job[2] for job in self.jobs.values())
        if not self.busy:
            self.progress.hide()
        if self.closing:
            return
        try:
            if result["error"]:
                (on_error or self.error)(result["error"])
            else:
                callback(result["result"])
        except Exception as error:
            self.error(str(error))

    def enable_diagnostics(self, enabled):
        self.diagnostics.enabled = enabled
        self.diagnostics.record("startup")

    def export_report(self):
        name, _ = QFileDialog.getSaveFileName(self, "Export diagnostic report", "sinhala-ocr-report.zip", "ZIP (*.zip)")
        if name:
            try:
                if any(Path(name).resolve() == Path(session.document.source).resolve() for session in self.sessions):
                    raise ValueError("Cannot overwrite an original source.")
                self.diagnostics.record("export_report")
                self.diagnostics.export(Path(name))
            except Exception as error:
                self.error(str(error))

    def error(self, message):
        self.diagnostics.record("operation_failed")
        QMessageBox.warning(self, "Operation could not complete", message)

    def closeEvent(self, event):
        if self.busy:
            self.error("Please wait for the current OCR/import/export operation to finish.")
            event.ignore()
            return
        self.commit_input()
        if self.document and not all(self.confirm_close(session) for session in self.sessions):
            event.ignore()
            return
        self.closing = True
        self.preview_generation += 1
        event.accept()


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
    app.setStyle("Fusion")
    QFontDatabase.addApplicationFont(str(Path(__file__).parent / "assets" / "NotoSansSinhala.ttf"))
    window = MainWindow()
    window.show()
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(200, lambda: smoke_test(app, window))
    result = app.exec()
    QThreadPool.globalInstance().waitForDone()
    if smoke_settings:
        smoke_settings.cleanup()
    return result


def smoke_test(app, window):
    from .smoke_report import SmokeReport
    from contextlib import ExitStack
    import tempfile
    from PIL import Image
    from pypdf import PdfWriter
    report = SmokeReport()
    try:
        with tempfile.TemporaryDirectory() as folder, ExitStack() as cleanup:
            cleanup.callback(QThreadPool.globalInstance().waitForDone)
            image = Path(folder) / "blank.png"
            Image.new("RGB", (500, 200), "white").save(image)
            report.phase("offline_ocr")
            report.check(not TesseractEngine().recognize(image).text.strip(), "Blank-image OCR returned unexpected text")
            if sys.platform == "win32":
                report.phase("windows_credential_backend")
                from .advanced_ocr import CredentialStore
                CredentialStore().backend()  # Check packaging only; do not read/store credentials.
                if app.platformName() == "windows":
                    report.phase("native_typing_pad")
                    from .windows_input import WindowsInputDialog
                    native = WindowsInputDialog("වස්තුවක්\nසිංහල x²", window)
                    native.show()
                    app.processEvents()
                    report.check(native.control.text() == "", "Typing pad was not initially empty")
                    for character in "වස්තුවක්\nසිංහල x²":
                        native.control.message(0x102, 13 if character == "\n" else ord(character))
                    native.accept()
                    report.check(native.result_text == "වස්තුවක්\nසිංහල x²",
                                 "Synthetic multiline typing differs: expected " + repr("වස්තුවක්\nසිංහල x²") + "; actual " + repr(native.result_text))
            report.phase("pdf_import_render")
            pdf = Path(folder) / "pages.pdf"
            writer = PdfWriter()
            writer.add_blank_page(300, 400)
            writer.add_blank_page(400, 300)
            writer.write(pdf)
            document = import_document(pdf)
            report.check(len(document.pages) == 2, "Expected two imported PDF pages")
            report.check(render_page(pdf, 1).startswith(b"\x89PNG"), "PDFium did not return a PNG")
            report.phase("workspace_and_equation_preview")
            window.display_document(document)
            window.pages.setCurrentRow(1)
            window.editor.setPlainText("සිංහල වස්තුවක් English x² = ½")
            window.latex_toggle.setChecked(True)
            equation = Equation(latex=r"E=\frac{1}{2}mv^2", placement="inline")
            equation.accept()
            window.attach_equation(equation)
            preview = EquationEditor(equation, window)
            report.check(preview.update_preview(), "Equation preview failed: " + preview.message.text())
            report.phase("docx_export")
            export_document(document, Path(folder) / "smoke.docx")
            report.phase("tabs_and_themes")
            window.display_document(import_document(image))
            window.tabs.setCurrentIndex(0)
            report.check("වස්තුවක්" in window.editor.toPlainText(), "Page text was not preserved when switching tabs")
            for theme in ["Dark", "Light"]:
                window.theme.setCurrentText(theme)
            # Drain page rendering before temporary source files disappear.
            QThreadPool.globalInstance().waitForDone()
            app.processEvents()
        report.finish()
        app.exit(0)
    except Exception as error:
        report.fail(error)
        app.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
