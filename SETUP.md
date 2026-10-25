# Setup and use

For a packaged Windows build, Python and Tesseract do not need separate installation. Follow DOWNLOAD_WINDOWS.md to download the latest successful **0.2.5** experimental artifact, extract the complete folder and launch SinhalaOCRStudio.exe. Keep `_internal` beside the EXE.

## Workspace

1. Choose **Import files** and select one or more PDFs/photos. Each file opens in its own tab. Importing another file no longer requires closing the current document.
2. Select a thumbnail or **Previous/Next** to change pages. Drag the original page to pan; use **Fit**, **+/-**, or Ctrl+mouse wheel to zoom.
3. Choose **Recognize page** for offline OCR of that page. Selectable PDF text is extracted directly. If a PDF text layer is garbled, use **More → Recognize visual page (ignore PDF text)**.
4. Review the suggestion before applying it. Applying a result saves the prior page in project history; **More → Restore previous OCR result** can recover it. Manual edits/Undo/Redo remain with each page while switching tabs.
5. **Save project** saves all pages of the active document. Close a tab using its ×; modified tabs offer Save, Discard or Cancel. **Export document** includes all pages of that tab.

## Sinhala input and remembered words

On Windows, open a document and choose **Windows Sinhala editor · type with Helakuru** above the main text editor. Type using your installed Helakuru keyboard in this native Windows control, then choose **Apply** to transfer the page back. Apply is undoable from the main editor. **Cancel** leaves the page unchanged and asks before discarding typing. Save the project afterwards. This bypass is awaiting actual Helakuru verification; the ordinary Qt editor's direct-input problem is not claimed fixed. The previous **Sinhala typing** diagnostic button is now called **Keyboard check**.

The Windows Sinhala editor also provides **Undo**, **Redo**, and **Saved words** directly. Select a word there to save or replace it without applying the entire page first.

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
