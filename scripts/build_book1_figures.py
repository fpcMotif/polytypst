from __future__ import annotations

import argparse
import re
from collections.abc import Callable
from pathlib import Path

import pymupdf

from scripts.book2_figures.engine import ThemeMode

BOOK_DIR = Path("output/1_宏观经济与产业结构")


def load_all_generators() -> dict[str, Callable[[ThemeMode], str]]:
    from scripts.book1_figures import (
        ch1_2,
        ch3_4,
        ch5_6a,
        ch6b_9,
        ch7,
        ch8_13,
        ch10,
        ch11_12a,
        ch12b,
    )

    merged: dict[str, Callable[[ThemeMode], str]] = {}
    for mod in (ch1_2, ch3_4, ch5_6a, ch6b_9, ch7, ch8_13, ch10, ch11_12a, ch12b):
        merged.update(mod.get_generators())
    return merged


def figure_order(fid: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", fid))


def main() -> None:
    parser = argparse.ArgumentParser(description="Redraw book 1's chart figures as monochrome SVGs beside the scan crops.")
    parser.add_argument("ids", nargs="*", help="figure ids such as 1-1 or 12-4; all when omitted")
    parser.add_argument("--png", type=Path, help="also write a 150-dpi PNG of each SVG into this folder")
    args = parser.parse_args()

    fig_dir = BOOK_DIR / "figures"
    generators = load_all_generators()
    unknown = [fid for fid in args.ids if fid not in generators]
    if unknown:
        raise SystemExit(f"no generator for {unknown}")
    for fid in args.ids or sorted(generators, key=figure_order):
        svg = generators[fid]("mono")
        (fig_dir / f"fig_{fid}.svg").write_text(svg, encoding="utf-8")
        if args.png:
            args.png.mkdir(parents=True, exist_ok=True)
            doc = pymupdf.open("svg", svg.encode("utf-8"))
            doc[0].get_pixmap(dpi=150).save(str(args.png / f"fig_{fid}.png"))
            doc.close()

    crops = {p.stem.removeprefix("fig_") for p in fig_dir.glob("fig_*.png")}
    left = sorted(crops - set(generators), key=figure_order)
    print(f"{len(generators)} figures redrawn, {len(left)} left as crops: {' '.join(left)}")


if __name__ == "__main__":
    main()
