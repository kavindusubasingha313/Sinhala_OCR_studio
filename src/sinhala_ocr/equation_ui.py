"""Native Qt equation editor and image-region selection, with local SVG preview."""
from PySide6.QtCore import QByteArray, QRect, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QHBoxLayout,
                               QLabel, QPlainTextEdit, QPushButton, QRubberBand,
                               QScrollArea, QVBoxLayout)

from .equations import EquationError, render_equation


class EquationEditor(QDialog):
    def __init__(self, equation, parent=None):
        super().__init__(parent)
        self.equation = equation
        self.setWindowTitle("Equation editor — changes kept in project; Save project to persist")
        self.resize(780, 650)
        layout = QVBoxLayout(self)
        original = QLabel("Original equation image (none for a manually entered equation)")
        original.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if equation.image_png:
            import base64
            image = QPixmap()
            image.loadFromData(base64.b64decode(equation.image_png))
            original.setPixmap(image.scaled(700, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(original)
        self.offline_button = QPushButton("Recognize equation · Offline")
        self.offline_button.setEnabled(bool(equation.image_png) and hasattr(parent, "offline_equation"))
        self.offline_button.clicked.connect(lambda: parent.offline_equation(self))
        layout.addWidget(self.offline_button)
        self.recognize_button = QPushButton("Recognize this equation · AI")
        self.recognize_button.setEnabled(bool(equation.image_png) and hasattr(parent, "advanced_ocr"))
        self.recognize_button.clicked.connect(lambda: parent.advanced_ocr(equation_editor=self))
        layout.addWidget(self.recognize_button)
        note = QLabel("With LaTeX ON, Offline recognizes this crop on your CPU without uploads. Review the suggestion before accepting. The optional AI button uses your API key and asks before uploading.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.placement = QComboBox()
        self.placement.addItems(["inline", "display"])
        self.placement.setCurrentText(equation.placement)
        self.placement.currentTextChanged.connect(self.change_placement)
        layout.addWidget(self.placement)
        layout.addWidget(QLabel("LaTeX source — enter math without $ delimiters"))
        self.source = QPlainTextEdit(equation.latex)
        self.source.setPlaceholderText(r"E = \frac{1}{2}mv^2")
        self.source.textChanged.connect(self.changed)
        layout.addWidget(self.source)
        self.preview = QSvgWidget()
        self.preview.setStyleSheet("background: white;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.preview)
        layout.addWidget(scroll)
        self.message = QLabel()
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        controls = QHBoxLayout()
        for title, callback in [("Accept", self.accept_equation), ("Reject", self.reject_equation),
                                ("Undo", self.source.undo), ("Redo", self.source.redo),
                                ("Restore Original", self.restore_original)]:
            button = QPushButton(title)
            button.clicked.connect(callback)
            controls.addWidget(button)
        layout.addLayout(controls)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.close)
        layout.addWidget(close)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.update_preview)
        self.update_preview()

    def changed(self):
        self.equation.edit(self.source.toPlainText())
        self.preview.hide()  # Never leave a stale preview beside changed source.
        self.message.setText("Updating preview…")
        self.timer.start()

    def change_placement(self, placement):
        self.equation.placement = placement
        self.equation.status = "draft"
        self.update_preview()

    def update_preview(self):
        self.timer.stop()
        try:
            svg = render_equation(self.equation.latex, self.equation.placement)
            self.preview.load(QByteArray(svg))
            self.preview.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
            if not self.preview.renderer().isValid():
                raise EquationError("Qt could not display the equation preview.")
            self.preview.show()
            self.message.setText(f"{self.equation.status.capitalize()} · Local preview; Word appearance still requires verification.")
            return True
        except EquationError as error:
            self.preview.hide()
            self.message.setText(str(error))
            return False

    def accept_equation(self):
        if self.update_preview():
            self.equation.accept()
            self.message.setText("Accepted · Save project to persist this equation.")

    def reject_equation(self):
        self.equation.status = "rejected"
        self.message.setText("Rejected · Source and image retained. Remove its text marker to omit it from export, or edit and Accept again.")

    def restore_original(self):
        # Use the native document undo stack; restoration is itself undoable.
        self.source.selectAll()
        self.source.insertPlainText(self.equation.original_latex)
        self.equation.status = "draft"
        self.update_preview()


class RegionSelector(QLabel):
    def __init__(self, pixmap):
        super().__init__()
        self.original = pixmap
        self.original_size = pixmap.size()
        self.setPixmap(pixmap.scaled(900, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setFixedSize(self.pixmap().size())
        self.band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.origin = None
        self.selection = QRect()

    def set_zoom(self, scale):
        bbox = self.source_bbox() if self.selection.width() >= 3 and self.selection.height() >= 3 else None
        scale = max(0.1, min(4.0, scale))
        self.setPixmap(self.original.scaled(
            round(self.original_size.width() * scale), round(self.original_size.height() * scale),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setFixedSize(self.pixmap().size())
        if bbox:
            sx = self.width() / self.original_size.width()
            sy = self.height() / self.original_size.height()
            x, y, right, bottom = bbox
            self.selection = QRect(round(x * sx), round(y * sy), round((right-x) * sx), round((bottom-y) * sy))
            self.band.setGeometry(self.selection)
            self.band.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.position().toPoint()
            self.selection = QRect()
            self.band.setGeometry(QRect(self.origin, self.origin))
            self.band.show()

    def mouseMoveEvent(self, event):
        if self.origin is not None:
            self.selection = QRect(self.origin, event.position().toPoint()).normalized().intersected(self.rect())
            self.band.setGeometry(self.selection)

    def mouseReleaseEvent(self, event):
        self.mouseMoveEvent(event)
        self.origin = None

    def source_bbox(self):
        if self.selection.width() < 3 or self.selection.height() < 3:
            raise EquationError("Drag across an equation region before choosing Use region.")
        sx = self.original_size.width() / self.width()
        sy = self.original_size.height() / self.height()
        rect = self.selection
        return (int(rect.x() * sx), int(rect.y() * sy),
                min(self.original_size.width(), int((rect.x() + rect.width()) * sx)),
                min(self.original_size.height(), int((rect.y() + rect.height()) * sy)))


class RegionDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mark equation — drag around the original expression")
        layout = QVBoxLayout(self)
        self.selector = RegionSelector(pixmap)
        self.resize(1000, 750)
        toolbar = QHBoxLayout()
        self.zoom_label = QLabel()
        for title, callback in [("−", lambda: self.zoom(1 / 1.25)),
                                ("+", lambda: self.zoom(1.25)),
                                ("100%", lambda: self.set_zoom(1)), ("Fit", self.fit)]:
            control = QPushButton(title)
            control.clicked.connect(callback)
            toolbar.addWidget(control)
        toolbar.addWidget(self.zoom_label)
        layout.addLayout(toolbar)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.selector)
        layout.addWidget(self.scroll, 1)
        self.set_zoom(self.selector.width() / pixmap.width())
        self.message = QLabel("Drag to select an equation. The original crop will be embedded in your project.")
        layout.addWidget(self.message)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Use region")
        buttons.accepted.connect(self.use_region)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def set_zoom(self, scale):
        self.selector.set_zoom(scale)
        self.zoom_label.setText(f"{self.selector.width() / self.selector.original_size.width():.0%}")

    def zoom(self, factor):
        self.set_zoom(self.selector.width() / self.selector.original_size.width() * factor)

    def fit(self):
        size = self.scroll.viewport().size()
        original = self.selector.original_size
        self.set_zoom(min(size.width() / original.width(), size.height() / original.height()))

    def use_region(self):
        try:
            self.selector.source_bbox()
        except EquationError as error:
            self.message.setText(str(error))
        else:
            self.accept()
