0.3.1: image_intake.py owns explicit local bitmap/file intake, bounded image loading, white alpha compositing and atomic capture persistence under AppDataLocation. App coordination opens each capture as an independent document and reuses existing reviewed OCR/export or equation recognition. Ctrl+V is scoped to the image dialog, never intercepted in text/IME controls. Captured source images persist outside Git; no automatic upload or deletion. Equation preprocessing preserves the original stored crop and supplies a white-padded inference copy.

0.3.0 adds offline_equations.py: a lazy, locked CPU model adapter with verified explicit asset paths and no inference-time downloads. The equation editor invokes it on a worker; replacement requires review and retains source Undo. Model preparation is build-time via fetch-equation-models.py, separate from core Sinhala OCR. Windows packaging includes ONNX Runtime, RapidLaTeXOCR, tokenizer/config assets, model weights and license notices. Offline selection recognition and whole-page region detection are distinct; only selection recognition is implemented here. No PyTorch/GPU dependency is used.

0.2.8 adds a scrollable, scaled region selector with source-pixel coordinate mapping. Export validates placement page by page before selecting a destination and directs the user to the first broken anchor. The blank-page OCR queue processes sequential background tasks with explicit per-page review; cancellation/failure stops it, and nonempty/protected pages are skipped. AI equation recognition reuses the existing provider and consent layer. Input composition remains unchanged.

`synthetic_input.py` generates explicit Enter key sequences for smoke fixtures. It is never attached to the user input pipeline; native Windows/Helakuru composition remains unfiltered. Multiline fixtures preserve exact newline assertions.

Explicit synthetic smoke execution uses `smoke_report.py` for checkpoint/error JSON. It never opens user documents or reads provider keys. CI separately checks source and frozen execution, publishes errors and prevents artifact release without a passed report. Normal application diagnostics retain their existing privacy restrictions.

# Current input architecture (0.2.7)

QTextDocument owns document text and all replacement/Undo/Redo operations. WindowsInputDialog is a blank native typing pad with read-only selection context. Its Insert action transfers new Unicode text through the captured QTextCursor in one edit block; it never seeds RichEdit with original document content. Empty results are ignored; page/session/text changes prevent stale insertion. Saved vocabulary remains in the main Qt editor. DiagnosticWindowsEditor retains the former full-document native implementation solely for reproduction. Diagnostic native replacement failures are not treated as product successes.

Technology decision: retain Python 3.12 and PySide6 6.8.3, whose text engine is Qt C++; use the OS RichEdit control only for native typing. The supplied matrix supports Qt replacement history, while actual Helakuru must be tested separately. C#/WPF or WinUI could be evaluated later if needed, but neither a language switch nor an accuracy/performance advantage is established by current evidence. No new dependency was added.

`diagnostics/input_lab.py` is an isolated investigation harness, not production code. Raw Win32 workers use only the standard library and run in separate processes from Qt; Qt baseline and current app workers provide comparison. The manual lab is packaged in its own diagnostic-only workflow. Synthetic clipboard probing is restricted to GitHub Actions; manual typing is neither recorded nor uploaded.

As of 0.2.6 the native RichEdit window uses standard rich-text/Unicode/multilevel-undo mode to investigate cross-script Undo failures in the restricted plain-text mode. Text-only extraction and project persistence remain unchanged; rich formatting and embedded objects are outside the typing-window transfer contract. Actual Windows validation is still required. Emoji recognition is outside product scope; mathematical symbols remain covered.

Native replacement records deletion and insertion separately within the TOM undo collection. A single EM_REPLACESEL remained incorrect for the Latin-to-Sinhala undo fixture on Windows despite grouping; the explicit two-message path is under Windows validation.

Programmatic native word replacement uses ITextDocument BeginEditCollection/EndEditCollection with explicit typing boundaries, so deletion and insertion form one undo unit. COM references are scoped to each replacement; failure to obtain grouping support prevents insertion. This does not hook or rewrite IME events.

The 0.2.3 native input dialog includes saved-word selection/insertion and explicit Undo/Redo. Selection extraction uses RichEdit UTF-16 character ranges rather than slicing Python text at Win32 positions. Closed control reads fail instead of returning empty text.

## Windows input and personal vocabulary (0.2.2)

`windows_input.py` hosts a real Windows RICHEDIT50W child HWND from the system Msftedit library inside a Qt dialog. Windows handles keystrokes, composition, selection and undo directly; no Qt key remapping or speculative deduplication is used. The main editor remains Qt. The Windows Sinhala editor explicitly transfers a full-page edit on Apply as one undoable Qt change; Cancel retains the page, and discarding typed changes requires confirmation. Only CR/CRLF paragraph separators are adapted to Qt LF; Sinhala sequences, ZWJ and repeated characters are retained. The native surface uses Nirmala UI and native Windows rendering. Handles/fonts are released when the dialog finishes. Real Helakuru verification is pending.

