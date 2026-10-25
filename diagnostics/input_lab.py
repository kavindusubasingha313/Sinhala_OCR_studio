"""Isolated Windows input lab. Raw workers import no Qt or application code."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

_qt_app = None

SAMPLES = [('bad', 'good'), ('bad', 'වස්තුවක්'), ('වස්තුවක්', 'bad'), ('𝑥', 'වස්තුවක්')]


class Native:
    def __init__(self, plain=False):
        from ctypes import wintypes as w
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.library = ctypes.WinDLL('Msftedit.dll')
        declarations = {
            'CreateWindowExW': ([w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, w.HWND, w.HMENU, w.HINSTANCE, w.LPVOID], w.HWND),
            'SendMessageW': ([w.HWND, w.UINT, ctypes.c_size_t, ctypes.c_ssize_t], ctypes.c_ssize_t),
            'SetWindowTextW': ([w.HWND, w.LPCWSTR], w.BOOL),
            'GetWindowTextLengthW': ([w.HWND], ctypes.c_int),
            'GetWindowTextW': ([w.HWND, w.LPWSTR, ctypes.c_int], ctypes.c_int),
            'DestroyWindow': ([w.HWND], w.BOOL),
            'IsWindow': ([w.HWND], w.BOOL),
            'SetFocus': ([w.HWND], w.HWND),
            'PeekMessageW': ([ctypes.POINTER(w.MSG), w.HWND, w.UINT, w.UINT, w.UINT], w.BOOL),
            'TranslateMessage': ([ctypes.POINTER(w.MSG)], w.BOOL),
            'DispatchMessageW': ([ctypes.POINTER(w.MSG)], ctypes.c_ssize_t),
            'OpenClipboard': ([w.HWND], w.BOOL), 'EmptyClipboard': ([], w.BOOL),
            'SetClipboardData': ([w.UINT, w.HANDLE], w.HANDLE), 'CloseClipboard': ([], w.BOOL),
        }
        for name, (arguments, result) in declarations.items():
            func = getattr(self.user, name)
            func.argtypes, func.restype = arguments, result
        title = 'Standalone ' + ('plain' if plain else 'rich') + ' Windows editor (no Qt) — Ctrl+Z Undo, Ctrl+Y Redo'
        self.parent = self.user.CreateWindowExW(0, 'STATIC', title,
                                               0x10CF0000, 80, 80, 900, 650, None, None, None, None)
        if not self.parent:
            raise ctypes.WinError(ctypes.get_last_error())
        self.hwnd = self.user.CreateWindowExW(0x200, 'RICHEDIT50W', '', 0x50211044,
                                             15, 15, 850, 560, self.parent, None, None, None)
        if not self.hwnd:
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())
        mode = (1 if plain else 2) | 8 | 32
        if self.send(0x459, mode) != 0:
            self.close()
            raise RuntimeError('Cannot set native text mode')
        self.gdi = ctypes.WinDLL('gdi32')
        self.gdi.GetStockObject.argtypes, self.gdi.GetStockObject.restype = [ctypes.c_int], w.HANDLE
        self.send(0x30, self.gdi.GetStockObject(17), 1)  # DEFAULT_GUI_FONT, system-owned
        self.user.SetFocus(self.hwnd)

    def send(self, code, wparam=0, lparam=0):
        return self.user.SendMessageW(self.hwnd, code, wparam, lparam)

    def load(self, text):
        if not self.user.SetWindowTextW(self.hwnd, text):
            raise RuntimeError('SetWindowText failed')

    def text(self):
        buffer = ctypes.create_unicode_buffer(self.user.GetWindowTextLengthW(self.hwnd) + 1)
        self.user.GetWindowTextW(self.hwnd, buffer, len(buffer))
        return buffer.value.replace('\r\n', '\n').replace('\r', '\n')

    def pump(self):
        from ctypes.wintypes import MSG
        message = MSG()
        while self.user.PeekMessageW(ctypes.byref(message), None, 0, 0, 1):
            self.user.TranslateMessage(ctypes.byref(message))
            self.user.DispatchMessageW(ctypes.byref(message))

    def close(self):
        if self.parent and self.user.IsWindow(self.parent):
            self.user.DestroyWindow(self.parent)
        self.parent = None


def clipboard_text(native, text):
    """CI-only: its disposable clipboard contains synthetic fixtures, no user data."""
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Automated clipboard probing is limited to the disposable GitHub runner.')
    from ctypes import wintypes as w
    kernel = native.kernel
    for name, args, result in [('GlobalAlloc', [w.UINT, ctypes.c_size_t], w.HANDLE),
                               ('GlobalLock', [w.HANDLE], w.LPVOID),
                               ('GlobalUnlock', [w.HANDLE], w.BOOL),
                               ('GlobalFree', [w.HANDLE], w.HANDLE)]:
        getattr(kernel, name).argtypes, getattr(kernel, name).restype = args, result
    raw = (text + '\0').encode('utf-16-le')
    memory = kernel.GlobalAlloc(0x42, len(raw))
    if not memory:
        raise MemoryError('Clipboard allocation failed')
    try:
        pointer = kernel.GlobalLock(memory)
        if not pointer:
            raise RuntimeError('Clipboard memory lock failed')
        ctypes.memmove(pointer, raw, len(raw))
        kernel.GlobalUnlock(memory)
        for attempt in range(20):
            if native.user.OpenClipboard(native.parent):
                break
            time.sleep(.05)
        else:
            raise RuntimeError('Clipboard unavailable')
        try:
            if not native.user.EmptyClipboard() or not native.user.SetClipboardData(13, memory):
                raise RuntimeError('Clipboard write failed')
            memory = None  # Windows owns the memory after SetClipboardData.
        finally:
            native.user.CloseClipboard()
    finally:
        if memory:
            kernel.GlobalFree(memory)


def exercise(kind, method, before, after):
    global _qt_app
    original = before + ' English'
    trace = {'control': kind, 'operation': method, 'before': before, 'after': after}
    native = None
    widget = None
    try:
        if kind.startswith('raw'):
            native = Native(plain=kind == 'raw_plain')
            native.load(original)
            native.pump()
            get_text, send, undo, redo = native.text, native.send, lambda: native.send(0xC7), lambda: native.send(0x454)
            send(0xB1, 0, len(before.encode('utf-16-le')) // 2)
            trace['text_mode'] = send(0x45A)
        else:
            from PySide6.QtWidgets import QApplication, QPlainTextEdit
            _qt_app = QApplication.instance() or QApplication([])
            app = _qt_app
            if kind == 'qt_plain':
                widget = QPlainTextEdit()
                widget.setPlainText(original)
                widget.show()
                cursor = widget.textCursor()
                cursor.setPosition(0)
                cursor.setPosition(len(before.encode('utf-16-le')) // 2, cursor.MoveMode.KeepAnchor)
                widget.setTextCursor(cursor)
                get_text, undo, redo = widget.toPlainText, widget.undo, widget.redo
            else:
                from sinhala_ocr.windows_input import WindowsTextControl
                widget = WindowsTextControl(original)
                widget.show()
                send = widget.message
                send(0xB1, 0, len(before.encode('utf-16-le')) // 2)
                get_text, undo, redo = widget.text, lambda: send(0xC7), lambda: send(0x454)
                trace['text_mode'] = send(0x45A)
            app.processEvents()
        trace['initial'] = get_text()
        if kind == 'qt_plain':
            if method == 'paste':
                if os.environ.get('GITHUB_ACTIONS') != 'true':
                    raise RuntimeError('Clipboard probing requires CI')
                app.clipboard().setText(after)
                widget.paste()
            elif method == 'characters':
                from PySide6.QtCore import Qt
                from PySide6.QtGui import QKeyEvent
                from PySide6.QtCore import QEvent
                for char in after:
                    app.sendEvent(widget, QKeyEvent(QEvent.Type.KeyPress, 0, Qt.KeyboardModifier.NoModifier, char))
            else:
                cursor.insertText(after)
        elif method == 'paste':
            clipboard_owner = native or Native()
            try:
                clipboard_text(clipboard_owner, after)
                send(0x302)  # WM_PASTE
            finally:
                if not native:
                    clipboard_owner.close()
        elif method == 'characters':
            raw = after.encode('utf-16-le')
            for i in range(0, len(raw), 2):
                send(0x102, int.from_bytes(raw[i:i+2], 'little'))  # WM_CHAR; not a real IME
        elif kind == 'app_native':
            widget.replace_selection(after)
        else:
            buffer = ctypes.create_unicode_buffer(after)
            send(0xC2, 1, ctypes.addressof(buffer))
        trace['inserted'] = get_text()
        undo()
        trace['undo_once'] = get_text()
        redo()
        trace['redo_once'] = get_text()
        trace['matches'] = (trace['initial'] == original and trace['inserted'] == after + ' English'
                            and trace['undo_once'] == original and trace['redo_once'] == after + ' English')
        # More history helps distinguish a split undo unit from discarded text.
        undo()
        undo()
        trace['undo_twice'] = get_text()
    except Exception as error:
        trace['error'] = type(error).__name__ + ': ' + str(error)
        trace['matches'] = False
    finally:
        if native:
            native.close()
        if widget:
            if hasattr(widget, 'dispose'):
                widget.dispose()
            widget.close()
    trace['qt_imported'] = any(name.startswith('PySide6') for name in sys.modules)
    return trace


def worker(kind, output):
    results = [exercise(kind, method, before, after) for method in ['replace', 'characters', 'paste'] for before, after in SAMPLES]
    Path(output).write_text(json.dumps({'control': kind, 'windows': platform.platform(), 'python': platform.python_version(),
                                      'note': 'Synthetic messages/paste only. No genuine Helakuru or human typing test.', 'cases': results}, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0  # A diagnostic observation is not a product release gate.


def command(*args):
    return [sys.executable, *([] if getattr(sys, 'frozen', False) else [str(Path(__file__).resolve())]), *args]


def run_all(folder):
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    for kind in ['raw_plain', 'raw_rich', 'qt_plain', 'app_native']:
        target = folder / (kind + '.json')
        try:
            process = subprocess.run(command('--worker', kind, '--output', str(target)), timeout=90, capture_output=True, text=True)
            (folder / (kind + '.log')).write_text(process.stdout + process.stderr, encoding='utf-8')
            if process.returncode or not target.exists():
                target.write_text(json.dumps({'control': kind, 'error': 'Worker failed', 'exit_code': process.returncode}), encoding='utf-8')
        except subprocess.TimeoutExpired:
            target.write_text(json.dumps({'control': kind, 'error': 'Worker timed out after 90 seconds'}), encoding='utf-8')
    summarize(folder)
    reports = [json.loads(path.read_text(encoding='utf-8')) for path in folder.glob('*.json')]
    return int(any('error' in report or any('error' in case for case in report.get('cases', [])) for report in reports))


def summarize(folder):
    lines = ['# Windows input isolation report', '', 'Diagnostic observations only; not a passing product build or verified Helakuru support.',
             'Character cases inject messages. They do not emulate a real keyboard/IME. A mismatch can reflect undo grouping semantics; inspect the trace.', '',
             '| Control | Operation | Original | Replacement | One Undo/Redo matches |', '|---|---|---|---|---|']
    for path in sorted(Path(folder).glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        if 'error' in data:
            lines.append(f"| {data['control']} | worker error | | | {data['error']} |")
        for case in data.get('cases', []):
            lines.append(f"| {case['control']} | {case['operation']} | {case['before']} | {case['after']} | {'yes' if case['matches'] else 'NO'} |")
    lines.extend(['', '## Mismatch traces (synthetic samples only)', ''])
    for path in sorted(Path(folder).glob('*.json')):
        for case in json.loads(path.read_text(encoding='utf-8')).get('cases', []):
            if not case['matches']:
                lines.extend(['```json', json.dumps(case, ensure_ascii=False, indent=2), '```'])
    Path(folder, 'SUMMARY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def manual():
    from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QPlainTextEdit
    app = QApplication.instance() or QApplication([])
    from sinhala_ocr.windows_input import WindowsInputDialog
    window = QDialog()
    window.setWindowTitle('Sinhala Input Lab — diagnostic only')
    window.resize(850, 650)
    layout = QVBoxLayout(window)
    note = QLabel('Type වස්තුවක් in each editor with the same Helakuru mode. Compare with Notepad.\nThis is a diagnostic, not the OCR application. It does not save or upload your typing.\nThe box below is a standard Qt editor. Use only disposable sample text.')
    note.setWordWrap(True)
    layout.addWidget(note)
    layout.addWidget(QPlainTextEdit())
    children = []
    for plain in [True, False]:
        button = QPushButton('Open standalone Windows editor · ' + ('plain text' if plain else 'standard rich text'))
        button.clicked.connect(lambda checked=False, p=plain: children.append(subprocess.Popen(command('--manual-native', 'plain' if p else 'rich'))))
        layout.addWidget(button)
    embedded = QPushButton('Open current app Windows editor')
    embedded.clicked.connect(lambda: WindowsInputDialog('', window).exec())
    layout.addWidget(embedded)
    window.show()
    result = app.exec()
    # Independent native windows remain open until the user closes them.
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', choices=['raw_plain', 'raw_rich', 'qt_plain', 'app_native'])
    parser.add_argument('--output', default='input-lab-results')
    parser.add_argument('--automatic', action='store_true')
    parser.add_argument('--manual-native', choices=['plain', 'rich'])
    options = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('This diagnostic requires Windows. Linux cannot establish Windows input behavior.')
    if options.worker:
        return worker(options.worker, options.output)
    if options.automatic:
        return run_all(options.output)
    if options.manual_native:
        native = Native(options.manual_native == 'plain')
        try:
            while native.user.IsWindow(native.parent):
                native.pump()
                time.sleep(.01)
        finally:
            native.close()
        return 0
    return manual()


if __name__ == '__main__':
    raise SystemExit(main())
