"""Optical parity: where a rebuilt page's ink differs from the scan's, found from the two page images alone.

Rebuilt ink with no scan ink within `MATCH_PT` is extra; scan ink the rebuilt page lacks is missing.
Nearby differing ink joins into one region, boxed in pt. The check reads no OCR and no text layer,
so it works for any edition whose pages map onto the scan's.
"""

import csv
import html
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pymupdf
from PIL import Image, ImageDraw

from .compare import _dilate, common_crop
from .report import write_overlay
from .words import EDGE_GAP_PT, PT_PER_PX, line_measure, page_ink, without_edge_lines

MATCH_PT = 1.0
MERGE_X_PT = 6.0
MERGE_Y_PT = 2.0
MIN_AREA_PT2 = 4.0
REGRESSION_SHARE = 0.002
CROP_DPI = 150
CROP_PAD_PT = 8.0
OVERLAY_DPI = 100
TOP_REGIONS = 100
LAYOUT_COLUMNS = 12
LAYOUT_INK_SHARE = 0.02
LAYOUT_LIMIT = 0.25
LINE_ROW_MIN_PX = 2
LINE_GAP_PX = 4
LINE_MIN_INK_PX = 40
DUST_LINE_SHARE = 0.4
COLOURS = {"extra": (0, 150, 210), "missing": (220, 0, 0)}


@dataclass(frozen=True)
class Region:
    """Differing ink: `extra` only in the rebuilt page, `missing` only on the scan; `box` is (left, top, right, bottom) pt."""

    kind: Literal["extra", "missing"]
    box: tuple[float, float, float, float]
    area_pt2: float


@dataclass(frozen=True)
class PageVisual:
    """One page's share of rebuilt ink not on the scan (`extra`), of scan ink not rebuilt (`missing`), and the regions."""

    source_page: int
    rebuilt_page: int
    extra: float
    missing: float
    regions: tuple[Region, ...] = ()
    layout: float = 0.0
    shift: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

    @property
    def score(self) -> float:
        return self.extra + self.missing

    @property
    def offset(self) -> float:
        """The largest move (pt) of one edge of the text block, rebuilt against scan."""
        return max(abs(d) for d in self.shift)


def _near(ink: np.ndarray) -> np.ndarray:
    out = ink
    for _ in range(round(MATCH_PT / PT_PER_PX)):
        out = _dilate(out)
    return out


def _runs(idx: np.ndarray, gap_px: int) -> list[np.ndarray]:
    return np.split(idx, np.flatnonzero(np.diff(idx) > gap_px) + 1) if idx.size else []


def _regions(mask: np.ndarray, kind: Literal["extra", "missing"]) -> list[Region]:
    out = []
    for band in _runs(np.flatnonzero(mask.any(axis=1)), round(MERGE_Y_PT / PT_PER_PX)):
        rows = mask[band[0] : band[-1] + 1]
        for run in _runs(np.flatnonzero(rows.any(axis=0)), round(MERGE_X_PT / PT_PER_PX)):
            block = rows[:, run[0] : run[-1] + 1]
            area = float(block.sum()) * PT_PER_PX**2
            if area < MIN_AREA_PT2:
                continue
            ys = np.flatnonzero(block.any(axis=1)) + band[0]
            box = (run[0] * PT_PER_PX, ys[0] * PT_PER_PX, (run[-1] + 1) * PT_PER_PX, (ys[-1] + 1) * PT_PER_PX)
            out.append(Region(kind, tuple(round(float(v), 2) for v in box), round(area, 1)))
    return out


