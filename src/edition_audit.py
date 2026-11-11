"""Audit one edition of a book: every rule's hits, the type profile of its body text, and how its counts moved.

`polytypst audit`, `polytypst build`, `page-check gate`, `scripts/math_books.py` and `scripts/one_book.py`
all audit an edition through `audit_edition`. Only the callers compare and print.
"""

import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path

from .checker import (
    LAYOUT_TIER,
    STRUCTURE_TIER,
    TEXT_TIER,
    AuditSpec,
    DocumentQualityChecker,
)
from .compiler.math_arrays import array_misuses
from .compiler.monograph import build_source
from .edition import Book, Edition
from .figure_leaks import FIGURE_TEXT_LEAK, figure_text_leaks
from .literal_numbers import edition_literal_hits
from .ocr.scan import SourceScanError
from .parity import FACSIMILE
from .parity.source import source_pdf
from .parity.visual import LAYOUT_LIMIT, layout_check

BASELINE = Path(__file__).resolve().parent.parent / "quality" / "baseline.json"
DOCUMENT_FORMATS = {"pdf": "", "epub": "EPUB_"}
TIER_STAGES = {TEXT_TIER: "pdf-text", LAYOUT_TIER: "pdf-layout", STRUCTURE_TIER: "pdf-structure"}
STAGES = frozenset({*TIER_STAGES.values(), "source", "transcript", "facsimile"})
FACSIMILE_LAYOUT = "facsimile_layout"
LAYOUT_SAMPLE_EVERY = 10
TYPE_TARGETS = {"latin": ((45, 80), (1.15, 1.5)), "cjk": ((50, 90), (1.4, 1.8))}


@dataclass(frozen=True)
class Hit:
    """One place a rule found: its stage (as `polytypst rules` prints it), where it is, and the text there."""

    stage: str
    where: str
    text: str

    @property
    def line(self) -> str:
        return f"{self.where}: {self.text}"


@dataclass(frozen=True)
class TypeProfile:
    """The body text's script, median characters per full line, and median line pitch over the body size."""

    script: str
    cpl: int
    pitch: float

    @property
    def ok(self) -> bool:
        (cpl_lo, cpl_hi), (pitch_lo, pitch_hi) = TYPE_TARGETS[self.script]
        return cpl_lo <= self.cpl <= cpl_hi and pitch_lo <= self.pitch <= pitch_hi


@dataclass(frozen=True)
class EditionAudit:
    """Every audited rule of one edition with its hits. A rule may hold no hits; it still counts as 0."""

    hits: dict[str, list[Hit]] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)
    type_profile: TypeProfile | None = None

    @property
    def counts(self) -> Counter[str]:
        return Counter({rule: len(hits) for rule, hits in self.hits.items()})

    def stage(self, stage: str) -> dict[str, list[Hit]]:
        return {rule: hits for rule, hits in self.hits.items() if any(h.stage == stage for h in hits)}


class EditionNotBuilt(Exception):
    """The edition declares formats that have no output beside its rebuilt PDF."""

    def __init__(self, edition: Edition, formats: list[str]) -> None:
        self.formats = formats
        super().__init__(f"{edition.rebuilt} has no {', '.join(formats)} output")


def output_path(edition: Edition, fmt: str) -> Path:
    """The file an edition writes for `fmt`: its rebuilt PDF or EPUB, or the source in `build/` named like it."""
    return edition.rebuilt.with_suffix(f".{fmt}") if fmt in ("pdf", "epub") else edition.source(fmt)


def audit_edition(book: Book, name: str, stages: frozenset[str] = STAGES) -> EditionAudit:
    """Run the rules of `stages` on edition `name` of `book`.

    The pdf stages read every declared document format and raise `EditionNotBuilt` when a declared
    format has no output. `source` reads only the generated Typst and LaTeX, so a build can call it
    without a PDF. A rule that cannot run, such as facsimile layout without its scan, lands in `skipped`.
    """
    edition = book.editions[name]
    hits: dict[str, list[Hit]] = {}
    skipped: dict[str, str] = {}
    profile = None
    tiers = frozenset(tier for tier, stage in TIER_STAGES.items() if stage in stages)
    if tiers:
        if missing := [f for f in sorted(edition.formats | {"pdf"}) if not output_path(edition, f).exists()]:
            raise EditionNotBuilt(edition, missing)
        spec = AuditSpec.from_monograph(edition.spec) if edition.spec else AuditSpec()
        spec = replace(spec, scan_line_breaks=edition.scan_line_breaks)
        for fmt in sorted(f for f in edition.formats | {"pdf"} if f in DOCUMENT_FORMATS):
            path = output_path(edition, fmt)
            checker = DocumentQualityChecker(path, spec)
            for issue in checker.run_all_checks(tiers).issues:
                hit = Hit(TIER_STAGES[issue.tier], f"{path} page {issue.page_num}", f"{issue.message} {issue.context_snippet}".rstrip())
                hits.setdefault(f"{DOCUMENT_FORMATS[fmt]}{issue.rule_name}", []).append(hit)
            if fmt == "pdf" and (measured := checker.type_profile()):
                profile = TypeProfile(*measured)
    if edition.spec and "source" in stages:
        for rule, found in edition_literal_hits(edition.rebuilt, edition.spec).items():
            hits.setdefault(rule, []).extend(Hit("source", f"{path}:{hit.line}", hit.text) for path, hit in found)
    if edition.spec and "source" in stages and (md := build_source(edition.rebuilt, "md")).exists():
        for misuse in array_misuses(md.read_text(encoding="utf-8")):
            hits.setdefault(misuse.rule, []).append(Hit("source", f"{md}:{misuse.line}", misuse.text))
    if edition.spec and "transcript" in stages and (leaks := figure_text_leaks(book)):
        hits[FIGURE_TEXT_LEAK] = [
            Hit("transcript", f"scan page {page} figure {figure}", text) for page, figure, _, _, text in leaks
        ]
    if "facsimile" in stages and edition.parity is not None and edition.parity.tolerance is FACSIMILE:
        try:
            source = source_pdf(book.spec, None)
        except SourceScanError as error:
            skipped[FACSIMILE_LAYOUT] = str(error)
        else:
            page_map = edition.parity.page_map()
            sample = {p: v for p, v in page_map.items() if p % LAYOUT_SAMPLE_EVERY == 0}
            hits[FACSIMILE_LAYOUT] = [
                Hit("facsimile", f"scan page {page}", f"layout share {share:.2f} > {LAYOUT_LIMIT}")
                for page, share in layout_check(source, edition.rebuilt, sample).items()
                if share > LAYOUT_LIMIT
            ]
    return EditionAudit(hits, skipped, profile)


def rises(counts: Mapping[str, int], recorded: Mapping[str, int]) -> tuple[list[str], list[str]]:
    """The rules whose count rose above the record, and the recorded rules whose count fell, as `RULE n > m` and `RULE n < m`."""
    rose = [f"{rule} {n} > {recorded.get(rule, 0)}" for rule, n in sorted(counts.items()) if n > recorded.get(rule, 0)]
    fell = [f"{rule} {counts.get(rule, 0)} < {n}" for rule, n in sorted(recorded.items()) if counts.get(rule, 0) < n]
    return rose, fell


def read_baseline(path: Path = BASELINE) -> dict[str, dict[str, dict[str, int]]]:
    """The recorded rule counts per book key and edition name; empty when the file does not exist."""
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
