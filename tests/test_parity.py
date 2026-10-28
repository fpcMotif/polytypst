import json
from pathlib import Path

import numpy as np
import pymupdf
import pytest

from polytypst.compiler.typst_math import typst_command
from polytypst.parity import (
    FACSIMILE,
    SOURCE_PAGINATED,
    PageParity,
    compare,
    verdict,
    write_report,
)
from polytypst.parity.compare import right_overflow_lines
from polytypst.parity.diagrams import DiagramText, find_diagram

W, H = 388.0, 609.0
FONT, SIZE, LEAD = "tiro", 10.0, 14.0
ABOVE = [
    "Let A be a commutative ring and M an A-module of finite type.",
    "The canonical homomorphism of M into its bidual is injective",
    "whenever M is projective, and bijective when M is projective",
    "and finitely generated over the ring A considered above here.",
    "Consider now the exact sequence formed by the modules below,",
    "whose rows are exact and whose squares are all commutative.",
]
BELOW = [
    "Then the homomorphism deduced from the diagram is an isomorphism",
    "and the sequence obtained by tensoring with N remains exact.",
    "This proves the proposition for every flat module over the ring.",
]
DIAGRAM = (164.0, 205.0, 224.0, 235.0)


def write_page(path: Path, dx: float = 0.0, dy: float = 0.0, word_shift: dict[str, float] | None = None, rect_dx: float | None = None) -> None:
    """One page of text set word by word, so a single word can be moved; optionally a diagram rectangle."""
    doc = pymupdf.open()
    page = doc.new_page(width=W, height=H)
    space = pymupdf.get_text_length(" ", fontname=FONT, fontsize=SIZE)
    baselines = [100.0 + LEAD * i for i in range(len(ABOVE))] + [255.0 + LEAD * i for i in range(len(BELOW))]
    for text, base in zip(ABOVE + BELOW, baselines):
        x = 40.0
        for word in text.split():
            shift = (word_shift or {}).get(word, 0.0)
            page.insert_text((x + dx + shift, base + dy), word, fontname=FONT, fontsize=SIZE)
            x += pymupdf.get_text_length(word, fontname=FONT, fontsize=SIZE) + space
    if rect_dx is not None:
        l, t, r, b = DIAGRAM
        page.draw_rect(pymupdf.Rect(l + rect_dx, t, r + rect_dx, b), color=(0, 0, 0), width=1.0)
    doc.save(path)


def write_ocr(source: Path, cache: Path) -> None:
    """The Vision OCR cache the source page would get: one box per text line, page fractions from the bottom left."""
    cache.mkdir(parents=True, exist_ok=True)
    page = pymupdf.open(source)[0]
    lines: dict[float, list[tuple[float, float, float, float, str]]] = {}
    for x0, y0, x1, y1, word, *_ in page.get_text("words"):
        lines.setdefault(round(y1), []).append((x0, y0, x1, y1, word))
    out = []
    for words in lines.values():
        words.sort()
        x0, y0 = min(w[0] for w in words), min(w[1] for w in words)
        x1, y1 = max(w[2] for w in words), max(w[3] for w in words)
        out.append({"text": " ".join(w[4] for w in words), "x": x0 / W, "y": (H - y1) / H, "w": (x1 - x0) / W, "h": (y1 - y0) / H})
    (cache / "p001.json").write_text(json.dumps(out), encoding="utf-8")
    (cache / "pages.json").write_text(json.dumps({"1": [W, H]}), encoding="utf-8")


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "source.pdf"
    write_page(path)
    write_ocr(path, tmp_path / "ocr")
    return path


def run(source: Path, rebuilt: Path, diagrams: Path | None = None) -> PageParity:
    text = DiagramText(font="Libertinus Serif", size=10.0, weight=400) if diagrams else None
    return compare(source, rebuilt, {1: [1]}, ocr=source.parent / "ocr", diagrams=diagrams, diagram_text=text, work=source.parent / "work")[0]


def test_an_identical_page_matches_every_word_in_place_and_passes(source: Path, tmp_path: Path) -> None:
    rebuilt = tmp_path / "rebuilt.pdf"
    write_page(rebuilt)
    page = run(source, rebuilt)
    assert len(page.words) == page.words_source == sum(len(t.split()) for t in ABOVE + BELOW)
    assert abs(page.page_dx) <= 0.25 and abs(page.page_dy) <= 0.25
    assert verdict(page, FACSIMILE) == []


def test_a_shifted_page_reports_the_shift_in_absolute_points(source: Path, tmp_path: Path) -> None:
    rebuilt = tmp_path / "rebuilt.pdf"
    write_page(rebuilt, dx=2.5, dy=1.0)
    page = run(source, rebuilt)
    assert page.page_dx == pytest.approx(2.5, abs=0.25)
    assert page.page_dy == pytest.approx(1.0, abs=0.25)
    assert any(r.startswith("page offset") for r in verdict(page, FACSIMILE))


