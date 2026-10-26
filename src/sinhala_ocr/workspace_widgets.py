"""Reusable document-view widgets and explicit review/consent dialogs."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QPainter, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                               QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout)

from .advanced_ocr import CredentialStore, DEFAULT_MODEL


def sinhala_font(family="Noto Sans Sinhala", size=13):
    font = QFont()
    font.setFamilies([family, "Noto Sans Sinhala", "Nirmala UI", "Iskoola Pota", "Segoe UI"])
    font.setPointSize(size)
    return font


class UnicodeEditor(QPlainTextEdit):
    """Native Qt plain-text editing: no key remapping, normalization or filtering."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        self.setInputMethodHints(Qt.InputMethodHint.ImhNone)
        self.setFont(sinhala_font())
        self.setTabChangesFocus(False)
        self.setPlaceholderText("Recognized text appears here. Click to type with your installed Sinhala keyboard.")


class PageViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene_object = QGraphicsScene(self)
        self.setScene(self.scene_object)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.fit_mode = True
        self.image_item = None
        self.pixmap = QPixmap()
        self.set_message("Import a PDF or photo to start\nYour original page will appear here")

    def set_message(self, text):
        self.scene_object.clear()
        self.image_item = None
        self.pixmap = QPixmap()
        self.resetTransform()
        item = self.scene_object.addText(text)
        item.setDefaultTextColor(Qt.GlobalColor.gray)
        self.setSceneRect(item.boundingRect())

    def set_page(self, pixmap):
        self.scene_object.clear()
        self.pixmap = pixmap
        self.image_item = self.scene_object.addPixmap(pixmap)
        self.image_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.setSceneRect(self.image_item.boundingRect())
        self.fit_page()

    def fit_page(self):
        self.fit_mode = True
        if self.image_item:
            self.fitInView(self.image_item, Qt.AspectRatioMode.KeepAspectRatio)

    def zoom_by(self, factor):
        if self.image_item:
            self.fit_mode = False
            scale = self.transform().m11() * factor
            if 0.05 <= scale <= 8:
                self.scale(factor, factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fit_mode:
            self.fit_page()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom_by(1.2 if event.angleDelta().y() > 0 else 1 / 1.2)
            event.accept()
        else:
            super().wheelEvent(event)


class CandidateDialog(QDialog):
    def __init__(self, text, equation_count=0, ai=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review AI suggestion" if ai else "Review OCR result")
        self.resize(800, 650)
        layout = QVBoxLayout(self)
        label = QLabel("Compare this suggestion with the original page before applying it. AI may transcribe incorrectly." if ai else "Review the recognized text. Applying it replaces the current page and saves its previous contents in page history.")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.text = UnicodeEditor()
        self.text.setReadOnly(True)
        self.text.setPlainText(text)
        layout.addWidget(self.text)
        layout.addWidget(QLabel(f"{equation_count} separate equation(s) returned. Review their sources before export." if ai else "Offline text OCR does not recognize separate equations. Use Equations → Recognize page equations · AI, or enter LaTeX manually."))
        self.confirm = QCheckBox("Replace this page’s text and equations; preserve the previous version in page history")
        layout.addWidget(self.confirm)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Apply to this page")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.confirm.toggled.connect(buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class AiSettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Advanced OCR · provider settings")
        self.resize(560, 360)
        layout = QVBoxLayout(self)
        info = QLabel("Advanced OCR uses OpenAI’s image-capable API. An API account with billing is required; a ChatGPT subscription alone does not supply API credits. Keys are stored in the operating-system credential vault. Uploads require consent for each page.")
        info.setWordWrap(True)
        layout.addWidget(info)
        form = QFormLayout()
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("New API key (leave blank to keep the saved key)")
        form.addRow("API key", self.key)
        self.model = QLineEdit(settings.value("ai/model", DEFAULT_MODEL))
        form.addRow("Model", self.model)
        self.limit = QSpinBox()
        self.limit.setRange(1, 50)
        self.limit.setValue(settings.value("ai/daily_limit", 10, type=int))
        form.addRow("Daily request limit", self.limit)
        layout.addLayout(form)
        self.message = QLabel("One selected page per request · up to 4,096 output tokens · no automatic retries.")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        delete = QPushButton("Remove saved API key")
        delete.clicked.connect(self.remove_key)
        layout.addWidget(delete)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save_settings(self):
        import re
        from .advanced_ocr import AdvancedOcrError
        try:
            if not re.fullmatch(r"[A-Za-z0-9._:-]{1,100}", self.model.text()):
                raise AdvancedOcrError("Enter a valid model identifier.")
            if self.key.text():
                CredentialStore().save(self.key.text())
                self.key.clear()
            self.settings.setValue("ai/model", self.model.text())
            self.settings.setValue("ai/daily_limit", self.limit.value())
            self.accept()
        except AdvancedOcrError as error:
            self.message.setText(str(error))

    def remove_key(self):
        try:
            CredentialStore().delete()
            self.message.setText("Saved API key removed.")
        except ValueError as error:
            self.message.setText(str(error))


class KeyboardDialog(QDialog):
    def __init__(self, settings, apply_font, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Qt font diagnostic — use Sinhala typing pad for Helakuru")
        self.resize(700, 450)
        layout = QVBoxLayout(self)
        help_text = QLabel("This is the Qt diagnostic editor, not the native Sinhala typing pad. Direct Helakuru typing here has a reported repeated-character defect. Use the main window’s Sinhala typing pad button for native input; Notepad then paste remains the confirmed workaround.\n\nSelect your installed Helakuru Sinhala input mode in Windows, click the typing area, and type වස්තුවක්. This panel preserves exactly what the input method commits. Try another font if the same text has misplaced vowel signs. Repeated letters in the Unicode output indicate an input sequence problem, not just a font. If direct typing repeats letters, compare typing in Windows Notepad and paste that text here with Ctrl+V. Correct pasted text isolates the problem to direct input; preserve your text rather than deleting repeated letters automatically.")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        combo = QComboBox()
        families = QFontDatabase.families()
        combo.addItems([name for name in ["Noto Sans Sinhala", "Nirmala UI", "Iskoola Pota"] if name in families])
        combo.setCurrentText(settings.value("editor/font", "Noto Sans Sinhala"))
        layout.addWidget(combo)
        pad = UnicodeEditor()
        pad.setPlaceholderText("Click here and type වස්තුවක් with Helakuru")
        layout.addWidget(pad)
        codes = QLabel("Unicode output appears here after text is committed.")
        codes.setWordWrap(True)
        layout.addWidget(codes)
        pad.textChanged.connect(lambda: codes.setText(" ".join(f"U+{ord(c):04X}" for c in pad.toPlainText()[:100])))
        def changed(name):
            settings.setValue("editor/font", name)
            pad.setFont(sinhala_font(name))
            apply_font()
        combo.currentTextChanged.connect(changed)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)
        pad.setFocus()


def button(text, callback, name=""):
    widget = QPushButton(text)
    widget.setObjectName(name)
    widget.clicked.connect(callback)
    return widget


def row(*widgets):
    layout = QHBoxLayout()
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def display_text(text, equations):
    for index, equation in enumerate(equations, 1):
        text = text.replace(equation.marker, f"⟦Equation {index}⟧")
    return text


def model_text(text, equations):
    for index, equation in enumerate(equations, 1):
        text = text.replace(f"⟦Equation {index}⟧", equation.marker)
    return text
