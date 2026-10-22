"""Equation data and bounded offline LaTeX processing; no model imports here."""
from dataclasses import dataclass, field
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Callable, Protocol
from uuid import uuid4
import base64
import re
import xml.etree.ElementTree as ET

from PIL import Image, ImageOps


class EquationError(ValueError):
    """Unsupported or malformed equation; never silently substitute text."""


@dataclass
class Equation:
    latex: str = ""
    original_latex: str = ""
    placement: str = "display"
    status: str = "draft"
    id: str = field(default_factory=lambda: uuid4().hex)
    image_png: str = ""  # Embedded lossless crop survives source relocation.
    bbox: list[int] | None = None  # EXIF-oriented source pixel coordinates.

    @property
    def marker(self):
        return f"[[eq:{self.id}]]"

    def edit(self, latex):
        if self.latex != latex:
            self.latex = latex
            self.status = "draft"

    def accept(self):
        render_equation(self.latex, self.placement)
        self.status = "accepted"

    def restore(self):
        self.latex = self.original_latex
        self.status = "draft"


def equation_crop(source: Path, bbox: tuple[int, int, int, int]) -> Equation:
    with Image.open(source) as raw:
        image = ImageOps.exif_transpose(raw)
        left, top, right, bottom = bbox
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise EquationError("Select a nonempty region inside the image.")
        output = BytesIO()
        image.crop(bbox).convert("RGB").save(output, format="PNG")
    return Equation(image_png=base64.b64encode(output.getvalue()).decode("ascii"), bbox=list(bbox))


# Deliberately finite dialect: arbitrary TeX macros, file IO and document commands
# are not executed. Expand this list only with renderer and export regressions.
COMMANDS = set("""frac dfrac tfrac sqrt alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi varpi rho varrho sigma varsigma tau upsilon phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega int iint iiint oint sum prod lim sin cos tan cot sec csc sinh cosh tanh log ln exp min max det inf sup vec hat bar overline dot ddot mathbf mathrm mathit mathcal mathbb text left right begin end cdot times div pm mp le leq ge geq ne neq approx equiv sim simeq propto infty partial nabla degree circ perp parallel angle in notin subset supset subseteq supseteq cup cap forall exists to rightarrow leftarrow leftrightarrow Rightarrow Leftarrow Leftrightarrow ldots cdots vdots ddots quad qquad lvert rvert vert lVert rVert Vert langle rangle lbrace rbrace limits nolimits displaystyle textstyle""".split())
ENVIRONMENTS = {"matrix", "pmatrix", "bmatrix", "Bmatrix", "vmatrix", "Vmatrix"}
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
OMML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


@lru_cache(maxsize=128)
def mathml(latex: str, placement: str = "display") -> str:
    if placement not in {"inline", "display"}:
        raise EquationError("Choose inline or display placement.")
    if not latex.strip():
        raise EquationError("Enter a LaTeX equation.")
    if len(latex) > 4000:
        raise EquationError("Equation exceeds the 4000-character preview limit.")
    if "$" in latex or "%" in latex or "#" in latex:
        raise EquationError("Enter math source without dollar delimiters, comments or macro parameters.")
    for token in re.findall(r"\\(?:[A-Za-z]+|.)", latex):
        command = token[1:]
        if command.isalpha() and command not in COMMANDS:
            raise EquationError(f"Unsupported LaTeX command: {token}")
        if not command.isalpha() and command not in "{},;:! |\\":
            raise EquationError(f"Unsupported escape: {token}")
    depth = 0
    for token in re.findall(r"\\.|[{}]", latex):
        if token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
        if depth < 0 or depth > 32:
            raise EquationError("Unbalanced or excessively nested braces.")
    if depth:
        raise EquationError("Unbalanced braces.")
    environments = []
    for kind, name in re.findall(r"\\(begin|end)\{([^{}]+)\}", latex):
        if name not in ENVIRONMENTS:
            raise EquationError(f"Unsupported environment: {name}")
        if kind == "begin":
            environments.append(name)
        elif not environments or environments.pop() != name:
            raise EquationError("Mismatched equation environments.")
    if environments:
        raise EquationError("Unclosed equation environment.")
    try:
        from latex2mathml.converter import convert
        xml = convert(latex, display="block" if placement == "display" else "inline")
        root = ET.fromstring(xml)
        arity = {"mfrac": 2, "msup": 2, "msub": 2, "msubsup": 3,
                 "mroot": 2, "mover": 2, "munder": 2, "munderover": 3}
        allowed = {"math", "mrow", "mi", "mn", "mo", "mtext", "mspace", "mstyle",
                   "msqrt", "mtable", "mtr", "mtd", "mfenced", *arity}
        for node in root.iter():
            tag = node.tag.split("}")[-1]
            if tag not in allowed:
                raise EquationError(f"Unsupported mathematical structure: {tag}")
            if tag in arity and len(node) != arity[tag]:
                raise EquationError(f"Missing argument in {tag}.")
            if tag in arity or tag == "msqrt":
                if any(not "".join(child.itertext()).strip() for child in node):
                    raise EquationError(f"Empty argument in {tag}.")
            if tag in {"mi", "mn", "mo"} and not (node.text or "").strip():
                raise EquationError("Missing mathematical operand.")
            if node.text and "\\" in node.text:
                raise EquationError(f"Unconverted LaTeX token: {node.text}")
        return xml
    except EquationError:
        raise
    except Exception as error:
        raise EquationError(f"Invalid LaTeX syntax ({type(error).__name__}).") from error


@lru_cache(maxsize=128)
def render_equation(latex: str, placement: str = "display") -> bytes:
    xml = mathml(latex, placement)
    try:
        import ziamath
        ziamath.config.svg2 = False  # Qt SVG 1.1 support; paths, no browser/network.
        drawing = ziamath.Math(xml, size=24)
        svg = drawing.svg()
        root = ET.fromstring(svg)
        if float(root.attrib["width"]) > 8000 or float(root.attrib["height"]) > 8000:
            raise EquationError("Equation is too large to preview.")
        return svg.encode("utf-8")
    except EquationError:
        raise
    except Exception as error:
        raise EquationError(f"Cannot render this equation ({type(error).__name__}).") from error


def equation_omml(equation: Equation):
    from .omml import convert_mathml
    return convert_mathml(mathml(equation.latex, equation.placement))


@dataclass
class EquationDetection:
    bbox: tuple[int, int, int, int]
    latex: str
    placement: str = "display"


class EquationEngine(Protocol):
    """Future optional local/provider adapter; construction must be lazy."""
    def detect_and_recognize(self, source: Path) -> list[EquationDetection]: ...


@dataclass
class PipelineResult:
    text_result: object
    equations: list[Equation] = field(default_factory=list)
    notice: str = ""


def recognize_document(source, text_engine, latex_enabled=False,
                       equation_engine_factory: Callable[[], EquationEngine] | None = None):
    text = text_engine.recognize(source)
    if not latex_enabled:
        return PipelineResult(text)  # Factory is never called or imported when OFF.
    if equation_engine_factory is None:
        return PipelineResult(text, notice="Automatic equation recognition is not installed. Use Add equation or Mark equation region.")
    equations = []
    for detected in equation_engine_factory().detect_and_recognize(source):
        equation = equation_crop(source, detected.bbox)
        equation.latex = equation.original_latex = detected.latex
        equation.placement = detected.placement
        equations.append(equation)
    return PipelineResult(text, equations)