`word_memory.py` stores only explicitly saved words/short phrases in versioned UTF-8 JSON under Qt's local AppDataLocation. Writes are validated and atomically replaced; malformed existing data is not silently reset. Suggestions use substring/string similarity, not a linguistic model. Insertion is manual and undoable. This is a personal vocabulary, not OCR training or automatic spell correction. No vocabulary is uploaded automatically. Users can remove entries in the dialog.

# Architecture

Sinhala OCR Studio 0.2.0 is an offline-first Python/PySide6 application with an explicitly opt-in provider adapter.

## Workspace and persistence

`core.py` owns Document/DocumentPage, backward-compatible JSON projects, protected atomic writes and export dispatch. Page data owns text, equation objects, approval and previous OCR-result history. The root document mirrors its selected page for compatibility with the earlier project/API shape. Page capture occurs before switching, saving and exporting. All-page export flattens a snapshot; it does not reconstruct the original document layout.

`app.py` coordinates Session objects, tab/page navigation, saved/dirty state, background jobs and explicit result review. Each open page retains its native QTextDocument and undo history. Worker completions are delivered through a main-thread Qt slot. Preview generation IDs prevent old jobs from replacing the current page. Imports can open multiple files without closing an existing tab; dirty closing requires Save/Discard/Cancel. Export uses a deep snapshot. OCR replacements record the previous page and require explicit user confirmation.

`documents.py` imports PDF/image page metadata and selectable text, renders individual PDF pages/image frames, and runs selected-page baseline OCR. PDFium access is serialized because the renderer is not thread-safe. Rendering is bounded to 3,500 pixels on the longest edge; AI uses 2,000. Import accepts up to 500 pages/frames. Preview caches retain three full pages per session; the first 60 thumbnails are prefetched, with later pages rendered on demand.

## UI and input

`workspace_widgets.py` provides a panning/zooming page viewer, native QPlainTextEdit, consent/result dialogs, provider settings and a Sinhala typing panel. `themes.py` scopes Fusion styling for light/dark/system modes. The editor uses explicit Sinhala-capable font families, native IME support and no key filtering/normalization. OCR/Accept shortcuts no longer occupy global composition-related shortcuts. Actual Windows Helakuru compatibility requires verification; simulated preedit/commit events are regression-tested with වස්තුවක්.

Stable project equation IDs remain internal. Readable ⟦Equation N⟧ references are mapped to/from those IDs by the UI; malformed/missing/duplicated anchors are rejected at export.

## Equations and export

`equations.py` owns source/crop data, bounded LaTeX validation, rendering and the optional engine contract. `equation_ui.py` retains manual source editing, crop comparison, live preview and review actions. `omml.py` performs conservative native Word conversion. `equation_export.py` validates Unicode context, equation counts/placement, absence of text boxes and explicit fallback images before atomic replacement. Word math font is set to Cambria Math; no supported equation is silently rasterized. `.md`/`.tex` preserve sources; searchable/equation-aware PDF output is pending.

Recognition, rendering, typography and layout remain separate concerns. No offline neural equation model is included. Sinhala font assets use the SIL OFL licence in the assets directory; Word reading systems still need suitable Sinhala fonts.

## Advanced OCR privacy and costs

`advanced_ocr.py` implements the OpenAI Responses API adapter. It receives only the rendered selected page after explicit per-request consent. `store:false` is requested; provider retention policies still apply. A structured response separates exact-transcription text from LaTeX equations. Results stay drafts until user review; the adapter validates sizes, completion state and anchors. Provider output is treated as untrusted data.

The API key is read from an allowlisted OS-vault keyring backend (Windows Credential Manager, macOS Keychain or Secret Service); plaintext/fallback stores are rejected. Credentials and provider payloads are never logged or saved in projects. HTTP redirects are refused to avoid forwarding credentials. No automatic retries occur. The UI enforces a persisted daily attempt cap (default 10, maximum 50), bounded image size and 4,096 output tokens. These are usage controls, not a fixed currency budget. Only OpenAI is currently implemented; live requests require the owner's account and consent.

Diagnostics remain opt-in, bounded and limited to event names without typed text, documents, environment variables or credentials.

## Evaluation and release

The equation benchmark scores externally supplied held-out predictions; synthetic fixtures are not recognition accuracy evidence. Training/validation/test provenance and independent Sinhala A/L Physics evaluation remain required. Windows CI runs tests, creates an experimental directory build, checks packaged page rendering/tab navigation/equation output, and uploads build/test/log artifacts. Local Linux tests/frozen-app checks do not establish Windows, Helakuru or Microsoft Word fidelity. Stable promotion remains a separate gate.
