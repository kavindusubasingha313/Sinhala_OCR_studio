# Architecture

Stage 1 uses Python 3.11+ and PySide6. `app.py` owns the desktop shell, native Qt text editing, theme/settings, progress and QRunnable workers. `core.py` owns document state, image/PDF import, OCR protocol, Tesseract adapter, project persistence and atomic validated exports. There are no network upload adapters or cloud credentials.

Recognition, font selection and future layout reconstruction are separate responsibilities. Current DOCX output is plain paragraphs with Nirmala UI complex-script properties; layout, font detection and equation reconstruction are not implemented. Mathematical Unicode is retained as text, not converted into editable equations.

An existing text body or approval blocks recognition replacement. Editing invalidates approval. JSON projects persist text and approval, referencing the original source by path. Moving the source breaks preview but preserves project text. User-initiated exports are snapshots. Future region-level correction history must use stable region IDs and explicit merge/conflict decisions.

Planned interfaces: page/region layout model; recognition adapters returning per-region confidence; separate layout and export services; review queue with durable transactions; optional consent-bound cloud adapters using OS credential storage. Do not add cloud calls to offline engine methods.

Accuracy evaluation will use separately versioned training/validation/held-out test manifests, private document storage outside Git, grapheme-aware and codepoint CER, tokenization-documented WER, layout metrics and wall time. No benchmark or superiority claim is available in Stage 1.

UI font fallback prefers Nirmala UI, Iskoola Pota, bundled Noto Sans Sinhala and Segoe UI. The bundled font and its OFL license were fetched from google/fonts `ofl/notosanssinhala` on 2026-10-22. DOCX readers still require their own installed fonts; fonts are not embedded in DOCX. Diagnostics use a bounded allowlist of event names, exclude exception messages and document data, and require opt-in each session. No automatic uploads.
