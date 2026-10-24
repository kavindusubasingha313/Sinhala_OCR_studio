"""Create a synthetic Word editability check; no OCR result or private data."""
import argparse
from pathlib import Path

from sinhala_ocr.core import Document, export_document
from sinhala_ocr.equations import Equation

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output", type=Path)
args = parser.parse_args()
examples = [
    ("Inline physics notation", "F=ma", "inline"),
    ("Fraction and power", r"E_k=\frac{1}{2}mv^2", "display"),
    ("Square root", r"v=\sqrt{2gh}", "display"),
    ("Vector", r"\vec{F}=m\vec{a}", "display"),
    ("Matrix", r"\begin{pmatrix}a&b\\c&d\end{pmatrix}", "display"),
]
equations = []
text = "Sinhala OCR Studio · Editable equation check\n\nThis is a synthetic validation sample, not recognized text. In Microsoft Word, enable editing if needed and click a formula. Equation Tools should appear; the numerator, denominator and symbols should be editable, without picture-selection handles.\n\nSinhala text: වස්තුවක් මත ක්‍රියා කරන බලය\n"
for title, latex, placement in examples:
    equation = Equation(latex=latex, original_latex=latex, placement=placement)
    equation.accept()
    equations.append(equation)
    text += "\n" + title + ": " + equation.marker + "\n"
args.output.parent.mkdir(parents=True, exist_ok=True)
export_document(Document("synthetic-equation-check", text, equations=equations), args.output)
