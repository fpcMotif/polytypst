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


_KEYCAP_RE = re.compile("([0-9#*])\ufe0f?\u20e3")
_CODE_POINT_ESCAPE_RE = re.compile(r"\\u([0-9a-fA-F]{4})|\\U([0-9a-fA-F]{8})")
_NUMERIC_ENTITY_RE = re.compile(r"&#(?:[xX]([0-9a-fA-F]{1,6})|([0-9]{1,7}));")
_SURROGATE_PAIR_RE = re.compile("([\ud800-\udbff])([\udc00-\udfff])")
_MATH_SPAN_RE = re.compile(
    r"\$\$.*?\$\$|(?<!\\)\$(?:\\.|[^$\\])+?\$|\\\[.*?\\\]|\\\(.*?\\\)", re.DOTALL
)
_EMOJI_SELECTED_RE = re.compile("(.)\ufe0f")
_DROPPED_RUN_RE = re.compile("( *)\ufffd+( *)")
_EMOJI_PRESENTATION = frozenset(
    "⌚⌛⏩⏪⏫⏬⏰⏳◽◾☔☕♈♉♊♋♌♍♎♏♐♑♒♓♿⚓⚡⚪⚫⚽⚾⛄⛅⛎⛔⛪⛲⛳⛵⛺⛽✅✊✋✨❌❎❓❔❕❗➰➿⬛⬜⭐⭕"
)
_EMOJI_OPERATORS = str.maketrans({"➕": "+", "➖": "−", "➗": "÷", "✖": "×"})
_FULLWIDTH_TO_ASCII = {c: c - 0xFEE0 for c in range(0xFF01, 0xFF5F)} | {0x3000: 0x20}
_VARIATION_SELECTORS = frozenset(range(0xFE00, 0xFE10)) | frozenset(range(0xE0100, 0xE01F0))


def _code_point(digits: str, base: int) -> str:
    n = int(digits, base)
    return chr(n) if n <= 0x10FFFF else "\ufffd"


def _decoded_escapes(text: str) -> str:
    text = _CODE_POINT_ESCAPE_RE.sub(lambda m: _code_point(m[1] or m[2], 16), text)
    text = _NUMERIC_ENTITY_RE.sub(
        lambda m: c if ord(c := _code_point(m[1], 16) if m[1] else _code_point(m[2], 10)) >= 0x80 else m[0],
        text,
    )
    return _SURROGATE_PAIR_RE.sub(
        lambda m: chr(0x10000 + ((ord(m[1]) - 0xD800) << 10) + ord(m[2]) - 0xDC00), text
    )


def _enclosed_alphanumeric(c: str) -> str:
    """Parenthesized and dotted numbers become plain text, other circled styles the circled digit."""
    n = ord(c)
    if 0x2474 <= n <= 0x24B5:
        return unicodedata.normalize("NFKC", c)
    if 0x2776 <= n <= 0x2793:
        return chr(0x2460 + (n - 0x2776) % 10)
    if 0x24EB <= n <= 0x24F4:
        return chr(0x246A + n - 0x24EB)
    if 0x24F5 <= n <= 0x24FE:
        return chr(0x2460 + n - 0x24F5)
    return "⓪" if n == 0x24FF else c


def _is_invisible(c: str) -> bool:
    category = unicodedata.category(c)
    return (category == "Cc" and c not in "\t\n") or category == "Cf"


def _is_undrawable(c: str) -> bool:
    n = ord(c)
    return (
        unicodedata.category(c) in ("Co", "Cs", "Cn")
        or 0x1F000 <= n <= 0x1FAFF
        or c in _EMOJI_PRESENTATION
        or n in _VARIATION_SELECTORS
    )


def _without_baseless_marks(text: str) -> str:
    kept: list[str] = []
    for c in text:
        if unicodedata.category(c) in ("Mn", "Me") and not (
            kept and unicodedata.category(kept[-1])[0] in "LNM"
        ):
            continue
        kept.append(c)
    return "".join(kept)


def typesettable_markdown(text: str) -> str:
    """OCR markdown with only characters the book fonts draw in Typst and LaTeX.

    Keycaps become their digit, `\\#`, or `*` in math and `\\*` in prose. Circled numbers and
    letters stay for the footnote splitter and the circle rules, and other enclosed forms and
    emoji operators become their plain characters. Fullwidth math becomes ASCII. Emoji,
    private-use and invisible format characters are removed."""
    text = _MATH_SPAN_RE.sub(
        lambda m: _KEYCAP_RE.sub(lambda k: "\\#" if k[1] == "#" else k[1], m[0]).translate(_FULLWIDTH_TO_ASCII),
        _decoded_escapes(text),
    )
    text = _KEYCAP_RE.sub(lambda m: m[1] if m[1].isdigit() else "\\" + m[1], text)
    text = text.translate(_EMOJI_OPERATORS)
    text = _EMOJI_SELECTED_RE.sub(lambda m: "\ufffd" if unicodedata.category(m[1]) == "So" else m[0], text)
    text = "".join(_enclosed_alphanumeric(c) for c in text)
    text = "".join("\ufffd" if _is_undrawable(c) else c for c in text if not _is_invisible(c))
    text = _DROPPED_RUN_RE.sub(lambda m: "" if not m[2] else m[1][:1] or m[2], text)
    return _without_baseless_marks(text)


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
        return typesettable_markdown(path.read_text(encoding="utf-8")) if path.exists() else None

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
