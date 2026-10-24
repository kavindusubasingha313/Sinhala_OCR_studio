"""Windows RichEdit input bridge; Windows owns composition and editing messages.

No Qt key filter, keyboard hook or character normalization is used. Keystrokes
are delivered to a real RichEdit HWND rather than a QPlainTextEdit.
"""
import ctypes
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QMessageBox, QVBoxLayout, QWidget

MAX_TEXT = 2_000_000


class WindowsTextControl(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        if sys.platform != "win32":
            raise RuntimeError("Windows Sinhala input is available only on Windows.")
        from ctypes import wintypes as w
        self.hwnd = None
        self.font_handle = None
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.gdi = ctypes.WinDLL("gdi32", use_last_error=True)
        # Keep the system DLL loaded for the entire life of its window class.
        self.library = ctypes.WinDLL("Msftedit.dll", use_last_error=True)
        signatures = {
            "CreateWindowExW": ([w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, w.HWND, w.HMENU, w.HINSTANCE, w.LPVOID], w.HWND),
            "SendMessageW": ([w.HWND, w.UINT, ctypes.c_size_t, ctypes.c_ssize_t], ctypes.c_ssize_t),
            "SetWindowTextW": ([w.HWND, w.LPCWSTR], w.BOOL),
            "GetWindowTextLengthW": ([w.HWND], ctypes.c_int),
            "GetWindowTextW": ([w.HWND, w.LPWSTR, ctypes.c_int], ctypes.c_int),
            "SetFocus": ([w.HWND], w.HWND),
            "MoveWindow": ([w.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, w.BOOL], w.BOOL),
            "DestroyWindow": ([w.HWND], w.BOOL),
            "IsWindow": ([w.HWND], w.BOOL),
            "GetClientRect": ([w.HWND, ctypes.POINTER(w.RECT)], w.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.user, name)
            function.argtypes, function.restype = arguments, result
        self.gdi.CreateFontW.argtypes = [ctypes.c_int] * 5 + [w.DWORD] * 8 + [w.LPCWSTR]
        self.gdi.CreateFontW.restype = w.HANDLE
        self.gdi.DeleteObject.argtypes, self.gdi.DeleteObject.restype = [w.HANDLE], w.BOOL
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(400, 250)
        # Child, visible, tab stop, vertical scroll; multiline, autoscroll,
        # return inserts a paragraph. Deliberately let RichEdit process keys.
        style = 0x40000000 | 0x10000000 | 0x00010000 | 0x00200000 | 0x0004 | 0x0040 | 0x1000
        self.hwnd = self.user.CreateWindowExW(0x00000200, "RICHEDIT50W", "", style,
                                             0, 0, 400, 250, int(self.winId()), None, None, None)
        if not self.hwnd:
            raise RuntimeError("Windows could not create the native text editor.")
        try:
            self.message(0x0459, 1)  # EM_SETTEXTMODE: plain text, before setting text
            self.message(0x0435, 0, MAX_TEXT)  # EM_EXLIMITTEXT, UTF-16 units
            self.font_handle = self.gdi.CreateFontW(-round(20 * self.devicePixelRatioF()), 0, 0, 0, 400,
                                                   0, 0, 0, 1, 0, 0, 5, 0, "Nirmala UI")
            if self.font_handle:
                self.message(0x0030, self.font_handle, 1)  # WM_SETFONT
            self.set_text(text)
        except Exception:
            self.dispose()
            raise

    def message(self, message, wparam=0, lparam=0):
        if not self.hwnd:
            raise RuntimeError("Windows text editor is closed.")
        return self.user.SendMessageW(self.hwnd, message, wparam, lparam)

    def set_text(self, text):
        if '\x00' in text or len(text.encode('utf-16-le')) // 2 > MAX_TEXT:
            raise ValueError("Text contains a null character or exceeds the native editor limit.")
        if not self.user.SetWindowTextW(self.hwnd, text.replace('\n', '\r\n')):
            raise RuntimeError("Windows could not load the text; your page was not changed.")
        if self.text() != text:
            raise RuntimeError("Windows text integrity check failed; your page was not changed.")

    def text(self):
        length = self.user.GetWindowTextLengthW(self.hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        copied = self.user.GetWindowTextW(self.hwnd, buffer, length + 1)
        if length and not copied:
            raise RuntimeError("Could not retrieve native text; the editor remains open.")
        # RichEdit paragraph separators differ from QTextDocument. Only newlines
        # are adapted; all Sinhala characters, ZWJ and repetitions are preserved.
        return buffer.value.replace('\r\n', '\n').replace('\r', '\n')

    def replace_selection(self, text):
        buffer = ctypes.create_unicode_buffer(text)
        self.message(0x00C2, 1, ctypes.addressof(buffer))  # EM_REPLACESEL, undoable

    def focus_native(self):
        if self.hwnd:
            self.user.SetFocus(self.hwnd)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focus_native()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.hwnd:
            from ctypes.wintypes import RECT
            rectangle = RECT()
            if self.user.GetClientRect(int(self.winId()), ctypes.byref(rectangle)):
                self.user.MoveWindow(self.hwnd, 0, 0, rectangle.right, rectangle.bottom, True)

    def dispose(self):
        if self.hwnd:
            if self.user.IsWindow(self.hwnd):
                self.user.DestroyWindow(self.hwnd)
            self.hwnd = None
        if self.font_handle:
            self.gdi.DeleteObject(self.font_handle)
            self.font_handle = None


class WindowsInputDialog(QDialog):
    """Explicit Apply/Cancel protects page text until editing is complete."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.initial_text = text
        self.result_text = text
        self.setWindowTitle("Windows Sinhala editor · Helakuru input")
        self.resize(850, 620)
        layout = QVBoxLayout(self)
        label = QLabel("Type here with Helakuru. This uses the Windows RichEdit control instead of Qt text input. Apply transfers your edits to the page; Undo in the page editor can reverse that transfer. Save the project afterwards.")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.control = WindowsTextControl(text, self)
        layout.addWidget(self.control, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        # A neutral native editing surface avoids breaking native composition
        # with Qt styling. RichEdit uses Windows text/selection rendering.
        QTimer.singleShot(0, self.control.focus_native)

    def accept(self):
        try:
            self.result_text = self.control.text()
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Text could not be applied", str(error))
            return
        self.control.dispose()
        super().accept()

    def reject(self):
        if self.control.hwnd and self.control.text() != self.initial_text:
            if QMessageBox.question(self, "Discard typing?", "Discard the changes in this typing window? Your saved page will remain unchanged.",
                                    QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                    QMessageBox.StandardButton.Cancel) != QMessageBox.StandardButton.Discard:
                return
        self.control.dispose()
        super().reject()
