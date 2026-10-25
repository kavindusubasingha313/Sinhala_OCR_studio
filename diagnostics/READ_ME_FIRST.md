# Sinhala Input Lab — diagnostic only

This is a separate typing experiment, not an updated OCR application or a stable release. No Python installation is needed for its Windows ZIP.

1. In GitHub Actions, open **Windows input investigation (diagnostic only)**.
2. Its Summary contains automated comparison results. Share that comparison first; you do not need to download anything for these results.
3. For real Helakuru testing, download the **SinhalaInputLab-DIAGNOSTIC-…** artifact. Extract the artifact ZIP and the build ZIP inside it. Keep the entire folder together and open **SinhalaInputLab.exe**.
4. In its Qt text box, type **වස්තුවක්** using Helakuru. Repeat in Notepad with the same input mode.
5. Open each standalone Windows editor with the buttons. These run in separate processes without importing Qt. Type the same word, select it, replace it, and press Ctrl+Z and Ctrl+Y. Repeat by pasting a word copied from Notepad.
6. Open **current app typing pad** to test new typing in the blank native control. In the actual app, insertion and document Undo use Qt. The automated `app_native` worker deliberately still exercises the retired native replacement backend.
7. Report which editor repeated letters or lost the original text on Undo, plus Windows version, Helakuru version and phonetic/Wijesekara mode. Use only disposable samples; these windows do not save your typing. Close every standalone window when finished.

The manual lab sends no network requests, records no typing and uploads nothing. Its automatic CI runs use fixed synthetic samples and record their text states. Automated clipboard tests run only in GitHub's disposable runner; they are blocked on an ordinary computer. Programmatically injected character messages are **not** genuine Helakuru interaction or human keyboard input.

## Reading the automated comparison

- **raw_plain / raw_rich**: Windows RichEdit created through a separate standard-library-only implementation, with no Qt or app imports. Compares restricted plain-text versus standard rich-text mode.
- **qt_plain**: standard Qt text editor without the app's event handling.
- **app_native**: current app Windows control, including its replacement/undo code.
- **replace**: one programmatic replacement (the app control uses its own replacement method).
- **characters**: synthetic character messages, not a real IME. Undo grouping may legitimately differ from a single replacement.
- **paste**: paste from a synthetic Unicode clipboard value on CI.
- **matches** means initial text, replacement, one Undo and one Redo match the fixture. A mismatch is an observation to investigate, not proof of a Windows defect.
- **undo_twice** helps distinguish a split undo unit from lost text. Worker errors/timeouts are reported separately, not counted as passes.

Compare Latin-to-Latin and Latin-to-Sinhala replacement on fresh controls first. If only the app control fails, investigate its bridge. If raw controls fail too, investigate the native operation/control behavior before changing the app again. If only synthetic character cases differ, inspect grouping semantics. Actual typing must still be checked manually.

The existing application workflow remains unchanged and continues to block release packaging on failed native tests. A green diagnostic workflow means the experiment ran; it does not approve an application release.

The archived `test_retired_native_editor.py` tests retain the old failing assertions and run explicitly in the diagnostic workflow. That step can remain red: it reproduces the retired native editing defect. Production tests now validate the new blank-pad-to-Qt transfer. No diagnostic mismatch has been reclassified as a passing native fix.
