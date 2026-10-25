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
