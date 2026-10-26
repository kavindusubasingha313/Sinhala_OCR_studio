# Offline equation recognition (0.3.0)

1. Download and fully extract the latest successful **0.3.0 experimental Windows build**. Keep `_internal` beside the EXE; it contains the equation runtime and models. This build is larger because it works offline.
2. Open a document and turn **LaTeX ON**.
3. Choose **Equations → Mark region**. Zoom in and drag tightly around one equation, leaving a small white margin. Choose **Use region**.
4. Local recognition starts in the equation editor. Review the proposed LaTeX against the crop and choose Yes only to use that suggestion. For an existing crop, choose **Recognize equation · Offline**.
5. Correct any mistakes, inspect the preview, and choose **Accept**. Save the project. Export DOCX for editable supported Word equations.

No API key, upload, GPU or separate installation is needed for this offline path. Model output can be wrong, especially long expressions; acceptance is always manual. Unsupported LaTeX remains visible as source with an explicit preview/export error. OFF never starts offline recognition and preserves previous equations. Automatic detection across a full mixed Sinhala page is not included; the optional AI page action remains available with upload consent.

Source developers: install `requirements-equations.txt` in the project environment, then run `python scripts/fetch-equation-models.py` once while online. Subsequent inference is offline. `SINHALA_EQUATION_MODELS` can point to a directory containing all four verified model assets. Packaged users do not need these commands.

# Download and try the Windows application

These are experimental test builds, not stable releases. Python and Tesseract do not need to be installed separately: a successful Windows build includes the application and its offline OCR runtime.

1. Open this repository on GitHub and choose **Actions** → **Windows experimental build**.
2. Select the latest run for the intended commit. Only use a run with a green success check. A failed run is not a usable release.
3. Under **Artifacts**, download **SinhalaOCRStudio-experimental-windows-0.2.7-COMMIT**. GitHub sign-in/access may be required for private repositories.
4. Right-click the downloaded ZIP and choose **Extract All**. If it contains another ZIP, extract that too. Open the SinhalaOCRStudio folder.
5. Double-click **SinhalaOCRStudio.exe**. Keep the entire folder, including `_internal`, together. Do not run from inside the ZIP or copy only the EXE.

The build is unsigned. Windows may show a security warning; verify the repository and run provenance, and follow your organization's policy. Do not disable antivirus protection. No stable releases are published automatically. Stable release promotion requires a separate explicit gate after manual compatibility and licensing/signing checks.

Try a nonprivate image with Sinhala and English. Check editing, Undo/Redo, Accept, Save project, reopening, Light/Dark, and DOCX export in Word. Helakuru requires the actual installed Windows keyboard. Review WINDOWS_COMPATIBILITY_CHECKLIST.md; machine tests cannot certify this interaction.

If something fails, enable **Diagnostic logging**, repeat the operation and choose **Export bug report**. The ZIP contains OS/version and allowlisted event names, without documents, paths, keys or typed text. Add the build commit, what you expected and what happened. Attach only redacted screenshots. Submit through your usual project channel; the app does not upload automatically.

No downloadable build exists until this workflow has run successfully on GitHub. Linux tests do not prove that the Windows executable launches.

For version 0.2.7, use Import files to open several documents, then switch tabs and page thumbnails. The previous requirement to close one document before opening another is removed. Save each edited tab as a project before closing it. Advanced OCR is optional and requires your own API account/key plus per-page upload consent; no AI charges occur from ordinary offline OCR.

The 0.2.7 build also includes **Editable-Equation-Check.docx**, a synthetic sample. Open it in Microsoft Word, enable editing if prompted, and click a formula. Equation Tools should appear, and fraction components should be editable. This checks Word compatibility independently of recognition accuracy. If it shows picture handles instead, report your Word version and which formula you selected.

For direct Helakuru typing in 0.2.7, select a word or place your cursor, open **Sinhala typing pad**, type new text, then choose **Insert into document** and Save project. Use Undo/Redo, paste and Saved words in the main editor. The **Saved words** button stores reviewed spellings for later manual insertion.
