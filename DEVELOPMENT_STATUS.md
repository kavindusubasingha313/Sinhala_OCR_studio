# Development status

2026-10-22: Stage 1 foundation implemented on Linux, not a production release.

Implemented: launchable Qt shell, action navigation, document list, image preview and zoom, split editor, System/Light/Dark settings persistence, worker progress, Unicode editing, full-document approval, JSON save/reopen, protected OCR reruns, modular Tesseract adapter, selectable PDF extraction, atomic validated TXT/DOCX exports and regression tests.

Next: Stage 2 functional document pipeline: multipage PDF rendering/scanned OCR, page thumbnails, sequential batch jobs with cancellation, per-region confidence and stable IDs, responsive large-document handling and real Sinhala-English recognition fixtures. Complete this gate before claiming functional general-purpose OCR. Stage 3 handles layout/export fidelity; Stage 4 adds complete correction queue and Windows Helakuru validation. Do not skip these gates.

No accuracy benchmarks, cloud providers, searchable PDF export, Windows package or model training are implemented. No remote push or repository visibility change performed.

Additional Windows delivery foundation: GitHub push/PR workflow installs dependencies and Tesseract, runs tests and static checks, builds a complete PyInstaller directory with Sinhala/English OCR runtime, checks packaged launch, and uploads version/commit experimental ZIP plus separate test/log artifacts. No automatic stable releases. Workflow has not yet executed on GitHub. Optional privacy-limited diagnostic events and bug-report ZIP are implemented. Bundled Noto Sans Sinhala (SIL OFL, license in assets) supplies a Sinhala-capable UI fallback; actual glyph/Word rendering still needs Windows inspection.
