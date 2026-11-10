"""Master figure aggregator and generator for Algebra I: Basic Notions of Algebra.

Renders all 45 figures as crisp SVGs and 300-DPI raster PNGs into the target directory.
"""

import json
from collections.abc import Callable
from pathlib import Path

import pymupdf

from polytypst.paths import OUTPUT

from .figures_1_15 import (
    gen_fig_1,
    gen_fig_2,
    gen_fig_3,
    gen_fig_4,
    gen_fig_5,
    gen_fig_6,
    gen_fig_7,
    gen_fig_8,
    gen_fig_9,
    gen_fig_10,
    gen_fig_11,
    gen_fig_12,
    gen_fig_13,
    gen_fig_14,
    gen_fig_15,
)
from .figures_16_30 import (
    gen_fig_16,
    gen_fig_17,
    gen_fig_18,
    gen_fig_19,
    gen_fig_20,
    gen_fig_21,
    gen_fig_22,
    gen_fig_23,
    gen_fig_24,
    gen_fig_25,
    gen_fig_26,
    gen_fig_27,
    gen_fig_28,
    gen_fig_29,
    gen_fig_30,
)
from .figures_31_45 import (
    gen_fig_31,
    gen_fig_32,
    gen_fig_33,
    gen_fig_34,
    gen_fig_35,
    gen_fig_36,
    gen_fig_37,
    gen_fig_38,
    gen_fig_39,
    gen_fig_40,
    gen_fig_41,
    gen_fig_42,
    gen_fig_43,
    gen_fig_44,
    gen_fig_45,
)

FIGURE_GENERATORS: dict[int, Callable[[], str]] = {
    1: gen_fig_1,
    2: gen_fig_2,
    3: gen_fig_3,
    4: gen_fig_4,
    5: gen_fig_5,
    6: gen_fig_6,
    7: gen_fig_7,
    8: gen_fig_8,
    9: gen_fig_9,
    10: gen_fig_10,
    11: gen_fig_11,
    12: gen_fig_12,
    13: gen_fig_13,
    14: gen_fig_14,
    15: gen_fig_15,
    16: gen_fig_16,
    17: gen_fig_17,
    18: gen_fig_18,
    19: gen_fig_19,
    20: gen_fig_20,
    21: gen_fig_21,
    22: gen_fig_22,
    23: gen_fig_23,
    24: gen_fig_24,
    25: gen_fig_25,
    26: gen_fig_26,
    27: gen_fig_27,
    28: gen_fig_28,
    29: gen_fig_29,
    30: gen_fig_30,
    31: gen_fig_31,
    32: gen_fig_32,
    33: gen_fig_33,
    34: gen_fig_34,
    35: gen_fig_35,
    36: gen_fig_36,
    37: gen_fig_37,
    38: gen_fig_38,
    39: gen_fig_39,
    40: gen_fig_40,
    41: gen_fig_41,
    42: gen_fig_42,
    43: gen_fig_43,
    44: gen_fig_44,
    45: gen_fig_45,
}

FIGURE_PAGES: dict[int, int] = {
    1: 11, 2: 11, 3: 12, 4: 12, 5: 15, 6: 15, 7: 17, 8: 22, 9: 22, 10: 67,
    11: 88, 12: 88, 13: 89, 14: 97, 15: 99, 16: 99, 17: 100, 18: 112, 19: 113, 20: 113,
    21: 115, 22: 115, 23: 118, 24: 119, 25: 120, 26: 122, 27: 129, 28: 131, 29: 131, 30: 132,
    31: 133, 32: 135, 33: 136, 34: 139, 35: 139, 36: 140, 37: 141, 38: 163, 39: 176, 40: 209,
    41: 212, 42: 213, 43: 214, 44: 216, 45: 217,
}


def generate_all_algebra1_figures(out_dir: Path) -> None:
    """Generate all 45 figures as SVG and 300-DPI PNG files, updating figures_manifest.json."""
    fig_dir = out_dir / "figures" if out_dir.name != "figures" else out_dir
    manifest_dir = fig_dir.parent if fig_dir.name == "figures" else fig_dir
    fig_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries: list[dict[str, object]] = []

    for fid, gen in sorted(FIGURE_GENERATORS.items()):
        svg_content = gen()
        svg_path = fig_dir / f"fig_{fid}.svg"
        png_path = fig_dir / f"fig_{fid}.png"
        _ = svg_path.write_text(svg_content, encoding="utf-8")

        with pymupdf.open("svg", svg_content.encode("utf-8")) as doc:
            pix = doc[0].get_pixmap(dpi=300)
            pix.save(str(png_path))

        manifest_entries.append({
            "figure_id": str(fid),
            "caption": f"Fig. {fid}",
            "image_rel_path": f"figures/fig_{fid}.png",
            "source_page": FIGURE_PAGES.get(fid, 1),
            "box": None,
            "width_px": pix.width,
            "height_px": pix.height,
            "chapter": None,
            "title": f"Figure {fid}",
            "alt": f"Figure {fid}",
            "description": f"Vector illustration of Figure {fid}",
            "note": "",
            "source": "",
            "scan_crop_path": "",
            "svg_path": f"figures/fig_{fid}.svg",
            "reproduced_by": "vector",
        })

    manifest_path = manifest_dir / "figures_manifest.json"
    _ = manifest_path.write_text(json.dumps(manifest_entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {len(FIGURE_GENERATORS)} vector figures (SVG + 300-DPI PNG) -> {fig_dir}")


if __name__ == "__main__":
    generate_all_algebra1_figures(OUTPUT / "algebra1" / "figures")
