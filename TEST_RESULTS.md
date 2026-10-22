# Executed checks — 2026-10-22

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
