# Version 0.2.0 update

Advanced OCR now optionally requests separate equation sources from OpenAI when LaTeX is ON, behind per-page consent and OS-vault credentials. This is a cloud adapter, not an offline mathematical model. Provider responses are mocked in automated tests; live accuracy remains unverified. Compare with the original page and Accept each equation before native Word export.

PDF pages now render, and manual region selection works on the selected rendered PDF/image page. Projects preserve equations per page. The editor shows readable ⟦Equation N⟧ references while retaining stable IDs in project data. “Convert selected LaTeX to equation” creates an editable object from source text. Native OMML remains the default; a supported expression is not replaced by an image. Word font is explicitly Cambria Math. No actual Word 2019 verification is claimed.

The following initial-milestone record describes the earlier behavior and dialect. Its statements that PDF rendering/cloud adapters are absent are superseded by this update. Offline neural recognition, real Sinhala A/L Physics evaluation and equation-aware PDF export remain pending.

# LaTeX equation workflow and release gates

The first equation milestone adds manual entry, region capture, live local preview and project persistence. It also provides an **experimental native OMML export foundation** for the explicitly tested subset. This is not a declaration that mathematical OCR, Word visual fidelity or the equation release gate is complete.

## What works now

- A clearly visible **LaTeX ON/OFF** workspace control. A clean settings profile defaults to OFF. User changes become the preferred mode for new imports; each saved project stores its own mode. Opening a project restores its mode without changing the preferred default.
- OFF uses the ordinary OCR path and never calls the optional equation-engine factory. Switching OFF does not remove crops, edits, approval states, markers or LaTeX source. Existing equations remain editable.
- ON enables manual equation entry and image-region selection. **No automatic equation detection/recognition model is installed.** The workspace and OCR result explicitly report this. The lazy `EquationEngine` protocol is a future integration boundary, not a shipped model or provider.
- **Add equation** inserts an equation marker at the text cursor. **Mark equation region** opens the image for rectangle selection and embeds a PNG crop in the project. Image coordinates use the same EXIF orientation as preview. PDF region selection awaits PDF rendering.
- Select an equation in the left list and choose **Edit selected equation**, or double-click it. The editor shows the original crop (when present), editable LaTeX, inline/display placement, live SVG preview and syntax/unsupported-command messages. Rendering is offline; no TeX installation, browser or network is used.
- **Accept**, **Reject**, native text **Undo/Redo**, and **Restore Original** are supported. Editing invalidates equation acceptance. Restore Original restores the initial OCR/manual source and can itself be undone. A newly created manual equation has empty original source. Reject retains both source and crop; it does not erase the equation.
- **Save project** atomically persists current and original LaTeX, crop, coordinates, stable ID, placement, status and mode. Save remains explicit, not autosave. Older projects without equation fields still load.

## Placement and export

Markers look like `[[eq:…]]`. Move a whole marker in the text editor to position an equation among Sinhala/English text. Inline equations remain in that paragraph. Display equations occupy a separate equation paragraph. The **Insert equation marker** button recovers a missing marker at the cursor. Export refuses broken, duplicate or missing markers rather than silently discarding equations. To omit a rejected equation, deliberately remove its marker; the source remains in the project.

DOCX converts supported accepted equations into `m:oMath`/`m:oMathPara` objects, with real fraction, radical, subscript/superscript, accent, limit and matrix structures. Ordinary text stays in Word paragraphs. No text boxes are generated. The converter is owned by this project and intentionally bounded; it does not assume arbitrary TeX is convertible.

Tested formula categories: fractions, powers, subscripts, square roots, Greek letters, integral and summation limits, vectors and rectangular matrices. Editable integral/summation limits use native OMML script/limit structures; full semantic equation reconstruction is not claimed. MathML renderer and OMML export are separate modules. A mathematically valid preview does not guarantee every Word conversion is supported.

DOCX export validates surrounding Unicode text, equation counts, inline/display placement, image counts, absence of text boxes and archive reopening before atomic replacement. Unsupported conversion normally stops. If the equation has an original crop, the UI offers an explicit **original-image fallback**, labelled “Equation image fallback — not editable” in the document. It never manufactures a preview from unsupported LaTeX. Supported equations still require Accept. Without a crop, correct the source or export it as LaTeX/Markdown.

