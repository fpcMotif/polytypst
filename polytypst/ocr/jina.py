"""Jina AI Reader / Document OCR engine."""

import os
from pathlib import Path
from typing import List, Optional
import httpx

from .base import OCREngine, OCRLine, OCRPage


class JinaOCREngine(OCREngine):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("JINA_API_KEY")
        if not self.api_key:
            candidate_paths = [
                Path("mise.local.toml"),
                Path.home() / "devv" / "mise.local.toml",
                Path(".env"),
                Path.home() / "devv" / ".env"
            ]
            for cp in candidate_paths:
                if cp.exists():
                    try:
                        with open(cp) as f:
                            for line in f:
                                line = line.strip()
                                if line.startswith("JINA_API_KEY") and "=" in line:
                                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                                    if val and not val.startswith("your-"):
                                        self.api_key = val
                                        break
                    except Exception:
                        pass
                if self.api_key:
                    break

        if not self.api_key:
            raise ValueError("JinaOCREngine requires JINA_API_KEY in environment or mise.local.toml.")
        self.endpoint = "https://r.jina.ai/"

    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Return-Format": "markdown"
        }
        with open(image_path, "rb") as f:
            files = {"file": (image_path.name, f, "image/png")}
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(self.endpoint, headers=headers, files=files)
                resp.raise_for_status()
                md_text = resp.text

        lines = [OCRLine(text=l, x=0.1, y=0.5, w=0.8, h=0.03) for l in md_text.splitlines() if l.strip()]
        return OCRPage(page_number, 0, 0, lines, raw_text=md_text)

    def recognize_document(self, image_paths: List[Path]) -> List[OCRPage]:
        return [self.recognize_page(p, idx + 1) for idx, p in enumerate(image_paths)]
