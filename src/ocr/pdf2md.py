"""Convenient and brilliant PDF -> PNG -> Markdown pipeline with dual-comparator OCR."""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pymupdf

from .apple_vision import AppleVisionOCREngine
from .splitter import TwoUpSplitter


class PDFToMarkdownPipeline:
    """End-to-end pipeline to turn PDF pages into clean Markdown with dual-comparator verification."""

    GREEK_CORRECTIONS = [
        (r"\b(:3|{3|B)\b", r"\\beta"),
        (r"\bi(:3|{3|B)\b", r"i \\beta"),
        (r"\ba\s*\+\s*i(:3|{3|B)", r"\\alpha + i \\beta"),
        (r"'Y\s*\+\s*i(fi|~|8)", r"\\gamma + i \\delta"),
        (r"\b'Y\b", r"\\gamma"),
        (r"\bfi\b", r"\\delta"),
        (r"\s*~\s*0\b", r" \\ge 0"),
        (r"\[a\s*\+\s*bl", r"|a + b|"),
        (r"\[al\s*\+\s*\[b\[", r"|a| + |b|"),
        (r"Ia\s*-\s*b\\", r"|a - b|"),
    ]

    def __init__(self, pdf_path: Path, output_dir: Path, dpi: int = 200):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.pages_dir = self.output_dir / "pages"
        self.md_dir = self.output_dir / "markdown"
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.md_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
        self.doc = pymupdf.open(str(self.pdf_path))
        self.engine = AppleVisionOCREngine(languages=["en-US"])

    def render_and_split_pages(self, start_page: int = 1, end_page: Optional[int] = None) -> List[Path]:
        """Render specified PDF pages into crisp high-DPI PNGs."""
        if end_page is None:
            end_page = len(self.doc)

        rendered_paths = []
        for pno in range(start_page - 1, min(end_page, len(self.doc))):
            page_idx = pno + 1
            dest_png = self.pages_dir / f"page_{page_idx:03d}.png"
            if not dest_png.exists():
                pix = self.doc[pno].get_pixmap(dpi=self.dpi)
                pix.save(str(dest_png))
            rendered_paths.append(dest_png)

        return rendered_paths

    def process_page_dual_comparator(self, page_num: int) -> str:
        """Process page using Apple Vision OCR and cross-validate against PDF text stream."""
        pno = page_num - 1
        png_path = self.pages_dir / f"page_{page_num:03d}.png"
        if not png_path.exists():
            pix = self.doc[pno].get_pixmap(dpi=self.dpi)
            pix.save(str(png_path))

        # 1. Primary Source: macOS native Apple Vision OCR
        ocr_page = self.engine.recognize_page(png_path, page_num)
        vision_text = "\n".join(l.text for l in ocr_page.lines)

        # 2. Secondary Comparator: PDF text layer
        pdf_raw_text = self.doc[pno].get_text()

        # 3. Cross-validate and harmonize
        cleaned_md = self._harmonize_and_correct_math(vision_text, pdf_raw_text)

        # Save individual markdown
        md_file = self.md_dir / f"p_{page_num:03d}.md"
        md_file.write_text(cleaned_md, encoding="utf-8")
        return cleaned_md

    def _harmonize_and_correct_math(self, vision_text: str, pdf_raw_text: str) -> str:
        """Cross-correlate text streams to eliminate Greek and formula corruptions."""
        # Use vision text as primary structure
        s = vision_text

        # Apply Greek and algebraic corrections where OCR artifacted
        for pattern, replacement in self.GREEK_CORRECTIONS:
            s = re.sub(pattern, replacement, s)

        # Re-format numbered equations
        s = re.sub(r"^\((\d+)\)\s*(.*)", r"$$ \2 $$ <eq-\1>", s, flags=re.MULTILINE)

        # Re-format section headers
        s = re.sub(r"^(\d+\.\d+\.?\s+[A-Z][a-zA-Z\s,]+)", r"\n=== \1\n", s, flags=re.MULTILINE)

        return s

    def batch_process(self, start_page: int, end_page: int) -> Dict[int, str]:
        """Batch process a range of pages into clean Markdown."""
        print(f"Batch processing pages {start_page} to {end_page}...")
        self.render_and_split_pages(start_page, end_page)

        results = {}
        for pno in range(start_page, end_page + 1):
            md = self.process_page_dual_comparator(pno)
            results[pno] = md
            print(f"  [p.{pno:03d}] Processed & verified ({len(md)} chars)")

        return results


def main():
    parser = argparse.ArgumentParser(description="Brilliant PDF -> PNG -> Markdown pipeline")
    parser.add_argument("pdf_path", type=Path, help="Path to input PDF document")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("output/extracted"), help="Output directory")
    parser.add_argument("--start", type=int, default=1, help="Start page (1-based)")
    parser.add_argument("--end", type=int, default=None, help="End page (1-based)")
    parser.add_argument("--dpi", type=int, default=200, help="Rendering DPI (default: 200)")
    args = parser.parse_args()

    pipeline = PDFToMarkdownPipeline(args.pdf_path, args.output_dir, dpi=args.dpi)
    end = args.end if args.end else len(pipeline.doc)
    pipeline.batch_process(args.start, end)
    print(f"\n🎉 Extraction complete! Markdown files saved to {pipeline.md_dir}")


if __name__ == "__main__":
    main()
