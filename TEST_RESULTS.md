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

# Isolated input diagnostic validation — 2026-10-25

Local Linux suite: **91 passed, 12 Windows-only skipped**. Ruff, pip check and git diff --check passed. New tests validate comparison reporting with preserved mismatch text, continuation after worker exit/timeout, and refusal of automated clipboard writes outside GitHub Actions. These are harness checks, not execution of the native controls.

The diagnostic workflow independently builds a manual Input Lab, runs isolated source workers and packaged workers, and uploads observation JSON/logs plus a readable Summary. It records mismatches rather than calling them a production pass. Execution errors make the diagnostic job fail; actual undo mismatches remain explicit observations. The unchanged application workflow still blocks release on its native failures. No Windows diagnostic outcome or Helakuru compatibility is claimed before the runner/manual results arrive.

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

# Version 0.2.3 follow-up validation — 2026-10-25

Executed on Linux: pytest **81 passed, 6 skipped**; Ruff, pip check and source smoke passed. Native Windows tests now also exercise UTF-16 selection following an emoji, a Sinhala ZWJ-containing word, saved-word replacement with undo, and rejection of reads from closed controls. These were collected but skipped on Linux; they must run in the dedicated native Windows CI step. The Actions API returned Forbidden, so this session cannot establish the new Windows CI outcome. No actual Helakuru test is claimed.

# Version 0.2.2 validation — 2026-10-25

Executed: `QT_QPA_PLATFORM=offscreen TESSDATA_PREFIX=/workspace/ocr-tessdata /workspace/ocr-venv/bin/pytest -q --tb=short`: **81 passed, 3 skipped** on Linux. Ruff, pip check, git diff --check and the application `--smoke-test` passed.

New executed checks cover native-dialog Apply/Cancel integration using a stand-in dialog, whole-page undo/redo and project round-trip preservation, insertion of only a selected saved word with undo, exact vocabulary persistence (including Sinhala ZWJ/repetitions), similarity suggestions without rewriting, invalid-file protection, and disk-write failure protection.

The 3 skipped tests require actual Windows HWNDs and the Windows Qt platform: RichEdit Unicode/multiline/non-BMP round trip and Apply, native replace/Undo/Redo, and Cancel/Discard protection. A dedicated Windows Actions step runs them with `QT_QPA_PLATFORM=windows` and writes separate XML/log artifacts. Packaged Windows smoke also creates the native control. These checks do not emulate Helakuru.

No Windows or genuine Helakuru execution is claimed from this Linux run. The user-confirmed Notepad/paste comparison establishes a working fallback, not that the new native editor works with Helakuru. No new OCR accuracy result is claimed.

Earlier records follow.

# Equation crop recognition follow-up — 2026-10-25

Version 0.2.1 adds **Recognize this equation · AI** inside the equation editor. It uploads only the stored crop after consent, uses the existing OS-vault API key and daily limit, requires exactly one returned equation, and asks before replacing the source. Replacement is undoable and stays draft until accepted. Closing the editor or changing source while recognition runs prevents replacement. No offline equation recognition model is bundled; region marking alone does not recognize mathematics.

The owner confirmed that 0.2.0 still repeats Sinhala characters. Their typing-panel screenshot shows repeated U+0DC0 code points. Font changes cannot repair that sequence. Actual Helakuru integration remains unresolved: compare typing in Notepad and pasting into the native editor before changing input handling. No speculative deduplication is applied. Incorrect OCR text is a separate recognition-quality issue.

Follow-up validation: 73 tests passed on Linux, Ruff passed and pip check found no broken dependencies. Crop recognition was tested with mocked transport, including consent, crop-only payload, source review and undo. Clipboard Sinhala preservation passed. No live API or Windows Helakuru test was performed.

# Version 0.2.0 workspace validation — 2026-10-24

Executed on Debian Linux / Python 3.12 / PySide6 6.8.3:

