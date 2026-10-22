"""Universal figure and diagram extractor for scanned and digital PDFs."""

import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path
from typing import Any, final

import numpy as np
import pymupdf
from PIL import Image

from ..ocr.lines import DEFAULT_OCR_LANGUAGES, LineStore, line_reader
from ..ocr.pages import LinePage, LineReader, OcrLine, page_images
from ..ocr.transcripts import TranscriptStore
from .cropper import HighDPICropper

FIGURES_MANIFEST_NAME = "figures_manifest.json"
MIN_FIGURE_INK_RATIO = 0.002


def _crop_ink_ratio(img: Image.Image) -> float:
    """Share of dark pixels in a crop; near-zero means blank paper, not a diagram."""
    gray = img.convert("L")
    dark = sum(gray.histogram()[:200])
    return dark / max(1, gray.width * gray.height)


@dataclass
class ExtractedFigure:
    figure_id: str
    caption: str
    image_rel_path: str
    source_page: int
    box: tuple[float, float, float, float] | None = None
    width_px: int = 0
    height_px: int = 0


def write_figures_manifest(path: Path, figures: list[ExtractedFigure]) -> None:
    _ = path.write_text(
        json.dumps([asdict(f) for f in figures], indent=2),
        encoding="utf-8",
    )


def load_figures_manifest(path: Path) -> list[ExtractedFigure]:
    figures: list[ExtractedFigure] = []
    for item in json.loads(path.read_text(encoding="utf-8")):
        box = item.get("box")
        figures.append(
            ExtractedFigure(
                figure_id=str(item["figure_id"]),
                caption=str(item["caption"]),
                image_rel_path=str(item["image_rel_path"]),
                source_page=int(item["source_page"]),
                box=(float(box[0]), float(box[1]), float(box[2]), float(box[3]))
                if box
                else None,
                width_px=int(item.get("width_px", 0)),
                height_px=int(item.get("height_px", 0)),
            )
        )
    return figures


def load_complete_figures_manifest(path: Path) -> list[ExtractedFigure] | None:
    if not path.exists():
        return None
    figures = load_figures_manifest(path)
    if figures and all((path.parent / f.image_rel_path).exists() for f in figures):
        return figures
    return None


def _text_layer_rows(
    page_dict: dict[str, Any],
) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Text-layer lines, with pieces on one baseline and close together joined."""
    pieces: list[tuple[str, tuple[float, float, float, float]]] = []
    for b in page_dict.get("blocks", []):
        if b.get("type") != 0:
            continue
        for line in b.get("lines", []):
            txt = "".join(str(s.get("text", "")) for s in line.get("spans", []))
            x0, y0, x1, y1 = (float(v) for v in line.get("bbox", (0, 0, 0, 0)))
            if txt.strip():
                pieces.append((txt.strip(), (x0, y0, x1, y1)))
    pieces.sort(key=lambda p: (round(p[1][1] / 3), p[1][0]))
    rows: list[tuple[str, tuple[float, float, float, float]]] = []
    for txt, box in pieces:
        if rows:
            prev_txt, prev = rows[-1]
            if abs(prev[1] - box[1]) < 3 and 0 <= box[0] - prev[2] < 30:
                rows[-1] = (
                    f"{prev_txt} {txt}",
                    (prev[0], min(prev[1], box[1]), box[2], max(prev[3], box[3])),
                )
                continue
        rows.append((txt, box))
    return rows


def _caption_column(
    page_caps: list[tuple[str, float, float]], idx: int, w_px: int
) -> tuple[int, int] | None:
    """Pixel x-range of a caption's figure when another caption shares its row."""
    _, top, cx = page_caps[idx]
    peers = sorted(c for _, t, c in page_caps if abs(t - top) < 0.02)
    if len(peers) < 2:
        return None
    pos = peers.index(cx)
    lo = 0.06 if pos == 0 else (peers[pos - 1] + cx) / 2
    hi = 0.94 if pos == len(peers) - 1 else (cx + peers[pos + 1]) / 2
    return int(lo * w_px), int(hi * w_px)


