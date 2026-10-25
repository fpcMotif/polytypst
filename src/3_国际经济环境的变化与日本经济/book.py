import json
from pathlib import Path

import pymupdf

from ..edition import OUTPUT, Book, monograph_edition
from ..parity.source import source_pdf
from .spec import INTL_ECON_ILLUSTRATED_SPEC, INTL_ECON_SPEC, PREFACE_CHART

OUT_DIR = OUTPUT / "3_国际经济环境的变化与日本经济"

# The preface's exchange-rate chart has no figure number, so figure extraction skips it.
PREFACE_CHART_PAGE = 17
PREFACE_CHART_BOX = (0.15, 0.555, 0.83, 0.835)


def crop_preface_chart(out_dir: Path) -> None:
    """Crop the uncaptioned preface chart, with its printed title, from the scan at the scan's own size."""
    target = out_dir / INTL_ECON_SPEC.figure_dir / PREFACE_CHART
    if target.exists():
        return
    with pymupdf.open(source_pdf(INTL_ECON_SPEC)) as scan:
        page = scan[PREFACE_CHART_PAGE - 1]
        x0, y0, x1, y1 = PREFACE_CHART_BOX
        r = page.rect
        clip = pymupdf.Rect(
            r.x0 + r.width * x0,
            r.y0 + r.height * y0,
            r.x0 + r.width * x1,
            r.y0 + r.height * y1,
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        page.get_pixmap(dpi=300, clip=clip).save(target)


# Scan p313 prints two charts, 10-7A (women) and 10-7B (men); figure extraction kept one box as 10-7.
SPLIT_FIGURES = {
    "10-7A": (
        313,
        (0.1805, 0.372, 0.8301, 0.6052),
        "图 10-7A 新员工各年龄段的薪酬（女性，月收入）",
    ),
    "10-7B": (
        313,
        (0.1805, 0.643, 0.8301, 0.856),
        "图 10-7B 新员工各年龄段的薪酬（男性，月收入）",
    ),
}


def split_figure_10_7(out_dir: Path) -> None:
    manifest_path = out_dir / "figures_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not any(f["figure_id"] == "10-7" for f in manifest):
        return
    entries = []
    with pymupdf.open(source_pdf(INTL_ECON_SPEC)) as scan:
        for figure_id, (page_number, box, caption) in SPLIT_FIGURES.items():
            page = scan[page_number - 1]
            r = page.rect
            x0, y0, x1, y1 = box
            clip = pymupdf.Rect(
                r.width * x0, r.height * y0, r.width * x1, r.height * y1
            )
            rel = f"{INTL_ECON_SPEC.figure_dir}/fig_{figure_id}.png"
            pix = page.get_pixmap(dpi=600, clip=clip)
            pix.save(out_dir / rel)
            entries.append(
                {
                    "figure_id": figure_id,
                    "caption": caption,
                    "image_rel_path": rel,
                    "source_page": page_number,
                    "box": list(box),
                    "width_px": pix.width,
                    "height_px": pix.height,
                }
            )
    at = next(i for i, f in enumerate(manifest) if f["figure_id"] == "10-7")
    (out_dir / manifest[at]["image_rel_path"]).unlink(missing_ok=True)
    manifest[at : at + 1] = entries
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def prepare_figures(out_dir: Path) -> None:
    crop_preface_chart(out_dir)
    split_figure_10_7(out_dir)


BOOK = Book(
    INTL_ECON_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(
            INTL_ECON_SPEC, OUT_DIR, "11 chapters, monochrome academic monograph"
        ),
        "illustrated": monograph_edition(
            INTL_ECON_ILLUSTRATED_SPEC,
            OUT_DIR,
            "11 chapters, illustrated monograph with scan figures",
        ),
    },
    prepare_figures,
)
