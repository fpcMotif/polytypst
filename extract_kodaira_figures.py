"""High-precision 300-DPI diagram cropper for Kunihiko Kodaira's Complex Analysis.

Locates every standalone `Fig. X.Y` caption across all pages and crops the diagram
above each caption using horizontal whitespace band isolation and tight ink bounding boxes.
"""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import pymupdf
from PIL import Image

from polytypst.ocr.apple_vision import AppleVisionOCREngine


@dataclass
class KodairaFigure:
    fig_id: str  # e.g. "1_1"
    fig_label: str  # e.g. "Fig. 1.1"
    pdf_page: int
    image_rel_path: str
    width_px: int
    height_px: int


def find_whitespace_isolated_diagram(
    img: Image.Image,
    cap_top_px: int,
    upper_bound_px: int,
    pad_px: int = 18,
) -> tuple[int, int, int, int] | None:
    """Find tight (left, top, right, bottom) ink box of diagram above cap_top_px."""
    gray = img.convert("L")
    w, h = gray.size
    pixels = gray.load()
    if pixels is None:
        return None

    x_margin = int(w * 0.06)
    scan_bot = max(upper_bound_px + 10, min(h - 1, cap_top_px - 4))
    scan_top = max(int(h * 0.065), upper_bound_px + 4)
    if scan_bot <= scan_top + 20:
        return None

    # Compute dark pixel count per row in [scan_top, scan_bot]
    row_dark: list[int] = []
    for y in range(scan_top, scan_bot):
        cnt = 0
        for x in range(x_margin, w - x_margin, 2):
            val = pixels[x, y]
            if isinstance(val, (int, float)) and val < 190:
                cnt += 1
        row_dark.append(cnt)

    # Find bottom of diagram (first dark row going upward from scan_bot)
    rel_bot = len(row_dark) - 1
    while rel_bot >= 0 and row_dark[rel_bot] <= 1:
        rel_bot -= 1
    if rel_bot < 10:
        return None

    # Walk upward through diagram; if we hit a wide whitespace gap (>= 28 empty rows)
    # after having seen substantial diagram height (>= 50 rows), check if above is prose
    rel_top = rel_bot
    empty_run = 0
    best_top = 0
    for r in range(rel_bot, -1, -1):
        if row_dark[r] == 0:
            empty_run += 1
            if (rel_bot - r) >= 70 and empty_run >= 34:
                best_top = r + empty_run
                break
        else:
            empty_run = 0
            best_top = r

    y0 = scan_top + best_top
    y1 = scan_top + rel_bot + 1

    # Now find horizontal ink bounds in [y0, y1]
    min_x = w
    max_x = 0
    min_y = y1
    max_y = y0
    for y in range(y0, y1):
        for x in range(x_margin, w - x_margin):
            val = pixels[x, y]
            if isinstance(val, (int, float)) and val < 190:
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

    if max_x <= min_x + 15 or max_y <= min_y + 15:
        return None

    return (
        max(0, min_x - pad_px),
        max(0, min_y - pad_px),
        min(w, max_x + pad_px),
        min(h, max_y + pad_px),
    )


