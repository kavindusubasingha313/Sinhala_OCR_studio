"""Conservative MathML→OMML conversion for the tested equation dialect.

Unsupported structures/attributes fail explicitly. This does not compile TeX.
"""
import xml.etree.ElementTree as ET
from lxml import etree

from .equations import EquationError, OMML_NS


def element(tag, *children, **attrs):
    node = etree.Element(f"{{{OMML_NS}}}{tag}")
    for name, value in attrs.items():
        node.set(f"{{{OMML_NS}}}{name}", value)
    node.extend(children)
    return node


def local(node):
    return node.tag.split("}")[-1]


def convert_mathml(xml):
    root = ET.fromstring(xml)

    def convert(node, variant=None):
        tag = local(node)
        variant = node.get("mathvariant", variant)
        children = list(node)

        def group(name, child):
            return element(name, *convert(child, variant))

        if tag in {"math", "mrow", "mstyle"}:
            if len(children) >= 3 and local(children[0]) == local(children[-1]) == "mo":
                first, last = children[0], children[-1]
                if first.get("fence") == last.get("fence") == "true":
                    props = element("dPr", element("begChr", val=first.text or ""), element("endChr", val=last.text or ""))
                    body = [item for child in children[1:-1] for item in convert(child, variant)]
                    return [element("d", props, element("e", *body))]
            return [item for child in children for item in convert(child, variant)]
        if tag in {"mi", "mn", "mo", "mtext", "mspace"}:
            content = " " if tag == "mspace" else node.text or ""
            text = element("t")
            text.text = content
            text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            props = element("rPr")
            if tag == "mtext":
                props.append(element("nor"))
            style = "i" if tag == "mi" and len(content) == 1 else "p"
            if variant in {"normal", "italic", "bold", "bold-italic"}:
                style = {"normal": "p", "italic": "i", "bold": "b", "bold-italic": "bi"}[variant]
            elif variant in {"double-struck", "script", "fraktur", "sans-serif", "monospace"}:
                props.append(element("scr", val=variant))
                style = "p"
            elif variant:
                raise EquationError(f"Unsupported Word equation font variant: {variant}")
            props.append(element("sty", val=style))
            return [element("r", props, text)]
        if tag == "mfrac":
            return [element("f", group("num", children[0]), group("den", children[1]))]
        if tag in {"msup", "msub", "msubsup"}:
            target = {"msup": "sSup", "msub": "sSub", "msubsup": "sSubSup"}[tag]
            result = element(target, group("e", children[0]))
            if tag in {"msub", "msubsup"}:
                result.append(group("sub", children[1]))
            if tag in {"msup", "msubsup"}:
                result.append(group("sup", children[-1]))
            return [result]
        if tag in {"msqrt", "mroot"}:
            if tag == "mroot":
                degree = group("deg", children[1])
                body = group("e", children[0])
            else:
                degree = element("deg")
                body = element("e", *[item for child in children for item in convert(child, variant)])
            props = element("radPr", element("degHide", val="1" if tag == "msqrt" else "0"))
            return [element("rad", props, degree, body)]
        if tag in {"mover", "munder", "munderover"}:
            base = children[0]
            accent_text = "".join(children[-1].itertext())
            is_accent = node.get("accent") == "true" or children[-1].get("accent") == "true" or (children[-1].get("stretchy") == "true" and accent_text in {"→", "←", "↔"})
            if tag == "mover" and is_accent:
                accent = "".join(children[1].itertext())
                if len(accent) != 1:
                    raise EquationError("Word conversion supports single-character accents only.")
                return [element("acc", element("accPr", element("chr", val=accent)), group("e", base))]
            if tag == "munderover":
                under = element("limLow", group("e", base), group("lim", children[1]))
                return [element("limUpp", element("e", under), group("lim", children[2]))]
            return [element("limUpp" if tag == "mover" else "limLow", group("e", base), group("lim", children[1]))]
        if tag == "mtable":
            rows = []
            widths = set()
            for row in children:
                if local(row) != "mtr" or any(local(cell) != "mtd" for cell in row):
                    raise EquationError("Unsupported matrix row structure.")
                widths.add(len(row))
                rows.append(element("mr", *[group("e", cell) for cell in row]))
            if len(widths) != 1 or not rows or 0 in widths:
                raise EquationError("Word export requires a nonempty rectangular matrix.")
            return [element("m", *rows)]
        if tag == "mtd":
            return [item for child in children for item in convert(child, variant)]
        if tag == "mfenced":
            props = element("dPr", element("begChr", val=node.get("open", "(")),
                            element("endChr", val=node.get("close", ")")),
                            element("sepChr", val=node.get("separators", ",")))
            return [element("d", props, *[group("e", child) for child in children])]
        raise EquationError(f"Unsupported Word equation structure: {tag}")

    result = element("oMath", *convert(root))
    if not result.xpath(".//m:t", namespaces={"m": OMML_NS}):
        raise EquationError("Word conversion produced an empty equation.")
    return result
