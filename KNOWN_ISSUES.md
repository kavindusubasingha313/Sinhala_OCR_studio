# Version 0.2.5 — investigate cross-script native Undo — 2026-10-25

The owner supplied the next Windows run: **2 failed, 5 passed**. TOM grouping alone did not fix the saved-word Undo defect. Both failing cases lost `bad` after undoing a Latin-to-Sinhala replacement; the Sinhala selection replacement test passed. The earlier grouping diagnosis was insufficient.

Replacement now records an explicit undoable deletion, then insertion, inside the existing TOM collection. This is a candidate repair pending Windows validation, not a confirmed fix. All failing assertions remain. Five additional native cases isolate Latin/Latin, Latin/Sinhala, Sinhala/Latin, Sinhala/Sinhala and emoji/Sinhala replacement with one Undo and one Redo. Synthetic trace output and actual failure text are added to CI logs and the run summary to reduce manual log searching.

Linux checks: **86 passed, 12 native Windows tests skipped**; Ruff, dependency consistency and source smoke passed. No actual Windows or Helakuru execution occurred in this session. Stable packaging still requires passing native tests; no gate was disabled.

# Version 0.2.4 — native saved-word Undo repair — 2026-10-25

The owner supplied the Windows failure for run 40153356253: **5 native tests passed, 1 failed**. In `test_native_saved_word_replaces_only_selection`, insertion succeeded but Undo yielded ` English` instead of restoring `bad English`. Packaging was correctly skipped. This is evidence of a replacement-undo defect, not a Helakuru keyboard test.

Saved-word replacements now use RichEdit Text Object Model BeginEditCollection/EndEditCollection to group deletion and insertion into one undo unit, with typing-group boundaries on either side. Native keyboard input is untouched. The failing assertion remains; it now checks Redo too. An additional Windows test checks two consecutive replacements and both Undo/Redo operations. Interface-acquisition errors abort before editing, and COM references are released on success and failure.

Local validation: **86 tests passed, 7 Windows-only tests skipped** on Linux; Ruff and pip check passed. Five new fake-COM tests cover grouping order and interface cleanup on query, begin, edit and end failure. These do not substitute for the seven native Windows tests. The new Windows CI result and real Helakuru typing remain unverified.

# Version 0.2.3 follow-up — 2026-10-25

Saved words, Undo and Redo are now accessible inside the native Windows Sinhala editor. Native selections use UTF-16 positions so Sinhala joiners and characters following supplementary Unicode characters remain intact. A closed/unavailable native control now raises an error rather than returning empty text that could replace the page; failed reads keep the typing window open.

The owner has not yet tested 0.2.2. Real Helakuru remains unverified. GitHub Actions status lookup returned Forbidden in this session; no successful Windows run is claimed. Linux validation passed with 81 tests and 6 Windows-only tests skipped; the dedicated Windows CI step runs those native-control tests. Use the latest successful 0.2.3 build for the manual input gate.

# Current input status — 0.2.2 — 2026-10-25

- Notepad typing followed by paste works correctly (owner confirmed). Direct Helakuru input into the Qt editor still has an unresolved compatibility defect.
- **Windows Sinhala editor** bypasses Qt input with a native Windows RichEdit control inside the app. It must be tested with the installed Helakuru keyboard before claiming resolution. Its native editing surface uses Windows rendering rather than the app's dark theme. The ordinary Qt editor is retained; use the new button for direct Sinhala typing.
- Personal words are manually reviewed suggestions, not automatic OCR training. They cannot recover wrong keystrokes or guarantee recognition accuracy. Words remain in the local application-data folder until explicitly deleted; uninstalling an experimental ZIP does not remove that folder.
- Real native-control tests are Windows-only. Linux tests exercise the integration and data protections, not Windows input messages. The Windows CI step and manual compatibility checklist remain release gates.

Earlier milestone limitations follow; the status above supersedes their input-workaround descriptions.

