from __future__ import annotations

import argparse
import importlib
from collections.abc import Callable, Sequence
from pathlib import Path

import pymupdf

from polytypst.books import book_by_key
from scripts.book2_figures.engine import ThemeMode, chart_svg, scan_canvas

BOOK_DIR = book_by_key("5_财政政策与社会保障").out_dir


MODULES = ("ch1_2", "ch5_6", "ch7_8", "ch9_10_14", "ch11", "ch12")


def load_generators(
    modules: Sequence[str] = MODULES,
) -> dict[str, Callable[[ThemeMode], str]]:
    merged: dict[str, Callable[[ThemeMode], str]] = {}
    for name in modules:
        merged.update(
            importlib.import_module(f"scripts.book5_figures.{name}").get_generators()
        )
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Redraw book 5's chart figures as monochrome SVGs beside the scan crops."
    )
    parser.add_argument(
        "ids", nargs="*", help="figure ids such as 1-1; all when omitted"
    )
    parser.add_argument(
        "--png", type=Path, help="also write a 150-dpi PNG of each SVG into this folder"
    )
    parser.add_argument("--style", choices=("a", "b"), default="a", help="a: the redraw style; b: the scan's chart style in the body fonts")
    parser.add_argument(
        "--module",
        choices=MODULES,
        action="append",
        help="load only this chapter module",
    )
    args = parser.parse_args()

    fig_dir = BOOK_DIR / "figures"
    generators = load_generators(args.module or MODULES)
    unknown = [fid for fid in args.ids if fid not in generators]
    if unknown:
        raise SystemExit(f"no generator for {unknown}")
    for fid in args.ids or sorted(
        generators, key=lambda f: tuple(int(p) for p in f.split("-"))
    ):
        with scan_canvas(BOOK_DIR, fid):
            svg = chart_svg(generators[fid], args.style)
        (fig_dir / f"fig_{fid}.svg").write_text(svg, encoding="utf-8")
        if args.png:
            args.png.mkdir(parents=True, exist_ok=True)
            doc = pymupdf.open("svg", svg.encode("utf-8"))
            doc[0].get_pixmap(dpi=150).save(str(args.png / f"fig_{fid}.png"))
            doc.close()

    crops = {p.stem.removeprefix("fig_") for p in fig_dir.glob("fig_*.png")}
    left = sorted(
        crops - set(generators), key=lambda f: tuple(int(p) for p in f.split("-"))
    )
    print(
        f"{len(generators)} figures redrawn, {len(left)} left as crops: {' '.join(left)}"
    )


if __name__ == "__main__":
    main()
