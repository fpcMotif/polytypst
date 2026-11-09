import re
import unicodedata
from pathlib import Path

from .compiler.monograph import build_source

BUILD_TAILS = (".md", ".typ", ".tex", "-numbering-resyncs.txt")
NAME =re.compile(r"[a-z][a-z0-9]*(-[a-z0-9]+)*")
TITLE_SKIP = frozenset(
    {"a", "an", "the", "on", "of", "to", "and", "in", "for", "with", "basic", "introduction", "elements", "lectures", "notes"}
)


class BookNameError(ValueError):
    pass


def _ascii_words(text: str) -> list[str]:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z]+", folded.lower())


def default_name(author: str, title: str, year: int | None) -> str | None:
    """`<surname><year>-<title word>`, such as ahlfors1979-complex, or None when the author or title has no Latin word."""
    first_author = re.split(r",| and |&|、|;", author)[0]
    surname = next(reversed(_ascii_words(first_author)), "")
    word = next((w for w in _ascii_words(title) if w not in TITLE_SKIP and len(w) > 2), "")
    if not surname or not word:
        return None
    return f"{surname}{year or ''}-{word}"


def check_name(name: str, where: str) -> str:
    if not NAME.fullmatch(name):
        raise BookNameError(f"{where}: {name!r} is not a book name; use lowercase letters, digits and hyphens, such as ahlfors1979-complex")
    return name


def rename_build(rebuilt: Path, stem: str) -> Path:
    """Move a built PDF, its EPUB, and its sources in `build/` to `stem`; returns the new PDF path."""
    build = build_source(rebuilt, "typ").parent
    moves = [(rebuilt.with_suffix(f".{ext}"), rebuilt.with_name(f"{stem}.{ext}")) for ext in ("pdf", "epub")]
    moves += [(build / f"{rebuilt.stem}{tail}", build / f"{stem}{tail}") for tail in BUILD_TAILS]
    for old, new in moves:
        if old.exists():
            _ = old.replace(new)
    return rebuilt.with_name(f"{stem}.pdf")


def edition_file(book_name: str, edition: str, first: bool) -> str:
    """The PDF stem of an edition: the book name, plus `.<edition>` for every edition after the first."""
    return book_name if first else f"{book_name}.{edition}"
