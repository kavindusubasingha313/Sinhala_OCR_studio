"""Windows RichEdit input bridge; Windows owns composition and editing messages.

No Qt key filter, keyboard hook or character normalization is used. Keystrokes
are delivered to a real RichEdit HWND rather than a QPlainTextEdit.
"""
import ctypes
from contextlib import contextmanager
from uuid import UUID
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

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
            # Keep independent script/format runs in the native control. The
            # restricted TM_PLAINTEXT path lost Latin text during cross-script
            # undo on the Windows runner. Persistence still extracts text only.
            mode = 0x02 | 0x08 | 0x20  # rich text, multilevel undo, Unicode
            if self.message(0x0459, mode) != 0 or self.message(0x045A) != mode:
                raise RuntimeError("Windows could not enable Unicode editing with multilevel undo.")
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
        if not self.hwnd or not self.user.IsWindow(self.hwnd):
            raise RuntimeError("The Windows editor is unavailable; your page was not changed.")
        length = self.user.GetWindowTextLengthW(self.hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        copied = self.user.GetWindowTextW(self.hwnd, buffer, length + 1)
        if length and not copied:
            raise RuntimeError("Could not retrieve native text; the editor remains open.")
        # RichEdit paragraph separators differ from QTextDocument. Only newlines
        # are adapted; all Sinhala characters, ZWJ and repetitions are preserved.
        return buffer.value.replace('\r\n', '\n').replace('\r', '\n')

    def selected_text(self):
        from ctypes import wintypes as w
        class CharacterRange(ctypes.Structure):
            _fields_ = [("start", w.LONG), ("end", w.LONG)]
        selection = CharacterRange()
        self.message(0x0434, 0, ctypes.addressof(selection))  # EM_EXGETSEL
        length = selection.end - selection.start
        if not 0 <= length <= MAX_TEXT:
            raise RuntimeError("Windows returned an invalid text selection.")
        buffer = ctypes.create_unicode_buffer(length + 1)
        self.message(0x043E, 0, ctypes.addressof(buffer))  # EM_GETSELTEXT
        return buffer.value.replace('\r\n', '\n').replace('\r', '\n')

    @contextmanager
    def undo_collection(self):
        """Group deletion/insertion via RichEdit's Text Object Model (TOM).

        This collection groups programmatic deletion and insertion only;
        it does not intercept keyboard input. Windows CI exercises the real
        undo history, including replacements between different scripts.
        """
        ole = ctypes.c_void_p()
        document = ctypes.c_void_p()
        if not self.message(0x043C, 0, ctypes.addressof(ole)) or not ole.value:
            raise RuntimeError("Windows undo support is unavailable; no word was inserted.")

        def method(pointer, slot, result, *arguments):
            table = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            return ctypes.WINFUNCTYPE(result, ctypes.c_void_p, *arguments)(table[slot])

        try:
            # ITextDocument derives from IDispatch; slots 20/21 are
            # BeginEditCollection/EndEditCollection in the Windows TOM ABI.
            iid = (ctypes.c_ubyte * 16).from_buffer_copy(UUID('8cc497c0-a1df-11ce-8098-00aa0047be5d').bytes_le)
            query = method(ole, 0, ctypes.c_int32, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
            if query(ole, ctypes.addressof(iid), ctypes.byref(document)) < 0 or not document.value:
                raise RuntimeError("Windows undo grouping is unavailable; no word was inserted.")
            self.message(0x0458)  # EM_STOPGROUPTYPING: keep prior typing separate
            begin = method(document, 20, ctypes.c_int32)
            end = method(document, 21, ctypes.c_int32)
            if begin(document) < 0:
                raise RuntimeError("Could not start an undoable word replacement.")
            try:
                yield
            finally:
                result = end(document)
                self.message(0x0458)
                if result < 0:
                    raise RuntimeError("Windows could not finish undo grouping. Check the inserted word before applying the page.")
        finally:
            if document.value:
                method(document, 2, ctypes.c_uint32)(document)  # IUnknown.Release
            method(ole, 2, ctypes.c_uint32)(ole)

    def replace_selection(self, text):
        if '\x00' in text:
            raise ValueError("Text cannot contain a null character.")
        proposed = len(self.text().encode('utf-16-le')) - len(self.selected_text().encode('utf-16-le')) + len(text.encode('utf-16-le'))
        if proposed // 2 > MAX_TEXT:
            raise ValueError("The inserted text exceeds the Windows editor limit.")
        buffer = ctypes.create_unicode_buffer(text)
        with self.undo_collection():
            # Record removal independently before inserting a different script.
            # A single replace call lost the original Latin selection on Undo
            # in Windows CI, even inside a TOM edit collection.
            empty = ctypes.create_unicode_buffer("")
            self.message(0x00C2, 1, ctypes.addressof(empty))
            self.message(0x00C2, 1, ctypes.addressof(buffer))

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
        label = QLabel("Type here with Helakuru. This uses the Windows RichEdit control instead of Qt text input. Apply transfers your edits to the page; Undo in the page editor can reverse that transfer. Save the project afterwards. Only text is transferred; use the equation editor for formulas and image objects.")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.control = WindowsTextControl(text, self)
        layout.addWidget(self.control, 1)
        editing = QHBoxLayout()
        for label, callback in [("Undo", lambda: self.edit_command(0x00C7)),
                                ("Redo", lambda: self.edit_command(0x0454)),
                                ("Saved words", self.saved_words)]:
            button = QPushButton(label)
            button.setAutoDefault(False)
            button.clicked.connect(callback)
            editing.addWidget(button)
        editing.addStretch()
        layout.addLayout(editing)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        # A neutral native editing surface avoids breaking native composition
        # with Qt styling. RichEdit uses Windows text/selection rendering.
        QTimer.singleShot(0, self.control.focus_native)

    def edit_command(self, command):
        self.control.message(command)
        self.control.focus_native()

    def saved_words(self):
        from .word_memory import WordMemory, WordMemoryDialog
        try:
            dialog = WordMemoryDialog(WordMemory(), self.control.selected_text(), self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.control.replace_selection(dialog.chosen)
        except (ValueError, RuntimeError, OSError) as error:
            QMessageBox.warning(self, "Personal words unavailable", str(error))
        self.control.focus_native()

    def accept(self):
        try:
            self.result_text = self.control.text()
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Text could not be applied", str(error))
            return
        self.control.dispose()
        super().accept()

    def reject(self):
        try:
            changed = self.control.hwnd and self.control.text() != self.initial_text
        except RuntimeError as error:
            QMessageBox.warning(self, "Text could not be read", str(error))
            return
        if changed:
            if QMessageBox.question(self, "Discard typing?", "Discard the changes in this typing window? Your saved page will remain unchanged.",
                                    QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                    QMessageBox.StandardButton.Cancel) != QMessageBox.StandardButton.Discard:
                return
        self.control.dispose()
        super().reject()
