"""2-Up spread splitter for scanned book spreads."""

from pathlib import Path

import pymupdf


class TwoUpSplitter:
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.doc = pymupdf.open(pdf_path)

    def is_two_up(self) -> bool:
        """Detect if the PDF is scanned as 2-up spreads (width > height)."""
        sample_pages = min(5, len(self.doc))
        landscape_count = sum(1 for i in range(sample_pages) if self.doc[i].rect.width > self.doc[i].rect.height * 1.1)
        return landscape_count >= 3

    def split_and_render_all(self, out_dir: Path, dpi: int = 150) -> list[Path]:
        """Split all 2-up spreads into individual left and right portrait page images."""
        out_dir.mkdir(parents=True, exist_ok=True)
        rendered_paths = []

        is_spread = self.is_two_up()
        print(f"Document 2-up spread detected: {is_spread} ({len(self.doc)} sheets)")

        page_counter = 1
        for idx, page in enumerate(self.doc):
            w = page.rect.width
            h = page.rect.height

            if is_spread:
                # Left page
                left_rect = pymupdf.Rect(0, 0, w / 2, h)
                pix_left = page.get_pixmap(clip=left_rect, dpi=dpi)
                left_path = out_dir / f"p_{page_counter:03d}.png"
                pix_left.save(left_path)
                rendered_paths.append(left_path)
                page_counter += 1

                # Right page
                right_rect = pymupdf.Rect(w / 2, 0, w, h)
                pix_right = page.get_pixmap(clip=right_rect, dpi=dpi)
                right_path = out_dir / f"p_{page_counter:03d}.png"
                pix_right.save(right_path)
                rendered_paths.append(right_path)
                page_counter += 1
            else:
                pix = page.get_pixmap(dpi=dpi)
                p_path = out_dir / f"p_{page_counter:03d}.png"
                pix.save(p_path)
                rendered_paths.append(p_path)
                page_counter += 1

        print(f"Extracted and rendered {len(rendered_paths)} individual portrait book pages.")
        return rendered_paths
