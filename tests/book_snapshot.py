"""A JSON form of every book, its editions and their specs, so that a move of the book files can be checked."""

import dataclasses
import hashlib
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from polytypst.edition import Book

ROOT = Path(__file__).resolve().parents[1]
LONG = 160


def short(text: str) -> str:
    """A long string, such as a preamble, as its hash, which keeps the snapshot file small."""
    return text if len(text) <= LONG else "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def _callable(fn: Callable[..., object], expand: bool) -> object:
    name = getattr(fn, "__qualname__", type(fn).__qualname__)
    code = getattr(fn, "__code__", None)
    if not expand or code is None or not fn.__closure__:
        return f"<fn {name}>"
    cells = {var: cell.cell_contents for var, cell in zip(code.co_freevars, fn.__closure__, strict=True)}
    return {"fn": name, "closure": {var: _plain(value, expand=False) for var, value in sorted(cells.items())}}


def _plain(value: Any, expand: bool = False) -> object:
    if isinstance(value, str):
        return short(value.replace(str(ROOT), "<root>"))
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, Path):
        path = value.resolve() if value.is_absolute() else value
        return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(value)
    if isinstance(value, re.Pattern):
        return {"re": value.pattern, "flags": value.flags}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        fields = {f.name: _plain(getattr(value, f.name), expand) for f in dataclasses.fields(value)}
        return {"type": type(value).__name__, **fields}
    if isinstance(value, dict):
        return {str(k): _plain(v, expand) for k, v in value.items()}
    if isinstance(value, frozenset | set):
        return sorted((_plain(v, expand) for v in value), key=repr)
    if isinstance(value, tuple | list):
        return [_plain(v, expand) for v in value]
    if callable(value):
        return _callable(value, expand)
    return repr(value)


def snapshot(book: Book) -> dict[str, object]:
    """The book as plain JSON data. Each edition's build and page map show the values they close over."""
    editions = {
        name: {
            "rebuilt": _plain(e.rebuilt),
            "summary": e.summary,
            "formats": _plain(e.formats),
            "scan_line_breaks": e.scan_line_breaks,
            "spec": _plain(e.spec),
            "build": _callable(e.build, expand=True),
            "parity": None if e.parity is None else {
                "page_map": _callable(e.parity.page_map, expand=True),
                **{k: _plain(getattr(e.parity, k)) for k in ("tolerance", "diagrams", "diagram_text", "visual")},
            },
        }
        for name, e in book.editions.items()
    }
    return {
        "spec": _plain(book.spec),
        "out_dir": _plain(book.out_dir),
        "figures": None if book.figures is None else _callable(book.figures, expand=False),
        "editions": editions,
    }