def find_whitespace_isolated_diagram(
    img: Image.Image,
    cap_top_px: int,
    upper_bound_px: int,
    pad_px: int = 18,
    x_range_px: tuple[int, int] | None = None,
) -> tuple[int, int, int, int] | None:
    """Find tight (left, top, right, bottom) ink box of diagram above cap_top_px."""
    gray = np.asarray(img.convert("L"))
    h, w = gray.shape

    x_margin = int(w * 0.06)
    x_lo, x_hi = x_range_px or (x_margin, w - x_margin)
    scan_bot = max(upper_bound_px + 10, min(h - 1, cap_top_px - 4))
    scan_top = max(int(h * 0.065), upper_bound_px + 4)
    if scan_bot <= scan_top + 20:
        return None

    band_ink = gray[scan_top:scan_bot, x_lo:x_hi] < 190
    row_dark: list[int] = band_ink[:, ::2].sum(axis=1).tolist()

    rel_bot = len(row_dark) - 1
    while rel_bot >= 0 and row_dark[rel_bot] <= 1:
        rel_bot -= 1
    if rel_bot < 10:
        return None

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

    ys, xs = np.nonzero(band_ink[best_top : rel_bot + 1])
    if ys.size == 0:
        return None
    min_x = x_lo + int(xs.min())
    max_x = x_lo + int(xs.max())
    min_y = scan_top + best_top + int(ys.min())
    max_y = scan_top + best_top + int(ys.max())

    if max_x <= min_x + 15 or max_y <= min_y + 15:
        return None

    return (
        max(0, min_x - pad_px),
        max(0, min_y - pad_px),
        min(w, max_x + pad_px),
        min(h, max_y + pad_px),
    )


