"""Synthetic Windows messages for smoke fixtures, never real user input hooks.

RichEdit handles Enter at WM_KEYDOWN; WM_CHAR alone is not an Enter key
sequence. These messages do not emulate Helakuru/IME composition.
"""


def type_fixture(send_message, text):
    for character in text:
        if character == '\n':
            # VK_RETURN, scan code 0x1c, repeat count 1. TranslateMessage would
            # normally produce WM_CHAR between key-down and key-up.
            send_message(0x0100, 0x0D, 0x001C0001)
            send_message(0x0102, 0x0D, 0x001C0001)
            send_message(0x0101, 0x0D, 0xC01C0001)
        else:
            units = character.encode('utf-16-le')
            for offset in range(0, len(units), 2):
                send_message(0x0102, int.from_bytes(units[offset:offset + 2], 'little'), 1)