- **71 tests passed**, no skipped tests. This includes the earlier regression suite plus page rendering/navigation and actual viewport pixels in both themes, multi-frame TIFF, document switching, page-specific Undo/Redo and corrections, closing/cancellation, project round trips, native OMML across multiple pages, readable equation references, prior-result history, and simulated Sinhala composition.
- The IME regression sends successive preedit states followed by one commit of **වස්තුවක්** and checks exact output with no duplicates plus Undo/Redo. This is **not actual Helakuru verification**. The owner’s repeated-character/vowel-sign issue still needs a Windows retest.
- AI tests use mock transport: no request without consent, no request beyond the daily cap, one-page payload and bounded output, LaTeX OFF behavior, equation-anchor validation, malformed/incomplete response rejection and refusal of plaintext credential backends. **No live API request or AI accuracy evaluation was run.**
- `bash scripts/setup-cloud.sh`: successful installation with pinned PDFium/keyring dependencies, Sinhala-model checksum, full tests, static checks and dependency consistency.
- `ruff check .`, `pip check`, `git diff --check`: passed.
- Source `--smoke-test`: passed, including multipage PDF rendering, switching document tabs, Sinhala text, baseline OCR, equation preview and native OMML output.
- PyInstaller 6.12.0 **Linux** directory build: completed successfully. The frozen application ran `--smoke-test` from a separate temporary working directory and wrote `{"status": "passed"}`. It included PDFium, fonts, Tesseract/language data and provider-support modules. This does not establish that the new Windows build succeeds.
- Actual light/dark workspace screenshots were inspected using a clearly synthetic physics document. Screenshots are UI evidence, not OCR accuracy evidence.

The owner previously supplied a successful Windows Actions result for **a6e0ef1**. The new 0.2.0 Windows workflow has been updated to collect PDFium and Windows credential backend resources, and to check packaged page/tab/equation functionality and credential-backend loading without reading/storing a key. **The new Windows run, real Helakuru, live provider request, Word 2019 editability/rendering and high-DPI behavior remain unverified here.**

The default equation export regression checks true `m:oMath`/fraction structures and zero `w:drawing`/text boxes, plus a Cambria Math setting. This establishes file structure, not Word’s visual output. Unsupported image fallback remains an explicit user choice.

The records below are historical; their earlier “not implemented” statements are superseded by the current status and KNOWN_ISSUES.md.

---

# Windows CI failure investigation

The owner supplied a screenshot showing the first two Windows workflow runs failed. The general release-gate summary does not identify the failed step. Direct Actions API access from this cloud environment is blocked by the network proxy (CONNECT 403), so the original failure log remains unavailable.

A code review identified a separate Windows compatibility defect: `atomic_write` reopened the temporary file read-only before calling `os.fsync`. On Windows this ultimately flushes a file handle that requires write access. The file is now reopened with `r+b`, retaining its validated contents while supplying write access. Microsoft documents this requirement for [FlushFileBuffers](https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers). This fix is not yet confirmed as the cause of either failed workflow run.

After the change, all **53 tests passed** on Linux; Ruff and pip dependency checks passed. Windows-target dependency resolution against public PyPI completed, which checks wheel availability but does not execute Windows code or validate installation on the runner. Workflow YAML parsed successfully. The workflow summary now lists failed step IDs to help locate the actual error.

A successful new Windows run and the original failed-step log are still required before declaring the CI problem resolved. No executable build is claimed from this investigation.

# Equation milestone — 2026-10-22

Current checks executed on Debian 13 / Python 3.12.14:

- `bash scripts/setup-cloud.sh`: successful repeat installation with pinned equation dependencies, model checksum verification, tests, static checks and dependency consistency.
- Final `TESSDATA_PREFIX=/workspace/ocr-tessdata QT_QPA_PLATFORM=offscreen /workspace/ocr-venv/bin/pytest -q`: **53 passed**, no skipped tests.
- `ruff check .` and `pip check`: passed; no broken requirements.
- Headless desktop `--smoke-test`: exit 0, including standard OCR, equation preview and native OMML DOCX export. Smoke settings are isolated from user preferences.
- Equation benchmark CLI: executed on two deliberately synthetic predictions; asserted exact-match rate 0.5 and character error rate 1/6. This validates scoring, not recognition accuracy.
- Windows workflow YAML parsed locally; collection rules now include renderer/font packages. No Windows runner or Windows executable execution is claimed.
- Local Qt equation-editor screenshot inspected for vector, fraction and matrix preview. Preview now preserves aspect ratio; this is Linux offscreen evidence, not Word/Windows verification.

