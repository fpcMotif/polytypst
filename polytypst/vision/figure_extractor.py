"""Universal figure and diagram extractor for scanned and digital PDFs."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import final

import pymupdf

from ..ocr.base import OCRLine, OCRPage
from .cropper import HighDPICropper


@dataclass
class ExtractedFigure:
    figure_id: str
    caption: str
    image_rel_path: str
    source_page: int
    box: tuple[float, float, float, float] | None = None


@final
class FigureExtractor:
    """Detects, crops, and catalogues figures and diagrams from any PDF (scanned or digital)."""

    FIGURE_CAPTION_REGEX: re.Pattern[str] = re.compile(
        r"\b(FIG|Fig|Figure|Abbildung|图)\.?\s*([0-9]+[A-Za-z0-9\-\.]*)",
        re.IGNORECASE,
    )

    def __init__(self, pdf_path: Path) -> None:
        self.pdf_path: Path = Path(pdf_path)
        self.cropper: HighDPICropper = HighDPICropper(self.pdf_path)

    @staticmethod
    def detect_figure_box(
        page_lines: list[OCRLine],
        cap_line: OCRLine,
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
                    )
                )
        return figures

    def extract_figures_from_ocr_pages(
        self,
        ocr_pages: list[OCRPage],
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
            pno = page.page_number
            for line in page.lines:
                m = self.FIGURE_CAPTION_REGEX.search(line.text)
                if not m:
                    continue

                raw_label = m.group(2).strip().rstrip(".:;,")
                fig_id = re.sub(r"[^0-9A-Za-z_-]", "_", raw_label)
                if not fig_id or fig_id in seen_ids:
                    fig_id = f"p{pno}_{len(seen_ids) + 1}"
                seen_ids.add(fig_id)

                box = self.detect_figure_box(page.lines, line)
                fig_filename = f"fig_{fig_id}.png"
                dest_path = out_dir / fig_filename

                page_png = out_dir.parent / "pages" / f"p_{pno:03d}.png"
                try:
                    if page_png.exists() and jev.api_key:
                        det = jev.detect_diagram(
                            page_png, fig_label=f"FIG. {raw_label}"
                        )
                        if det.has_diagram and det.box:
                            box = det.box
                            _ = TypeSafeJevVision.crop_pure_diagram(
                                page_png, det, dest_path
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
                    figures.append(
                        ExtractedFigure(
                            figure_id=fig_id,
                            caption=line.text.strip(),
                            image_rel_path=f"figures/{fig_filename}",
                            source_page=pno,
                            box=box,
                        )
                    )
                except (OSError, ValueError, RuntimeError) as e:
                    print(f"Warning: Failed to crop figure {fig_id} on page {pno}: {e}")

        return figures

    def extract_all(
        self,
        out_dir: Path,
        ocr_pages: list[OCRPage] | None = None,
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
