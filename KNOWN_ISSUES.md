# 0.2.8 workspace repair — 2026-10-26

Owner reports export blocked by a missing equation marker, blank unrecognized pages, repeated Sinhala characters in the Qt Keyboard check, and legacy-looking PDF text. The preceding Windows build was reported successful by the owner; genuine input compatibility is not established.

- Region marking now supports zoom out/in, Fit, 100%, and scrollbars. Selection maps back to original pixels and is retained while zooming.
- Export preflight opens the first page with invalid equation placement and selects a missing equation. The user restores its marker at the intended position or explicitly rejects it; no equation is silently discarded or appended at a guessed position.
- Recognize blank pages queues only pages without text, approval or equations. It uses visual offline OCR, reviews each result, and stops on Cancel or an error. Existing pages remain protected. This is not automatic OCR of every imported page.
- Garbled PDF text has a visible Recognize visual page action. No unverified legacy encoding conversion is applied.
- Equations has a direct Recognize page equations · AI action, enabling LaTeX and using existing credential/consent/review controls. Offline OCR remains text-only; no offline equation detector/model or recognition accuracy improvement is claimed. Zero returned equations can still occur.
- Keyboard check is explicitly labelled as the Qt diagnostic with its known direct-input defect. Native typing-pad input is unchanged pending clarification/testing. Notepad then paste remains the owner-confirmed workaround. Dictionary suggestions cannot repair an input-method event defect.

Validation: Linux pytest **102 passed, 7 Windows-only skipped**; Ruff, pip check, diff whitespace check and source desktop-entry smoke passed (offline OCR, PDF rendering, workspace/equation preview, DOCX export, tabs/themes). Smoke emitted a font-cache warning but completed with a passed JSON report. Windows CI, extended genuine Helakuru typing and Word 2019 rendering remain unverified for this commit.

# Smoke Enter-event correction — 2026-10-25

The owner supplied an actionable source-smoke failure at `native_typing_pad`: expected `වස්තුවක්\nසිංහල x²`, received `වස්තුවක්සිංහල x²`. Offline OCR and credential-backend stages passed. The missing newline was in a synthetic character-only input sequence, not evidence that genuine Helakuru typing or a packaged dependency failed.

The fixture driver omitted Enter key-down/key-up and sent only WM_CHAR(13). RichEdit handles Enter on the key-down path. `synthetic_input.type_fixture` now sends WM_KEYDOWN(VK_RETURN), WM_CHAR(13), WM_KEYUP(VK_RETURN) with repeat count/scan code, preserving the expected newline assertion. Other fixture characters use UTF-16 units. This helper runs only in synthetic tests; it does not hook or transform user input. Real Windows execution must confirm the correction.

New Windows regressions check multiline Sinhala and leading/trailing/blank lines through the native pad, transfer and Qt Undo/Redo. Local validation: **99 passed, 7 Windows-only tests skipped**; Ruff, pip check and Linux source smoke passed. The reported font-fallback warnings are separate from the newline assertion; real rendering and Helakuru still require manual verification. Product version stays 0.2.7; this commit corrects its test driver.

# Packaged-smoke investigation — 2026-10-25

The owner provided a run where application packaging succeeded but `Verify packaged launch and bundled OCR/export` returned exit 1. The screenshot does not identify the underlying exception; no cause or repair is claimed. Earlier native test gates were passed in that run, since packaging executed.

The explicit synthetic smoke test now checkpoints offline OCR, credential-backend loading, native typing, PDF rendering, workspace/equation preview, DOCX export and tabs/themes. Failures include the stage, bounded exception message and traceback; native multiline mismatch reports expected/actual synthetic text. Startup exceptions are also written by the executable entry point. Worker cleanup occurs before temporary files are removed even on failure.

CI runs the same source smoke before packaging, then runs the packaged test with a 60-second timeout. Reports and stderr are printed on failure and reports appear in the Actions Summary. Both checks require an explicit passed report; old reports are removed. No failed stage is bypassed.

