## 0.3.1 quick image workflow (pending on real Windows)

- Copy a Snipping Tool crop and paste via button/Ctrl+V in Paste / drop image; verify preview and resolution.
- Drag a local PNG/JPEG into that dialog and also test Choose image. Verify browser links are rejected without downloads.
- Recognize Sinhala+English text, review, edit and export UTF-8 TXT and DOCX; compare against the crop. Save/reopen the project and confirm its image remains available after restarting.
- Choose Single equation for a formula crop and verify offline source review, Accept and editable Word export. Also test the visible Equations-tab offline action with no selection, LaTeX OFF and another task running.
- Verify the version header is 0.3.1 and the complete build folder is extracted. Ordinary text-editor Ctrl+V and Helakuru behavior must be tested separately.

## 0.3.0 offline recognition checks (manual, pending)

- Disconnect networking, enable LaTeX, mark a clean equation with zoom, and confirm a reviewable source suggestion appears without credentials or uploads.
- Repeat for a fraction, root, power and a real A/L Physics crop. Compare every term; record errors rather than accepting automatically.
- Change source or close the editor while recognition runs; confirm the late result does not overwrite edits. Verify source Undo/Redo and project save/reopen.
- Turn LaTeX OFF; verify normal text OCR works and offline equation recognition does not start.
- Accept a supported result, export DOCX, and edit the equation inside Microsoft Word 2019. Confirm Sinhala context remains unchanged.
- Verify the fully extracted build on Windows 10/11 without Python or separately installed equation dependencies. Keep Helakuru testing separate; it is not fixed by this recognizer.

# 0.2.7 production input gate

- [ ] Select `bad` in `bad English`, open the blank Sinhala typing pad, type වස්තුවක් with real Helakuru, insert, Undo and Redo in the document. The English suffix and original word must be preserved.
- [ ] Repeat at a cursor without a selection, with Sinhala conjuncts, mixed English and mathematical symbols, on multiple pages. Save/reopen and export to verify exact text.
- [ ] An empty pad and Cancel cannot erase selected document text; discarding unsent typing requires confirmation.
- [ ] Paste and Saved words in the main Qt editor preserve Undo/Redo. The pad is for new typing; the native paste/replacement defect remains documented.
- [ ] Record Windows and Helakuru versions and phonetic/Wijesekara modes. Synthetic CI messages are not a substitute for this check.

Older checklists below describe retired full-document native-editor behavior; use the current gate above for release.

# 0.2.2 critical Sinhala input checks

- [ ] In **Windows Sinhala editor**, type වස්තුවක්, ශ්‍රී, mixed Sinhala/English, legitimate repeated letters, vowel signs, conjuncts and punctuation using actual Helakuru. Compare Unicode with Notepad; record Windows/Helakuru versions and phonetic/Wijesekara mode.
- [ ] Exercise Backspace/Delete, selection replacement, copy/paste, native Undo/Redo, mouse focus changes, multiline typing and 100%/150%/200% DPI.
- [ ] Apply, undo/redo the transfer, switch pages, save/reopen and export TXT/DOCX; verify all characters persist.
- [ ] Cancel and window-close do not discard changed typing without confirmation.
- [ ] Save a reviewed word, restart, find it from a similar spelling, insert it and undo; delete it and confirm it stays removed after restart.
- [ ] Native control and packaged smoke jobs pass; real Helakuru remains a separate manual gate.

# Windows manual gate — all unchecked

- [ ] Windows 10 and 11 clean install/start; missing Tesseract/data errors; offline run.
- [ ] Helakuru installed: phonetic and Wijesekara input in QTextEdit; composition, vowel signs, conjuncts, cursor movement, selection, paste, Undo/Redo and shortcuts.
- [ ] Confirm composition is not interrupted by menu shortcuts or approval; mixed Sinhala-English typing.
- [ ] 100%, 150%, 200% DPI and multiple monitors; keyboard navigation and assistive technology.
- [ ] Light/dark/system theme transitions and settings after restart.
- [ ] Nirmala UI/Iskoola Pota availability and fallback; Sinhala shaping in preview/editor and actual Microsoft Word DOCX rendering.
- [ ] Save/reopen corrections, approval invalidation, protected rerun, crash recovery requirements.
- [ ] Unicode Windows paths, locked destination, disk full, antivirus interference and atomic replacement failure.
- [ ] Packaged installer, signing, license notices, uninstall and clean offline computer.

Record OS build, Helakuru version, input mode, steps, screenshots without private documents, and pass/fail evidence. No item has been verified in this Linux environment.

## Equation gate — all unverified on real Windows

- [ ] Microsoft Word 2019: all physics equation fixtures open without repair; native editing and save/reopen retain fractions, powers, indices, roots, Greek letters, integral/summation limits, vectors and matrices.
- [ ] Inline/display positioning among Sinhala-English paragraphs; no unwanted text boxes; clearly labelled non-editable original-image fallbacks.
- [ ] LaTeX OFF default and saved preference; per-project mode; OFF preserves approved and manually edited equations after reopen.
- [ ] Region selection and preserved crops at multiple DPI settings; no equation preview distortion; unsupported-command and syntax-error reporting.
- [ ] Equation source Undo/Redo/Restore Original; genuine Helakuru input in surrounding text; document and equation edits survive explicit Save project.
- [ ] Packaged executable previews and exports equations entirely offline with bundled mathematical fonts.

## Version 0.2.0 retest

- [ ] Real Helakuru: type වස්තුවක් and compare with Notepad; test successive composition, vowel signs, ZWJ sequences, mixed English, selection, backspace and Undo/Redo. Record whether repeated ව characters occur in the typing panel's Unicode output.
- [ ] Switch among multiple PDF/photo tabs, page 1/page 2/last page, portrait/landscape pages and TIFF frames; verify previews and modifications stay attached to the correct page.
- [ ] Switch themes/high DPI while previewing; test Fit, zoom and panning without blank pages.
- [ ] Close clean and edited tabs; confirm Save/Discard/Cancel behavior and reopen all saved page corrections.
- [ ] Native DOCX equations: click a supported formula in Word 2019; verify Equation Tools and editable numerator/denominator, with no image selection handles. Confirm all exported page text is present.
- [ ] Advanced OCR first-use setup: Windows Credential Manager storage/removal; decline consent and verify no request; verify daily cap, provider errors and review-before-apply/history restoration.
- [ ] With explicit owner consent and an API account, run a real Sinhala/English/physics page through Advanced OCR. Validate transcription independently; do not mistake provider completion for accuracy.
