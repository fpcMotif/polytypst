import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import cached_property
from pathlib import Path

import pymupdf

from ..books import book_key, books
from ..edition import Book
from ..evidence import strip
from ..figure_leaks import apply_page_fixups
from ..ocr.lines import LineStore
from ..ocr.pages import OcrLine
from ..ocr.transcripts import TranscriptStore
from ..parity.source import source_pdf
from .results import KINDS, Results, Tally

RESULTS = Path("output/page_check")
LEGACY = Path("quality/page_check_legacy.json")
KEPT_CHAR = re.compile(r"[一-鿿A-Za-z0-9.%]")
BAND_PAD = 0.02
STRIP_PAD = 0.008

type Band = tuple[float, float]
type Table = list[list[str]]


def norm(text: str) -> str:
    return "".join(KEPT_CHAR.findall(unicodedata.normalize("NFKC", text)))


def top(line: OcrLine) -> float:
    return 1 - line.y - line.h


def bottom(line: OcrLine) -> float:
    return 1 - line.y


def prose_lines(markdown: str) -> list[tuple[int, str]]:
    """Each transcript line that holds prose, with its line number. Tables, display math and images are left out,
    and inline math is blanked, because the local OCR reads them as noise."""
    kept: list[tuple[int, str]] = []
    in_table = in_math = False
    for n, line in enumerate(markdown.splitlines(), 1):
        stripped = line.strip()
        if "<table" in stripped:
            in_table = True
        if in_table:
            in_table = "</table>" not in stripped
            continue
        if stripped.startswith("$$"):
            in_math = not (stripped.endswith("$$") and len(stripped) > 2) and not in_math
            continue
        if in_math or stripped.startswith(("|", "![")):
            continue
        kept.append((n, re.sub(r"\$[^$]*\$", " ", re.sub(r"<[^>]+>", "", line))))
    return kept


def cell_text(cell: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", re.sub(r"<[^>]+>", "", cell)))


def table_rows(markdown: str) -> list[Table]:
    tables: list[Table] = []
    for html in re.findall(r"<table.*?</table>", markdown, re.DOTALL):
        rows = [
            re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.DOTALL)
            for r in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
        ]
        tables.append([[cell_text(c) for c in r] for r in rows if r])
    block: Table = []
    for line in [*markdown.splitlines(), ""]:
        if line.strip().startswith("|"):
            cells = line.strip().strip("|").split("|")
            if not all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells):
                block.append([cell_text(c) for c in cells])
        elif block:
            tables.append(block)
            block = []
    return tables


def table_diff(transcript: Table, scan: Table) -> list[str]:
    t_cells, s_cells = max(map(len, transcript), default=0), max(map(len, scan), default=0)
    out = [f"shape: transcript {len(transcript)} rows x {t_cells} cells, scan {len(scan)} rows x {s_cells} cells"]
    unpaired = list(range(len(transcript)))
    for s_row in scan:
        label = s_row[0] if s_row else ""
        match = next((i for i in unpaired if transcript[i][:1] == [label]), None)
        if match is None:
            out.append(f"row only in scan: {' | '.join(s_row)}")
            continue
        unpaired.remove(match)
        if diffs := cell_diffs(transcript[match], s_row):
            out.append(f"row {label!r}: " + "; ".join(diffs))
    out += [f"row only in transcript: {' | '.join(transcript[i])}" for i in unpaired]
    return out


def cell_diffs(t_row: list[str], s_row: list[str]) -> list[str]:
    diffs = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, t_row, s_row, autojunk=False).get_opcodes():
        if op == "replace":
            diffs.append(f"col {j1 + 1}: transcript {' | '.join(t_row[i1:i2])!r} scan {' | '.join(s_row[j1:j2])!r}")
        elif op == "insert":
            diffs.append(f"col {j1 + 1}: missing {' | '.join(s_row[j1:j2])!r}")
        elif op == "delete":
            diffs.append(f"col {j1 + 1}: extra {' | '.join(t_row[i1:i2])!r}")
    return diffs


def ranges(pages: list[int]) -> str:
    spans: list[list[int]] = []
    for p in pages:
        if spans and p == spans[-1][1] + 1:
            spans[-1][1] = p
        else:
            spans.append([p, p])
    return ",".join(f"{a}" if a == b else f"{a}-{b}" for a, b in spans)


