import re
import tomllib
from dataclasses import replace
from pathlib import Path

import pymupdf
from PIL import Image

from polytypst.parity.source import source_pdf
from polytypst.vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    load_figures_manifest,
    write_figures_manifest,
)

FOLDER = Path(__file__).parent
_BOOK = tomllib.loads((FOLDER / "book.toml").read_text(encoding="utf-8"))
RUNNING_HEADER_REGEXES = tuple(_BOOK["running_header_regexes"])
CHAPTERS = _BOOK["chapters"]

BYLINES = {
    1: "樱川昌哉 樱川幸恵",
    2: "山崎福寿",
    3: "池尾和人",
    4: "田中亘",
    5: "深尾光洋",
    6: "植村信保",
    7: "久米郁男",
    8: "西村吉正",
    9: "深尾光洋",
    10: "小川一夫",
    11: "樱川昌哉 渡边善次",
    12: "吉野直行 饭岛高雄",
}
TOP_LEVEL_HEADINGS = re.compile(r"^(?:导\s*语|参考文献|附录\s*\d|补充说明)")
TABLE_TITLE = re.compile(r"^(?:附)?表\s*\d+[-.]\d+")


def npl_heading_hook(lt: str, chapter: int) -> str | None:
    """Sections become `##`, subsections `###`; chapter titles, subtitles and running heads drop; bylines stay text.

    The shared cleaner drops a `###` heading that any earlier chapter already had, which loses each
    chapter's "导 语" and "1 前言", so every heading line returns here."""
    text = re.sub(r"^#+\s*", "", lt).strip()
    if any(re.match(rx, lt) for rx in RUNNING_HEADER_REGEXES):
        return ""
    if not chapter and any(c["title"] == text for c in CHAPTERS):
        return ""
    title = next((c["title"] for c in CHAPTERS if c["number"] == chapter and chapter), "")
    if chapter and re.match(rf"^{chapter}\s+", text) and title.startswith(re.sub(r"^\d+\s+|①$", "", text)):
        return ""
    if text.startswith("——") and title.endswith(text.split("（")[0]):
        return ""
    if text == BYLINES.get(chapter):
        return text
    if not lt.startswith("#") or TABLE_TITLE.match(text):
        return text if lt.startswith("#") else None
    if re.match(r"^\d+\.\d+\s", text):
        return f"### {text}"
    if re.match(r"^\d+\s+\D", text) or TOP_LEVEL_HEADINGS.match(text):
        return f"## {text}"
    return f"### {text}"


# Scan page and (x0, y0, x1, y1) page fractions of each figure whose automatic crop missed its chart.
# 图 9-29 stacks panels ① and ② from one page above panel ③ from the next.
RECROPS = {
    "2-1": ((70, (0.11, 0.11, 0.91, 0.44)),),
    "5-2": ((157, (0.15, 0.235, 0.84, 0.528)),),
    "8-3": ((244, (0.13, 0.262, 0.86, 0.529)),),
    "9-16": ((273, (0.17, 0.567, 0.87, 0.815)),),
    "9-19": ((275, (0.15, 0.622, 0.84, 0.877)),),
    "9-22": ((280, (0.17, 0.115, 0.84, 0.37)),),
    "9-29": ((290, (0.14, 0.315, 0.85, 0.845)), (291, (0.14, 0.127, 0.85, 0.375))),
}


def draw_figures(out_dir: Path) -> list[Path]:
    from polytypst.books import book_by_key

    scan = pymupdf.open(source_pdf(book_by_key(FOLDER.name).spec))
    paths = []
    sheets: dict[str, tuple[tuple[float, float, float, float], tuple[int, int]]] = {}
    for fig_id, boxes in RECROPS.items():
        panels = []
        for number, (x0, y0, x1, y1) in boxes:
            page = scan[number - 1]
            w, h = page.rect.width, page.rect.height
            pix = page.get_pixmap(dpi=600, colorspace=pymupdf.csGRAY, clip=pymupdf.Rect(x0 * w, y0 * h, x1 * w, y1 * h))
            panels.append(Image.frombytes("L", (pix.width, pix.height), pix.samples))
        sheet = Image.new("L", (max(p.width for p in panels), sum(p.height for p in panels)), 255)
        top = 0
        for panel in panels:
            sheet.paste(panel, (0, top))
            top += panel.height
        path = out_dir / "figures" / f"fig_{fig_id}.png"
        sheet.save(path)
        paths.append(path)
        sheets[fig_id] = (_stacked_box([box for _, box in boxes]), sheet.size)
    manifest = out_dir / FIGURES_MANIFEST_NAME
    if manifest.exists():
        write_figures_manifest(
            manifest,
            [
                replace(f, box=sheets[f.figure_id][0], width_px=sheets[f.figure_id][1][0], height_px=sheets[f.figure_id][1][1])
                if f.figure_id in sheets
                else f
                for f in load_figures_manifest(manifest)
            ],
        )
    return paths


def _stacked_box(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    top = boxes[0][1]
    return (min(b[0] for b in boxes), top, max(b[2] for b in boxes), top + sum(b[3] - b[1] for b in boxes))
