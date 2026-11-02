"""Check each redrawn chart SVG against the book figure spec, measured at its printed size.

Usage: uv run python scripts/figure_lint.py [KEY ...] [--svg FILE ...] [--strict]

A full-width chart prints its SVG width on the 330 pt text line, or smaller when the book caps
figure height. The checks, after the spec that BOOK_STYLE in scripts/book2_figures/engine.py follows:

- type: text under 6.5 pt, the least that CJK strokes survive in offset print (error).
- hairline: a stroke under 0.25 pt, which plate exposure loses (error).
- tint: a colour that is not a pure grey, so it prints as rich black or a tint (error).
- faint: a data line lighter than 50% K, which halftone screening breaks up (error).
- decimals: one axis whose numeric tick labels mix decimals, such as 0.8 beside 1 (error).
- rotated: rotated tick text, which slows reading (warning).
- families: text in more than one font family (error).
- aspect: a single plot whose width to height falls outside 1.3:1 to 1.9:1 (warning).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from polytypst.books import book_by_key, book_folders

TEXT_LINE_PT = 330.0
PT_PER_PX = 0.625
MIN_TYPE_PT = 6.5
MIN_STROKE_PT = 0.25
FAINTEST_DATA_GREY = 0x80
ASPECT_RANGE = (1.3, 1.9)
ERRORS = {"type", "hairline", "tint", "faint", "decimals", "baked_note", "families"}
HEIGHT_CAP = re.compile(r"page\.flipped \{ \d+pt \} else \{ (\d+)pt \}")
NUMBER = re.compile(r"^[−-]?\d+(?:\.(\d+))?%?$")
BAKED_NOTE = re.compile(r"^\s*[（(\[［]?\s*(?:资料来源|数据来源|注)\s*[：:]")


@dataclass(frozen=True)
class Finding:
    rule: str
    detail: str

    @property
    def error(self) -> bool:
        return self.rule in ERRORS


def print_scale(svg: str, max_height_pt: float | None = None) -> float:
    """Printed pt per SVG px: a chart prints at its drawn size (svg_pt_per_px) unless the line or the height
    cap shrinks it."""
    width, height = (float(v) for v in re.search(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"', svg).groups())
    scale = min(PT_PER_PX, TEXT_LINE_PT / width)
    return min(scale, max_height_pt / height) if max_height_pt else scale


def _grey(hex6: str) -> int | None:
    r, g, b = (int(hex6[i : i + 2], 16) for i in (0, 2, 4))
    return r if r == g == b else None


def lint_svg(svg: str, max_height_pt: float | None = None) -> list[Finding]:
    scale = print_scale(svg, max_height_pt)
    found: list[Finding] = []
    for m in re.finditer(r'<text [^>]*font-size="([\d.]+)"[^>]*>([^<]*)</text>', svg):
        if float(m[1]) * scale < MIN_TYPE_PT:
            found.append(Finding("type", f"{m[2]!r} prints at {float(m[1]) * scale:.1f} pt"))
        if BAKED_NOTE.match(m[2]):
            found.append(Finding("baked_note", f"{m[2]!r} belongs in #fig-note, not SVG"))
    thinnest = min((float(w) for w in re.findall(r'stroke-width="([\d.]+)"', svg) if float(w) > 0), default=None)
    if thinnest is not None and thinnest * scale < MIN_STROKE_PT:
        found.append(Finding("hairline", f"a {thinnest * scale:.2f} pt stroke"))
    tints = sorted({c for c in re.findall(r'(?:stroke|fill)="#([0-9a-fA-F]{6})"', svg) if _grey(c.lower()) is None})
    if tints:
        found.append(Finding("tint", " ".join(f"#{c}" for c in tints)))
    for colour in sorted(set(re.findall(r'<path [^>]*stroke="#([0-9a-fA-F]{6})"[^>]*stroke-linejoin', svg))):
        grey = _grey(colour.lower())
        if grey is not None and grey > FAINTEST_DATA_GREY:
            found.append(Finding("faint", f"a data line in #{colour}, {100 - grey * 100 // 255}% K"))
    columns: dict[tuple[str, str], list[str]] = defaultdict(list)
    for m in re.finditer(r'<text x="([\d.]+)" y="[\d.]+" text-anchor="(end|start)"[^>]*>([^<]*)</text>', svg):
        if NUMBER.match(m[3]):
            columns[(m[1], m[2])].append(m[3])
    for labels in columns.values():
        places = {len(NUMBER.match(lab)[1] or "") for lab in labels}
        if len(labels) > 2 and len(places) > 1:
            found.append(Finding("decimals", " ".join(labels)))
    if len(families := set(re.findall(r'font-family="([^"]+)"', svg))) > 1:
        found.append(Finding("families", f"{len(families)} font stacks"))
    if rotated := re.findall(r'<text transform="[^"]*rotate\([^>]*>([^<]*)</text>', svg):
        found.append(Finding("rotated", f"{len(rotated)} labels, such as {rotated[0]!r}"))
    plots = set(re.findall(r'<clipPath [^>]*><rect x="[\d.]+" y="[\d.]+" width="([\d.]+)" height="([\d.]+)"', svg))
    if len(plots) == 1:
        w, h = (float(v) for v in plots.pop())
        if h and not ASPECT_RANGE[0] <= w / h <= ASPECT_RANGE[1]:
            found.append(Finding("aspect", f"plot is {w / h:.2f}:1"))
    return found


def book_height_cap(key: str) -> float | None:
    cap = HEIGHT_CAP.search((book_folders()[key] / "book.toml").read_text(encoding="utf-8"))
    return float(cap[1]) if cap else None


def book_svgs(key: str) -> list[Path]:
    return sorted((book_by_key(key).out_dir / "figures").glob("fig_*.svg"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("keys", nargs="*", help="book keys; the six economics books 1_… to 6_… when omitted")
    parser.add_argument("--svg", nargs="*", type=Path, default=[], help="lint these SVG files instead")
    parser.add_argument("--strict", action="store_true", help="exit 1 on warnings as well as errors")
    args = parser.parse_args()

    targets: list[tuple[Path, float | None]] = [(p, None) for p in args.svg]
    if not args.svg:
        keys = args.keys or sorted(k for k in book_folders() if re.match(r"[1-6]_", k))
        targets = [(p, book_height_cap(k)) for k in keys for p in book_svgs(k)]
    counts: dict[str, int] = defaultdict(int)
    failed = False
    for path, cap in targets:
        for f in lint_svg(path.read_text(encoding="utf-8"), cap):
            counts[f.rule] += 1
            failed |= f.error or args.strict
            print(f"{path.parent.parent.name}/{path.name}: {'error' if f.error else 'warning'} {f.rule}: {f.detail}")
    summary = ", ".join(f"{rule} {n}" for rule, n in sorted(counts.items())) or "clean"
    print(f"{len(targets)} figures: {summary}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
