import re
from collections.abc import Iterator
from pathlib import Path

import pymupdf

from ..evidence import pixmap_png
from ..process_pool import process_pool
from . import PageCheck
from .agents import Job, Runner, omp, run_agents

CAPTION = re.compile(r"^(附表|表|图)[\s ]*(\d+-\d+|[A-Z])(?:\s|$)")
CAPTION_MAX_CHARS = 80
SENTENCE = re.compile(r"。|^(附表|表|图)[\s ]*(?:\d+-\d+|[A-Z])\s*(显示|所示|表明|中|是|给出|列出|反映|的)")
ENGLISH_CAPTION = re.compile(r"^(Figure|Fig\.|Table)\s*(\d+(?:[-.]\d+)?|[A-Z])(?:[.:]?\s+|[.:]?$)")
ENGLISH_SENTENCE = re.compile(
    r"^\S+\s+\S+\s+(shows?|lists?|gives?|is|are|was|presents?|summari[sz]es?|illustrates?|compares?|contains?|reports?|displays?|depicts?)\b"
)
DPI = 110
RUNBOOK = "docs/render-check.md"
MODEL = "gemini-3.8-flash"
RENDER_CHECK = Path("output/render_check")


def caption_label(text: str) -> str | None:
    """The label of a caption line, such as 表1-1. A sentence that names a table is not a caption."""
    text = text.strip()
    if len(text) > CAPTION_MAX_CHARS:
        return None
    if m := ENGLISH_CAPTION.match(text):
        kind = "Table" if m[1] == "Table" else "Figure"
        return None if ENGLISH_SENTENCE.match(text) else f"{kind}{m[2]}"
    if SENTENCE.search(text) or not (m := CAPTION.match(text)):
        return None
    return f"{m[1]}{m[2]}"


def rebuilt_pages(pdf: pymupdf.Document) -> dict[str, int]:
    pages: dict[str, int] = {}
    for number in range(1, pdf.page_count + 1):
        for block in pdf[number - 1].get_text("blocks"):
            if (label := caption_label(block[4])) and label not in pages:
                pages[label] = number
    return pages


def scan_pages(check: PageCheck) -> dict[str, int]:
    pages: dict[str, int] = {}
    for number in check.pages():
        for line in check.ocr_lines(number):
            if (label := caption_label(line.text)) and label not in pages:
                pages[label] = number
    return pages


def render(doc: pymupdf.Document, page: int, path: Path) -> None:
    """The caption page and the page after it, side by side, so that a table or a note that runs on is in view."""
    pages = [doc[n] for n in (page - 1, page) if n < len(doc)]
    width, height = sum(p.rect.width for p in pages), max(p.rect.height for p in pages)
    spread = pymupdf.open()
    sheet = spread.new_page(width=width, height=height)
    x = 0.0
    for p in pages:
        sheet.show_pdf_page(pymupdf.Rect(x, 0, x + p.rect.width, p.rect.height), doc, p.number)
        x += p.rect.width
    path.write_bytes(pixmap_png(sheet.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72))))


_DOCS: dict[str, pymupdf.Document] = {}


def _open_docs(rebuilt: Path, scan: Path) -> None:
    _DOCS["rebuilt"], _DOCS["scan"] = pymupdf.open(rebuilt), pymupdf.open(scan)


def _render_job(job: tuple[str, int, Path]) -> None:
    render(_DOCS[job[0]], job[1], job[2])


class RenderCheck:
    def __init__(self, check: PageCheck, rebuilt: Path, out: Path | None = None) -> None:
        self.check = check
        self.rebuilt_path = rebuilt
        self.rebuilt_doc = pymupdf.open(rebuilt)
        self.out = out or RENDER_CHECK / check.key
        self.rebuilt = rebuilt_pages(self.rebuilt_doc)
        self.scan = scan_pages(check)

    def paired(self) -> list[str]:
        return [label for label in self.rebuilt if label in self.scan]

    def render(self, label: str) -> tuple[Path, Path]:
        self.out.mkdir(parents=True, exist_ok=True)
        rebuilt, scan = self.out / f"{label}_rebuilt.png", self.out / f"{label}_scan.png"
        render(self.rebuilt_doc, self.rebuilt[label], rebuilt)
        render(self.check.scan_doc, self.scan[label], scan)
        return rebuilt, scan

    def run(self, size: int, jobs: int, model: str, runner: Runner = omp) -> Iterator[str]:
        paired = self.paired()
        self.out.mkdir(parents=True, exist_ok=True)
        renders = [
            job
            for label in paired
            for job in (
                ("rebuilt", self.rebuilt[label], self.out / f"{label}_rebuilt.png"),
                ("scan", self.scan[label], self.out / f"{label}_scan.png"),
            )
        ]
        with process_pool(len(renders), _open_docs, (self.rebuilt_path, self.check.scan)) as pool:
            list(pool.map(_render_job, renders, chunksize=4))
        batches = [(paired[i : i + size], self.out / f"r{i // size + 1}.jsonl") for i in range(0, len(paired), size)]
        todo = {out.with_suffix(".log"): (labels, out) for labels, out in batches if not out.exists()}
        yield f"{len(paired)} pairs, {len(todo)} of {len(batches)} batches to run, {jobs} at a time"
        agent_jobs = [
            Job(f"Follow this runbook with BOOK={self.check.key} DIR={self.out} ITEMS={','.join(labels)} OUT={out}.", log)
            for log, (labels, out) in todo.items()
        ]
        for job, code in run_agents(RUNBOOK, agent_jobs, model, jobs, runner):
            labels, out = todo[job.log]
            lines = sum(1 for line in out.read_text(encoding="utf-8").splitlines() if line.strip()) if out.exists() else 0
            yield f"{out.name}: exit {code}, {lines} of {len(labels)} items"
