from pathlib import Path

import numpy as np
import pymupdf
import pytest

from polytypst.compiler.diagram_cache import CACHE_DIR, with_cached_diagrams
from polytypst.compiler.typst_math import compile_typst, typst_command

pytestmark = pytest.mark.skipif(typst_command() is None, reason="needs typst to render diagrams")

PREAMBLE = (
    '#import "@preview/fletcher:0.5.8" as fletcher\n#set text(font: "STIX Two Text", size: 10pt)\n'
    '#show math.equation: set text(font: "STIX Two Math")\n'
)
NUMBERED = (
    '#set math.equation(numbering: "(1)")\n'
    "#show math.equation.where(block: true): it => if it.numbering == none { it } else { grid(columns: (1fr, auto), "
    "align: (center + horizon, right + horizon), it.body, [(1)]) }\n"
)
SNIPPET = """#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $( caron(M)^Delta )^m$),
  fletcher.node((1, 0), $( op("Hom")_A ( M \\, N ) )^Delta$),
  fletcher.node((0, 1), $cal(H) italic("om")_(cal(O)_(frak(X))) ( M^Delta \\, cal(O)_(frak(X))^m )$),
  fletcher.node((1, 1), $cal(H) italic("om")_(cal(O)_(frak(X))) ( M^Delta \\, N^Delta )$),
  fletcher.edge((0, 0), (1, 0), "->", $tilde$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->"),
)
"""
BODY = 'Before.\n\n$ #(include "figures/fig_001_001.typ") $\n\nAfter.\n'


def _book(tmp_path: Path) -> Path:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "fig_001_001.typ").write_text(SNIPPET, encoding="utf-8")
    return tmp_path


def _ink(out_dir: Path, name: str, source: str) -> np.ndarray:
    typ = out_dir / f"{name}.typ"
    typ.write_text(source, encoding="utf-8")
    compile_typst(typ, out_dir / f"{name}.pdf")
    pix = pymupdf.open(out_dir / f"{name}.pdf")[0].get_pixmap(dpi=144, colorspace="gray")
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width) < 128


@pytest.mark.parametrize("rules", ["", NUMBERED], ids=["display", "numbered"])
def test_cached_diagram_prints_like_its_include(tmp_path: Path, rules: str) -> None:
    out = _book(tmp_path)
    preamble = PREAMBLE + rules
    page = "#set page(width: 400pt, height: 240pt, margin: 30pt)\n"
    included = _ink(out, "included", preamble + page + BODY)
    cached = _ink(out, "cached", preamble + page + with_cached_diagrams(BODY, preamble, out))
    assert included.sum() > 0
    assert (included != cached).sum() <= 0.005 * included.sum()


def test_a_second_build_reuses_the_render_and_an_edit_renders_again(tmp_path: Path) -> None:
    out = _book(tmp_path)
    first = with_cached_diagrams(BODY, PREAMBLE, out)
    renders = sorted((out / CACHE_DIR).glob("*.pdf"))
    stamps = [p.stat().st_mtime_ns for p in renders]
    assert len(renders) == 1
    assert with_cached_diagrams(BODY, PREAMBLE, out) == first
    assert [p.stat().st_mtime_ns for p in renders] == stamps
    snippet = out / "figures" / "fig_001_001.typ"
    snippet.write_text(snippet.read_text(encoding="utf-8").replace("2.6em", "4em"), encoding="utf-8")
    assert with_cached_diagrams(BODY, PREAMBLE, out) != first
    assert len(list((out / CACHE_DIR).glob("*.pdf"))) == 2


def test_typst_without_diagrams_is_left_as_it_is(tmp_path: Path) -> None:
    text = "Plain $x^2$ text.\n"
    assert with_cached_diagrams(text, PREAMBLE, tmp_path) == text
    assert not (tmp_path / CACHE_DIR).exists()
