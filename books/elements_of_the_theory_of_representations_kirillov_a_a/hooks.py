import re
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

from polytypst.books import book_by_key
from polytypst.parity.source import source_pdf
from polytypst.vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    write_figures_manifest,
)

FOLDER = Path(__file__).parent

_DROP_HEADINGS = re.compile(
    r"^(?:Translator's Preface|Preface|First Part\..*|Second Part\..*|Third Part\..*"
    r"|A Short Historical Sketch.*|Bibliography[¹]?|Subject Index)$",
    re.IGNORECASE,
)

_FIGURES: tuple[tuple[str, int, int, str, tuple[float, float, float, float], tuple[float, float, float, float] | None], ...] = (
    ("1", 88, 1, "Fig. 1", (95.0, 492.0, 390.0, 544.5), (95.0, 540.5, 132.0, 544.5)),
    ("2", 104, 1, "Fig. 2", (90.0, 226.0, 385.0, 293.0), None),
    ("3", 104, 1, "Fig. 3", (90.0, 350.0, 384.0, 382.0), None),
    ("4", 274, 3, "Fig. 4", (94.0, 156.0, 304.0, 323.0), None),
)


def heading_hook(lt: str, chapter: int) -> str | None:
    if not lt.startswith("#"):
        return None
    text = re.sub(r"^#+\s*", "", lt).strip()
    if _DROP_HEADINGS.match(text):
        return ""
    if re.match(r"^§\s*\d+\.\s+\S", text):
        return f"## {text}"
    if re.match(r"^\d+\.\d+\.\s+\S", text):
        return f"### {text}"
    if re.match(r"^[ab]\)\s+\S", text):
        return f"*{text}*"
    if lt.startswith("## "):
        return f"## {text}"
    return f"### {text}"


def draw_figures(out_dir: Path) -> list[Path]:
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    scan = pymupdf.open(source_pdf(book_by_key(FOLDER.name).spec))
    paths: list[Path] = []
    entries: list[ExtractedFigure] = []
    dpi = 600
    scale = dpi / 72.0
    for fid, pno, chap, caption, clip_box, mask_box in _FIGURES:
        page = scan[pno - 1]
        rect = pymupdf.Rect(*clip_box)
        w, h = page.rect.width, page.rect.height
        pix = page.get_pixmap(dpi=dpi, clip=rect)
        out_path = fig_dir / f"fig_{fid}.png"
        pix.save(out_path)
        if mask_box is not None:
            with Image.open(out_path) as im:
                draw = ImageDraw.Draw(im)
                mx0 = max(0, int((mask_box[0] - clip_box[0]) * scale))
                my0 = max(0, int((mask_box[1] - clip_box[1]) * scale))
                mx1 = min(im.width, int((mask_box[2] - clip_box[0]) * scale) + 1)
                my1 = min(im.height, int((mask_box[3] - clip_box[1]) * scale) + 1)
                draw.rectangle((mx0, my0, mx1, my1), fill=(255, 255, 255))
                im.save(out_path, dpi=(dpi, dpi))
        paths.append(out_path)
        entries.append(
            ExtractedFigure(
                figure_id=fid,
                caption=caption,
                image_rel_path=f"figures/fig_{fid}.png",
                source_page=pno,
                box=(rect.x0 / w, rect.y0 / h, rect.x1 / w, rect.y1 / h),
                width_px=pix.width,
                height_px=pix.height,
                chapter=chap,
            )
        )
    write_figures_manifest(out_dir / FIGURES_MANIFEST_NAME, entries)
    return paths
