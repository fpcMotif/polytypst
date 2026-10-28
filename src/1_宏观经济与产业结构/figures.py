from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

from ..book_state import book_state
from ..facsimile_figures import FigureArt
from ..ocr.lines import LineStore, source_ocr_dir
from ..ocr.pages import PageImage
from ..vision.cjk_charts import (
    PAD,
    _ink_box,
    _stack,
    extract_cjk_charts,
    transcript_figure_ids,
)
from ..vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    write_figures_manifest,
)

SCAN_CAPTIONS = {
    "6-17": "图6-17 向发达经济体出口模式的变化（1980—2004年：在发达经济体进口市场（按附加值水平划分）上的份额）",
    "6-18": "图6-18 向亚洲新兴经济体出口模式的变化（1980—2004年：在亚洲新兴经济体进口市场（按附加值水平划分）上的份额）",
    "6-19": "图6-19 日本出口份额（按附加值水平划分，%）的变化（1980-2004年：发达经济体市场VS.亚洲新兴经济体市场）",
}

BAND_OVERRIDES: dict[str, list[tuple[int, tuple[float, float, float, float]]]] = {
    "1-5": [(47, (0.04, 0.327, 0.96, 0.852)), (48, (0.04, 0.090, 0.96, 0.368))],
    "1-7": [(50, (0.04, 0.170, 0.96, 0.459))],
    "2-3": [(74, (0.04, 0.530, 0.96, 0.870))],
    "6-10": [(204, (0.04, 0.332, 0.96, 0.575))],
    "6-12": [(205, (0.04, 0.075, 0.96, 0.347))],
    "6-17": [(213, (0.13, 0.09, 0.84, 0.92)), (214, (0.11, 0.095, 0.81, 0.92))],
    "6-18": [(215, (0.13, 0.09, 0.84, 0.92)), (216, (0.11, 0.095, 0.81, 0.92))],
    "7-10": [(246, (0.04, 0.228, 0.96, 0.506))],
    "9-1": [(297, (0.04, 0.285, 0.96, 0.409))],
    "10-12": [(338, (0.04, 0.118, 0.96, 0.489))],
    "11-6": [(365, (0.04, 0.625, 0.96, 0.880))],
}
BAND_TURNS = {"6-17": -90, "6-18": -90}
FACSIMILE_BANDS: dict[str, list[tuple[int, tuple[float, float, float, float]]]] = {
    "1-4": [(45, (0.04, 0.425, 0.96, 0.72)), (46, (0.04, 0.10, 0.96, 0.378))],
    "1-9": [(55, (0.04, 0.60, 0.96, 0.885)), (56, (0.04, 0.10, 0.96, 0.405))],
    "7-2": [(226, (0.04, 0.50, 0.96, 0.86)), (227, (0.04, 0.10, 0.96, 0.475))],
    "7-5": [(233, (0.04, 0.51, 0.96, 0.76)), (234, (0.04, 0.10, 0.96, 0.362))],
    "7-6": [(237, (0.04, 0.65, 0.96, 0.90)), (238, (0.04, 0.10, 0.96, 0.630))],
    "11-3": [(359, (0.04, 0.285, 0.96, 0.785)), (360, (0.04, 0.10, 0.96, 0.368))],
    "11-5": [(362, (0.04, 0.485, 0.96, 0.93)), (363, (0.04, 0.10, 0.96, 0.355))],
    "13-3": [(414, (0.04, 0.60, 0.96, 0.85)), (415, (0.04, 0.10, 0.96, 0.61))],
    "6-14": [(205, (0.04, 0.685, 0.96, 0.935)), (206, (0.04, 0.10, 0.96, 0.866))],
    "6-19": [(218, (0.11, 0.13, 0.83, 0.91))],
}
FACSIMILE_TURNS = {**BAND_TURNS, "6-19": -90}


def _clean_monochrome_raster(raw_path: Path, dst_path: Path) -> None:
    im = Image.open(raw_path).convert("L")
    arr = np.asarray(im, dtype=np.float32) / 255.0
    cleaned = np.clip((arr - 0.14) / (0.88 - 0.14), 0.0, 1.0)
    out = (cleaned * 255.0).astype(np.uint8)
    Image.fromarray(out, mode="L").convert("RGB").save(dst_path)


