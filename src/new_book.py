"""`polytypst new-book`: write the `src/<key>/` package of a new book and list it in pyproject.toml."""

import json
import re
from pathlib import Path

from .compiler.presets import domain_profile

PACKAGES_RE = re.compile(r"^packages = \[\n(?P<body>(?:    \".*\",\n)*)\]", re.MULTILINE)


def _spec_name(key: str) -> str:
    return f"{key.upper()}_SPEC"


def _quote(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def _files(key: str, title: str, author: str, source_pdf: str, pages: int, domain: str) -> dict[str, str]:
    spec = _spec_name(key)
    return {
        "__init__.py": f'"""{author}: {title}."""\n\nfrom .book import BOOK\nfrom .spec import {spec}\n\n__all__ = ["BOOK", "{spec}"]\n',
        "spec.py": (
            f'"""{author}: {title}."""\n\n'
            "from ..compiler.monograph import ChapterSpec, MonographSpec\n\n"
            f"{spec} = MonographSpec(\n"
            f"    slug={_quote(key)},\n"
            f"    title={_quote(title)},\n"
            f"    author={_quote(author)},\n"
            f"    domain={_quote(domain)},\n"
            f"    source_pdf={_quote(source_pdf)},\n"
            f"    pdf_page_count={pages},\n"
            "    cross_references=True,\n"
            f"    chapters=[ChapterSpec(1, {_quote(title)}, 1, {pages})],\n"
            ")\n"
        ),
        "book.py": (
            "from ..edition import OUTPUT, Book, monograph_edition\n"
            f"from .spec import {spec}\n\n"
            f'OUT_DIR = OUTPUT / "{key}"\n\n'
            f'BOOK = Book({spec}, OUT_DIR, {{"monograph": monograph_edition({spec}, OUT_DIR, "monograph")}})\n'
        ),
    }


def _list_package(pyproject: Path, package: str) -> None:
    text = pyproject.read_text(encoding="utf-8")
    match = PACKAGES_RE.search(text)
    if match is None:
        raise ValueError(f"{pyproject} has no one-per-line `packages = [...]` list")
    names = re.findall(r'"(.*)"', match["body"])
    body = "".join(f'    "{name}",\n' for name in sorted({*names, package}))
    pyproject.write_text(text[: match.start("body")] + body + text[match.end("body") :], encoding="utf-8")


def scaffold_book(root: Path, key: str, title: str, author: str, source_pdf: str, pages: int, *, domain: str) -> list[Path]:
    """Write `src/<key>/{__init__,spec,book}.py` under `root` and add `polytypst.<key>` to its pyproject.toml."""
    if not key.isidentifier():
        raise ValueError(f"book key {key!r} must be a Python identifier; use underscores, not dashes")
    domain_profile(domain)
    folder = root / "src" / key
    if folder.exists():
        raise ValueError(f"{folder} exists")
    folder.mkdir(parents=True)
    written = []
    for name, text in _files(key, title, author, source_pdf, pages, domain).items():
        path = folder / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    _list_package(root / "pyproject.toml", f"polytypst.{key}")
    return written
