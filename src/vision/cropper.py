"""High-DPI diagram cropping with content-aware margin trimming."""

from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image


class HighDPICropper:
    def __init__(self, doc_path: Path):
        self.doc_path = doc_path
        self._doc = pymupdf.open(doc_path)

    def crop_figure(
        self,
        page_num: int,
        box: tuple[float, float, float, float],  # (left, top, right, bottom) normalized 0.0 - 1.0 from top-left
        out_path: Path,
        dpi: int = 300,
        pad_px: int = 15
    ) -> Path:
        """Crop a figure from the PDF page at high DPI with tight border trimming."""
        page = self._doc[page_num - 1]
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        W, H = img.size
        left, top, right, bottom = box

        x0 = max(0, int(left * W))
        y0 = max(0, int(top * H))
        x1 = min(W, int(right * W))
        y1 = min(H, int(bottom * H))

        cropped = img.crop((x0, y0, x1, y1))

        # Auto-trim blank background margins
        gray = np.array(cropped.convert("L"))
        # Content pixels (darker than 235)
        content_y, content_x = np.where(gray < 235)
        if len(content_y) > 0 and len(content_x) > 0:
            cy0 = max(0, content_y.min() - pad_px)
            cy1 = min(cropped.height, content_y.max() + pad_px)
            cx0 = max(0, content_x.min() - pad_px)
            cx1 = min(cropped.width, content_x.max() + pad_px)
            final_crop = cropped.crop((cx0, cy0, cx1, cy1))
        else:
            final_crop = cropped

        out_path.parent.mkdir(parents=True, exist_ok=True)
        final_crop.save(out_path, format="PNG")
        return out_path
