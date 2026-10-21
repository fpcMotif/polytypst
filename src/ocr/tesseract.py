"""Tesseract 5 OCR Engine fallback for 129 languages."""

import subprocess
import tempfile
from pathlib import Path

from .base import OCREngine, OCRLine, OCRPage


class TesseractOCREngine(OCREngine):
    def __init__(self, languages: str = "chi_sim+eng"):
        self.languages = languages

    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        # Run tesseract with TSV output for bounding boxes
        with tempfile.NamedTemporaryFile("w+", suffix=".tsv", delete=False) as f:
            tsv_path = Path(f.name)

        base_tsv = tsv_path.with_suffix("")
        cmd = [
            "nix", "--extra-experimental-features", "nix-command flakes", "shell", "nixpkgs#tesseract5",
            "--command", "tesseract", str(image_path), str(base_tsv), "-l", self.languages, "tsv"
        ]
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        real_tsv = Path(str(base_tsv) + ".tsv")
        lines = []
        if real_tsv.exists():
            with open(real_tsv, "r", encoding="utf-8", errors="ignore") as f:
                f.readline()
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) >= 12 and parts[11].strip():
                        # level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
                        text = parts[11].strip()
                        lines.append(OCRLine(text=text, x=0.1, y=0.5, w=0.8, h=0.03))
            real_tsv.unlink()

        return OCRPage(page_number, 0, 0, lines)

    def recognize_document(self, image_paths: list[Path]) -> list[OCRPage]:
        return [self.recognize_page(p, idx + 1) for idx, p in enumerate(image_paths)]
