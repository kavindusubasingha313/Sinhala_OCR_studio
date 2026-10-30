0.3.1 packaging validation: Linux source and PyInstaller frozen smoke both passed, including image_intake, offline_equation_recognition and DOCX export. The Linux frozen check used copied test tessdata and the system Tesseract executable; Windows CI separately bundles the Windows runtime. Font-cache warnings did not fail smoke. Windows execution remains pending.

# Quick image OCR and equation access — 0.3.1 — 2026-10-30

Added Paste / drop image: a dialog with local-file drag/drop, explicit clipboard paste (button or dialog-scoped Ctrl+V), file chooser, preview, and text/equation mode. Text mode opens a new document tab and runs visual offline Sinhala+English OCR with existing result review and TXT/DOCX export. Equation mode enables LaTeX for the new document, stores the whole crop as an equation and opens offline recognition directly. Existing tabs, corrections and approvals are preserved. No Sinhala TrOCR integration was added.

Captures are stored as unique PNGs in QStandardPaths AppDataLocation/captured-images, validated and atomically written. They persist after closing so project source paths continue to work on this machine. Copies are not automatically deleted or uploaded; users should retain them while projects reference them. Input is bounded to 12 megapixels. Transparent images are composited on white. Only one local image or bitmap is accepted; text/web links are not fetched.

The owner clarified that the equation button is missing or nothing happens. The prior offline action was nested inside the editor. A prominent Recognize selected equation · Offline action is now in the Equations tab, with actionable messages for missing selection/image or a busy worker. With LaTeX OFF, explicit confirmation enables the mode before recognition; declining never loads a model. Quick-image equation mode avoids re-marking a crop. Recognition preprocessing now composites transparent pixels onto white and adds a 12-pixel margin; a transparent black-glyph fixture previously reached the blank-image error. No general model accuracy fix, full-page detector or Windows compatibility success is claimed.

Validation: Linux pytest **113 passed, 7 Windows-only skipped**; Ruff and pip check passed. Real CPU equation fixture plus editable Word structure still pass after preprocessing. New regressions cover clipboard MIME/local-file intake, rejection of web URLs, local persistence/project reopen, Unicode TXT integrity, both intake routes, protection of other tabs and transparency handling. Source smoke includes synthetic image intake/persistence/TXT export in addition to actual model inference. The upstream NumPy deprecation warnings remain. Real Windows clipboard/Snipping Tool/file drag-drop, native input and Word rendering require manual testing.

# Offline equation recognition — 0.3.0 — 2026-10-26

Implemented CPU crop-to-LaTeX recognition using RapidLaTeXOCR 0.0.9 and ONNX Runtime 1.20.1. With LaTeX ON, marking a region opens the editor and starts local recognition. Existing crops have a Recognize equation · Offline button. Results require explicit review before insertion, remain drafts, and support source Undo. Accepted equations still use the existing guarded OMML exporter. Original crops and recognized source remain in saved projects. No document is uploaded by this path.

The engine imports/loads lazily, validates four pinned model hashes, and supplies all model paths explicitly to disable the upstream implicit download path. LaTeX OFF and blank crops fail before loading a model. Background execution retains the original source if the editor closes or the user edits while inference runs. There is no automatic whole-page offline equation detector; select one expression with Mark region. Optional whole-page AI remains separate and consent-based.

Windows CI installs the CPU dependencies, downloads and verifies approximately 171 MiB of model assets at build time, and bundles them with the EXE. Source and frozen smoke gates now execute genuine model inference on a synthetic x=1 PNG. No end-user Python, API key, model download or GPU is required by the complete Windows artifact. Model files are ignored by Git. License texts and a generated synthetic fixture are included. Python source environments require 3.11/3.12 and requirements-equations.txt; setup-cloud.sh handles these and the model fetch.

Executed on Linux: **108 passed, 7 Windows-only skipped**, Ruff and pip check passed. Source smoke and a PyInstaller Linux build/frozen smoke both passed, including real offline equation recognition and DOCX export. For the Linux frozen check, test Tesseract data was copied alongside the executable and the system Tesseract binary was used; Windows CI bundles the full Windows OCR runtime. Upstream emitted four NumPy scalar-conversion deprecation warnings with pinned NumPy 1.26.4; no failing checks. Qt emitted a font-cache warning during smoke but the report passed.

Synthetic model observations (not an independent accuracy benchmark):
- x=1 → `x\,=\,1` (correct after ignoring spacing).
- E=\frac{1}{2}mv^2 → `E\:=\:\frac{1}{2}m v^{2}` (correct expression).
- m=\sqrt{100^2+200^2+2\times100\times200\times\frac{1}{2}} → `m\,=\,\sqrt{100^{2}+200^{2}+\,2\times100\times200\times200\times\frac{1}{2}}` (**incorrect extra ×200**).

