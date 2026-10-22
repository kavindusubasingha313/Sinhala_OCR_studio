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