def _masks(source: np.ndarray, rebuilt: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a, b = common_crop(source, rebuilt)
    return b & ~_near(a), a & ~_near(b)


def ink_regions(source: np.ndarray, rebuilt: np.ndarray) -> list[Region]:
    """The extra and missing regions of two page ink masks compared in place, largest first."""
    extra, missing = _masks(source, rebuilt)
    return sorted(_regions(extra, "extra") + _regions(missing, "missing"), key=lambda r: -r.area_pt2)


def _inked_cells(ink: np.ndarray, cell_px: int) -> np.ndarray:
    h, w = ink.shape[0] // cell_px * cell_px, ink.shape[1] // cell_px * cell_px
    cells = ink[:h, :w].reshape(h // cell_px, cell_px, w // cell_px, cell_px)
    return cells.mean(axis=(1, 3)) >= LAYOUT_INK_SHARE


def layout_share(source: np.ndarray, rebuilt: np.ndarray) -> float:
    a, b = common_crop(source, rebuilt)
    cell_px = max(1, a.shape[1] // LAYOUT_COLUMNS)
    ca, cb = _inked_cells(a, cell_px), _inked_cells(b, cell_px)
    union = int((ca | cb).sum())
    return round(float((ca ^ cb).sum() / union), 4) if union else 0.0


def _lines(ink: np.ndarray) -> list[tuple[int, int]]:
    rows = np.flatnonzero(ink.sum(axis=1) > LINE_ROW_MIN_PX)
    bands = [(int(r[0]), int(r[-1]) + 1) for r in _runs(rows, LINE_GAP_PX)]
    bands = [(a, b) for a, b in bands if ink[a:b].sum() > LINE_MIN_INK_PX]
    if not bands:
        return []
    height = float(np.median([b - a for a, b in bands]))
    while len(bands) > 1 and bands[0][1] - bands[0][0] < DUST_LINE_SHARE * height:
        bands.pop(0)
    while len(bands) > 1 and bands[-1][1] - bands[-1][0] < DUST_LINE_SHARE * height:
        bands.pop()
    return bands


def _line_extent(band: np.ndarray) -> tuple[int, int] | None:
    """First and last ink column of a text line, leaving out specks set apart from the text by `EDGE_GAP_PT`."""
    runs = [r for r in _runs(np.flatnonzero(band.any(axis=0)), round(EDGE_GAP_PT / PT_PER_PX))
            if band[:, r[0] : r[-1] + 1].sum() > LINE_MIN_INK_PX]
    return (int(runs[0][0]), int(runs[-1][-1])) if runs else None


def _edges(ink: np.ndarray) -> tuple[float, float, float, float]:
    lines = _lines(ink)
    if not lines:
        return (0.0, 0.0, 0.0, 0.0)
    extents = [ext for a, b in lines if (ext := _line_extent(ink[a:b])) is not None]
    if not extents:
        return (0.0, 0.0, 0.0, 0.0)
    starts, ends = zip(*extents, strict=True)
    left, right = line_measure([int(s) for s in starts], [int(e) + 1 for e in ends])
    return (left * PT_PER_PX, lines[0][0] * PT_PER_PX, right * PT_PER_PX, lines[-1][1] * PT_PER_PX)


def text_block_shift(source: np.ndarray, rebuilt: np.ndarray) -> tuple[float, float, float, float]:
    """How far (pt) each edge of the rebuilt text block (left, top, right, bottom) sits from the scan's.
    Top and bottom are the first and last text line, without dust lines thinner than `DUST_LINE_SHARE`
    of the median line; left and right come from the line starts and ends by `line_measure`."""
    a, b = common_crop(without_edge_lines(source), without_edge_lines(rebuilt))
    sa, sb = _edges(a), _edges(b)
    return (round(sb[0] - sa[0], 1), round(sb[1] - sa[1], 1), round(sb[2] - sa[2], 1), round(sb[3] - sa[3], 1))


def page_visual(source: np.ndarray, rebuilt: np.ndarray, source_page: int, rebuilt_page: int) -> PageVisual:
    extra, missing = _masks(source, rebuilt)
    a, b = common_crop(source, rebuilt)
    return PageVisual(
        source_page, rebuilt_page,
        round(float(extra.sum() / max(1, b.sum())), 4),
        round(float(missing.sum() / max(1, a.sum())), 4),
        tuple(ink_regions(source, rebuilt)),
        layout_share(source, rebuilt),
        text_block_shift(source, rebuilt),
    )


def layout_check(source: Path, rebuilt: Path, page_map: dict[int, list[int]]) -> dict[int, float]:
    src, ours = pymupdf.open(source), pymupdf.open(rebuilt)
    return {
        pno: layout_share(page_ink(src[pno - 1]), page_ink(ours[pages[0] - 1]))
        for pno, pages in sorted(page_map.items())
    }


def visual_check(source: Path, rebuilt: Path, page_map: dict[int, list[int]]) -> list[PageVisual]:
    """Optical parity of every mapped page, on the first rebuilt page each source page maps to."""
    src, ours = pymupdf.open(source), pymupdf.open(rebuilt)
    out = []
    for pno, pages in sorted(page_map.items()):
        out.append(page_visual(page_ink(src[pno - 1]), page_ink(ours[pages[0] - 1]), pno, pages[0]))
    return out


def compare_runs(new: list[PageVisual], old: list[PageVisual]) -> dict[str, list[int]]:
    """Source pages whose differing ink fell (`improved`) or rose (`regressed`) by more than `REGRESSION_SHARE`."""
    before = {p.source_page: p.score for p in old}
    changes: dict[str, list[int]] = {"improved": [], "regressed": []}
    for p in new:
        if p.source_page in before:
            delta = p.score - before[p.source_page]
            if delta > REGRESSION_SHARE:
                changes["regressed"].append(p.source_page)
            elif delta < -REGRESSION_SHARE:
                changes["improved"].append(p.source_page)
    return changes


def _crop(doc: pymupdf.Document, page: int, region: Region, path: Path) -> None:
    width = doc[page - 1].rect.width
    clip = pymupdf.Rect(0, region.box[1] - CROP_PAD_PT, width, region.box[3] + CROP_PAD_PT)
    pix = doc[page - 1].get_pixmap(dpi=CROP_DPI, clip=clip)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    k = CROP_DPI / 72
    left, top, right, bottom = region.box
    ImageDraw.Draw(img).rectangle(
        ((left - clip.x0) * k - 2, (top - clip.y0) * k - 2, (right - clip.x0) * k + 2, (bottom - clip.y0) * k + 2),
        outline=COLOURS[region.kind], width=2,
    )
    img.save(path)


def _gray(doc: pymupdf.Document, page: int) -> np.ndarray:
    pix = doc[page - 1].get_pixmap(dpi=OVERLAY_DPI, colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)


def write_visual_report(
    results: list[PageVisual], out_dir: Path, source: Path, rebuilt: Path,
    against: tuple[Path, list[PageVisual]] | None = None, top: int = TOP_REGIONS,
) -> dict[str, object]:
    """Write regions.csv, summary.json and index.html: crops of the book's `top` largest regions, then every
    differing page with its overlay, worst first. Returns the summary."""
    img = out_dir / "img"
    img.mkdir(parents=True, exist_ok=True)
    docs = {"scan": pymupdf.open(source), "rebuilt": pymupdf.open(rebuilt)}
    old = {p.source_page: p for p in against[1]} if against else {}
    if against:
        docs["before"] = pymupdf.open(against[0])
    changes = compare_runs(results, against[1]) if against else {}
    with (out_dir / "regions.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["source_page", "rebuilt_page", "kind", "left_pt", "top_pt", "right_pt", "bottom_pt", "area_pt2"])
        for p in results:
            for r in p.regions:
                writer.writerow([p.source_page, p.rebuilt_page, r.kind, *r.box, r.area_pt2])
    largest = sorted(((r, p) for p in results for r in p.regions), key=lambda rp: -rp[0].area_pt2)[:top]
    crops = []
    for n, (r, p) in enumerate(largest):
        cells = []
        for name, doc in docs.items():
            if name == "before" and p.source_page not in old:
                continue
            page = p.source_page if name == "scan" else old[p.source_page].rebuilt_page if name == "before" else p.rebuilt_page
            path = img / f"r{n:04d}_p{p.source_page:03d}_{name}.png"
            _crop(doc, page, r, path)
            cells.append(f'<figure><figcaption>{name}</figcaption><img loading="lazy" src="img/{path.name}"></figure>')
        crops.append(
            f'<div class="region {r.kind}"><b>#{n + 1} {r.kind}</b> source page {p.source_page}, '
            f'{r.area_pt2}pt² at {r.box}{"".join(cells)}</div>'
        )
    rows = []
    for p in sorted(results, key=lambda p: -p.score):
        if not p.regions and p.source_page not in old:
            continue
        stem = f"p{p.source_page:03d}"
        write_overlay(_gray(docs["scan"], p.source_page), _gray(docs["rebuilt"], p.rebuilt_page), img / f"{stem}_overlay.png")
        change = f" (before {old[p.source_page].score:.4f})" if p.source_page in old else ""
        tag = "regressed" if p.source_page in changes.get("regressed", []) else "improved" if p.source_page in changes.get("improved", []) else ""
        rows.append(
            f'<tr class="{tag}"><td class="meta"><b>source page {p.source_page}</b> {tag}<br>'
            f"extra {p.extra:.4f}, missing {p.missing:.4f}{html.escape(change)}<br>layout {p.layout:.4f}<br>"
            f"offset {p.offset:.1f}pt (left, top, right, bottom: {', '.join(f'{d:+.1f}' for d in p.shift)})<br>{len(p.regions)} regions</td>"
            f'<td><img class="overlay" loading="lazy" src="img/{stem}_overlay.png" alt="overlay {p.source_page}"></td></tr>'
        )
    summary: dict[str, object] = {
        "pages": len(results),
        "pages_with_regions": sum(1 for p in results if p.regions),
        "regions": {k: sum(1 for p in results for r in p.regions if r.kind == k) for k in ("extra", "missing")},
        "mean_extra": round(float(np.mean([p.extra for p in results])), 4) if results else 0.0,
        "mean_missing": round(float(np.mean([p.missing for p in results])), 4) if results else 0.0,
        "mean_layout": round(float(np.mean([p.layout for p in results])), 4) if results else 0.0,
        "max_offset": max((p.offset for p in results), default=0.0),
        "worst_pages": [asdict(p) | {"regions": len(p.regions)} for p in sorted(results, key=lambda p: -p.score)[:20]],
        "settings": {"match_pt": MATCH_PT, "merge_x_pt": MERGE_X_PT, "merge_y_pt": MERGE_Y_PT, "min_area_pt2": MIN_AREA_PT2,
                     "layout_columns": LAYOUT_COLUMNS, "layout_ink_share": LAYOUT_INK_SHARE},
    }
    if against:
        summary |= {"against": str(against[0]), **changes}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (out_dir / "index.html").write_text(_page_html(summary, "".join(crops), "".join(rows)), encoding="utf-8")
    return summary


def _page_html(summary: dict[str, object], crops: str, rows: str) -> str:
    regions = summary["regions"]
    changes = ""
    if "against" in summary:
        changes = f"<p>Against {html.escape(str(summary['against']))}: {len(summary['improved'])} pages improved, {len(summary['regressed'])} regressed.</p>"
    return f"""<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Optical parity</title>
<style>
body {{ font: 14px system-ui, sans-serif; margin: 16px; background: #fff; color: #111; }}
table {{ border-collapse: collapse; }}
td {{ border-bottom: 1px solid #ddd; padding: 8px; vertical-align: top; }}
.meta {{ font-size: 12px; color: #444; width: 240px; }}
img {{ max-width: 100%; height: auto; display: block; }}
img.overlay {{ width: 220px; margin-top: 8px; border: 1px solid #eee; }}
.region {{ margin-bottom: 12px; font-size: 12px; }}
.region.extra b {{ color: #0096d2; }} .region.missing b {{ color: #dc0000; }}
figure {{ margin: 2px 0; }} figcaption {{ font-size: 11px; color: #666; }}
tr.regressed .meta b {{ color: #dc0000; }} tr.improved .meta b {{ color: #080; }}
</style>
<h1>Optical parity</h1>
<p>{summary["pages_with_regions"]} of {summary["pages"]} pages differ from the scan: {regions["extra"]} extra regions
(blue box: rebuilt ink with no scan ink within {MATCH_PT}pt) and {regions["missing"]} missing regions (red box: scan ink not rebuilt).
Mean share per page: {summary["mean_extra"]} extra, {summary["mean_missing"]} missing,
{summary["mean_layout"]} layout (cells of a {LAYOUT_COLUMNS}-column grid inked on one page only, over cells inked on either).
Largest text block offset: {summary["max_offset"]}pt (the furthest any edge of a page's rebuilt ink sits from the scan's).</p>
{changes}
<h2>Largest regions</h2>
{crops}
<h2>Pages, worst first</h2>
<p>Overlay: red ink only on the scan, cyan only in the rebuilt page, black in both.</p>
<table><tbody>{rows}</tbody></table>
"""