This error is retained as an observed limitation, not silently corrected. Long expressions, small scans, matrices, handwriting and mixed text need review and representative evaluation. Whole-page offline detection, held-out Sinhala A/L Physics accuracy, Windows packaged inference, Microsoft Word rendering, and genuine Helakuru tests remain pending. Earlier statements that no offline recognizer is installed are superseded for selected crops only. No Helakuru input changes are made by this milestone.

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

# Version 0.2.2 — Windows input bypass and personal words — 2026-10-25

The owner verified that Helakuru typing in Notepad and pasting into the application is correct. The Qt direct-input defect therefore remains a compatibility issue, not something a font/dictionary can repair. Added an integrated **Windows Sinhala editor** using the OS RichEdit control, bypassing Qt text input. Apply/Cancel, native editing undo and undoable transfer preserve the existing page. This is an implemented compatibility path, not yet a verified Helakuru fix.

Added **Saved words**: explicitly save reviewed Sinhala spellings/short phrases, search with similar-word suggestions, insert manually, and delete entries. Vocabulary persists locally and does not silently rewrite OCR results. Existing OCR/equation functionality is retained.

Validation: 81 Linux tests passed; 3 native Windows tests skipped locally and scheduled in a dedicated Windows CI step. Ruff, pip check and source smoke passed. Packaged Windows smoke now uses the Windows Qt platform and checks the native control. The new Windows build and actual Helakuru keyboard interaction remain pending. Next gate: type the same word in the new Windows Sinhala editor, apply, save/reopen and export; compare exact Unicode with Notepad.

Earlier milestone records follow.

# Equation crop recognition follow-up — 2026-10-25

Version 0.2.1 adds **Recognize this equation · AI** inside the equation editor. It uploads only the stored crop after consent, uses the existing OS-vault API key and daily limit, requires exactly one returned equation, and asks before replacing the source. Replacement is undoable and stays draft until accepted. Closing the editor or changing source while recognition runs prevents replacement. No offline equation recognition model is bundled; region marking alone does not recognize mathematics.

The owner confirmed that 0.2.0 still repeats Sinhala characters. Their typing-panel screenshot shows repeated U+0DC0 code points. Font changes cannot repair that sequence. Actual Helakuru integration remains unresolved: compare typing in Notepad and pasting into the native editor before changing input handling. No speculative deduplication is applied. Incorrect OCR text is a separate recognition-quality issue.

Validation for this follow-up is recorded below; live provider accuracy and genuine Windows input still require manual testing.

# Development status — 2026-10-24

Version 0.2.0 is an experimental workspace update. The owner confirmed the earlier Windows build at a6e0ef1 passed via a GitHub Actions screenshot. This update requires its own successful Windows CI run and manual compatibility checks.

Implemented:

- Fusion-based light/dark/system themes, responsive split workspace, independent document tabs, explicit per-tab closing and Save/Discard/Cancel for modified documents.
- Multi-file import, PDF pages and multi-frame TIFF navigation, thumbnail sidebar, selected-page preview, fit/zoom/pan, and background rendering. Undo history and corrections remain with their page while switching files.
- Page-aware project persistence and all-page text/DOCX/source export. Older projects still load as their original single combined page. OCR result replacement is explicit and records the prior page text/equations/approval in persistent history.
- Native plain-text Unicode editor with explicit Sinhala font fallback, a keyboard/font testing panel and composition regression using වස්තුවක්. Actual Helakuru behavior remains unverified; the owner reported repeated consonants/wrong vowel signs in the previous application.
- Standard offline selected-page OCR, direct selectable PDF text, and an explicit visual-OCR option for PDFs with broken text mappings.
- Advanced OCR button with an optional OpenAI adapter, per-page upload consent, OS-vault key storage, daily request limits, bounded output and review-before-apply. When LaTeX is ON, the provider is asked for separate equation sources and text anchors. Live API transcription and actual paid usage are not tested here.
- Existing manual equation/crop editing, source preview, review actions and native OMML export retained. Readable equation references replace internal IDs in the editor. Native editable Word export is the default; an image fallback always needs explicit consent. Fractions/equation XML and absence of drawing/text-box replacements are regression-tested.

Validation: 71 tests pass on Linux; static/dependency checks pass; source and packaged Linux smoke checks pass. The Windows workflow now collects PDFium and credential-backend resources and exercises a multipage/tabbed packaged smoke check.

Next gate: successful Windows 0.2.0 build, real Helakuru typing of the reported word, Microsoft Word 2019 equation editability, and an opt-in live provider request. Next development work: representative Sinhala A/L document accuracy evaluation, region-level confidence/layout, offline neural equations, searchable PDF export, batch cancellation and installer/release hardening. No superior accuracy or production-readiness claim is made.
