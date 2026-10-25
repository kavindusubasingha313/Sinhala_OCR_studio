"""Windows release gate for native typing and Qt-owned replacement/undo."""
import os
import sys

import pytest
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from sinhala_ocr.windows_input import WindowsInputDialog
from sinhala_ocr.workspace_widgets import UnicodeEditor

pytestmark = pytest.mark.skipif(sys.platform != 'win32' or os.environ.get('QT_QPA_PLATFORM') == 'offscreen',
                                reason='Requires Windows native controls; dedicated CI step runs this.')


@pytest.fixture
def application():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize('before', ['bad', 'වස්තුවක්', '𝑥'])
def test_typing_transfer_keeps_original_until_insert_and_restores_it_on_undo(application, before):
    editor = UnicodeEditor()
    original = before + ' English'
    editor.setPlainText(original)
    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(len(before.encode('utf-16-le')) // 2, cursor.MoveMode.KeepAnchor)
    dialog = WindowsInputDialog(cursor.selectedText())
    try:
        dialog.show()
        application.processEvents()
        assert dialog.control.text() == ''
        for character in 'වස්තුවක්':
            dialog.control.message(0x102, ord(character))
        assert dialog.control.text() == 'වස්තුවක්'
        assert editor.toPlainText() == original
        dialog.accept()
        assert dialog.result() == QDialog.DialogCode.Accepted
        cursor.beginEditBlock()
        cursor.insertText(dialog.result_text)
        cursor.endEditBlock()
        assert editor.toPlainText() == 'වස්තුවක් English'
        editor.undo()
        assert editor.toPlainText() == original
        editor.redo()
        assert editor.toPlainText() == 'වස්තුවක් English'
    finally:
        dialog.control.dispose()
        dialog.done(0)
        editor.close()


def test_empty_pad_cannot_erase_selected_text(application, monkeypatch):
    dialog = WindowsInputDialog('bad English')
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: None)
    try:
        dialog.accept()
        assert dialog.result() != QDialog.DialogCode.Accepted
        assert dialog.control.hwnd
        assert dialog.result_text == ''
    finally:
        dialog.control.dispose()
        dialog.done(0)


def test_cancel_protects_unsent_typing(application, monkeypatch):
    dialog = WindowsInputDialog('bad')
    try:
        dialog.control.message(0x102, ord('ව'))
        monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Cancel)
        dialog.reject()
        assert dialog.control.text() == 'ව'
        monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Discard)
        dialog.reject()
        assert not dialog.control.hwnd
        assert dialog.result_text == ''
    finally:
        dialog.control.dispose()
        dialog.done(0)


@pytest.mark.parametrize('text', ['වස්තුවක්\nසිංහල x²', '\nවස්තුවක්\n\nසිංහල\n'])
def test_enter_preserves_lines_through_native_pad_and_qt_undo(application, text):
    from sinhala_ocr.synthetic_input import type_fixture
    dialog = WindowsInputDialog('original English')
    editor = UnicodeEditor()
    editor.setPlainText('original English')
    try:
        dialog.show()
        application.processEvents()
        type_fixture(dialog.control.message, text)
        assert dialog.control.text() == text
        dialog.accept()
        assert dialog.result_text == text
        editor.selectAll()
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.insertText(dialog.result_text)
        cursor.endEditBlock()
        assert editor.toPlainText() == text
        editor.undo()
        assert editor.toPlainText() == 'original English'
        editor.redo()
        assert editor.toPlainText() == text
    finally:
        dialog.control.dispose()
        dialog.done(0)
        editor.close()
