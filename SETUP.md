# Paste a crop and export text — 0.3.1

1. In Windows Snipping Tool, capture the text area and copy the image.
2. In Sinhala OCR Studio choose **Paste / drop image**, then **Paste image** (or Ctrl+V inside that dialog). Alternatively drop one local image file or choose **Choose image**.
3. Leave **Sinhala + English text → TXT / DOCX** selected and click **Open and recognize**.
4. Compare the OCR suggestion with the image, apply it, and correct any mistakes in the editor.
5. Choose **Export document**, select **Unicode text (*.txt)** or **Word**, and save. Save project separately to retain the editable workspace.

For a cropped formula, choose **Single equation → editable LaTeX / DOCX** in step 3. Offline recognition starts in its equation editor; review the proposed source, correct it and Accept before exporting Word. For previously marked equations use the visible **Equations → Recognize selected equation · Offline** button. If prompted, confirm LaTeX ON. No API key or image upload is needed for offline recognition.

Look for **v0.3.1** in the application title/header after downloading the latest successful experimental build. The capture is retained under the application's local data directory in `captured-images`; do not delete it while a saved project still references it. Captured images are not embedded into the project as full-page sources and moving a project to another computer requires retaining its source image. Clipboard is read only when Paste is requested; Ctrl+V in the ordinary text editor remains normal text paste.

# Offline equation recognition (0.3.0)

1. Download and fully extract the latest successful **0.3.0 experimental Windows build**. Keep `_internal` beside the EXE; it contains the equation runtime and models. This build is larger because it works offline.
2. Open a document and turn **LaTeX ON**.
3. Choose **Equations → Mark region**. Zoom in and drag tightly around one equation, leaving a small white margin. Choose **Use region**.
4. Local recognition starts in the equation editor. Review the proposed LaTeX against the crop and choose Yes only to use that suggestion. For an existing crop, choose **Recognize equation · Offline**.
5. Correct any mistakes, inspect the preview, and choose **Accept**. Save the project. Export DOCX for editable supported Word equations.

No API key, upload, GPU or separate installation is needed for this offline path. Model output can be wrong, especially long expressions; acceptance is always manual. Unsupported LaTeX remains visible as source with an explicit preview/export error. OFF never starts offline recognition and preserves previous equations. Automatic detection across a full mixed Sinhala page is not included; the optional AI page action remains available with upload consent.

Source developers: install `requirements-equations.txt` in the project environment, then run `python scripts/fetch-equation-models.py` once while online. Subsequent inference is offline. `SINHALA_EQUATION_MODELS` can point to a directory containing all four verified model assets. Packaged users do not need these commands.

# Workspace changes in 0.2.8

- Choose **Recognize blank pages** to process the active document's empty pages. Review/Apply each result; Cancel stops the queue. Pages already containing text, equations or approvals are skipped.
- For garbled selectable PDF text, use **Garbled PDF text? Recognize visual page** on that page, then review before replacement.
- In **Equations → Mark region**, use **+**, **−**, **100%**, **Fit** and scrollbars to select a small expression. Marking stores an image; use the equation editor's AI action or enter its LaTeX source.
- **Equations → Recognize page equations · AI** enables LaTeX and requests the selected page through the configured provider, after upload consent. It requires an API key/billing and cannot guarantee recognition. Offline Tesseract does not produce separate equations.
- If export finds a missing equation reference, it opens that page and selects the equation. Click the intended position in the Text editor, return to Equations and click **Insert in text**, then export again. Reject unwanted equations explicitly instead of losing their data.
- **Qt font diagnostic** is not the **Sinhala typing pad**. Repeated direct-input characters in Qt remain unresolved. Use the native pad for testing; if it also fails, type in Notepad and paste into the main document.

For the current input failure investigation, use the separate **Windows input investigation (diagnostic only)** Actions workflow. Its Summary contains comparisons; its optional standalone EXE and instructions are described in [diagnostics/READ_ME_FIRST.md](diagnostics/READ_ME_FIRST.md). This is not a new OCR release.

# Setup and use

For a packaged Windows build, Python and Tesseract do not need separate installation. Follow DOWNLOAD_WINDOWS.md to download the latest successful **0.2.8** experimental artifact, extract the complete folder and launch SinhalaOCRStudio.exe. Keep `_internal` beside the EXE.

## Workspace

