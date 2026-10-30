"""Explicit clipboard/file intake; captured images remain local and persistent."""
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QBuffer, QIODevice, QStandardPaths, Qt
from PySide6.QtGui import QImage, QImageReader, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDialogButtonBox,
                               QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout)

from .core import atomic_write

MAX_PIXELS = 12_000_000


def checked_image(image):
    if image.isNull():
        raise ValueError("No readable image found. Copy an image or use Windows Snipping Tool, then choose Paste image.")
    if image.width() * image.height() > MAX_PIXELS:
        raise ValueError("Select a smaller crop (maximum 12 megapixels).")
    return image.copy()


def read_image(path):
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    size = reader.size()
    if size.width() * size.height() > MAX_PIXELS:
        raise ValueError("Select a smaller crop (maximum 12 megapixels).")
    return checked_image(reader.read())


def persist_image(image, directory=None):
    image = checked_image(image)
    # Composite transparency on paper-white, without changing the captured original.
    from PySide6.QtGui import QPainter
    white = QImage(image.size(), QImage.Format.Format_RGB32)
    white.fill(Qt.GlobalColor.white)
    painter = QPainter(white)
    painter.drawImage(0, 0, image)
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not white.save(buffer, 'PNG'):
        raise ValueError("Could not encode the captured image.")
    directory = Path(directory or Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)) / 'captured-images')
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f'Capture-{uuid4().hex[:12]}.png'
    data = bytes(buffer.data())
    def validate(path):
        if read_image(path).size() != image.size():
            raise ValueError("Captured image validation failed.")
    atomic_write(destination, lambda path: path.write_bytes(data), validate)
    return destination


class ImageIntakeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick image OCR · Paste, drop or choose")
        self.resize(760, 600)
        self.setAcceptDrops(True)
        self.image = QImage()
        layout = QVBoxLayout(self)
        self.preview = QLabel("Drop an image here\n\nor paste a screenshot with Ctrl+V")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(400, 300)
        self.preview.setStyleSheet("border: 2px dashed #8c80ff; border-radius: 12px; padding: 12px;")
        layout.addWidget(self.preview, 1)
        actions = QHBoxLayout()
        for text, callback in [('Paste image', self.paste), ('Choose image…', self.choose)]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.mode = QComboBox()
        self.mode.addItems(['Sinhala + English text → TXT / DOCX', 'Single equation → editable LaTeX / DOCX'])
        layout.addWidget(self.mode)
        self.message = QLabel("Images stay on this computer. A local copy is retained so saved projects can reopen it. Review recognition before export.")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Open and recognize')
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        # Shortcut is scoped to this image dialog, never the document/IME editor.
        self.paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        self.paste_shortcut.activated.connect(self.paste)

    def set_image(self, image):
        self.image = checked_image(image)
        self.preview.setPixmap(QPixmap.fromImage(self.image).scaled(680, 380, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        self.message.setText(f"{self.image.width()} × {self.image.height()} pixels · A local copy will be retained. Choose text or a single equation below.")

    def consume(self, mime):
        try:
            if mime.hasImage():
                data = mime.imageData()
                self.set_image(data.toImage() if isinstance(data, QPixmap) else QImage(data))
            elif mime.hasUrls() and len(mime.urls()) == 1 and mime.urls()[0].isLocalFile():
                self.set_image(read_image(mime.urls()[0].toLocalFile()))
            else:
                raise ValueError("Paste an image or drop one local image file. Text and web links are not image uploads.")
            return True
        except (ValueError, TypeError) as error:
            self.message.setText(str(error))
            return False

    def paste(self):
        self.consume(QApplication.clipboard().mimeData())

    def choose(self):
        name, _ = QFileDialog.getOpenFileName(self, 'Choose a cropped image', '', 'Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)')
        if name:
            try:
                self.set_image(read_image(name))
            except ValueError as error:
                self.message.setText(str(error))

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasImage() or (mime.hasUrls() and len(mime.urls()) == 1 and mime.urls()[0].isLocalFile()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if self.consume(event.mimeData()):
            event.acceptProposedAction()
