"""`polytypst review` and `polytypst checklist`: measure any output folder against its scan, and track findings.

Review works on a folder with no book key. It maps each scan page to the rebuilt page that holds its
text (the text map), so it needs no page map and works on reflowed editions. It records the measures
of every rebuilt PDF, Typst and LaTeX source, LaTeX log and transcript in `review/measures.json`, and
appends each run to `review/history.jsonl` so the next run prints what changed. `--visual` hands the
text map to optical parity, which draws the red/cyan overlays.
"""

import csv
import hashlib
import json
import re
import statistics
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from pathlib import Path

import pymupdf

from .compiler.source_numbers import LATEX, TYPST
from .literal_numbers import literal_numbering_counts
from .ocr.lines import LineStore, source_ocr_dir

GRAM = 4
CONTENT_BAND = (0.06, 0.9)
HALF = 0.5
OVERFULL_LIMIT_PT = 50.0
SEVERITIES = ("P0", "P1", "P2", "P3")
Measures = dict[str, float]

_CONTENT_CHAR = re.compile(r"[\u4e00-\u9fff0-9A-Za-z]")
_TYPED_NUMBER = r"(?:\d+(?:\.\d+)*\.?|[一二三四五六七八九十]+[、.]|[(（]\d+[)）]|第[一二三四五六七八九十\d]+[章节])\s"
_SOURCE = {
    "typst": {
        "headings": r"(?m)^=+ ",
        "headings_with_typed_numbers": rf"(?m)^=+ {_TYPED_NUMBER}",
        "links": r"(?<![A-Za-z0-9_.])@[A-Za-z][\w-]*|#link\(<",
        "footnotes": r"#footnote\[",
        "chained_footnotes": r"\]#footnote\[",
        "footnotes_in_headings": r"(?m)^=+ [^\n]*#footnote\[",
        "tables": r"#table\(",
    },
    "latex": {
        "headings": r"\\(?:chapter|(?:sub)*section)\*?\{",
        "headings_with_typed_numbers": rf"\\(?:chapter|(?:sub)*section)\*?\{{{_TYPED_NUMBER}",
        "links": r"\\(?:ref|eqref|autoref|cref|hyperlink)\{",
        "footnotes": r"\\footnote\{",
        "chained_footnotes": r"\}\\footnote\{",
        "footnotes_in_headings": r"\\(?:chapter|(?:sub)*section)\{[^\n]*\\footnote",
        "unnumbered_display_math": r"\\\[|\$\$",
        "tables": r"\\begin\{(?:longtable|tabular)\}",
    },
}
_LITERAL_REFS = {
    "literal_figure_refs": r"图\s*\d+\s*[-－—.]\s*\d+",
    "literal_table_refs": r"表\s*\d+\s*[-－—.]\s*\d+",
    "literal_equation_refs": r"[式程]\s*[（(]\s*\d+\s*\.\s*\d+\s*[）)]",
}


@dataclass(frozen=True)
class PageMatch:
    scan_page: int
    rebuilt_page: int | None
    coverage: float


@dataclass(frozen=True)
class Finding:
    """One review finding. Severity: P0 content wrong or lost, P1 visibly broken layout,
    P2 typographic bad practice, P3 nit. Status: open, fixed or wontfix."""

    id: str
    book: str
    severity: str
    format: str
    where: str
    what: str
    evidence: str
    status: str = "open"


def _grams(text: str) -> set[str]:
    s = "".join(_CONTENT_CHAR.findall(text))
    return {s[i : i + GRAM] for i in range(len(s) - GRAM + 1)}


def scan_grams(ocr_dir: Path) -> dict[int, set[str]]:
    """The text 4-grams of each scan page's OCR lines, without the running head and folio bands."""
    store = LineStore(ocr_dir)
    numbers = sorted(int(p.stem[1:]) for p in ocr_dir.glob("p[0-9][0-9][0-9].json"))
    low, high = CONTENT_BAND
    return {
        n: _grams(
            "".join(line.text for line in store.lines(n) or () if low < line.y < high)
        )
        for n in numbers
    }


