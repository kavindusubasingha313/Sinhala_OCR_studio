from sinhala_ocr.synthetic_input import type_fixture


def test_enter_fixture_contains_keydown_character_and_keyup():
    messages = []
    type_fixture(lambda *args: messages.append(args), 'ව\nසි')
    assert messages == [
        (0x102, ord('ව'), 1),
        (0x100, 13, 0x001C0001), (0x102, 13, 0x001C0001), (0x101, 13, 0xC01C0001),
        (0x102, ord('ස'), 1), (0x102, ord('ි'), 1),
    ]


def test_mathematical_symbol_uses_utf16_units():
    messages = []
    type_fixture(lambda *args: messages.append(args), '𝑥')
    encoded = b''.join(value.to_bytes(2, 'little') for code, value, flags in messages)
    assert encoded.decode('utf-16-le') == '𝑥'
    assert all(code == 0x102 and flags == 1 for code, value, flags in messages)