@final
class FigureExtractor:
    """Detects, crops, and catalogues figures and diagrams from any PDF (scanned or digital)."""

    FIGURE_CAPTION_REGEX: re.Pattern[str] = re.compile(
        r"^\s*(FIG|Fig|Figure|FIO|Fia|FIQ|F1G|F10|PIG|PI0|PIO|FG|FI|Abbildung|图)[\.,]?\s*([0-9]+(?:\s*,\s*[a-zA-Z]|\.[0-9]+[a-zA-Z]?|[A-Za-z0-9\-\.]*)?)\s*$",
        re.IGNORECASE,
    )

    def __init__(self, pdf_path: Path, reader: LineReader | None = None) -> None:
        self.pdf_path: Path = Path(pdf_path)
        self.cropper: HighDPICropper = HighDPICropper(self.pdf_path)
        self.reader: LineReader = reader or line_reader(DEFAULT_OCR_LANGUAGES)

    @staticmethod
    def detect_figure_box(
        page_lines: Sequence[OcrLine],
        cap_line: OcrLine,
    ) -> tuple[float, float, float, float]:
        """Determine normalized (left, top, right, bottom) bounding box for diagram from Apple Vision lines."""
        cap_cx = cap_line.x + cap_line.w / 2.0
        cap_y = cap_line.y

        # Side-by-side text lines typically occupy roughly half page width
        column_lines = [
            l for l in page_lines if 0.18 <= l.w <= 0.58 and abs(l.y - cap_y) < 0.28
        ]

        if cap_cx < 0.42 and column_lines:
            # Left side figure, body text on right
            right_body = [l for l in column_lines if l.x > 0.28]
            if right_body:
                y_max = max(l.y + l.h for l in right_body)
                y_min = min(cap_y, min(l.y for l in right_body))
                x_right_bound = min(l.x for l in right_body)
                return (
                    0.05,
                    max(0.0, 1.0 - (y_max + 0.03)),
                    min(0.55, x_right_bound - 0.01),
                    min(1.0, 1.0 - (y_min - 0.03)),
                )
        elif cap_cx > 0.52 and column_lines:
            # Right side figure, body text on left
            left_body = [l for l in column_lines if l.x < 0.28]
            if left_body:
                y_max = max(l.y + l.h for l in left_body)
                y_min = min(cap_y, min(l.y for l in left_body))
                x_left_bound = max(l.x + l.w for l in left_body)
                return (
                    max(0.38, x_left_bound + 0.01),
                    max(0.0, 1.0 - (y_max + 0.03)),
                    0.95,
                    min(1.0, 1.0 - (y_min - 0.03)),
                )

        # Block figure spanning across text column
        body_lines = [l for l in page_lines if l.w > 0.25]
        lines_above = [l for l in body_lines if l.y > cap_y + 0.03]
        y_top_limit = min(l.y for l in lines_above) if lines_above else (cap_y + 0.35)

        return (
            0.08,
            max(0.0, 1.0 - (y_top_limit + 0.02)),
            0.92,
            min(1.0, 1.0 - max(0.0, cap_y - 0.02)),
        )

    def extract_figures_from_digital_pdf(self, out_dir: Path) -> list[ExtractedFigure]:
        """Extract standalone embedded raster images from digital PDFs."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        figures: list[ExtractedFigure] = []

        doc = pymupdf.open(self.pdf_path)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            pno = page_idx + 1
            images = page.get_images()
            for idx, img_info in enumerate(images):
                xref = img_info[0]
                base_img = doc.extract_image(xref)
                if not base_img:
                    continue
                w = int(base_img.get("width", 0))
                h = int(base_img.get("height", 0))
                ext = str(base_img.get("ext", "png"))

                # Skip tiny icons or full-page backgrounds
                if w < 60 or h < 60:
                    continue
                # If image is a full page background scan, don't treat as standalone figure
                if w * h > 0.88 * (page.rect.width * page.rect.height * 4):
                    continue

                fig_name = f"fig_p{pno:03d}_{idx + 1}.{ext}"
                fig_path = out_dir / fig_name
                _ = fig_path.write_bytes(bytes(base_img["image"]))

                figures.append(
                    ExtractedFigure(
                        figure_id=f"p{pno}_{idx + 1}",
                        caption=f"Figure on page {pno}",
                        image_rel_path=f"figures/{fig_name}",
                        source_page=pno,
                        width_px=w,
                        height_px=h,
                    )
                )
        return figures

    def extract_whitespace_isolated_figures(
        self,
        renders_dir: Path,
        out_dir: Path,
        pages: range | None = None,
    ) -> list[ExtractedFigure]:
        """Extract diagrams above standalone Fig. X.Y captions using whitespace band isolation."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        doc = pymupdf.open(self.pdf_path)
        if pages is None:
            pages = range(1, len(doc) + 1)
        cap_re = re.compile(
            r"^(?:FIG|Fig|Figure)\.?\s*(\d+[\.\-]\d+[a-z]?)(?:\.?\s*$|\.\s+\S)",
            re.IGNORECASE,
        )

        extracted: list[ExtractedFigure] = []
        seen_ids: set[str] = set()
        pages_to_scan: set[int] = set()
        transcripts = TranscriptStore(out_dir.parent / "markdown_pages")
        for pno in pages:
            t = doc[pno - 1].get_text()
            md_txt = transcripts.text(pno) or ""
            if (
                "Fig" in t
                or "fig" in t
                or "FIG" in t
                or "Fig" in md_txt
                or "FIG" in md_txt
            ):
                pages_to_scan.update(p for p in (pno - 1, pno, pno + 1) if p in pages)

        renders = [page for page in page_images(renders_dir) if page.number in pages_to_scan]
        page_lines = LineStore(out_dir.parent / "source_ocr").read(renders, self.reader)
        for pno, png_path in ((page.number, page.path) for page in renders):
            with Image.open(png_path) as im:
                w_px, h_px = im.size

            page_caps: list[tuple[str, float, float]] = []
            prose_bottoms: list[float] = [0.072]

            d = doc[pno - 1].get_text("dict")
            pw = float(doc[pno - 1].rect.width)
            ph = float(doc[pno - 1].rect.height)

            for txt, (x0, y0, x1, y1) in _text_layer_rows(d):
                m = cap_re.match(txt)
                if m and (x1 - x0) < 0.7 * pw:
                    page_caps.append((m.group(1), y0 / ph, (x0 + x1) / 2 / pw))
                elif (x1 - x0) > 0.48 * pw and len(txt) > 28 and y0 > 0.07 * ph:
                    prose_bottoms.append(y1 / ph)

            for ol in page_lines.get(pno, ()):
                txt = ol.text.strip()
                m = cap_re.match(txt)
                top_frac = 1.0 - (ol.y + ol.h)
                bot_frac = 1.0 - ol.y
                if m and ol.w < 0.7:
                    fnum = m.group(1)
                    if not any(existing[0] == fnum for existing in page_caps):
                        page_caps.append((fnum, top_frac, ol.x + ol.w / 2))
                elif ol.w > 0.48 and len(txt) > 28 and top_frac > 0.07:
                    prose_bottoms.append(bot_frac)

            if not page_caps:
                continue

            page_caps.sort(key=lambda item: item[1])
            prose_bottoms.sort()

            with Image.open(png_path) as im:
                for idx, (fnum, cap_top_frac, _) in enumerate(page_caps):
                    fid = re.sub(r"[^0-9A-Za-z_]", "_", fnum)
                    if fid in seen_ids:
                        continue

                    upper_frac = 0.072
                    for pb in prose_bottoms:
                        if pb < cap_top_frac - 0.04:
                            upper_frac = max(upper_frac, pb)
                    for _, other_top, _ in page_caps[:idx]:
                        if other_top + 0.022 < cap_top_frac - 0.04:
                            upper_frac = max(upper_frac, other_top + 0.022)

                    cap_top_px = int(cap_top_frac * h_px)
                    upper_px = int(upper_frac * h_px)
                    x_range = _caption_column(page_caps, idx, w_px)

                    box_px = find_whitespace_isolated_diagram(
                        im, cap_top_px, upper_px, x_range_px=x_range
                    )
                    if box_px is None:
                        lo, hi = x_range or (int(w_px * 0.12), int(w_px * 0.88))
                        box_px = (
                            lo,
                            max(int(h_px * 0.075), upper_px + 8),
                            hi,
                            max(upper_px + 40, cap_top_px - 6),
                        )

                    cropped = im.crop(box_px)
                    if _crop_ink_ratio(cropped) < MIN_FIGURE_INK_RATIO:
                        continue
                    out_name = f"fig_{fid}.png"
                    out_path = out_dir / out_name
                    cropped.save(out_path, format="PNG")
                    seen_ids.add(fid)
                    extracted.append(
                        ExtractedFigure(
                            figure_id=fid,
                            caption=f"Fig. {fnum}",
                            image_rel_path=f"figures/{out_name}",
                            source_page=pno,
                            width_px=cropped.width,
                            height_px=cropped.height,
                        )
                    )

        return extracted

    def extract_figures_from_ocr_pages(
        self,
        ocr_pages: Sequence[LinePage],
        out_dir: Path,
        dpi: int = 300,
    ) -> list[ExtractedFigure]:
        """Extract diagrams from scanned pages using OCR caption coordinates and HighDPICropper."""
        from .typesafe_jev import TypeSafeJevVision

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        figures: list[ExtractedFigure] = []
        seen_ids: set[str] = set()
        jev = TypeSafeJevVision()

        for page in ocr_pages:
            pno = page.number
            for line in page.lines:
                if line.w > 0.35:
                    continue
                m = self.FIGURE_CAPTION_REGEX.match(line.text.strip())
                if not m:
                    continue

                raw_label = m.group(2).strip().rstrip(".:;,")
                raw_label_clean = re.sub(r"\s*,\s*", ", ", raw_label)
                fig_id = re.sub(r"[^0-9A-Za-z_-]", "_", raw_label_clean).strip("_")
                fig_id = re.sub(r"_+", "_", fig_id)
                if not fig_id or fig_id in seen_ids:
                    continue
                seen_ids.add(fig_id)

                box = self.detect_figure_box(page.lines, line)
                fig_filename = f"fig_{fig_id}.png"
                dest_path = out_dir / fig_filename

                page_png: Path | None = None
                for sub, suffix in product(("page_renders", "pages", "renders"), (".png", ".jpg")):
                    cand = out_dir.parent / sub / f"p_{pno:03d}{suffix}"
                    if cand.exists():
                        page_png = cand
                        break

                try:
                    if page_png is not None and jev.api_key:
                        det = jev.detect_diagram(
                            page_png, fig_label=f"FIG. {raw_label_clean}"
                        )
                        if det.has_diagram and det.box:
                            box = det.box
                            _ = TypeSafeJevVision.crop_pure_diagram(
                                page_png, det, dest_path, ocr_lines=page.lines, reader=self.reader
                            )
                        else:
                            _ = self.cropper.crop_figure(
                                page_num=pno,
                                box=box,
                                out_path=dest_path,
                                dpi=dpi,
                                pad_px=20,
                            )
                    else:
                        _ = self.cropper.crop_figure(
                            page_num=pno,
                            box=box,
                            out_path=dest_path,
                            dpi=dpi,
                            pad_px=20,
                        )
                    w_px, h_px = 0, 0
                    if dest_path.exists():
                        with Image.open(dest_path) as cim:
                            w_px, h_px = cim.size
                        ok, reasons = TypeSafeJevVision.verify_cropped_diagram(
                            dest_path, self.reader
                        )
                        if not ok:
                            print(
                                f"Warning: Figure {fig_id} on page {pno} verification warnings: {reasons}"
                            )
                    figures.append(
                        ExtractedFigure(
                            figure_id=fig_id,
                            caption=f"FIG. {raw_label_clean}",
                            image_rel_path=f"figures/{fig_filename}",
                            source_page=pno,
                            box=box,
                            width_px=w_px,
                            height_px=h_px,
                        )
                    )
                except (OSError, ValueError, RuntimeError) as e:
                    print(f"Warning: Failed to crop figure {fig_id} on page {pno}: {e}")

        return figures

    def extract_all(
        self,
        out_dir: Path,
        ocr_pages: Sequence[LinePage] | None = None,
        dpi: int = 300,
    ) -> list[ExtractedFigure]:
        """Universal figure extraction handler covering both digital and scanned documents."""
        figs: list[ExtractedFigure] = []
        digital_figs = self.extract_figures_from_digital_pdf(out_dir)
        if digital_figs:
            figs.extend(digital_figs)

        if ocr_pages:
            scanned_figs = self.extract_figures_from_ocr_pages(
                ocr_pages, out_dir, dpi=dpi
            )
            figs.extend(scanned_figs)

        return figs
