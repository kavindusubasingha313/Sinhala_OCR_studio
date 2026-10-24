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
