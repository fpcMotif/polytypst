"""Nicolas Bourbaki: Commutative Algebra Chapters 1-7 (Springer-Verlag, 1989)."""

import re
from dataclasses import replace
from pathlib import Path

from .linebreaks import last_line_fills, scan_line_breaks
from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"FLAT MODULES|LOCALIZATION|GRADUATIONS|FILTRATIONS|TOPOLOGIES|"
    r"ASSOCIATED PRIME IDEALS|PRIMARY DECOMPOSITION|INTEGERS|VALUATIONS|DIVISORS|"
    r"HISTORICAL NOTE|COMMUTATIVE ALGEBRA|TO THE READER|CONTENTS|INDEX"
)

BOURBAKI_OCR_PROMPT = (
    "Transcribe this page from Nicolas Bourbaki's Commutative Algebra into high-fidelity TeX-compatible Markdown.\n"
    "Rules:\n"
    "1. Format all mathematical expressions in exact LaTeX syntax: inline $...$ and display $$...$$.\n"
    "2. For 1D exact sequences and tensor products, transcribe in clean LaTeX (e.g. 0 \\to A \\xrightarrow{f} B \\to C \\to 0, E \\otimes_A N).\n"
    "3. Format chapter and section headings with Markdown (#, ##, ###).\n"
    "4. Bold structural environments: **Definition 1.**, **Proposition 2.**, **Theorem 1.**, **Lemma 3.**, **Corollary 4.**, and italicize *Proof.*\n"
    "5. Label display equations with exact numbering if present (e.g. $$ ... $$ (1)).\n"
    "6. When a 2D commutative diagram appears, if it has vertical and horizontal arrows, preserve all node labels and horizontal sequences faithfully.\n"
    "7. Preserve all body text, notes, and remarks without omitting content."
)

CHAPTERS = [
    ChapterSpec(0, "Introduction", 30, 30),
    ChapterSpec(1, "Flat Modules", 31, 80, label="Chapter I"),
    ChapterSpec(2, "Localization", 81, 184, label="Chapter II"),
    ChapterSpec(3, "Graduations, Filtrations and Topologies", 185, 290, label="Chapter III"),
    ChapterSpec(4, "Associated Prime Ideals and Primary Decomposition", 291, 332, label="Chapter IV"),
    ChapterSpec(5, "Integers", 333, 404, label="Chapter V"),
    ChapterSpec(6, "Valuations", 405, 504, label="Chapter VI"),
    ChapterSpec(7, "Divisors", 505, 608, label="Chapter VII"),
    ChapterSpec(8, "Historical Note (Chapters I to VII)", 609, 636),
    ChapterSpec(9, "Index of Notation and Terminology", 637, 660),
]

SECTION_TITLES: dict[int, tuple[str, ...]] = {
    1: (
        "Diagrams and exact sequences",
        "Flat modules",
        "Faithfully flat modules",
        "Flat modules and \"Tor\" functors",
    ),
    2: (
        "Prime ideals",
        "Rings and modules of fractions",
        "Local rings. Passage from the local to the global",
        "Spectra of rings and supports of modules",
        "Finitely generated projective modules. Invertible fractional ideals",
    ),
    3: (
        "Finitely generated graded algebras",
        "General results on filtered rings and modules",
        "m-adic topologies on Noetherian rings",
        "Lifting in complete rings",
        "Flatness properties of filtered modules",
    ),
    4: (
        "Prime ideals associated with a module",
        "Primary decomposition",
        "Primary decomposition in graded modules",
    ),
    5: (
        "Notion of an integral element",
        "The lift of prime ideals",
        "Finitely generated algebras over a field",
    ),
    6: (
        "Valuation rings",
        "Places",
        "Valuations",
        "The height of a valuation",
        "The topology defined by a valuation",
        "Absolute values",
        "Approximation theorem",
        "Extensions of a valuation to an algebraic extension",
        "Application: locally compact fields",
        "Extensions of a valuation to a transcendental extension",
    ),
    7: (
        "Krull domains",
        "Dedekind domains",
        "Factorial domains",
        "Modules over integrally closed Noetherian domains",
    ),
}

NUMBERED_HEADING_RE = re.compile(
    r"^(?:#+\s*)?(?:§\s*)?(?P<number>\d{1,2})\.\s+(?P<title>[^$]{3,}?)\s*(?P<note>\(\*\))?$"
)
CAPS_TITLE_RE = re.compile(r"^(?=[^a-z]*[A-Z]{3})[^a-z]+$")
UNNUMBERED_CAPS_HEADING_RE = re.compile(r"^#+\s*[^a-z0-9]{4,}$")


def _title_key(title: str) -> str:
    return re.sub(r"[^a-z]", "", title.lower())


def bourbaki_heading(line: str, chapter: int) -> str | None:
    """Map OCR headings to § (level 2) and no. (level 3), dropping stray running heads."""
    if re.match(r"^#+\s*EXERCISES\s*$", line):
        return "## Exercises"
    m = NUMBERED_HEADING_RE.match(line)
    if m is None:
        return "" if UNNUMBERED_CAPS_HEADING_RE.match(line) else None
    number, ocr_title = m.group("number"), m.group("title").strip()
    note = f" {m.group('note')}" if m.group("note") else ""
    sections = SECTION_TITLES.get(chapter, ())
    index = int(number) - 1
    if 0 <= index < len(sections):
        known, seen = _title_key(sections[index]), _title_key(ocr_title)
        if seen.removeprefix("the") == known.removeprefix("the") and line.startswith("#"):
            return f"## § {number}. {sections[index]}{note}"
    if not CAPS_TITLE_RE.match(ocr_title):
        return None
    return f"### {number}. {ocr_title[0]}{ocr_title[1:].lower()}{note}"


BOURBAKI_SPEC = MonographSpec(
    slug="bourbaki_commutative_algebra",
    title="Commutative Algebra (Chapters 1–7)",
    author="Nicolas Bourbaki",
    publisher="Springer-Verlag",
    series="Elements of Mathematics",
    year=1989,
    publisher_key="springer",
    lang="en",
    domain="math",
    pdf_page_count=660,
    pdf_name_markers=("bourbaki", "commutative algebra"),
    source_pdf="Elements of Mathematics Commutative Algebra Chapters 1-7 (Nicolas Bourbaki) .pdf",
    preface_page=11,
    ocr_prompt=BOURBAKI_OCR_PROMPT,
    chapters=CHAPTERS,
    heading_hook=bourbaki_heading,
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Diagram\s*(?P<chapter>\d+)[\.\-](?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*(?P<tail>.*)$",
        caption_ignore_case=True,
        caption_format="Diagram {chapter}.{number}",
    ),
    header_zone_lines=2,
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    drop_line_regexes=(
        r"^Springer-Verlag.*$",
        r"^Elements of Mathematics.*$",
        r"^\d+\s+[A-Z\s\$\-\.\,]+$",
        r"^[A-Z\s\$\-\.\,]+\s+\d+$",
    ),
    pre_math_rewrites=(
        (r"plus\.circle", r"\\u{2295}"),
    ),
)

VINTAGE_PREAMBLE = (Path(__file__).parent / "vintage_preamble.typ").read_text(encoding="utf-8")

BOURBAKI_1970_SPEC = replace(
    BOURBAKI_SPEC,
    slug="bourbaki_1970_vintage",
    publisher_key="bourbaki_1970",
    lang="en_baskerville",
    chapter_heading="{title}",
    typst_preamble=VINTAGE_PREAMBLE,
    paginate_like_source=True,
    source_line_breaks=scan_line_breaks,
    justify_page_end=last_line_fills,
)
