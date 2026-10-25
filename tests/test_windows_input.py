"""Real HWND tests run in the dedicated Windows CI step, not Linux emulation."""
import os
import sys

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from sinhala_ocr.windows_input import WindowsInputDialog

pytestmark = pytest.mark.skipif(sys.platform != 'win32' or os.environ.get('QT_QPA_PLATFORM') == 'offscreen',
                                reason='Requires Windows and the native windows Qt platform; separate CI step runs this.')


@pytest.fixture
def native():
    app = QApplication.instance() or QApplication([])
    dialog = WindowsInputDialog('වස්තුවක්\nශ්‍රී සිංහල x² 😀\nවවවව')
    dialog.show()
    app.processEvents()
    yield app, dialog
    dialog.control.dispose()
    dialog.done(0)


def test_native_unicode_roundtrip_and_apply(native):
    _, dialog = native
    assert dialog.control.text() == dialog.initial_text
    dialog.accept()
    assert dialog.result_text == dialog.initial_text
    assert not dialog.control.hwnd


def test_native_replace_undo_redo(native):
    _, dialog = native
    dialog.control.message(0x00B1, 0, -1)  # EM_SETSEL, entire document
    dialog.control.replace_selection('සංකීර්ණ වස්තුවක්')
    assert dialog.control.text() == 'සංකීර්ණ වස්තුවක්'
    dialog.control.message(0x00C7)  # EM_UNDO
    assert dialog.control.text() == dialog.initial_text
    dialog.control.message(0x0454)  # EM_REDO
    assert dialog.control.text() == 'සංකීර්ණ වස්තුවක්'


def test_cancel_retains_text_until_explicit_discard(native, monkeypatch):
    _, dialog = native
    dialog.control.message(0x00B1, 0, -1)
    dialog.control.replace_selection('වස්තුවක්')
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Cancel)
    dialog.reject()
    assert dialog.control.hwnd
    assert dialog.control.text() == 'වස්තුවක්'
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Discard)
    dialog.reject()
    assert not dialog.control.hwnd
    assert dialog.result_text == dialog.initial_text


def test_native_selection_uses_utf16_and_keeps_sinhala(native):
    _, dialog = native
    dialog.control.set_text('😀 ශ්‍රී වස්තුවක්')
    # Emoji is two UTF-16 units; Sinhala includes the zero-width joiner.
    dialog.control.message(0x00B1, 3, 3 + len('ශ්‍රී'.encode('utf-16-le')) // 2)
    assert dialog.control.selected_text() == 'ශ්‍රී'
    dialog.control.replace_selection('සිංහල')
    assert dialog.control.text() == '😀 සිංහල වස්තුවක්'
    dialog.edit_command(0x00C7)
    assert dialog.control.text() == '😀 ශ්‍රී වස්තුවක්'


def test_native_saved_word_replaces_only_selection(native, monkeypatch):
    from sinhala_ocr import word_memory
    from PySide6.QtWidgets import QDialog
    _, dialog = native
    dialog.control.set_text('bad English')
    dialog.control.message(0x00B1, 0, 3)
    monkeypatch.setattr(word_memory, 'WordMemory', lambda: None)
    class WordDialog:
        chosen = 'වස්තුවක්'
        def __init__(self, memory, selection, parent):
            assert selection == 'bad'
        def exec(self):
            return QDialog.DialogCode.Accepted
    monkeypatch.setattr(word_memory, 'WordMemoryDialog', WordDialog)
    dialog.saved_words()
    assert dialog.control.text() == 'වස්තුවක් English'
    dialog.edit_command(0x00C7)
    assert dialog.control.text() == 'bad English'


def test_closed_control_cannot_return_empty_text(native):
    _, dialog = native
    dialog.control.dispose()
    with pytest.raises(RuntimeError):
        dialog.control.text()
