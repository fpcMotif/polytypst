from pathlib import Path

import pymupdf
from PIL import Image

from polytypst.edition import OUTPUT, Book, monograph_edition
from polytypst.parity.source import source_pdf

from .spec import NPL_CRISIS_ILLUSTRATED_SPEC, NPL_CRISIS_SPEC

OUT_DIR = OUTPUT / "4_不良债权与金融危机"

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
    scan = pymupdf.open(source_pdf(NPL_CRISIS_SPEC))
    paths = []
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
    return paths


BOOK = Book(
    NPL_CRISIS_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(
            NPL_CRISIS_SPEC, OUT_DIR, "12 chapters, monochrome academic monograph"
        ),
        "illustrated": monograph_edition(
            NPL_CRISIS_ILLUSTRATED_SPEC,
            OUT_DIR,
            "12 chapters, illustrated monograph with scan figures",
        ),
    },
    draw_figures,
)
