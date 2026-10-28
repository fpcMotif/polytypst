from __future__ import annotations

import shutil
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from polytypst.books import book_by_key
from scripts.book2_figures.engine import ThemeMode, save_figure_outputs

BOOK_DIR = book_by_key("3_国际经济环境的变化与日本经济").out_dir
PREFACE_CHART = "preface_exchange_rate"


def load_all_generators() -> dict[str, Callable[[ThemeMode], str]]:
    from scripts.book3_figures import ch1_2, ch3_5, ch6, ch7_8, ch9_10, ch11

    merged: dict[str, Callable[[ThemeMode], str]] = {}
    for mod in (ch1_2, ch3_5, ch6, ch7_8, ch9_10, ch11):
        merged.update(mod.get_generators())
    return merged


def keep_scan_crops(fig_dir: Path, raw_dir: Path) -> None:
    """Copy each scan crop to figures_raw before the mono PNG takes its name in figures."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    for crop in fig_dir.glob("*.png"):
        if not (raw_dir / crop.name).exists():
            shutil.copy2(crop, raw_dir / crop.name)


def write_preface_chart(svg: str) -> None:
    """The preface page links its chart by name, and the scan crop keeps the PNG name."""
    (BOOK_DIR / "figures" / f"{PREFACE_CHART}.svg").write_text(svg, encoding="utf-8")


def main() -> None:
    generators = load_all_generators()
    keep_scan_crops(BOOK_DIR / "figures", BOOK_DIR / "figures_raw")

    def _render_one(fid: str) -> str:
        svg = generators[fid]("mono")
        if fid == PREFACE_CHART:
            write_preface_chart(svg)
        else:
            save_figure_outputs(fid, {"mono": svg}, book_dir=BOOK_DIR, dpi=300)
        return fid

    with ThreadPoolExecutor(max_workers=8) as pool:
        done = list(pool.map(_render_one, sorted(generators)))
    print(f"Rendered {len(done)} figures into {BOOK_DIR / 'figures'}.")


if __name__ == "__main__":
    main()