def extract_clean_raw_figures(out_dir: Path) -> list[dict[str, object]]:
    renders_dir = out_dir / "page_renders"
    md_dir = book_state(out_dir) / "markdown_pages"
    raw_dir = out_dir / "figures_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    store = LineStore(source_ocr_dir(out_dir))

    pages = [
        PageImage(number=int(p.stem.split("_")[1]), path=p)
        for p in sorted(renders_dir.glob("p_*.jpg"))
    ]

    lines = {p.number: store.lines(p.number) for p in pages}
    texts = [p.read_text(encoding="utf-8") for p in sorted(md_dir.glob("p_*.md"))]
    known = transcript_figure_ids(texts)
    extracted = extract_cjk_charts(pages, lines, raw_dir, known)
    by_id = {f.figure_id: f for f in extracted}

    for fid, pieces in BAND_OVERRIDES.items():
        crops: list[Image.Image] = []
        for page_num, band in pieces:
            img_path = renders_dir / f"p_{page_num:03d}.jpg"
            if not img_path.exists():
                break
            with Image.open(img_path) as im:
                page_img = im.convert("L")
            gray = np.asarray(page_img)
            h, w = gray.shape
            l, t, r, b = band
            box = _ink_box(gray, int((t + PAD) * h), int((b - PAD) * h), int(l * w), int(r * w))
            if box is None:
                break
            pad = int(PAD * h)
            box = (max(0, box[0] - pad), max(0, box[1] - pad), min(w, box[2] + pad), min(h, box[3] + pad))
            crop = page_img.crop(box)
            if fid in BAND_TURNS:
                crop = crop.rotate(BAND_TURNS[fid], expand=True)
            crops.append(crop)
        else:
            sheet = crops[0]
            for lower in crops[1:]:
                sheet = _stack(sheet, lower)
            sheet.save(raw_dir / f"fig_{fid}.png", format="PNG")

    records: list[dict[str, object]] = []
    seen: set[str] = set()
    img_re = re.compile(r"!\[([^\]]*)\]\(figures/fig_([0-9]+-[0-9]+)\.(?:png|svg)\)")
    for md_path in sorted(md_dir.glob("p_*.md")):
        page_num = int(md_path.stem.split("_")[1])
        text = md_path.read_text(encoding="utf-8")
        for m in img_re.finditer(text):
            alt_text, fig_id = m.group(1).strip(), m.group(2).strip()
            if fig_id in seen:
                continue
            seen.add(fig_id)
            ef = by_id.get(fig_id)
            source_page = ef.source_page if ef is not None else page_num
            band = next((b for p, b in BAND_OVERRIDES.get(fig_id, ()) if p == source_page), None)
            records.append(
                {
                    "id": fig_id,
                    "page": source_page,
                    "caption": SCAN_CAPTIONS.get(fig_id)
                    or (ef.caption if ef is not None else "")
                    or alt_text
                    or f"图 {fig_id}",
                    "box": band or (ef.box if ef is not None else None),
                }
            )
    return records


def figure_page_boxes(out_dir: Path) -> dict[int, list[tuple[float, float, float, float]]]:
    """Each scan page's figure art as page fractions: an overridden figure's bands, else the extractor's box."""
    boxes: dict[int, list[tuple[float, float, float, float]]] = {}
    for rec in json.loads((out_dir / FIGURES_MANIFEST_NAME).read_text(encoding="utf-8")):
        if rec["figure_id"] in BAND_OVERRIDES:
            for page, band in BAND_OVERRIDES[rec["figure_id"]]:
                boxes.setdefault(page, []).append(band)
        elif rec["box"]:
            boxes.setdefault(rec["source_page"], []).append(tuple(rec["box"]))
    return boxes


def figure_page_art(out_dir: Path) -> dict[int, list[FigureArt]]:
    """Each scan page's figure boxes with the figure's redrawn SVG: `FACSIMILE_BANDS` for a figure the extractor
    cut short, which the scan continues from the page before or prints sideways, else as in `figure_page_boxes`."""
    art: dict[int, list[FigureArt]] = {}
    for rec in json.loads((out_dir / FIGURES_MANIFEST_NAME).read_text(encoding="utf-8")):
        fid = rec["figure_id"]
        svg = out_dir / "figures_scan" / f"fig_{fid}.svg"
        if not svg.exists():
            svg = out_dir / "figures" / f"fig_{fid}.svg"
        if not svg.exists():
            continue
        bands = (
            FACSIMILE_BANDS.get(fid)
            or BAND_OVERRIDES.get(fid)
            or ([(rec["source_page"], tuple(rec["box"]))] if rec["box"] else [])
        )
        for page, band in bands:
            art.setdefault(page, []).append(FigureArt(fid, band, svg, FACSIMILE_TURNS.get(fid, 0)))
    return art


def crop_macro_figures(out_dir: Path) -> list[ExtractedFigure]:
    mono_dir = out_dir / "figures"
    mono_dir.mkdir(parents=True, exist_ok=True)

    figures: list[ExtractedFigure] = []
    records = extract_clean_raw_figures(out_dir)
    names = [f"fig_{rec['id']}.png" for rec in records]
    with ThreadPoolExecutor() as pool:
        _ = list(pool.map(lambda name: _clean_monochrome_raster(out_dir / "figures_raw" / name, mono_dir / name), names))
    for rec in records:
        fid = str(rec["id"])
        crop = mono_dir / f"fig_{fid}.png"
        with Image.open(crop) as im:
            width, height = im.size
        figures.append(
            ExtractedFigure(
                figure_id=fid,
                caption=str(rec["caption"]),
                image_rel_path=f"figures/fig_{fid}.png",
                source_page=int(rec["page"]),
                box=rec["box"],
                width_px=width,
                height_px=height,
            )
        )
    write_figures_manifest(out_dir / FIGURES_MANIFEST_NAME, figures)
    return figures