# Equation crop recognition follow-up — 2026-10-25

Version 0.2.1 adds **Recognize this equation · AI** inside the equation editor. It uploads only the stored crop after consent, uses the existing OS-vault API key and daily limit, requires exactly one returned equation, and asks before replacing the source. Replacement is undoable and stays draft until accepted. Closing the editor or changing source while recognition runs prevents replacement. No offline equation recognition model is bundled; region marking alone does not recognize mathematics.

The owner confirmed that 0.2.0 still repeats Sinhala characters. Their typing-panel screenshot shows repeated U+0DC0 code points. Font changes cannot repair that sequence. Actual Helakuru integration remains unresolved: compare typing in Notepad and pasting into the native editor before changing input handling. No speculative deduplication is applied. Incorrect OCR text is a separate recognition-quality issue.

Validation for this follow-up is recorded below; live provider accuracy and genuine Windows input still require manual testing.

# Known issues and verification limits

- **Helakuru:** the owner reported wrong Sinhala characters/vowel signs and supplied “වවවවවවවව වස්තුවක්”. The editor now uses native QPlainTextEdit, explicit Sinhala fonts and normal IME hints. Simulated composition preserves වස්තුවක් exactly without duplication. The real Windows Helakuru input sequence is not reproduced in Linux; compatibility is not yet certified. Use More → Keyboard & Sinhala font to compare fonts and inspect committed Unicode. No automatic deduplication or Unicode rewriting is applied.
- **Word equations:** supported LaTeX is exported as native OMML, not a drawing. The equation preview is a visual rendering; the source is edited separately. An original equation image is not automatically an editable formula under baseline Tesseract. Enter/convert LaTeX or request Advanced OCR with LaTeX ON, then review and Accept the source. Unsupported conversion stops or offers an explicitly labelled image fallback. Actual Word 2019 rendering/editability of 0.2.0 is not verified here.
- **Advanced OCR:** requires an OpenAI API key with model access/billing, saved through an OS-backed credential vault. Core offline OCR needs no key. Cloud calls are opt-in per page; no automatic retry. The request limit controls attempts, not a fixed dollar budget; use provider account spending controls. Transport/output/consent tests use mocks; no live AI accuracy claim is made. AI can hallucinate and requires review. Only OpenAI is currently implemented.
- **PDFs/layout:** all imported pages render and can be selected. Export includes page text and equations but does not reconstruct original page layouts/tables/diagrams. Selectable PDFs may contain broken/legacy Sinhala encodings; use More → Recognize visual page to bypass their text layer. Verified legacy conversion is still absent. Password-protected PDFs require an unlocked copy.
- **Resource bounds:** up to 500 pages/frames per file. The first 60 thumbnails are rendered in the background; later page thumbnails appear on selection. Three full preview pages are cached per open document. Very large source images still need adequate memory. Batch OCR/cancellation is not implemented; OCR targets one page at a time.
- **Saving:** each document tab is saved as its own project, including all page corrections and OCR replacement history. Original files are never changed. Native manual undo history persists while switching tabs/pages, not across application restarts. Save projects explicitly. Source file paths must remain available for preview; missing source paths produce an error message. Old projects with combined PDF text remain one combined page; reimport the source in a separate tab for page-aware work while retaining the old project.
- **Equations:** no offline neural mathematical recognition model is included. The bounded LaTeX dialect and experimental OMML converter remain as documented in LATEX_EQUATIONS.md. AI equation suggestions have source text but no automatically cropped image; compare with the original page. Equation-aware/searchable PDF export, automatic region-layout reconstruction and real A/L Physics benchmarks remain pending.
- **Windows release:** the earlier a6e0ef1 build passed (owner screenshot). This version has only Linux source/frozen-app validation so far; genuine Windows 10/11, Helakuru, Word 2019, high DPI, OS credential vault and packaging still require the new run and manual checks. Builds remain experimental and unsigned.
