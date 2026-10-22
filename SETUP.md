# Setup

Cloud Linux: `bash scripts/setup-cloud.sh` from this checkout. The existing image supplies Python 3.12 and Tesseract 5.5.0 with English data. Script installs pinned dependencies in `/workspace/ocr-venv`, downloads official tessdata_fast 4.1.0 Sinhala data with SHA-256 verification, and runs tests. OS prerequisites on another Debian machine: Tesseract 5 and English data, plus Qt platform libraries for interactive display.

Launch on a graphical desktop:

```sh
export TESSDATA_PREFIX=/workspace/ocr-tessdata
/workspace/ocr-venv/bin/sinhala-ocr-studio
```

Cloud headless validation:

```sh
TESSDATA_PREFIX=/workspace/ocr-tessdata QT_QPA_PLATFORM=offscreen /workspace/ocr-venv/bin/pytest -q
/workspace/ocr-venv/bin/ruff check .
```

Windows (not executed here): install Python 3.11+; `py -m venv .venv`; `.venv\Scripts\python -m pip install -e ".[dev]"`; install a trusted Tesseract 5 Windows distribution and sin+eng data, put Tesseract on PATH, set TESSDATA_PREFIX to its tessdata directory, then `.venv\Scripts\sinhala-ocr-studio`. Validate dependencies and font availability before distribution. Linux lock includes resolved versions from Linux; cross-platform wheel installation remains unverified.

Import PNG/JPEG/TIFF/BMP or selectable PDF; edit in the right pane; Accept marks the whole document approved; Save project persists text and approval. Export TXT or DOCX. Native QTextEdit provides Undo/Redo via Ctrl+Z/Ctrl+Y. PDF page preview, batch import and region correction queue are not yet available. Keep project and source together; projects currently reference source paths rather than embedding images.

No API key is required. Keep private samples, projects and credentials outside source control. Do not change the source document via export.

For nontechnical Windows testing see DOWNLOAD_WINDOWS.md. GitHub Actions provides experimental ZIPs only after a successful Windows run. The package bundles Tesseract and model data, Qt and the Python runtime. No local Python/dependency configuration is required for the tester. Real Helakuru and Word checks remain manual. Tesseract distribution licensing and signing must be reviewed before stable release.
