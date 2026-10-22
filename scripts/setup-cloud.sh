#!/usr/bin/env bash
set -euo pipefail
cd /workspace/Sinhala_OCR_studio
python -m venv /workspace/ocr-venv
/workspace/ocr-venv/bin/python -m pip install -r requirements-lock.txt
/workspace/ocr-venv/bin/python -m pip install --no-deps -e .
command -v tesseract >/dev/null || { echo 'Install Tesseract 5 using the OS package manager.' >&2; exit 1; }
mkdir -p /workspace/ocr-tessdata
curl --fail --location https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/sin.traineddata -o /workspace/ocr-tessdata/sin.traineddata
printf '%s\n' 'bc75c6df2375a30c9f7e759fa7d4b58ae3ecf9ce72668a702d01acb13e551422  /workspace/ocr-tessdata/sin.traineddata' | sha256sum -c -
# Existing system English data supplied by the cloud image.
test -f /usr/share/tesseract-ocr/5/tessdata/eng.traineddata
ln -sf /usr/share/tesseract-ocr/5/tessdata/eng.traineddata /workspace/ocr-tessdata/eng.traineddata
export TESSDATA_PREFIX=/workspace/ocr-tessdata
export QT_QPA_PLATFORM=offscreen
/workspace/ocr-venv/bin/python -m pytest -q
/workspace/ocr-venv/bin/ruff check .
/workspace/ocr-venv/bin/python -m pip check
