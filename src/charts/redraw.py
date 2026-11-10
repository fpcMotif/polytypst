from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from itertools import repeat
from pathlib import Path
from types import ModuleType

from ..books import book_by_key, book_folders, module
from ..process_pool import process_pool
from .engine import (
    ChartStyle,
    ThemeMode,
    chart_svg,
    enrich_book_figures_manifest,
    svg_to_png,
)

Generator = Callable[[ThemeMode], str]
CHARTS = "charts"


def chart_books() -> list[str]:
    return sorted(key for key, folder in book_folders().items() if (folder / CHARTS / "__init__.py").is_file())


def charts_package(key: str) -> ModuleType:
    return module(key, CHARTS)


def generators(key: str) -> dict[str, Generator]:
    merged: dict[str, Generator] = {}
    for path in sorted((book_folders()[key] / CHARTS).glob("ch*.py")):
        found = module(key, f"{CHARTS}.{path.stem}").get_generators()
        if twice := sorted(set(found) & set(merged)):
            raise ValueError(f"{key}: {path.name} redefines {twice}")
        merged.update(found)
    return merged


_generators = cache(generators)


def figure_order(fid: str) -> tuple[tuple[int, ...], str]:
    return tuple(int(n) for n in re.findall(r"\d+", fid)), fid


def default_chart_file(book_dir: Path, fid: str) -> Path:
    return book_dir / "figures" / f"fig_{fid}.svg"


def chart_file(key: str, book_dir: Path, fid: str) -> Path:
    return getattr(charts_package(key), "chart_file", default_chart_file)(book_dir, fid)


def write_chart(fid: str, generator: Generator, style: ChartStyle, book_dir: Path) -> None:
    default_chart_file(book_dir, fid).write_text(chart_svg(generator, style), encoding="utf-8")


def is_stale(key: str, fid: str, style: ChartStyle) -> bool:
    on_disk = chart_file(key, book_by_key(key).out_dir, fid)
    return not on_disk.is_file() or on_disk.read_text(encoding="utf-8") != chart_svg(_generators(key)[fid], style)


def stale_charts(key: str, style: ChartStyle = "a") -> list[str]:
    fids = sorted(generators(key), key=figure_order)
    with process_pool(len(fids)) as pool:
        flags = list(pool.map(is_stale, repeat(key), fids, repeat(style), chunksize=8))
    return [fid for fid, stale in zip(fids, flags, strict=True) if stale]


def draw_charts(
    found: Mapping[str, Generator],
    book_dir: Path,
    ids: Sequence[str] = (),
    style: ChartStyle = "a",
    package: ModuleType | None = None,
    png: Path | None = None,
) -> list[str]:
    """Write the charts `ids` (all of `found` when empty) into `book_dir/figures`, and return the ids drawn.

    A book's charts `package` may define `prepare(book_dir)` and `write(fid, generator, style, book_dir)`."""
    if unknown := [fid for fid in ids if fid not in found]:
        raise SystemExit(f"{book_dir.name}: no generator for {unknown}")
    (book_dir / "figures").mkdir(parents=True, exist_ok=True)
    if prepare := getattr(package, "prepare", None):
        prepare(book_dir)
    write = getattr(package, "write", write_chart)
    if png:
        png.mkdir(parents=True, exist_ok=True)

    def draw(fid: str) -> None:
        write(fid, found[fid], style, book_dir)
        if png:
            svg_to_png(chart_svg(found[fid], style), png / f"fig_{fid}.png", dpi=150)

    drawn = list(ids) or sorted(found, key=figure_order)
    with ThreadPoolExecutor(max_workers=8) as pool:
        _ = list(pool.map(draw, drawn))
    return drawn


def redraw(key: str, ids: list[str], style: ChartStyle, png: Path | None) -> None:
    book_dir = book_by_key(key).out_dir
    package = charts_package(key)
    found = generators(key)
    drawn = draw_charts(found, book_dir, ids, style, package, png)
    enrich_book_figures_manifest(key, found)
    if finish := getattr(package, "finish", None):
        finish(book_dir, found, style)
    crops = {p.stem.removeprefix("fig_") for p in (book_dir / "figures").glob("fig_*.png")}
    left = sorted(crops - set(found), key=figure_order)
    print(f"{key}: {len(drawn)} charts redrawn into {book_dir / 'figures'}, {len(left)} left as crops: {' '.join(left)}")


def refresh_charts(key: str) -> list[str]:
    """Redraw the book's stale charts and name every chart in its figure manifest; return the ids redrawn."""
    if stale := stale_charts(key):
        redraw(key, stale, "a", None)
    else:
        enrich_book_figures_manifest(key, generators(key))
    return stale


def with_charts(key: str, hook: Callable[[Path], object] | None) -> Callable[[Path], object]:
    """The figures step of a book with a charts package: its own figures `hook` first, then `refresh_charts`."""

    def figures(out_dir: Path) -> object:
        made = None if hook is None else hook(out_dir)
        _ = refresh_charts(key)
        return made

    return figures


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="polytypst charts",
        description="Redraw a book's chart figures from books/<key>/charts into its output folder, "
        "or with --check list the charts whose SVG on disk differs from what the code draws.",
    )
    parser.add_argument("key", nargs="?", help=f"book key; one of {', '.join(chart_books())}; every chart book with --check")
    parser.add_argument("ids", nargs="*", help="figure ids such as 1-1 or 12-4; all when omitted")
    parser.add_argument("--style", choices=("a", "b"), default="a", help="a: the redraw style; b: the scan's chart style in the body fonts")
    parser.add_argument("--png", type=Path, help="also write a 150-dpi PNG of each SVG into this folder")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 when an SVG on disk is missing or out of date")
    args = parser.parse_args(argv)
    if args.check:
        failed = False
        for key in [args.key] if args.key else chart_books():
            stale = stale_charts(key, args.style)
            failed |= bool(stale)
            print(f"{key}: {len(generators(key))} charts, {len(stale)} stale{': ' + ' '.join(stale) if stale else ''}")
        return int(failed)
    if not args.key:
        parser.error("name a book to redraw")
    if args.key not in chart_books():
        parser.error(f"{args.key} has no books/{args.key}/{CHARTS} package")
    redraw(args.key, args.ids, args.style, args.png)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
