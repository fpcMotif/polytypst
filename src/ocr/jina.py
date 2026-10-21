"""Jina AI cloud OCR engine (chat completions API with `jina-ocr-v1`)."""

import base64
import os
import time
from pathlib import Path

import httpx

from .base import OCREngine, OCRLine, OCRPage, normalize_ocr_markdown

JINA_CHAT_ENDPOINT = "https://api.jina.ai/v1/chat/completions"
JINA_OCR_MODEL = "jina-ocr-v1"
DEFAULT_JINA_PROMPT = (
    "Transcribe this document into clean Markdown format with LaTeX math."
)


class JinaCloudUnavailable(RuntimeError):
    """Raised after too many consecutive pages fail, so a caller can fall back to Colab."""


def _load_jina_api_key() -> str | None:
    key = os.environ.get("JINA_API_KEY")
    if key:
        return key
    for cp in (
        Path("mise.local.toml"),
        Path.home() / "devv" / "mise.local.toml",
        Path(".env"),
        Path.home() / "devv" / ".env",
    ):
        if not cp.exists():
            continue
        for line in cp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("JINA_API_KEY") and "=" in line:
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val and not val.startswith("your-"):
                    return val
    return None


class JinaCloudOCREngine(OCREngine):
    def __init__(
        self,
        api_key: str | None = None,
        prompt: str = DEFAULT_JINA_PROMPT,
        retries: int = 5,
        pacing_sec: float = 1.5,
        max_consecutive_failures: int = 5,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key or _load_jina_api_key()
        if not self.api_key:
            raise ValueError(
                "JinaCloudOCREngine requires JINA_API_KEY in environment or mise.local.toml."
            )
        self.prompt = prompt
        self.retries = retries
        self.pacing_sec = pacing_sec
        self.max_consecutive_failures = max_consecutive_failures
        self._client = client or httpx.Client(timeout=60.0)
        self._last_call = 0.0
        self._consecutive_failures = 0

    def _pace(self) -> None:
        wait = self._last_call + self.pacing_sec - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    def _request(self, image_path: Path) -> str:
        b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = {
            "model": JINA_OCR_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"},
                        },
                    ],
                }
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        backoff = 2.0
        last_error = ""
        for _ in range(self.retries):
            self._pace()
            try:
                resp = self._client.post(
                    JINA_CHAT_ENDPOINT, json=payload, headers=headers
                )
            except httpx.HTTPError as exc:
                last_error = str(exc)
                time.sleep(3.0)
                continue
            if resp.status_code == 200:
                return str(resp.json()["choices"][0]["message"]["content"])
            last_error = f"HTTP {resp.status_code}: {resp.text[:100]}"
            if resp.status_code == 429:
                time.sleep(backoff)
                backoff *= 1.5
            else:
                time.sleep(2.0)
        raise httpx.HTTPError(f"{image_path.name}: {last_error}")

    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        try:
            md_text = normalize_ocr_markdown(self._request(image_path))
        except httpx.HTTPError as exc:
            self._consecutive_failures += 1
            print(f"Jina cloud failed on {image_path.name}: {exc}")
            if self._consecutive_failures >= self.max_consecutive_failures:
                raise JinaCloudUnavailable(
                    f"{self._consecutive_failures} consecutive Jina cloud failures"
                ) from exc
            return OCRPage(page_number, 0, 0, [], raw_text="")
        self._consecutive_failures = 0
        lines = [
            OCRLine(text=l, x=0.1, y=0.5, w=0.8, h=0.03)
            for l in md_text.splitlines()
            if l.strip()
        ]
        return OCRPage(page_number, 0, 0, lines, raw_text=md_text)

    def recognize_document(self, image_paths: list[Path]) -> list[OCRPage]:
        return [self.recognize_page(p, idx + 1) for idx, p in enumerate(image_paths)]