def text_map(scan: dict[int, set[str]], pdf: Path) -> list[PageMatch]:
    """For each scan page with text: the rebuilt page that holds most of its 4-grams, and the share of
    its 4-grams found anywhere in the rebuilt PDF's text layer (text off the page is not counted)."""
    where: dict[str, set[int]] = {}
    for i, page in enumerate(pymupdf.open(pdf)):
        for g in _grams(page.get_text()):
            where.setdefault(g, set()).add(i + 1)
    out = []
    for number, grams in sorted(scan.items()):
        if not grams:
            continue
        hits = Counter(p for g in grams for p in where.get(g, ()))
        found = sum(1 for g in grams if g in where)
        best = hits.most_common(1)[0][0] if hits else None
        out.append(PageMatch(number, best, round(found / len(grams), 3)))
    return out


def coverage_measures(matches: Sequence[PageMatch]) -> Measures:
    values = [m.coverage for m in matches]
    return {
        "coverage_median": round(statistics.median(values), 3) if values else 0.0,
        "pages_coverage_below_half": sum(v < HALF for v in values),
        "scan_pages_unmapped": sum(m.rebuilt_page is None for m in matches),
    }


def pdf_measures(pdf: Path) -> Measures:
    """Page count, and the pages with text set past the right page edge."""
    flags = pymupdf.TEXTFLAGS_TEXT & ~pymupdf.TEXT_MEDIABOX_CLIP
    doc = pymupdf.open(pdf)
    past = sum(
        any(
            span["bbox"][2] > page.rect.width + 1
            for block in page.get_text("dict", flags=flags)["blocks"]
            for line in block.get("lines", ())
            for span in line["spans"]
            if span["text"].strip()
        )
        for page in doc
    )
    return {"pages": doc.page_count, "pages_text_past_edge": past}


def latex_log_measures(log: str) -> Measures:
    widths = [
        float(w) for w in re.findall(r"(?m)^Overfull \\hbox \(([\d.]+)pt too wide", log)
    ]
    return {
        "overfull_hbox": len(widths),
        "overfull_hbox_over_50pt": sum(w > OVERFULL_LIMIT_PT for w in widths),
        "max_overfull_pt": max(widths, default=0.0),
        "missing_glyphs": len(re.findall(r"Missing character: There is no", log)),
        "undefined_references": len(
            re.findall(r"(?:Reference|Citation) `[^']+' on page \d+ undefined", log)
        ),
        "font_shape_undefined": len(re.findall(r"Font shape `[^']+' undefined", log)),
        "rerun_needed": int("Rerun" in log),
    }


def source_measures(text: str, kind: str, running_heads: Iterable[str]) -> Measures:
    """Literal numbers, links, footnotes and leaked running heads in a Typst (`typst`) or LaTeX (`latex`) source."""
    m: Measures = {
        name: len(re.findall(rx, text))
        for name, rx in (_SOURCE[kind] | _LITERAL_REFS).items()
    }
    m["heading_numbering_rule"] = int(
        "set heading(numbering" in text
        if kind == "typst"
        else not re.search(r"secnumdepth\}\{-", text)
    )
    heads = "|".join(map(re.escape, running_heads))
    body = "\n".join(
        line
        for line in text.splitlines()
        if not re.match(r"^= [^=]|#set document", line)
    )
    m["running_head_leaks"] = (
        len(
            re.findall(
                rf"(?<![\"\w\[])\d{{1,3}} ?(?:{heads})(?![\"\]])|(?:{heads}) ?\d{{1,3}}\s*$",
                body,
                re.MULTILINE,
            )
        )
        if heads
        else 0
    )
    checker = literal_numbering_counts(text, TYPST if kind == "typst" else LATEX)
    return m | {f"checker_{rule}": n for rule, n in checker.items()}


def transcript_measures(text: str) -> Measures:
    sentences = Counter(
        s.strip() for s in re.split(r"[。！？]", text) if len(s.strip()) >= 15
    )
    return {
        "repeated_sentences": sum(n - 1 for n in sentences.values() if n > 1),
        "halfwidth_commas_after_han": len(re.findall(r"[\u4e00-\u9fff],", text)),
        "tables": len(re.findall(r"(?m)^\|\s*:?-{3,}:?\s*\|", text)),
    }