Linux validation: **97 passed, 5 Windows-only tests skipped**; Ruff, pip check and the source desktop-entry smoke passed. The Windows failure remains unresolved pending the new report. This change improves diagnosis only; product version remains 0.2.7 and artifacts identify the new commit.

# Version 0.2.7 — native typing, Qt document history — 2026-10-25

The owner supplied the isolated Windows comparison: all 12 Qt cases matched; each of the three native-control configurations failed 4 of 12 cases (Latin/mathematical text replaced or pasted with Sinhala). Native character-message cases matched. This identifies a native-path operation-dependent problem; it does not prove a Windows defect or establish actual Helakuru compatibility.

Production now uses a **blank Sinhala typing pad** for native keyboard input. The original selection stays in Qt and is shown as read-only context, never loaded into the native pad. **Insert into document** replaces only that selection, or inserts at the cursor, as one Qt undo block. Empty results and Cancel cannot erase the selection. Saved words, paste and document Undo/Redo remain in the main Qt editor. No normalization or keystroke hooks were added. Native-pad paste/undo behavior remains unreliable; use the pad for new typing, and the main editor for paste/replacement.

The retired full-document native editor and every prior regression assertion remain in `diagnostics/test_retired_native_editor.py`; the investigation workflow runs them explicitly and may still report known failures. They are no longer the production gate because that editor path is no longer exposed in the application. The production gate now tests the blank pad, explicit transfer, empty/Cancel protection, original-text restoration and Redo through Qt. No native defect is claimed fixed.

Local validation: **94 passed, 5 Windows-only tests skipped**, Ruff, pip check and source smoke passed. The new Windows product build and real Helakuru typing still require verification. Implementation remains Python/PySide6 (Qt's C++ editor) with the Windows system RichEdit control for typing. No additional package, model, API or language is required. A language rewrite would not by itself repair behavior reproduced outside the application.

# Diagnostic isolation — 2026-10-25

Production changes are paused. The latest owner-provided Windows result remains **4 failed, 8 passed**; the native text-mode change did not resolve the failure. No new product release or fix is claimed.

A separate **Windows input investigation (diagnostic only)** workflow builds a standalone Input Lab and compares fresh raw Windows plain/rich controls (no Qt imports), a standard Qt editor and the current app integration. Separate worker processes record initialization, replacement, Undo/Redo, additional Undo, mode and errors using fixed samples. Paste uses only the disposable CI clipboard; character-message injection is explicitly not Helakuru. The matrix compares Latin, Sinhala and mathematical symbols, not emojis. Results and mismatch traces are published in its Summary and observation artifacts; a diagnostic EXE is uploaded for optional manual Helakuru comparisons without Python installation.

See `diagnostics/READ_ME_FIRST.md` for owner instructions and interpretation. The production workflow and its failure gates are unchanged. Next decision requires the diagnostic Windows results, not another speculative editor patch.

# Version 0.2.6 — native text-mode investigation — 2026-10-25

The owner's latest Windows screenshot reports **4 failed, 8 passed**: explicit deletion plus insertion still did not fix cross-script Undo. Removing emoji coverage alone cannot fix the independently failing `bad English` restoration.

Emoji-specific fixtures are removed at the owner's request. Non-BMP selection coverage now uses mathematical italic x (𝑥), relevant to physics documents; no emoji recognition feature is implemented. Native RichEdit is now explicitly configured for its standard rich-text mode, multilevel undo and Unicode code pages, with a checked return value and mode readback. This replaces TM_PLAINTEXT's single-format restriction. Application persistence continues to extract Unicode text, not RTF. This is a candidate repair that requires the real Windows tests, not a claim that the cause has been proven or the failure resolved.

Executed on Linux: **86 passed, 12 native tests skipped**, Ruff and pip check passed, source smoke passed. The failing English/Sinhala assertions remain enabled. The Windows test log prints the actual control mode, and the run summary includes failures. Real Helakuru and Word tests remain outstanding.

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
