from pathlib import Path

import pymupdf

from polytypst.checker import _NAME_HYPHEN_RE
from polytypst.compiler.monograph import TYPST_UNBROKEN_NAMES, compile_typst

PROSE = "The effect was noted by Uzawa and later by Brecher and Diaz-Alejandro in a paper on tariffs. 是被和Diaz-Alejandro指出. " * 3


def line_ends(tmp_path: Path, rules: str) -> list[str]:
    pages = "\n".join(
        f'#page(width: {w}mm, height: auto, margin: 4mm)[#set par(justify: true)\n#set text(lang: "en", hyphenate: true)\n{PROSE}]'
        for w in range(40, 90, 2)
    )
    typ = tmp_path / "a.typ"
    typ.write_text(f"{rules}\n{pages}\n", encoding="utf-8")
    pdf = tmp_path / "a.pdf"
    compile_typst(typ, pdf)
    return [line.rstrip() for page in pymupdf.open(pdf) for line in page.get_text().splitlines()]


def test_hyphenated_names_never_break_at_a_line_end(tmp_path: Path) -> None:
    assert any(_NAME_HYPHEN_RE.search(line) for line in line_ends(tmp_path, ""))
    assert not [line for line in line_ends(tmp_path, TYPST_UNBROKEN_NAMES) if _NAME_HYPHEN_RE.search(line)]
