"""Put each redrawn chart beside its scan crop, so a reviewer can check the redraw's data against the scan.

Usage: mise exec -- uv run python scripts/figure_compare.py KEY [FIGURE_ID ...] [--out DIR]

Writes one PNG per figure, the scan crop on the left and the printed SVG on the right at the same height,
into output/KEY/review/figure_compare/ unless --out names another folder. The crop comes from the source
scan, $POLYTYPST_SOURCES/<source_pdf>, at the figure's figures_manifest.json box.
"""

from __future__ import annotations

import argparse
import json
import os
import tomllib
from pathlib import Path

from polytypst.books import book_by_key, book_folders
from polytypst.compare_sheet import Panel, write_sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("key")
    parser.add_argument("ids", nargs="*", help="figure ids such as 3-2; every redrawn figure when omitted")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    book = book_by_key(args.key)
    out_dir = book.out_dir
    source_pdf = tomllib.loads((book_folders()[args.key] / "book.toml").read_text(encoding="utf-8"))["source_pdf"]
    scan = Path(os.environ["POLYTYPST_SOURCES"]) / source_pdf
    manifest = {e["figure_id"]: e for e in json.loads((out_dir / "figures_manifest.json").read_text(encoding="utf-8"))}
    dest = args.out or out_dir / "review" / "figure_compare"
    dest.mkdir(parents=True, exist_ok=True)
    ids = args.ids or sorted(fid for fid in manifest if (out_dir / "figures" / f"fig_{fid}.svg").exists())
    done = 0
    for fid in ids:
        entry = manifest.get(fid)
        svg = out_dir / "figures" / f"fig_{fid}.svg"
        if not entry or not entry.get("box") or not svg.exists():
            print(f"{fid}: no scan box or no SVG")
            continue
        page = int(entry["source_page"])
        write_sheet([[Panel(f"scan p{page}", scan, page, tuple(entry["box"])), Panel(f"redrawn {fid}", svg, 1)]], dest / f"fig_{fid}.png")
        done += 1
    print(f"{done} comparisons in {dest}")


if __name__ == "__main__":
    main()
