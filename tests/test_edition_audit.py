from dataclasses import replace
from pathlib import Path

import pymupdf
import pytest

from polytypst.books import book_by_key
from polytypst.compiler.monograph import MonographSpec
from polytypst.compiler.source_numbers import TYPST
from polytypst.edition import Book, Edition
from polytypst.edition_audit import EditionNotBuilt, audit_edition, rises

LINE = "Each full line of this body text holds exactly seventy-seven characters too."
ALGEBRA3_SPEC = replace(book_by_key("algebra3").spec, cross_references=False)


def write_pages(path: Path, pages: int, lines: list[str], pitch: float = 15, size: float = 12) -> None:
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page(width=612, height=792)
        for i, line in enumerate(lines):
            _ = page.insert_text((72, 120 + pitch * i), line, fontsize=size)
    doc.save(path)


def book(tmp_path: Path, spec: MonographSpec | None = None, formats: frozenset[str] = frozenset()) -> Book:
    edition = Edition(tmp_path / "x.pdf", lambda source, formats, footnotes: None, spec=spec, formats=formats)
    return Book(spec or MonographSpec(domain="math", slug="x", title="X", author="A"), tmp_path, {"monograph": edition})


def test_hits_carry_their_rule_stage_and_place(tmp_path: Path) -> None:
    write_pages(tmp_path / "x.pdf", 6, [LINE, "Roy,~1952 wrote here"])
    audit = audit_edition(book(tmp_path), "monograph")

    tildes = audit.hits["NO_LITERAL_TILDE"]
    assert audit.counts["NO_LITERAL_TILDE"] == len(tildes) == 6
    assert {hit.stage for hit in tildes} == {"pdf-text"}
    assert tildes[0].line.startswith(f"{tmp_path / 'x.pdf'} page 1: ")


def test_source_stage_counts_literal_numbers_without_a_pdf(tmp_path: Path) -> None:
    text = TYPST.chapter_start + "#strong[定理 7] 设 $P$ 是域.\n"
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "x.typ").write_text(text, encoding="utf-8")
    audit = audit_edition(book(tmp_path, ALGEBRA3_SPEC), "monograph", stages=frozenset({"source"}))

    assert audit.counts == {"TYPST_LITERAL_ITEM_HEAD": 1}
    [hit] = audit.hits["TYPST_LITERAL_ITEM_HEAD"]
    line = 1 + text.splitlines().index("#strong[定理 7] 设 $P$ 是域.")
    assert hit.stage == "source" and hit.where == f"{tmp_path / 'build' / 'x.typ'}:{line}"
    assert audit.type_profile is None


def test_a_declared_format_without_output_is_not_built(tmp_path: Path) -> None:
    write_pages(tmp_path / "x.pdf", 6, [LINE])
    with pytest.raises(EditionNotBuilt) as error:
        audit_edition(book(tmp_path, formats=frozenset({"pdf", "epub", "tex"})), "monograph")
    assert error.value.formats == ["epub", "tex"]


@pytest.mark.slow
def test_type_profile_measures_full_body_lines(tmp_path: Path) -> None:
    write_pages(tmp_path / "x.pdf", 8, [LINE] * 12, pitch=15, size=12)
    profile = audit_edition(book(tmp_path), "monograph").type_profile

    assert profile is not None
    assert (profile.script, profile.cpl, profile.pitch) == ("latin", len(LINE), 1.25)
    assert profile.ok


@pytest.mark.slow
def test_type_profile_flags_loose_line_pitch(tmp_path: Path) -> None:
    write_pages(tmp_path / "x.pdf", 8, [LINE] * 12, pitch=24, size=12)
    profile = audit_edition(book(tmp_path), "monograph").type_profile

    assert profile is not None and profile.pitch == 2.0 and not profile.ok


def test_rises_names_each_rule_above_and_below_its_record() -> None:
    rose, fell = rises({"A": 2, "B": 0, "C": 1}, {"A": 1, "B": 3, "C": 1})
    assert rose == ["A 2 > 1"]
    assert fell == ["B 0 < 3"]
