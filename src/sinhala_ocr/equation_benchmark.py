"""Score held-out equation predictions. This tool does not run OCR or invent data.

Usage: python -m sinhala_ocr.equation_benchmark manifest.json report.json
"""
import argparse
import json
from pathlib import Path
import re

from .equations import Equation, EquationError, equation_omml, render_equation


def distance(expected, actual):
    previous = list(range(len(actual) + 1))
    for row, left in enumerate(expected, 1):
        current = [row]
        for column, right in enumerate(actual, 1):
            current.append(min(current[-1] + 1, previous[column] + 1,
                               previous[column - 1] + (left != right)))
        previous = current
    return previous[-1]


def tokens(source):
    """Keep whitespace within \\text/\\mathrm groups; tokenize syntax elsewhere."""
    return re.findall(r"\\(?:text|mathrm)\{[^{}]*\}|\\[A-Za-z]+|\\.|[^\s]", source)


def score_equations(records):
    if not records:
        raise ValueError("A benchmark must contain at least one held-out equation.")
    identifiers, documents = set(), set()
    exact = char_errors = char_total = token_errors = token_total = valid = editable = 0
    for item in records:
        if item["split"] != "test":
            raise ValueError("Only held-out test records may be scored; keep training/validation separate.")
        if item["id"] in identifiers:
            raise ValueError("Duplicate equation ID.")
        identifiers.add(item["id"])
        documents.add(item["document_id"])
        expected, predicted = item["reference"], item["prediction"]
        if not expected or max(len(expected), len(predicted)) > 4000:
            raise ValueError("Reference must be nonempty and each source at most 4000 characters.")
        exact += expected == predicted
        char_errors += distance(expected, predicted)
        char_total += len(expected)
        reference_tokens, predicted_tokens = tokens(expected), tokens(predicted)
        token_errors += distance(reference_tokens, predicted_tokens)
        token_total += len(reference_tokens)
        try:
            render_equation(predicted)
            valid += 1
        except EquationError:
            pass
        try:
            equation_omml(Equation(latex=predicted))
            editable += 1
        except EquationError:
            pass
    count = len(records)
    return {"equations": count, "documents": len(documents), "exact_match_rate": exact / count,
            "latex_character_error_rate": char_errors / char_total,
            "latex_token_error_rate": token_errors / max(1, token_total),
            "preview_valid_rate": valid / count, "editable_conversion_rate": editable / count,
            "notes": "Source metrics are not mathematical equivalence, visual Word correctness, region detection recall or Sinhala OCR accuracy. Dataset provenance and split disjointness require independent review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    if args.manifest.resolve() == args.report.resolve():
        parser.error("Report must not overwrite the input manifest.")
    report = score_equations(json.loads(args.manifest.read_text(encoding="utf-8")))
    from .core import atomic_write
    atomic_write(args.report, lambda p: p.write_text(json.dumps(report, indent=2), encoding="utf-8"),
                 lambda p: json.loads(p.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