def test_one_moved_word_is_reported_and_fails_the_facsimile_tolerance(source: Path, tmp_path: Path) -> None:
    rebuilt = tmp_path / "rebuilt.pdf"
    write_page(rebuilt, word_shift={"injective": 2.0})
    page = run(source, rebuilt)
    moved = [w for w in page.words if w.text == "injective"]
    assert len(moved) == 1 and moved[0].dx_left == pytest.approx(2.0, abs=0.25)
    others = [w for w in page.words if w.text != "injective"]
    assert max(abs(w.dx_left) for w in others) <= 0.25
    assert "1 words off by more than 0.5pt" in verdict(page, FACSIMILE)


def test_a_word_past_the_scan_text_edge_counts_as_one_overflowing_line(source: Path, tmp_path: Path) -> None:
    rebuilt = tmp_path / "rebuilt.pdf"
    write_page(rebuilt, word_shift={"injective": 60.0})
    page = run(source, rebuilt)
    assert page.right_overflow_lines == 1
    assert "1 lines cross the scan's right text edge" in verdict(page, FACSIMILE)
    assert verdict(page, SOURCE_PAGINATED)[-1] == "1 lines cross the scan's right text edge"


def test_a_whole_page_shifted_right_is_a_page_offset_not_an_overflow(source: Path, tmp_path: Path) -> None:
    rebuilt = tmp_path / "rebuilt.pdf"
    write_page(rebuilt, dx=6.0)
    page = run(source, rebuilt)
    assert page.right_overflow_lines == 0
    assert any(r.startswith("page offset") for r in verdict(page, FACSIMILE))


def test_overflow_counts_rebuilt_ink_by_the_same_column_rule_as_the_scan_edge() -> None:
    scan = np.zeros((200, 300), bool)
    scan[20:180, 10:200] = True
    speck, stroke = np.zeros_like(scan), np.zeros_like(scan)
    speck[50, 230] = True
    stroke[100:106, 230] = True
    assert right_overflow_lines(scan, speck) == 0
    assert right_overflow_lines(scan, stroke) == 1


@pytest.mark.skipif(typst_command() is None, reason="needs typst to render the diagram snippet")
def test_a_diagram_moved_sideways_reports_its_offset_and_scale(source: Path, tmp_path: Path) -> None:
    write_page(source, rect_dx=0.0)
    snippets = tmp_path / "diagrams"
    snippets.mkdir()
    l, t, r, b = DIAGRAM
    (snippets / "fig_001_001.typ").write_text(f"#rect(width: {r - l}pt, height: {b - t}pt, stroke: 1pt + black)\n", encoding="utf-8")
    rebuilt = tmp_path / "rebuilt.pdf"
    write_page(rebuilt, rect_dx=3.0)
    page = run(source, rebuilt, diagrams=snippets)
    (d,) = page.diagrams
    assert d.dx == pytest.approx(3.0, abs=0.25)
    assert d.dy == pytest.approx(0.0, abs=0.25)
    assert d.sx == pytest.approx(1.0, abs=0.01) and d.sy == pytest.approx(1.0, abs=0.01)
    assert any(r.startswith("diagram fig_001_001") for r in verdict(page, FACSIMILE))


def test_find_diagram_returns_the_page_position_of_a_diagram_set_in_an_indented_block() -> None:
    rng = np.random.default_rng(7)
    tmpl = np.zeros((120, 300), bool)
    for _ in range(12):
        y, x = rng.integers(0, 117), rng.integers(0, 240)
        tmpl[y : y + 3, x : x + 60] = True
        tmpl[rng.integers(0, 60) : rng.integers(60, 120), x : x + 3] = True
    page = np.zeros((1300, 900), bool)
    for y in [*range(40, 600, 30), *range(780, 1260, 30)]:
        page[y : y + 12, 50:850] = rng.random((12, 800)) < 0.3
    page[640:760, 300:600] = tmpl
    assert find_diagram(page, tmpl)[:4] == (640, 300, 120, 300)


def test_a_source_paginated_page_that_overflows_or_loses_a_line_fails() -> None:
    page = PageParity(Path("s.pdf"), Path("r.pdf"), 40, (52, 53), 0.0, 0.0, 0.9, 38, 37, 0)
    assert verdict(page, SOURCE_PAGINATED) == ["lines 38 vs 37", "overflows onto 1 more page(s)"]
    assert verdict(page, FACSIMILE) == []


def test_the_report_marks_failing_pages_and_returns_false(source: Path, tmp_path: Path) -> None:
    rebuilt = tmp_path / "rebuilt.pdf"
    write_page(rebuilt, dx=2.5)
    out = tmp_path / "report"
    assert write_report([run(source, rebuilt)], out, FACSIMILE) is False
    assert json.loads((out / "summary.json").read_text())["failed"] == 1
    assert (out / "img" / "p001_overlay.png").exists()
    assert "fail" in (out / "report.csv").read_text()
