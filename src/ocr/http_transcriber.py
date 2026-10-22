import base64
import io
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from PIL import Image

from .pages import OCRBackendError, PageImage, Transcript

BACKEND_STATUSES = frozenset({401, 403, 404})
_NATIVE = {
    ".png": ("image/png", "PNG"),
    ".jpg": ("image/jpeg", "JPEG"),
    ".jpeg": ("image/jpeg", "JPEG"),
}


@dataclass(frozen=True)
class EncodedImage:
    mime: str
    data: str

    @property
    def data_uri(self) -> str:
        return f"data:{self.mime};base64,{self.data}"


@dataclass(frozen=True)
class HttpRequest:
    url: str
    json: dict[str, Any]
    headers: dict[str, str]


class PageFailed(Exception):
    pass


def encode_image(path: Path, max_side: int) -> EncodedImage:
    mime, image_format = _NATIVE.get(path.suffix.lower(), ("image/png", "PNG"))
    with Image.open(path) as img:
        if path.suffix.lower() in _NATIVE and (
            not max_side or max(img.size) <= max_side
        ):
            raw = path.read_bytes()
        else:
            page = img.convert("RGB")
            if max_side:
                page.thumbnail((max_side, max_side))
            buffer = io.BytesIO()
            page.save(
                buffer,
                format=image_format,
                **({"quality": 90} if image_format == "JPEG" else {}),
            )
            raw = buffer.getvalue()
    return EncodedImage(mime, base64.b64encode(raw).decode("ascii"))


class HttpTranscriber(ABC):
    retries = 4
    max_failures_in_a_row = 5

    def __init__(
        self,
        *,
        provenance: str,
        concurrency: int,
        max_side: int,
        pace_sec: float = 0.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.provenance = provenance
        self.concurrency = max(1, concurrency)
        self.max_side = max_side
        self.pace_sec = pace_sec
        self._client = client or httpx.Client(timeout=180.0)
        self._lock = threading.Lock()
        self._next_start = 0.0
        self._failures_in_a_row = 0
        self._stopped = threading.Event()

    @abstractmethod
    def request(self, image: EncodedImage) -> HttpRequest: ...

    @abstractmethod
    def text(self, body: Any) -> str: ...

    def transcribe(self, pages: Sequence[PageImage]) -> Iterator[Transcript]:
        pool = ThreadPoolExecutor(max_workers=self.concurrency)
        try:
            for future in as_completed(
                [pool.submit(self._page, page) for page in pages]
            ):
                if (transcript := future.result()) is not None:
                    yield transcript
        finally:
            pool.shutdown(wait=True, cancel_futures=True)

    def _page(self, page: PageImage) -> Transcript | None:
        if self._stopped.is_set():
            return None
        try:
            text = self._post(self.request(encode_image(page.path, self.max_side)))
        except OCRBackendError:
            self._stopped.set()
            raise
        except PageFailed as exc:
            print(f"Page {page.number}: {exc}")
            with self._lock:
                self._failures_in_a_row += 1
                if self._failures_in_a_row >= self.max_failures_in_a_row:
                    self._stopped.set()
                    raise OCRBackendError(
                        f"{self._failures_in_a_row} pages failed in a row on {self.provenance}; last: {exc}"
                    ) from exc
            return None
        with self._lock:
            self._failures_in_a_row = 0
        return Transcript(page.number, text)

    def _pace(self) -> None:
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next_start)
            self._next_start = start + self.pace_sec
        if start > now:
            time.sleep(start - now)

    def _post(self, request: HttpRequest) -> str:
        backoff = 2.0
        last = ""
        for _ in range(self.retries):
            self._pace()
            try:
                response = self._client.post(
                    request.url, json=request.json, headers=request.headers
                )
            except httpx.TransportError as exc:
                last = f"{type(exc).__name__}: {exc}"
                time.sleep(backoff)
                backoff *= 2
                continue
            if response.status_code == 200:
                try:
                    return self.text(response.json())
                except (KeyError, IndexError, TypeError, ValueError) as exc:
                    raise PageFailed(
                        f"unexpected response {response.text[:200]!r}"
                    ) from exc
            if response.status_code in BACKEND_STATUSES:
                raise OCRBackendError(
                    f"{self.provenance}: HTTP {response.status_code}: {response.text[:200]}"
                )
            last = f"HTTP {response.status_code}: {response.text[:120]}"
            wait = response.headers.get("Retry-After", "")
            time.sleep(float(wait) if wait.isdigit() else backoff)
            backoff *= 2
        raise PageFailed(last)