def changes(old: Measures, new: Measures) -> list[str]:
    """Each measure that differs from the previous run, in key order."""
    out = []
    for key in sorted(old.keys() | new.keys()):
        if key not in old:
            out.append(f"{key}: new {new[key]}")
        elif key not in new:
            out.append(f"{key}: gone (was {old[key]})")
        elif old[key] != new[key]:
            out.append(f"{key}: {old[key]} -> {new[key]}")
    return out


def _flat(measures: dict[str, Measures]) -> Measures:
    return {
        f"{name} {metric}": v
        for name, ms in measures.items()
        for metric, v in ms.items()
    }


def _distinct(folder: Path, *patterns: str) -> list[Path]:
    seen: dict[str, Path] = {}
    for path in sorted(p for pattern in patterns for p in folder.glob(pattern)):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen:
            print(f"skip {path.name}: same bytes as {seen[digest].name}")
        else:
            seen[digest] = path
    return list(seen.values())


def review_folder(
    folder: Path,
    out: Path,
    running_heads: Sequence[str],
    scan: Path | None = None,
    visual: bool = False,
) -> dict[str, Measures]:
    """Measure every rebuilt PDF, source, LaTeX log and transcript in `folder`; write measures.json,
    pages.csv and history.jsonl to `out`, print the changes since the last run, and return the measures."""
    out.mkdir(parents=True, exist_ok=True)
    scan_text = scan_grams(source_ocr_dir(folder))
    measures: dict[str, Measures] = {}
    columns: dict[int, dict[str, object]] = {
        n: {"scan_page": n} for n, g in scan_text.items() if g
    }
    for pdf in _distinct(folder, "*.pdf"):
        matches = text_map(scan_text, pdf)
        measures[pdf.name] = pdf_measures(pdf) | coverage_measures(matches)
        for m in matches:
            columns[m.scan_page] |= {
                f"{pdf.name}:page": m.rebuilt_page or "",
                f"{pdf.name}:coverage": m.coverage,
            }
        if visual and scan is not None:
            from .parity.ink_cache import InkCache
            from .parity.visual import visual_check, write_visual_report
            from .parity.words import page_ink

            page_map = {
                m.scan_page: [m.rebuilt_page] for m in matches if m.rebuilt_page
            }
            summary = write_visual_report(
                visual_check(InkCache(scan, out / "ink", page_ink), pdf, page_map), out / f"visual_{pdf.stem}", scan, pdf
            )
            measures[pdf.name] |= {
                k: summary[k] for k in ("mean_missing", "mean_extra", "mean_layout")
            }
    sources = _distinct(folder, "*.typ", "*.tex")
    for path in sources:
        kind = "typst" if path.suffix == ".typ" else "latex"
        measures[path.name] = source_measures(
            path.read_text(encoding="utf-8"), kind, running_heads
        )
    for path in sorted(folder.glob("*.log")):
        log = path.read_text(encoding="utf-8", errors="replace")
        if "LaTeX2e" in log:
            measures[path.name] = latex_log_measures(log)
    for stem in sorted({p.stem for p in sources}):
        if (md := folder / f"{stem}.md").exists():
            measures[md.name] = transcript_measures(md.read_text(encoding="utf-8"))
            for source in (f"{stem}.typ", f"{stem}.tex"):
                if source in measures:
                    measures[source]["tables_missing"] = (
                        measures[md.name]["tables"] - measures[source]["tables"]
                    )

    rows = list(columns.values())
    names = [
        "scan_page",
        *dict.fromkeys(k for r in rows for k in r if k != "scan_page"),
    ]
    with (out / "pages.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=names, restval="")
        writer.writeheader()
        writer.writerows(rows)
    (out / "measures.json").write_text(
        json.dumps(measures, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    history = out / "history.jsonl"
    lines = history.read_text(encoding="utf-8").splitlines() if history.exists() else []
    if lines:
        diff = changes(_flat(json.loads(lines[-1])["measures"]), _flat(measures))
        print(
            f"{len(diff)} measures changed since the last review"
            + "".join(f"\n  {d}" for d in diff)
        )
    with history.open("a", encoding="utf-8") as fh:
        stamp = datetime.now(UTC).isoformat(timespec="seconds")
        fh.write(
            json.dumps({"time": stamp, "measures": measures}, ensure_ascii=False) + "\n"
        )
    return measures


def lowest_pages(pages_csv: Path, pdf_name: str, n: int = 10) -> str:
    """The `n` scan pages of `pages.csv` with the lowest coverage in `pdf_name`, as `scan S -> R (C)`."""
    with pages_csv.open(encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get(f"{pdf_name}:coverage")]
    rows.sort(key=lambda r: (float(r[f"{pdf_name}:coverage"]), int(r["scan_page"])))
    return ", ".join(
        f"scan {r['scan_page']} -> {r[f'{pdf_name}:page'] or 'none'} ({float(r[f'{pdf_name}:coverage'])})"
        for r in rows[:n]
    )


STATUSES = ("open", "fixed", "wontfix")


def read_findings(path: Path) -> list[Finding]:
    """The findings of a JSONL file; raises ValueError listing every bad line as `line N: problem`."""
    names = [f.name for f in fields(Finding)]
    findings: list[Finding] = []
    errors: list[str] = []
    seen: set[str] = set()
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"line {n}: not valid JSON ({error.msg})")
            continue
        row.setdefault("status", "open")
        problems = [f"missing field {k!r}" for k in names if k not in row]
        if row.get("severity") not in SEVERITIES:
            problems.append(
                f"severity {row.get('severity')!r} is not one of {', '.join(SEVERITIES)}"
            )
        if row["status"] not in STATUSES:
            problems.append(
                f"status {row['status']!r} is not one of {', '.join(STATUSES)}"
            )
        if row.get("id") in seen:
            problems.append(f"id {row['id']!r} is used on an earlier line")
        seen.add(row.get("id"))
        if problems:
            errors.append(f"line {n}: " + "; ".join(problems))
        else:
            findings.append(Finding(**{k: row[k] for k in names}))
    if errors:
        raise ValueError("\n".join(errors))
    return findings


def render_checklist(findings: Sequence[Finding]) -> str:
    """Markdown with one tick box per finding, grouped by book, by severity, open before closed."""
    books = list(dict.fromkeys(f.book for f in findings))
    lines = [
        "# Review checklist",
        "",
        "| Book | " + " | ".join(SEVERITIES) + " | Closed |",
        "|---" * 6 + "|",
    ]
    for book in books:
        mine = [f for f in findings if f.book == book]
        open_by = Counter(f.severity for f in mine if f.status == "open")
        closed = sum(f.status != "open" for f in mine)
        lines.append(
            f"| {book} | "
            + " | ".join(str(open_by[s]) for s in SEVERITIES)
            + f" | {closed} |"
        )
    for book in books:
        lines += ["", f"## {book}", ""]
        mine = [f for f in findings if f.book == book]
        for f in sorted(mine, key=lambda f: (f.severity, f.status != "open", f.id)):
            box = "[ ]" if f.status == "open" else "[x]"
            note = "" if f.status in ("open", "fixed") else f" ({f.status})"
            lines += [
                f"- {box} **{f.id}** {f.severity} `{f.format}` {f.what}{note}",
                f"  - Where: {f.where}",
                f"  - Evidence: {f.evidence}",
            ]
    return "\n".join(lines) + "\n"


def default_running_heads(folder: Path) -> list[str]:
    """The folder name without its leading number, as in `1_宏观经济与产业结构` -> `宏观经济与产业结构`."""
    title = re.sub(r"^[\d_\s-]+", "", folder.name)
    return [title] if title else []


__all__ = [
    "Finding",
    "PageMatch",
    "asdict",
    "changes",
    "coverage_measures",
    "default_running_heads",
    "latex_log_measures",
    "lowest_pages",
    "pdf_measures",
    "read_findings",
    "render_checklist",
    "review_folder",
    "scan_grams",
    "source_measures",
    "text_map",
    "transcript_measures",
]
