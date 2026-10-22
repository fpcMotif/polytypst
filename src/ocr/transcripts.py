import json
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from .blank import BLANK_TRANSCRIPT, is_blank_page
from .pages import PageImage, Transcriber

MIN_TRANSCRIPT_BYTES = 30
PROVENANCE_NAME = "transcripts.json"
UNKNOWN = "unknown"
BLANK = "blank"

_FENCED_RE = re.compile(
    r"\A\s*```(?:markdown|md|latex|tex)?\s*\n(.*?)\n\s*```\s*\Z", re.DOTALL
)
_OPEN_FENCE_RE = re.compile(r"\A\s*```(?:markdown|md|latex|tex)?[^\n]*\n")
_CLOSE_FENCE_RE = re.compile(r"\n\s*```\s*\Z")


def normalize_ocr_markdown(decoded: object) -> str:
    if isinstance(decoded, (list, tuple)):
        decoded = decoded[0] if decoded else ""
    text = unicodedata.normalize("NFC", str(decoded)).replace("\r\n", "\n")
    fenced = _FENCED_RE.match(text)
    if fenced:
        text = fenced.group(1)
    elif _OPEN_FENCE_RE.match(text):
        # A fence the model never closed would swallow the rest of the book.
        text = _CLOSE_FENCE_RE.sub("\n", _OPEN_FENCE_RE.sub("", text, count=1))
    return text.strip() + "\n" if text.strip() else ""


def _page_ranges(numbers: list[int]) -> str:
    spans: list[str] = []
    for n in sorted(numbers):
        if spans and spans[-1].rpartition("-")[2] == str(n - 1):
            spans[-1] = f"{spans[-1].partition('-')[0]}-{n}"
        else:
            spans.append(str(n))
    return ", ".join(spans)


class TranscriptStore:
    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)

    def _path(self, number: int) -> Path:
        return self.directory / f"p_{number:03d}.md"

    def text(self, number: int) -> str | None:
        path = self._path(number)
        return path.read_text(encoding="utf-8") if path.exists() else None

    def _made_by(self) -> dict[int, str]:
        path = self.directory / PROVENANCE_NAME
        if not path.exists():
            return {}
        pages = json.loads(path.read_text(encoding="utf-8"))["pages"]
        return {int(n): source for n, source in pages.items()}

    def _save_made_by(self, made_by: dict[int, str]) -> None:
        pages = {str(n): made_by[n] for n in sorted(made_by)}
        path = self.directory / PROVENANCE_NAME
        draft = path.with_suffix(".json.tmp")
        _ = draft.write_text(
            json.dumps({"pages": pages}, indent=1) + "\n", encoding="utf-8"
        )
        _ = draft.replace(path)

    def _write(
        self, number: int, text: str, source: str, made_by: dict[int, str]
    ) -> None:
        _ = self._path(number).write_text(text, encoding="utf-8")
        made_by[number] = source
        self._save_made_by(made_by)

    def _pending(
        self,
        pages: Sequence[PageImage],
        made_by: dict[int, str],
        transcriber: Transcriber,
        retranscribe: bool,
    ) -> list[PageImage]:
        pending: list[PageImage] = []
        kept: Counter[str] = Counter()
        for page in pages:
            path = self._path(page.number)
            source = made_by.get(page.number) if path.exists() else None
            if source is None:
                if self.text(page.number) == BLANK_TRANSCRIPT or is_blank_page(
                    page.path
                ):
                    self._write(page.number, BLANK_TRANSCRIPT, BLANK, made_by)
                    continue
                if path.exists() and path.stat().st_size >= MIN_TRANSCRIPT_BYTES:
                    source = made_by[page.number] = UNKNOWN
            if source == BLANK:
                continue
            if source is None or retranscribe:
                pending.append(page)
            elif source != transcriber.provenance:
                kept[source] += 1
        self._save_made_by(made_by)
        if kept:
            counts = ", ".join(
                f"{n} transcripts made by {s}" for s, n in kept.most_common()
            )
            print(
                f"Kept {counts}; pass --retranscribe to redo them with {transcriber.provenance}."
            )
        return pending

    def transcribe(
        self,
        pages: Sequence[PageImage],
        transcriber: Transcriber,
        retranscribe: bool = False,
    ) -> dict[int, str]:
        self.directory.mkdir(parents=True, exist_ok=True)
        made_by = self._made_by()
        pending = self._pending(pages, made_by, transcriber, retranscribe)
        written: set[int] = set()
        for transcript in transcriber.transcribe(pending):
            text = normalize_ocr_markdown(transcript.text)
            if not text:
                print(f"Page {transcript.number}: the transcript came back empty.")
                continue
            source = BLANK if text == BLANK_TRANSCRIPT else transcriber.provenance
            self._write(transcript.number, text, source, made_by)
            written.add(transcript.number)
        if missing := [p.number for p in pending if p.number not in written]:
            noun = "page" if len(missing) == 1 else "pages"
            print(f"{len(missing)} {noun} still pending: {_page_ranges(missing)}")
        return {
            p.number: text for p in pages if (text := self.text(p.number)) is not None
        }
