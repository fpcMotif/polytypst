from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image

from ..book_state import book_state
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
    "9-1": [(297, (0.04, 0.285, 0.96, 0.409))],
    "10-12": [(338, (0.04, 0.118, 0.96, 0.489))],
    "11-6": [(365, (0.04, 0.625, 0.96, 0.880))],
}


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
            crops.append(page_img.crop(box))
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
            records.append(
                {
                    "id": fig_id,
                    "page": ef.source_page if ef is not None else page_num,
                    "caption": SCAN_CAPTIONS.get(fig_id)
                    or (ef.caption if ef is not None else "")
                    or alt_text
                    or f"图 {fig_id}",
                    "box": ef.box if ef is not None else None,
                }
            )
    return records


def crop_macro_figures(out_dir: Path) -> list[ExtractedFigure]:
    mono_dir = out_dir / "figures"
    mono_dir.mkdir(parents=True, exist_ok=True)

    figures: list[ExtractedFigure] = []
    for rec in extract_clean_raw_figures(out_dir):
        fid = str(rec["id"])
        crop = mono_dir / f"fig_{fid}.png"
        _clean_monochrome_raster(out_dir / "figures_raw" / f"fig_{fid}.png", crop)
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