def extract_all_kodaira_figures(
    pdf_path: Path,
    renders_dir: Path,
    figs_dir: Path,
) -> list[KodairaFigure]:
    figs_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    vision_engine = AppleVisionOCREngine(languages=["en-US"])

    # Step 1: Collect candidate pages and captions from PDF text layer + text references
    cap_re = re.compile(r"^Fig\.\s*(\d+\.\d+[a-z]?)\.?\s*$", re.IGNORECASE)
    mention_re = re.compile(r"Fig\.\s*(\d+\.\d+[a-z]?)", re.IGNORECASE)

    # Map page -> list of (fig_num_str, cap_top_frac, upper_prose_bot_frac)
    extracted: list[KodairaFigure] = []
    seen_ids: set[str] = set()

    # Check which pages have Fig mentions or gaps
    pages_to_scan: set[int] = set()
    for pno in range(12, 413):
        t = doc[pno - 1].get_text()
        if "Fig" in t or "fig" in t:
            pages_to_scan.add(pno)
            pages_to_scan.add(max(12, pno - 1))
            pages_to_scan.add(min(412, pno + 1))

    for pno in sorted(pages_to_scan):
        png_path = renders_dir / f"p_{pno:03d}.png"
        if not png_path.exists():
            continue

        with Image.open(png_path) as im:
            w_px, h_px = im.size

        # First check PyMuPDF dict lines
        page_caps: list[tuple[str, float]] = []
        prose_bottoms: list[float] = [0.072]  # Running header bottom (~7.2% from top)

        d = doc[pno - 1].get_text("dict")
        pw = float(doc[pno - 1].rect.width)
        ph = float(doc[pno - 1].rect.height)

        for b in d.get("blocks", []):
            if b.get("type") != 0:
                continue
            for l in b.get("lines", []):
                txt = "".join(str(s.get("text", "")) for s in l.get("spans", [])).strip()
                bbox = l.get("bbox", (0.0, 0.0, 0.0, 0.0))
                x0, y0, x1, y1 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                m = cap_re.match(txt)
                if m:
                    page_caps.append((m.group(1), y0 / ph))
                elif (x1 - x0) > 0.48 * pw and len(txt) > 28 and y0 > 0.07 * ph:
                    prose_bottoms.append(y1 / ph)

        # Also run Apple Vision on pages where a figure might have been missed by PDF OCR
        ocr_page = vision_engine.recognize_page(png_path, pno)
        for ol in ocr_page.lines:
            txt = ol.text.strip()
            m = cap_re.match(txt)
            # Apple Vision y is from bottom (0=bottom, 1=top) -> top_frac = 1.0 - (ol.y + ol.h)
            top_frac = 1.0 - (ol.y + ol.h)
            bot_frac = 1.0 - ol.y
            if m:
                fnum = m.group(1)
                if not any(existing[0] == fnum for existing in page_caps):
                    page_caps.append((fnum, top_frac))
            elif ol.w > 0.48 and len(txt) > 28 and top_frac > 0.07:
                prose_bottoms.append(bot_frac)

        if not page_caps:
            continue

        page_caps.sort(key=lambda item: item[1])
        prose_bottoms.sort()

        with Image.open(png_path) as im:
            for idx, (fnum, cap_top_frac) in enumerate(page_caps):
                fid = fnum.replace(".", "_")
                if fid in seen_ids:
                    continue

                # Upper bound is the lowest prose bottom or previous caption bottom above cap_top_frac
                upper_frac = 0.072
                for pb in prose_bottoms:
                    if pb < cap_top_frac - 0.04:
                        upper_frac = max(upper_frac, pb)
                if idx > 0:
                    prev_cap_bot = page_caps[idx - 1][1] + 0.022
                    if prev_cap_bot < cap_top_frac - 0.04:
                        upper_frac = max(upper_frac, prev_cap_bot)

                cap_top_px = int(cap_top_frac * h_px)
                upper_px = int(upper_frac * h_px)

                box = find_whitespace_isolated_diagram(im, cap_top_px, upper_px)
                if box is None:
                    # Fallback box above caption
                    box = (
                        int(w_px * 0.12),
                        max(int(h_px * 0.075), upper_px + 8),
                        int(w_px * 0.88),
                        max(upper_px + 40, cap_top_px - 6),
                    )

                cropped = im.crop(box)
                out_name = f"fig_{fid}.png"
                out_path = figs_dir / out_name
                cropped.save(out_path, format="PNG")
                seen_ids.add(fid)
                extracted.append(
                    KodairaFigure(
                        fig_id=fid,
                        fig_label=f"Fig. {fnum}",
                        pdf_page=pno,
                        image_rel_path=f"figures/{out_name}",
                        width_px=cropped.width,
                        height_px=cropped.height,
                    )
                )

    manifest_path = figs_dir.parent / "figures_manifest.json"
    manifest_path.write_text(
        json.dumps([asdict(f) for f in extracted], indent=2),
        encoding="utf-8",
    )
    print(f"Extracted {len(extracted)} figures to {figs_dir} (manifest: {manifest_path})")
    return extracted


if __name__ == "__main__":
    extract_all_kodaira_figures(
        pdf_path=Path("/Users/martinfan/Downloads/Complex Analysis ( etc.).pdf"),
        renders_dir=Path("output/kodaira/page_renders"),
        figs_dir=Path("output/kodaira/figures"),
    )