@dataclass(frozen=True)
class PageCheck:
    key: str
    book: Book
    root: Path = RESULTS
    scan_override: Path | None = None

    @classmethod
    def named(cls, name: str, scan: Path | None = None) -> PageCheck:
        key = book_key(name)
        return cls(key, books()[key], scan_override=scan)

    @cached_property
    def store(self) -> TranscriptStore:
        return TranscriptStore(self.book.transcripts)

    @cached_property
    def lines(self) -> LineStore:
        return LineStore(self.book.ocr)

    @cached_property
    def results(self) -> Results:
        return Results(self.root / self.key)

    @cached_property
    def scan(self) -> Path:
        return self.scan_override or source_pdf(self.book.spec)

    @cached_property
    def scan_doc(self) -> pymupdf.Document:
        return pymupdf.open(self.scan)

    @property
    def title(self) -> str:
        return re.sub(r"^\d+[_ ]", "", self.key)

    def pages(self) -> list[int]:
        return self.store.pages()

    def has(self, page: int) -> bool:
        return self.store.path(page).exists()

    def transcript(self, page: int) -> str:
        return self.store.path(page).read_text(encoding="utf-8")

    def fixups(self, page: int) -> tuple[tuple[str, str], ...]:
        spec = self.book.spec
        return (*spec.transcript_fixups.get(page, ()), *spec.page_fixups.get(page, ()))

    def printed(self, page: int) -> str:
        return apply_page_fixups(self.transcript(page), self.fixups(page))

    def ocr_lines(self, page: int) -> list[OcrLine]:
        return sorted(self.lines.lines(page) or (), key=lambda line: (round(top(line), 2), line.x))

    def band(self, page: int, text: str) -> Band | None:
        key = norm(text)
        return next(((top(line), bottom(line)) for line in self.ocr_lines(page) if key in norm(line.text)), None)

    def suspects(self, page: int) -> list[str]:
        t_chars = [(c, n) for n, line in prose_lines(self.transcript(page)) for c in norm(line)]
        o_chars = [(c, top(line), bottom(line)) for line in self.ocr_lines(page) for c in norm(line.text)]
        if not o_chars:
            return ["no local OCR for this page"]
        t_text, o_text = "".join(c for c, _ in t_chars), "".join(c for c, *_ in o_chars)
        found = []
        for op, i1, i2, j1, j2 in SequenceMatcher(None, t_text, o_text, autojunk=False).get_opcodes():
            if op == "equal":
                continue
            j_near = min(j1, len(o_chars) - 1)
            upper = min((o_chars[j][1] for j in range(j1, j2)), default=o_chars[j_near][1])
            lower = max((o_chars[j][2] for j in range(j1, j2)), default=o_chars[j_near][2])
            line = t_chars[min(i1, len(t_chars) - 1)][1] if t_chars else 0
            band = f"{max(0.0, upper - BAND_PAD):.2f},{min(1.0, lower + BAND_PAD):.2f}"
            found.append(
                f"line {line} band {band} | transcript: {t_text[max(0, i1 - 4):i1]}[{t_text[i1:i2][:40]}]{t_text[i2:i2 + 4]}"
                f" | ocr: [{o_text[j1:j2][:40]}]"
            )
        return found

    def tables(self, page: int) -> list[Table]:
        return table_rows(self.transcript(page))

    def strip(self, page: int, band: Band, dpi: int) -> bytes:
        return strip(self.scan_doc, page, (band[0] - STRIP_PAD, band[1] + STRIP_PAD), dpi)

    def page_png(self, page: int) -> Path:
        return self.results.folder / "png" / f"p{page}.png"

    def receipt(self, page: int) -> str | None:
        """The proof that a check saw page PAGE: a hash of its rendered scan PNG and its transcript. `text` prints it."""
        png = self.page_png(page)
        if not png.is_file():
            return None
        return hashlib.sha256(png.read_bytes() + self.store.path(page).read_bytes()).hexdigest()[:12]

    def legacy_files(self) -> dict[str, str]:
        """Result files checked before receipts existed, by name, with the sha256 they had then."""
        return json.loads(LEGACY.read_text(encoding="utf-8")).get(self.key, {}) if LEGACY.is_file() else {}

    def tally(self) -> Tally:
        t = Tally(set(self.pages()), set(), set(), Counter(), [], set())
        legacy = self.legacy_files()
        for path in self.results.chunk_files():
            trusted = legacy.get(path.name) == hashlib.sha256(path.read_bytes()).hexdigest()
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                try:
                    record = json.loads(line)
                    page, issues = int(record["page"]), record["issues"]
                    kinds = [i["kind"] for i in issues]
                except (ValueError, KeyError, TypeError) as error:
                    t.bad_lines.append(f"{path}:{n}: {error}")
                    continue
                if unknown := [k for k in kinds if k not in KINDS]:
                    t.bad_lines.append(f"{path}:{n}: unknown kind {unknown}")
                if not trusted and (page not in t.pages or not record.get("receipt") or record["receipt"] != self.receipt(page)):
                    t.unproven.add(page)
                    continue
                t.checked.add(page)
                t.kinds.update(kinds)
                if issues:
                    t.issue_pages.add(page)
        return t

    def chunks(self, size: int) -> list[tuple[int, int]]:
        todo = sorted((t := self.tally()).pages - t.checked)
        return [(todo[i], todo[min(i + size, len(todo)) - 1]) for i in range(0, len(todo), size)]


__all__ = ["RESULTS", "PageCheck", "norm", "prose_lines", "ranges", "table_diff"]
