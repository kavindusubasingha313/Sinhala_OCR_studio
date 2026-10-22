# Development instructions

Use the existing checkout; each cloud task is isolated. Do not create worktrees unless requested. Read ARCHITECTURE.md, SETUP.md, DEVELOPMENT_STATUS.md and KNOWN_ISSUES.md before changes. Preserve existing features and manual corrections. Keep cloud uploads off by default. Do not intercept composition keystrokes in native Qt text controls.

Use `/workspace/ocr-venv/bin/python`; set TESSDATA_PREFIX=/workspace/ocr-tessdata and QT_QPA_PLATFORM=offscreen for Linux tests. Run pytest, ruff and pip check after meaningful changes. Keep test claims tied to actual executions. Never claim Windows/Helakuru verification from Linux. Do not commit documents, secrets or generated user projects. Add regression coverage for export integrity and protected text whenever those paths change.
