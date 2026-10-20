"""Kerodon Commutative Diagram Locator and High-Resolution PDF Cropper."""

from pathlib import Path

import pymupdf
from PIL import Image, ImageChops

from .extractor import KerodonChapter, KerodonEnvironment


class KerodonDiagramCropper:
    """Locates and crops commutative diagrams from kerodon.pdf at 300 DPI."""

    def __init__(self, pdf_path: Path, output_dir: Path):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.doc = pymupdf.open(str(self.pdf_path))

    def crop_chapter_diagrams(self, chapter: KerodonChapter, start_page: int = 18, end_page: int = 145) -> int:
        """Scan kerodon.pdf and crop high-res images for all diagrams in the chapter."""
        # Build tag-to-page index
        tag_page_map = {}
        for pno in range(start_page - 1, min(end_page, len(self.doc))):
            text = self.doc[pno].get_text()
            for token in text.split():
                clean_tok = token.strip()
                if len(clean_tok) == 4 and clean_tok.isalnum() and clean_tok == clean_tok.upper():
                    if clean_tok not in tag_page_map:
                        tag_page_map[clean_tok] = pno
        cropped_count = 0

        # Collect all environments
        all_envs: list[KerodonEnvironment] = []
        for s in chapter.sections:
            all_envs.extend(s.intro_environments)
            for sub in s.subsections:
                all_envs.extend(sub.environments)

        for env in all_envs:
            if not env.diagrams:
                continue

            tag = env.tag
            pno = tag_page_map.get(tag)
            if pno is None:
                continue

            for diag in env.diagrams:
                dest_file = self.output_dir / f"diag_{tag}_{diag.index}.png"
                if dest_file.exists():
                    diag.image_path = str(dest_file.relative_to(self.output_dir.parent))
                    cropped_count += 1
                    continue

                # Crop from pno or pno + 1
                success = self._crop_diagram_at_page(tag, diag.index, pno, dest_file)
                if not success and pno + 1 < len(self.doc):
                    success = self._crop_diagram_at_page(tag, diag.index, pno + 1, dest_file)

                if success:
                    diag.image_path = str(dest_file.relative_to(self.output_dir.parent))
                    cropped_count += 1

        return cropped_count

    def _crop_diagram_at_page(self, tag: str, index: int, pno: int, dest_file: Path) -> bool:
        """Attempt to locate and crop diagram from page pno."""
        page = self.doc[pno]
        blocks = page.get_text("blocks")

        # Find candidate bounding box around visual arrows or centered equation gaps
        for b in blocks:
            b_text = b[4]
            # Match common equation or diagram indicators
            is_diag_indicator = (
                ("pictorially" in b_text) or
                ("depict as" in b_text) or
                ("commutative diagram" in b_text) or
                ("is commutative" in b_text) or
                ("/" in b_text and len(b_text.strip()) < 40) or
                ("→" in b_text or "−→" in b_text or "hook" in b_text)
            )
            if is_diag_indicator:
                y0 = b[1] - 15 if "pictorially" not in b_text and "depict" not in b_text else b[3] + 4
                y1 = y0 + 135
                rect = pymupdf.Rect(page.rect.x0 + 40, y0, page.rect.x1 - 40, y1)

                pix = page.get_pixmap(clip=rect, dpi=300)
                tmp_path = self.output_dir / f"tmp_{tag}_{index}.png"
                pix.save(str(tmp_path))

                # Auto-trim white borders
                im = Image.open(tmp_path)
                bg = Image.new(im.mode, im.size, (255, 255, 255))
                diff = ImageChops.difference(im, bg)
                bbox = diff.getbbox()
                tmp_path.unlink(missing_ok=True)

                if bbox and (bbox[2] - bbox[0] > 40) and (bbox[3] - bbox[1] > 25):
                    trimmed = im.crop((
                        max(0, bbox[0] - 12),
                        max(0, bbox[1] - 12),
                        min(im.size[0], bbox[2] + 12),
                        min(im.size[1], bbox[3] + 12)
                    ))
                    trimmed.save(dest_file)
                    return True

        return False
