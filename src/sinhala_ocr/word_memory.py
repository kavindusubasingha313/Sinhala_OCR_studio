"""User-reviewed vocabulary, stored locally; never silently rewrites OCR."""
import difflib
import json
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout)

from .core import atomic_write


class WordMemory:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)) / 'personal-words.json'
        self.words = self.read(self.path) if self.path.exists() else []

    @staticmethod
    def read(path):
        data = json.loads(path.read_text(encoding='utf-8'))
        words = data.get('words') if isinstance(data, dict) else None
        if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(words, list) or len(words) > 10000:
            raise ValueError('Personal word file is invalid; it has not been overwritten.')
        for word in words:
            WordMemory.validate(word)
        return list(dict.fromkeys(words))

    @staticmethod
    def validate(word):
        if not isinstance(word, str) or not word.strip() or len(word) > 200 or any(c in word for c in '\x00\r\n'):
            raise ValueError('Save a word or short phrase of 1–200 characters, without line breaks.')

    def save(self, words):
        if len(words) > 10000:
            raise ValueError('Personal vocabulary is limited to 10,000 entries.')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({'version': 1, 'words': words}, ensure_ascii=False)
        atomic_write(self.path, lambda p: p.write_text(payload, encoding='utf-8'), self.read)
        self.words = words

    def add(self, word):
        word = word.strip()
        self.validate(word)
        if word not in self.words:
            self.save([*self.words, word])

    def remove(self, word):
        self.save([entry for entry in self.words if entry != word])

    def suggestions(self, query):
        query = query.strip()
        if not query:
            return sorted(self.words)
        direct = [word for word in self.words if query in word]
        similar = difflib.get_close_matches(query, self.words, n=20, cutoff=0.45)
        return list(dict.fromkeys([*sorted(direct), *similar]))[:100]


class WordMemoryDialog(QDialog):
    def __init__(self, memory, selection='', parent=None):
        super().__init__(parent)
        self.memory = memory
        self.chosen = None
        self.setWindowTitle('Personal Sinhala words · stored on this computer')
        self.resize(650, 500)
        layout = QVBoxLayout(self)
        note = QLabel('Save a spelling you have checked, then search and insert it in future documents. Similar spellings are suggestions only; no OCR or typed text is automatically replaced. Saved words stay on this computer. You can delete them here.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.query = QLineEdit(selection)
        self.query.setPlaceholderText('Search, paste or enter a reviewed word / short phrase')
        layout.addWidget(self.query)
        actions = QHBoxLayout()
        save = QPushButton('Save reviewed spelling')
        save.clicked.connect(self.save_word)
        remove = QPushButton('Delete selected saved word')
        remove.clicked.connect(self.remove_word)
        actions.addWidget(save)
        actions.addWidget(remove)
        layout.addLayout(actions)
        self.entries = QListWidget()
        layout.addWidget(self.entries)
        self.entries.itemDoubleClicked.connect(lambda _: self.accept())
        self.query.textChanged.connect(self.refresh)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Insert selected word')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.refresh()

    def refresh(self):
        self.entries.clear()
        self.entries.addItems(self.memory.suggestions(self.query.text()))
        if self.entries.count():
            self.entries.setCurrentRow(0)

    def save_word(self):
        try:
            self.memory.add(self.query.text())
            self.refresh()
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, 'Word could not be saved', str(error))

    def remove_word(self):
        entry = self.entries.currentItem()
        if entry and QMessageBox.question(self, 'Delete saved word?', 'Remove this word from your personal vocabulary?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                self.memory.remove(entry.text())
                self.refresh()
            except OSError as error:
                QMessageBox.warning(self, 'Word could not be removed', str(error))

    def accept(self):
        entry = self.entries.currentItem()
        if entry:
            self.chosen = entry.text()
            super().accept()
