"""Lazy CPU equation OCR. Model downloads are build-time only, never inference-time."""
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from threading import Lock
import hashlib
import os

from PIL import Image

from .equations import EquationError

MODEL_HASHES = {
    "encoder.onnx": "01bf5dc25539ca0cd5b1bd29296ea495977a6ba5f629dc4178277809d26e5e7d",
    "decoder.onnx": "bd695497bf1b22279b7626f5916c79226e1e244c84355f8da7edfd2d921d0072",
    "image_resizer.onnx": "e0b075c39700f64d50400f39c8fc186bbb3b5d84d31864008313f376603aca9d",
    "tokenizer.json": "1dc27b18d6a518d0d5ff3f4bb7bd98521fe80ad39e5b2a246d4109f1bb9d5019",
}
LOCK = Lock()


def model_directory():
    return Path(os.environ.get("SINHALA_EQUATION_MODELS", Path(__file__).parent / "assets" / "equation_models"))


def validate_models(directory):
    for name, expected in MODEL_HASHES.items():
        path = directory / name
        if not path.is_file():
            raise EquationError("Offline equation models are missing. Use the complete Windows build including its _internal folder. Source developers: run scripts/fetch-equation-models.py.")
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != expected:
            raise EquationError(f"Offline equation model integrity check failed: {name}. Download a fresh complete build.")


@lru_cache(maxsize=1)
def load_engine(directory):
    validate_models(directory)
    try:
        from rapid_latex_ocr import LaTeXOCR
    except ImportError as error:
        raise EquationError("Offline equation runtime is missing. Use the complete Windows build or install the project's equation dependencies.") from error
    # Explicit verified paths prevent the library's implicit download fallback.
    return LaTeXOCR(image_resizer_path=directory / 'image_resizer.onnx',
                    encoder_path=directory / 'encoder.onnx',
                    decoder_path=directory / 'decoder.onnx',
                    tokenizer_json=directory / 'tokenizer.json')


def recognize_equation(png: bytes, *, enabled: bool) -> str:
    if not enabled:
        raise EquationError("Turn LaTeX ON before recognizing equations. No equation model was loaded.")
    if not png or len(png) > 20_000_000:
        raise EquationError("Select a smaller, nonempty equation crop (maximum 20 MB).")
    with Image.open(BytesIO(png)) as image:
        if image.width * image.height > 12_000_000:
            raise EquationError("Equation crop exceeds 12 megapixels. Select just one expression.")
        gray = image.convert('L')
        low, high = gray.getextrema()
        if high - low < 10:
            raise EquationError("The selected region is blank. Select the printed equation.")
    with LOCK:
        source, _elapsed = load_engine(model_directory())(png)
    if not isinstance(source, str) or not source.strip() or len(source) > 4000:
        raise EquationError("No usable equation source was returned. Select a tighter crop or enter LaTeX manually.")
    # Keep unsupported output as a reviewable draft; rendering/export validate separately.
    return source.strip()
