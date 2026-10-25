"""Finds every book: a folder `src/<key>/` with a `book.py` that defines `BOOK`."""

import importlib
from functools import cache
from pathlib import Path

from .compiler.monograph import MonographSpec
from .edition import Book

PACKAGE = Path(__file__).parent


@cache
def books() -> dict[str, Book]:
    """Every book by key. The key is its package name and its folder under output/."""
    return {
        p.parent.name: importlib.import_module(f".{p.parent.name}.book", __package__).BOOK
        for p in sorted(PACKAGE.glob("*/book.py"))
    }


def book_specs() -> dict[str, MonographSpec]:
    """Every monograph spec of every edition, by slug."""
    return {
        e.spec.slug: e.spec for book in books().values() for e in book.editions.values() if e.spec is not None
    }


def _names(spec: MonographSpec, path: Path) -> bool:
    name = path.name.lower()
    return (
        path.stem == spec.slug
        or (bool(spec.source_pdf) and name == spec.source_pdf.lower())
        or any(marker in name for marker in spec.pdf_name_markers)
    )


def find_known_book(path: Path) -> MonographSpec | None:
    """The spec whose slug, scan file name or name markers match the file name; a page count is no match."""
    return next((spec for spec in book_specs().values() if _names(spec, path)), None)


def book_by_key(key: str) -> Book:
    """The book with key `key`, which may spell underscores as hyphens; raises KeyError naming the keys."""
    known = books()
    aliases = {
        "sga4half": "sga4_5",
        "sga4_half": "sga4_5",
        "sga4-half": "sga4_5",
        "sga-4-5": "sga4_5",
        "sga45": "sga4_5",
    }
    resolved_key = aliases.get(key, key)
    normalized = {**known, **{k.replace("_", "-"): v for k, v in known.items()}}
    if resolved_key not in normalized:
        raise KeyError(f"unknown book {key!r}; known: {', '.join(known)}")
    return normalized[resolved_key]


def book_for_scan(source: Path, key: str | None = None) -> Book | None:
    """The book named by `key`, else the book whose specs match the scan's file name."""
    if key is not None:
        return book_by_key(key)
    for book in books().values():
        specs = [book.spec, *(e.spec for e in book.editions.values() if e.spec is not None)]
        if any(_names(spec, source) for spec in specs):
            return book
    return None
