# Download and try the Windows application

These are experimental test builds, not stable releases. Python and Tesseract do not need to be installed separately: a successful Windows build includes the application and its offline OCR runtime.

1. Open this repository on GitHub and choose **Actions** → **Windows experimental build**.
2. Select the latest run for the intended commit. Only use a run with a green success check. A failed run is not a usable release.
3. Under **Artifacts**, download **SinhalaOCRStudio-experimental-windows-0.1.0-COMMIT**. GitHub sign-in/access may be required for private repositories.
4. Right-click the downloaded ZIP and choose **Extract All**. If it contains another ZIP, extract that too. Open the SinhalaOCRStudio folder.
5. Double-click **SinhalaOCRStudio.exe**. Keep the entire folder, including `_internal`, together. Do not run from inside the ZIP or copy only the EXE.

The build is unsigned. Windows may show a security warning; verify the repository and run provenance, and follow your organization's policy. Do not disable antivirus protection. No stable releases are published automatically. Stable release promotion requires a separate explicit gate after manual compatibility and licensing/signing checks.

Try a nonprivate image with Sinhala and English. Check editing, Undo/Redo, Accept, Save project, reopening, Light/Dark, and DOCX export in Word. Helakuru requires the actual installed Windows keyboard. Review WINDOWS_COMPATIBILITY_CHECKLIST.md; machine tests cannot certify this interaction.

If something fails, enable **Diagnostic logging**, repeat the operation and choose **Export bug report**. The ZIP contains OS/version and allowlisted event names, without documents, paths, keys or typed text. Add the build commit, what you expected and what happened. Attach only redacted screenshots. Submit through your usual project channel; the app does not upload automatically.

No downloadable build exists until this workflow has run successfully on GitHub. Linux tests do not prove that the Windows executable launches.
