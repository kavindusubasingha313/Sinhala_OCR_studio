# Regression fixtures and manual evidence

Automated synthetic fixtures live in test_core.py (Sinhala vowel signs, conjuncts, mixed English, numerals, mathematical Unicode, DOCX paragraphs/no text boxes, source preservation, selectable PDF and real Tesseract blank input) and test_ui.py (edit/undo/redo, approval, themes and worker).

No private documents belong here. Future recognition gold fixtures must include licensed synthetic/public images, independently checked UTF-8 transcripts, split assignment and provenance. Current blank-image engine smoke is not a recognition accuracy regression or CER/WER benchmark. This remains a Stage 2 gate.

For manual Word output use the same Sinhala/mixed/math corpus and verify visual glyphs in Word, not just XML. For Helakuru follow WINDOWS_COMPATIBILITY_CHECKLIST.md. Store only redacted evidence with OS/app versions; do not represent skipped checks as passed.