1. Choose **Import files** and select one or more PDFs/photos. Each file opens in its own tab. Importing another file no longer requires closing the current document.
2. Select a thumbnail or **Previous/Next** to change pages. Drag the original page to pan; use **Fit**, **+/-**, or Ctrl+mouse wheel to zoom.
3. Choose **Recognize page** for offline OCR of that page. Selectable PDF text is extracted directly. If a PDF text layer is garbled, use **More → Recognize visual page (ignore PDF text)**.
4. Review the suggestion before applying it. Applying a result saves the prior page in project history; **More → Restore previous OCR result** can recover it. Manual edits/Undo/Redo remain with each page while switching tabs.
5. **Save project** saves all pages of the active document. Close a tab using its ×; modified tabs offer Save, Discard or Cancel. **Export document** includes all pages of that tab.

## Sinhala input and remembered words

On Windows, select the word you want to replace (or place the cursor where new text belongs), then choose **Sinhala typing pad · Helakuru**. Type new text in the blank pad, then choose **Insert into document**. The original selection remains in your document until insertion. Use the main editor's **Undo** and **Redo** to reverse/reapply the entire insertion. Cancel leaves the page unchanged and asks before discarding unsent typing. Save your project afterwards.

Use the main editor for **paste, Saved words and document corrections**. The typing pad is for direct keyboard entry; native replacement/paste Undo remains unreliable. Actual Helakuru input still requires verification. The keyboard diagnostic panel remains available as **Keyboard check**.

To remember a complex spelling, select the correctly spelled word in the page editor, open **Saved words**, and choose **Save reviewed spelling**. In a later document, select an incorrect word, open **Saved words**, pick a saved suggestion and choose **Insert selected word**. It replaces only the selection and supports Undo. You can also search, add pasted words and delete saved words. Entries stay on your computer, outside project files; nothing is automatically corrected or uploaded. This feature does not train the recognition model.

If the native editor still has an input problem, compare the same word in Notepad and paste it into the page to preserve exact text. Record the Helakuru version/input mode and which editor failed for troubleshooting.

## Equations

Enable **LaTeX ON** for mathematical extraction with Advanced OCR. Standard offline Tesseract remains a text baseline. In the **Equations** tab, add source manually, select a region from the rendered original page, or convert selected LaTeX text into an equation. Double-click an equation to edit its source, preview and Accept it. For a marked crop, click **Recognize this equation · AI** in that editor to obtain a LaTeX suggestion using your configured API key; approve the crop upload, review the proposed source, then Accept after checking the preview. Marking alone does not recognize the equation. The text editor shows a readable reference such as ⟦Equation 1⟧; moving it changes equation placement.

Export **Word with editable equations** after accepting the sources. Supported formulas become genuine Word equation objects; they are not preview images. An unsupported source stops export and only uses an image if you explicitly choose that fallback. Markdown/LaTeX source exports retain the source. See LATEX_EQUATIONS.md for dialect limits. Actual Word 2019 visual/editing checks remain manual.

## Advanced OCR (optional)

Choose **Advanced OCR**, enter an OpenAI API key in the application’s settings on first use, and select a model if needed. An API account/billing is required; a ChatGPT subscription does not include these API calls. Keys are stored through Windows Credential Manager (or another supported OS vault), not in project files or plain settings. Never paste a key into chat or commit it.

Each call asks permission to send the **selected page only** to OpenAI. Default: at most 10 attempts/day, one page/request, 4,096 output tokens, no automatic retries. Review provider costs and set provider-side spending limits. The returned suggestion is reviewed before replacing text; equation suggestions need their own review/Accept before Word export. No live API call or accuracy benchmark was performed in development tests.

## Cloud/Linux development

```sh
cd /workspace/Sinhala_OCR_studio
bash scripts/setup-cloud.sh
export TESSDATA_PREFIX=/workspace/ocr-tessdata
QT_QPA_PLATFORM=offscreen /workspace/ocr-venv/bin/pytest -q
/workspace/ocr-venv/bin/ruff check .
QT_QPA_PLATFORM=offscreen /workspace/ocr-venv/bin/python -m sinhala_ocr.app --smoke-test
```

The setup script installs pinned dependencies in /workspace/ocr-venv and verifies the official Sinhala Tesseract model checksum. The image supplies Python 3.12/Tesseract 5.5.0 with English data. PDFium renders PDF pages, and the packaged mathematical fonts support local LaTeX preview. No TeX installation/browser is required.

For an interactive graphical desktop, launch `/workspace/ocr-venv/bin/sinhala-ocr-studio` without the offscreen setting. The cloud image has no usable credential vault by default; this does not block offline workflows. AI adapter tests use mocked transport.

Windows source development (not executed locally): Python 3.11+, a venv, `pip install -e ".[dev]"`, trusted Tesseract 5 plus sin/eng data, Tesseract on PATH and TESSDATA_PREFIX pointing at its tessdata folder. The Windows CI workflow installs and packages these dependencies for nontechnical testers.
