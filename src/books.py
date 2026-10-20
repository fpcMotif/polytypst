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


def render_book_figures(slug: str, out_dir: Path) -> bool:
    """Draw the code-reproduced figures of the book that owns the spec `slug` into `out_dir`."""
    for book in books().values():
        if book.figures and any(e.spec and e.spec.slug == slug for e in book.editions.values()):
            _ = book.figures(out_dir)
            return True
    return False


def find_known_book(pdf_path: Path, total_pages: int) -> MonographSpec | None:
    """Return the spec whose page count or file-name markers match the PDF."""
    name = pdf_path.name.lower()
    for spec in book_specs().values():
        if spec.pdf_page_count == total_pages or any(
            marker in name for marker in spec.pdf_name_markers
        ):
            return spec
    return None
