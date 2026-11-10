import os
from pathlib import Path

BOOKS_ENV = "POLYTYPST_BOOKS"
_TRANSCRIPTS = "markdown_pages"


class BookStateError(RuntimeError):
    pass


def _pin() -> Path:
    root = os.environ.get(BOOKS_ENV)
    if not root:
        raise BookStateError(
            f"set {BOOKS_ENV} (environment or mise.local.toml) to the folder that holds each book's state"
        )
    return Path(root).expanduser()


def book_state(out_dir: Path) -> Path:
    """The folder that holds this book's state, `<root>/<out_dir name>`.

    The pinned root $POLYTYPST_BOOKS wins when it holds the book. Otherwise the `polytypst-store-*`
    folders beside it are searched, and a book found in two of them raises BookStateError.
    A book found nowhere goes under the pinned root."""
    name = Path(out_dir).name
    pin = _pin()
    if (pin / name).is_dir():
        return pin / name
    found: dict[Path, Path] = {}
    for root in sorted(pin.parent.glob("polytypst-store-*")):
        if (root / name).is_dir():
            _ = found.setdefault((root / name).resolve(), root / name)
    if len(found) > 1:
        copies = ", ".join(map(str, found.values()))
        raise BookStateError(
            f"{name} is in {len(found)} stores ({copies}); set {BOOKS_ENV} to one or remove the stale copy"
        )
    return next(iter(found.values()), pin / name)


def transcripts(out_dir: Path) -> Path:
    """This book's transcript store."""
    return book_state(out_dir) / _TRANSCRIPTS
