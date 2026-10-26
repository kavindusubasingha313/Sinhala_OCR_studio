"""Build-time download of pinned RapidLaTeXOCR assets, with atomic verified writes."""
from pathlib import Path
import hashlib
import os
import sys
import tempfile
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sinhala_ocr.offline_equations import MODEL_HASHES, model_directory, validate_models  # noqa: E402


def main():
    directory = model_directory()
    directory.mkdir(parents=True, exist_ok=True)
    for name, expected in MODEL_HASHES.items():
        destination = directory / name
        if destination.is_file():
            with destination.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() == expected:
                    continue
        temp = None
        try:
            digest = hashlib.sha256()
            total = 0
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
                temp = Path(stream.name)
                with urlopen('https://github.com/RapidAI/RapidLaTeXOCR/releases/download/v0.0.0/' + name, timeout=120) as response:
                    while block := response.read(1024 * 1024):
                        total += len(block)
                        if total > 150_000_000:
                            raise ValueError('Model download exceeds size limit')
                        stream.write(block)
                        digest.update(block)
            if digest.hexdigest() != expected:
                raise ValueError(f'Model checksum mismatch: {name}')
            os.replace(temp, destination)
            print(f'Verified {name}: {total} bytes')
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
    validate_models(directory)


if __name__ == '__main__':
    main()
