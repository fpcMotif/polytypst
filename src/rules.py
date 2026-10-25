"""Every rule a book is checked against, read from the code that applies it.

- pdf-text, pdf-layout, pdf-structure: the checker's rules on a rebuilt PDF, by tier.
- source: the literal-number counts on the Typst and LaTeX beside a PDF.
- parity: the reasons a page fails scan parity, named after the tolerance each one tests.
- ocr: the anomalies the transcript verifier prints.

`polytypst audit` fails when a pdf or source count rises above quality/baseline.json.
`polytypst parity` fails on any parity reason. The ocr anomalies only print.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

SRC = Path(__file__).resolve().parent
TIERS = {"TEXT_TIER": "pdf-text", "LAYOUT_TIER": "pdf-layout", "STRUCTURE_TIER": "pdf-structure"}


@dataclass(frozen=True)
class Rule:
    stage: str
    name: str
    severity: str
    enforced: str
    path: str
    line: int


def _tree(path: str) -> ast.Module:
    return ast.parse((SRC / path).read_text(encoding="utf-8"))


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)


def _strings(node: ast.AST) -> list[ast.Constant]:
    return [n for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def checker_rules() -> list[Rule]:
    tree = _tree("checker.py")
    wiring = next(n for n in ast.walk(_function(tree, "_checks")) if isinstance(n, ast.Dict))
    tiers = {}
    for key, checks in zip(wiring.keys, wiring.values):
        for check in checks.elts:
            tiers[check.attr] = TIERS[key.id]
    out = {}
    for method, stage in tiers.items():
        for call in ast.walk(_function(tree, method)):
            if isinstance(call, ast.Call) and getattr(call.func, "attr", "") == "_issue":
                severity, rule = [a for a in call.args if isinstance(a, ast.Constant)][:2]
                out.setdefault(rule.value, Rule(stage, rule.value, severity.value, "audit", "src/checker.py", rule.lineno))
    return list(out.values())


def literal_rules() -> list[Rule]:
    counts = _function(_tree("literal_numbers.py"), "literal_numbering_counts")
    names = {}
    for node in ast.walk(counts):
        if isinstance(node, ast.Subscript) and getattr(node.value, "id", "") == "counts":
            for s in _strings(node.slice):
                names.setdefault(s.value, s.lineno)
    return [
        Rule("source", f"{prefix}_{name}", "count", "build,audit", "src/literal_numbers.py", line)
        for prefix in ("TYPST", "LATEX")
        for name, line in names.items()
    ]


def _appends(node: ast.AST, target: str) -> list[ast.Call]:
    return [
        n for n in ast.walk(node)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "append" and getattr(n.func.value, "id", "") == target
    ]


def parity_rules() -> list[Rule]:
    out = []
    for test in ast.walk(_function(_tree("parity/report.py"), "verdict")):
        if not isinstance(test, ast.If):
            continue
        (append,) = _appends(test, "reasons")
        attrs = [
            n.attr for part in (test.test, append) for n in ast.walk(part)
            if isinstance(n, ast.Attribute) and getattr(n.value, "id", "") == "tol"
        ]
        out.append(Rule("parity", f"PARITY_{attrs[0].upper()}", "fail", "parity", "src/parity/report.py", append.lineno))
    return sorted(out, key=lambda r: r.line)


def ocr_rules() -> list[Rule]:
    out = []
    for append in _appends(_tree("ocr/verifier.py"), "anomalies"):
        words = re.findall(r"[A-Za-z]+", _strings(append)[0].value)[:3]
        out.append(Rule("ocr", "OCR_" + "_".join(words).upper(), "advice", "no", "src/ocr/verifier.py", append.lineno))
    return sorted(out, key=lambda r: r.line)


def transcript_rules() -> list[Rule]:
    (name,) = [s for s in _strings(_tree("figure_leaks.py")) if s.value == "FIGURE_TEXT_LEAK"]
    return [Rule("transcript", str(name.value), "count", "audit", "src/figure_leaks.py", name.lineno)]


def all_rules() -> list[Rule]:
    return checker_rules() + literal_rules() + transcript_rules() + parity_rules() + ocr_rules()