New regressions exercise OFF never constructing an equation engine, ON dispatch through an injected test adapter, honest missing-model status, preferred/per-document modes, source crop persistence after original-file removal, old-project compatibility, marker integrity, selected-text preservation, source undo/redo/restore, acceptance/rejection, syntax errors, formula rendering, native OMML structures/placement, explicit original-crop fallback, no text boxes and atomic destination protection. The original 12 tests remain passing.

Actual Sinhala A/L Physics equation recognition, optional offline/cloud models, equation-aware PDF output, Microsoft Word 2019 rendering/editability and Windows 10/11/Helakuru tests remain **unrun or unimplemented**, as detailed in LATEX_EQUATIONS.md. Synthetic formula fixtures are not real examination pages or model outputs.

The first equation regression run exposed malformed-argument handling, a matrix-token parsing error and defects in an evaluated third-party OMML converter. These were corrected; the third-party converter was removed and replaced with a conservative project-owned converter. No failing cases were skipped or assertions disabled. An export preflight now distinguishes unaccepted supported equations from unsupported conversions eligible for crop fallback.

## Earlier Stage 1 execution record

### Executed checks — 2026-10-22

Environment: Debian 13 Linux, Python 3.12.14, PySide6 6.8.3, Tesseract 5.5.0, official tessdata_fast 4.1.0 Sinhala model plus installed English model.

- `bash scripts/setup-cloud.sh`: completed successfully, including repeat installation, Sinhala model checksum, editable installation, tests, static checks and dependency consistency.
- `TESSDATA_PREFIX=/workspace/ocr-tessdata QT_QPA_PLATFORM=offscreen /workspace/ocr-venv/bin/pytest -q`: **12 passed**, no skipped tests (final setup run: 0.97 seconds).
- `/workspace/ocr-venv/bin/ruff check .`: passed.
- `/workspace/ocr-venv/bin/pip check`: no broken requirements.
- `TESSDATA_PREFIX=/workspace/ocr-tessdata QT_QPA_PLATFORM=offscreen /workspace/ocr-venv/bin/python -m sinhala_ocr.app --smoke-test`: exit 0, report status passed; exercises launch, bundled Sinhala font registration, Unicode editor, theme changes, actual blank-image OCR and DOCX export.
- `git diff --check`: passed before milestone commit.

Coverage: Sinhala Unicode/vowel-sign and mathematical text round trips; mixed English; TXT/DOCX structure with no text boxes; protected original destination; failed validation preserving existing output; JSON correction/approval persistence; protected OCR replacement; image import; direct selectable PDF extraction; actual sin+eng engine invocation; deterministic synthetic English recognition (`TEST 123`); Qt edits/Undo/Redo/approval/theme/worker; opt-in diagnostic allowlist and ZIP export.

The initial static check found one unused test import, removed before rerunning. The first Qt smoke showed missing Sinhala fonts; bundling SIL-OFL Noto Sans Sinhala removed those script warnings. Remaining headless messages are fontconfig's unwritable default cache and offscreen plugin size-hint messages; checks exit 0. No visual glyph inspection was performed.

Windows GitHub Actions workflow is authored but not executed or validated on a Windows runner during this local session. PyInstaller Windows build, packaged runtime, genuine Helakuru, actual Word rendering, DPI and Windows 10/11 stability remain **unrun**. CI checks include offscreen Qt automation and a packaged executable smoke; that does not replace visual testing. No downloadable executable or stable release is claimed.

No Sinhala recognition gold corpus or CER/WER accuracy benchmark has run. Synthetic English recognition and blank-page integration are smoke/regression checks, not evidence of Sinhala accuracy. See tests/regression/README.md and WINDOWS_COMPATIBILITY_CHECKLIST.md.
