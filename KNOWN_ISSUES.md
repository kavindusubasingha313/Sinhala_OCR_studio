# Known issues and release blockers

- Linux headless checks cannot verify Windows IME/Helakuru, font shaping, printing, high DPI, native dialogs or installation.
- Stage 1 document navigation is a single-file list, not page thumbnails. No batch processing/cancellation. Very large images may consume substantial memory; no resource limits yet.
- PDFs extract selectable text but have no visual rendering or scanned-page OCR. Legacy Sinhala encoding detection/conversion is absent.
- Tesseract is a baseline adapter only. Confidence is unknown; all recognition requires review. No accuracy claims.
- Review is whole-document Accept with native editing/undo/redo. Reject, Next Issue, region queue and durable edit history are pending. Approval does not disable editing; edits invalidate approval. OCR replacement is conservatively blocked whenever text exists.
- Projects reference source paths and do not autosave. Close/import warns to save; no automatic recovery. Project write/export is atomic on supported local filesystems; directory fsync and power-loss durability are not guaranteed. UI prevents source overwrite; low-level save_project callers must also choose a separate path.
- DOCX contains plain paragraphs and complex-script font settings; no layout reconstruction, actual equations, tables, font detection or verified fallback. The Word reading machine needs a suitable Sinhala font; DOCX fonts are not embedded. Word rendering is unverified.
- No searchable PDF export or benchmark runner. Windows packaging and CI are configured but unexecuted. Dependency versions reflect this execution date and need a security/compatibility review before release.

## Equation-specific limitations

Manual equation editing is implemented; automatic equation detection/recognition is not installed. ON explicitly reports the manual workflow. No cloud equation provider is configured. Real Sinhala A/L Physics recognition has not been evaluated. Only the documented bounded LaTeX dialect is supported. Inline/display markers are visible text anchors; deleting or damaging them blocks export until repaired. Manual project saves are required. Crops increase project size.

Native OMML export is experimental and structurally tested, not visually verified in Microsoft Word 2019. DOCX fonts remain external to the document. Unsupported equations require an explicit original-crop fallback or source export. Equation-aware PDF export and arbitrary TeX compilation are pending; equations are not silently discarded to TXT/PDF. The prior text-only equation limitation is superseded for the tested OMML subset.
