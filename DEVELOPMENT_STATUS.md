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
