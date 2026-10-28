"""Compile each included diagram snippet once and place it as an image, so Typst lays out each fletcher drawing once
instead of on every layout pass of the book. A diagram is rendered with the book's own preamble, keyed by a hash of
the preamble, the snippet and the Typst version, and kept in `diagram_cache/` beside the book."""

import functools
import hashlib
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from .typst_math import run_typst, typst_command

INCLUDE_RE = re.compile(r'#\(include "([^"]+\.typ)"\)')
CACHE_DIR = "diagram_cache"
PAD_PT = 6.0
WRAPPER = (
    "\n#set page(width: auto, height: auto, margin: {pad}pt, header: none, footer: none)\n"
    "#set math.equation(numbering: none)\n"
    '$ #(include "{snippet}") $\n'
)


@dataclass(frozen=True)
class CachedDiagram:
    pdf: str
    page_width: float
    page_height: float

    def typst(self) -> str:
        return (
            f"#box(width: {self.page_width - 2 * PAD_PT:.3f}pt, height: {self.page_height - 2 * PAD_PT:.3f}pt, "
            f'place(top + left, dx: -{PAD_PT}pt, dy: -{PAD_PT}pt, image("{self.pdf}", '
            f"width: {self.page_width:.3f}pt, height: {self.page_height:.3f}pt)))"
        )


@functools.cache
def typst_version() -> str:
    cmd = typst_command(fallback_nix=True) or ("typst",)
    return subprocess.run([*cmd, "--version"], check=True, capture_output=True, text=True).stdout.strip()


def _render(out_dir: Path, preamble: str, snippet: str) -> CachedDiagram:
    source = (out_dir / snippet).read_text(encoding="utf-8")
    key = hashlib.sha256("\0".join((typst_version(), WRAPPER, str(PAD_PT), preamble, source)).encode()).hexdigest()[:24]
    pdf = out_dir / CACHE_DIR / f"{key}.pdf"
    if not pdf.exists():
        wrapper = out_dir / f".diagram_{key}.typ"
        wrapper.write_text(preamble + WRAPPER.format(pad=PAD_PT, snippet=snippet), encoding="utf-8")
        partial = pdf.with_suffix(".partial.pdf")
        try:
            _ = run_typst("compile", "--root", str(out_dir), str(wrapper), str(partial), capture_output=True)
            partial.replace(pdf)
        finally:
            wrapper.unlink(missing_ok=True)
    page = pymupdf.open(pdf)[0].rect
    return CachedDiagram(f"{CACHE_DIR}/{pdf.name}", page.width, page.height)


def with_cached_diagrams(typst: str, preamble: str, out_dir: Path) -> str:
    """`typst` with each diagram `#(include ...)` replaced by its cached render."""
    snippets = sorted(set(INCLUDE_RE.findall(typst)))
    if not snippets:
        return typst
    (out_dir / CACHE_DIR).mkdir(exist_ok=True)
    with ThreadPoolExecutor() as pool:
        cached = dict(zip(snippets, pool.map(lambda s: _render(out_dir, preamble, s), snippets), strict=True))
    return INCLUDE_RE.sub(lambda m: cached[m.group(1)].typst(), typst)
