"""`polytypst new-book`: write the `books/<key>/book.toml` of a new book."""

import json
from pathlib import Path

from .compiler.presets import domain_profile


def _quote(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def _book_toml(key: str, title: str, author: str, source_pdf: str, pages: int, domain: str) -> str:
    return (
        f"slug = {_quote(key)}\n"
        f"title = {_quote(title)}\n"
        f"author = {_quote(author)}\n"
        f"domain = {_quote(domain)}\n"
        f"source_pdf = {_quote(source_pdf)}\n"
        f"pdf_page_count = {pages}\n"
        "cross_references = true\n"
        "chapters = [\n"
        f"  {{ number = 1, title = {_quote(title)}, start_page = 1, end_page = {pages} }},\n"
        "]\n"
    )


def scaffold_book(root: Path, key: str, title: str, author: str, source_pdf: str, pages: int, *, domain: str) -> list[Path]:
    """Write `books/<key>/book.toml` under `root`. The catalog finds the folder; nothing else lists it."""
    if not key or "/" in key or key.startswith(".") or "-" in key:
        raise ValueError(f"book key {key!r} must be one folder name without dashes; use underscores")
    domain_profile(domain)
    folder = root / "books" / key
    if folder.exists():
        raise ValueError(f"{folder} exists")
    folder.mkdir(parents=True)
    path = folder / "book.toml"
    path.write_text(_book_toml(key, title, author, source_pdf, pages, domain), encoding="utf-8")
    return [path]
