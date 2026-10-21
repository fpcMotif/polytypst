"""Mistral OCR Engine integrating mistral-ocr-latest."""

import base64
import os
from pathlib import Path

import httpx

from .base import OCREngine, OCRLine, OCRPage


class MistralOCREngine(OCREngine):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        if not self.api_key:
            # Check mise.local.toml or .env in current working tree
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
                                if line.startswith("MISTRAL_API_KEY") and "=" in line:
                                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                                    if val and not val.startswith("your-"):
                                        self.api_key = val
                                        break
                    except OSError:
                        continue
                if self.api_key:
                    break

        if not self.api_key:
            raise ValueError("MistralOCREngine requires MISTRAL_API_KEY in environment or mise.local.toml.")
        self.endpoint = "https://api.mistral.ai/v1/ocr"

    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        with open(image_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("ascii")

        fmt = "png" if image_path.suffix.lower() == ".png" else "jpeg"
        data_url = f"data:image/{fmt};base64,{b64_data}"

        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "image_url",
                "image_url": data_url
            },
            "include_image_base64": True
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(self.endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Mistral OCR returns markdown per page with structured images
        pages = data.get("pages", [])
        if not pages:
            return OCRPage(page_number, 0, 0, [])

        p0 = pages[0]
        md_text = p0.get("markdown", "")
        dims = p0.get("dimensions", {})
        width = dims.get("width", 0)
        height = dims.get("height", 0)

        lines = [OCRLine(text=l, x=0.1, y=0.5, w=0.8, h=0.03) for l in md_text.splitlines() if l.strip()]
        return OCRPage(page_number, width, height, lines, raw_text=md_text)

    def recognize_document(self, image_paths: list[Path]) -> list[OCRPage]:
        return [self.recognize_page(p, idx + 1) for idx, p in enumerate(image_paths)]