`.md` and `.tex` exports preserve equation source and placement. `.tex` is a UTF-8 **fragment**, not a compiled document or a promise that arbitrary macros work. A surrounding XeLaTeX/LuaLaTeX document with Sinhala font configuration remains the user's downstream typesetting concern. These source formats intentionally preserve unaccepted source for further editing; DOCX requires acceptance for supported expressions.

Equation-aware PDF export is **pending**. TXT/PDF exports containing equation data fail clearly; existing equation-free TXT export continues to work. Original images and source documents are never replaced by export.

## Supported dialect and limits

Use math source without `$` delimiters. The bounded command allowlist in `equations.py` includes common physics symbols, functions, accents and `matrix`, `pmatrix`, `bmatrix`, `Bmatrix`, `vmatrix`, `Vmatrix`. Arbitrary macros, file IO, packages, equation numbering, alignment/cases environments and full TeX documents are unsupported. Syntax errors do not update the last preview; it is hidden until valid source is available. Preview preserves its aspect ratio. Source length is limited to 4000 characters and nesting to 32 levels.

## Recognition roadmap — next milestone

1. Select and license an optional offline equation model. Keep construction lazy and assets local; no automatic downloads during ordinary OCR. Add a detector that separates equation regions from Sinhala text and supports page coordinates/confidence. The current factory tests use an injected fake to verify dispatch only.
2. Reconcile detected equations and text layout into anchored inline/display objects. Preserve approved/manual equations on reruns, with explicit conflict review. Do not append overlapping OCR text and equation output as if layout reconstruction were complete.
3. Add optional provider adapters only behind explicit document/crop consent, uploads OFF by default, OS-backed credentials, quotas and cost controls. No cloud calls, credentials or provider configuration are implemented in this milestone.
4. Evaluate real Sinhala A/L Physics pages before claiming mathematical recognition. Owner-authorized samples, ground truth, provenance and disjoint train/validation/test splits are required. No such documents were supplied in this session.
5. Complete Word 2019/Windows visual tests and equation-aware PDF export before promoting experimental OMML support to release-ready.

## Accuracy metrics

`python -m sinhala_ocr.equation_benchmark manifest.json report.json` scores externally obtained held-out predictions. The manifest is a JSON list; each item has `id`, `document_id`, `split: "test"`, `reference`, and `prediction`. Store actual private pages and manifests outside Git. Predictions must come from the model/version being evaluated, not copied reference strings.

Reported metrics: exact source match rate, codepoint LaTeX character error rate, token error rate (commands retained as tokens), preview-valid rate and editable-conversion rate. Whitespace outside text/roman groups is ignored only in tokenization. Metrics are source comparisons, not mathematical equivalence or visual quality. Empty runs, duplicate IDs and non-test splits are rejected. Dataset provenance and split disjointness still need independent review. Detection/layout metrics and OCR runtime tracking are future additions.

`tests/regression/equations/physics.json` contains small synthetic A/L-style formula/context examples for preview/export regression. They are **not real scanned examination pages**, model predictions or an accuracy benchmark. No real Sinhala A/L Physics mathematical OCR accuracy result is available.

## Windows verification still required

- Microsoft Word **2019** on actual Windows: open every fixture; check no repair dialog, native equation editability, fractions/roots/limits/vectors/matrices, inline/display positions, Sinhala context, save/reopen and explicit image fallback labelling.
- Windows 10/11: LaTeX toggle preference and per-project restore; source-crop fidelity and selection at 100/150/200% DPI; equation preview and original text comparison; errors, undo/redo and preservation after OFF/reopen.
- Genuine installed Helakuru: surrounding Sinhala composition and shortcuts remain functional while equation workflows are open. Automated Qt editing is not a substitute.
- Packaged Windows executable: all renderer/font resources available offline. CI now collects ziamath, ziafont and latex2mathml resources and includes preview plus native-equation export in the executable smoke test. The changed workflow still requires a successful Windows run.
