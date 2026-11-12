import re
from pathlib import Path

import pymupdf

from polytypst.parity.source import source_pdf
from polytypst.vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    write_figures_manifest,
)

FOLDER = Path(__file__).parent

_DROP_HEADINGS = re.compile(
    r"^(?:Chapter\s+\d+\b.*|Book\s+\d+:.*|Basic Algebraic Geometry\s+2"
    r"|Schemes and Complex Manifolds|Preface to Books 2[–-]3|Schemes|Varieties"
    r"|The Topology of Algebraic Varieties|Complex Manifolds|Uniformisation"
    r"|Historical Sketch|References|Index)$",
    re.IGNORECASE,
)

_FIGURES: tuple[tuple[str, int, int, int, str], ...] = (
    ("22", 19, 0, 5, "Figure 22 a_phi : Spec(Z[i]) -> Spec Z"),
    ("23", 26, 0, 5, "Figure 23 a_phi : Spec(Z[sigma]/(sigma^2 - 1)) -> Spec Z"),
    ("24", 44, 0, 5, "Figure 24 The glueing conditions"),
    ("25", 88, 0, 6, "Figure 25 The first blowup"),
    ("26", 89, 0, 6, "Figure 26 The second blowup"),
    ("27", 91, 0, 6, "Figure 27 Hironaka's counterexample"),
    ("28", 119, 0, 6, "Figure 28 The affine cone"),
    ("29", 141, 0, 7, "Figure 29 The branch point z |-> z^k"),
    ("30", 143, 0, 7, "Figure 30 A triangulation of P^1(C)"),
    ("31", 149, 0, 7, "Figure 31 Subdivision of a triangulation"),
    ("32", 151, 0, 7, "Figure 32 A torus knot"),
    ("33", 229, 0, 9, "Figure 33 A fundamental polygon (the case g = 2)"),
)


def heading_hook(lt: str, chapter: int) -> str | None:
    if not lt.startswith("#"):
        return None
    text = re.sub(r"^#+\s*", "", lt).strip()
    if _DROP_HEADINGS.match(text):
        return ""
    if chapter == 0 and re.match(r"^\d+(?:\.\d+)?\s+\S", text):
        text = re.sub(r"^\d+(?:\.\d+)?\s+", "", text)
        return f"## {text}"
    if re.match(r"^\d+\.\d+\s+\S", text):
        return f"### {text}"
    if re.match(r"^\d+\s+\S", text):
        return f"## {text}"
    if lt.startswith("## "):
        return f"## {text}"
    return f"### {text}"


def draw_figures(out_dir: Path) -> list[Path]:
    from polytypst.books import book_by_key

    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    scan = pymupdf.open(source_pdf(book_by_key(FOLDER.name).spec))
    paths: list[Path] = []
    entries: list[ExtractedFigure] = []
    for fid, pno, idx, chap, caption in _FIGURES:
        page = scan[pno - 1]
        rects = sorted(
            (r for img in page.get_images(full=True) for r in page.get_image_rects(img[0])),
            key=lambda r: (round(r.y0, 1), round(r.x0, 1)),
        )
        rect = rects[idx]
        w, h = page.rect.width, page.rect.height
        pix = page.get_pixmap(dpi=600, clip=rect)
        out_path = fig_dir / f"fig_{fid}.png"
        pix.save(out_path)
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
