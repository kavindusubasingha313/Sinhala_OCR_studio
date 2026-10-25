"""ABI/lifetime checks with fake COM methods; not Windows integration tests."""
import ctypes
from types import SimpleNamespace

import pytest

from sinhala_ocr.windows_input import WindowsTextControl


@pytest.mark.parametrize('failure', [None, 'query', 'begin', 'edit', 'end'])
def test_undo_collection_releases_interfaces_and_bounds_edit(monkeypatch, failure):
    # On Linux, substitute the local calling convention solely for fake methods.
    monkeypatch.setattr(ctypes, 'WINFUNCTYPE', ctypes.CFUNCTYPE, raising=False)
    events = []
    functions = []
    def interface(size):
        table = (ctypes.c_void_p * size)()
        instance = (ctypes.POINTER(ctypes.c_void_p) * 1)(table)
        return table, instance
    doc_table, doc = interface(22)
    ole_table, ole = interface(3)
    def install(table, slot, result, callback, *args):
        function = ctypes.CFUNCTYPE(result, ctypes.c_void_p, *args)(callback)
        functions.append(function)
        table[slot] = ctypes.cast(function, ctypes.c_void_p).value
    def query(this, iid, output):
        events.append('query')
        if failure == 'query':
            return -1
        output[0] = ctypes.addressof(doc)
        return 0
    def call(name):
        def callback(this):
            events.append(name)
            return -1 if failure == name else 0
        return callback
    install(ole_table, 0, ctypes.c_int32, query, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
    install(ole_table, 2, ctypes.c_uint32, call('release_ole'))
    install(doc_table, 2, ctypes.c_uint32, call('release_doc'))
    install(doc_table, 20, ctypes.c_int32, call('begin'))
    install(doc_table, 21, ctypes.c_int32, call('end'))
    def message(code, wparam=0, lparam=0):
        if code == 0x043C:
            ctypes.cast(lparam, ctypes.POINTER(ctypes.c_void_p))[0] = ctypes.addressof(ole)
            return 1
        assert code == 0x0458
        events.append('stop_typing')
    def execute():
        with WindowsTextControl.undo_collection(SimpleNamespace(message=message)):
            events.append('edit')
            if failure == 'edit':
                raise RuntimeError('replacement failed')
    if failure:
        with pytest.raises(RuntimeError):
            execute()
    else:
        execute()
    assert events[-1] == 'release_ole'
    if failure != 'query':
        assert events[-2] == 'release_doc'
    if failure in {'query', 'begin'}:
        assert 'edit' not in events
        assert 'end' not in events
    else:
        assert events.index('begin') < events.index('edit') < events.index('end')
