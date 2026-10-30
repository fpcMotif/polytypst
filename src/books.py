"""Finds every book: a folder `books/<key>/` with a `book.toml`, or a `book.py` that defines `BOOK`.
A book loads only when it is first used, so a broken book stops only the commands that use it."""

import dataclasses
import hashlib
import importlib
import importlib.util
import re
import sys
import tomllib
import types
import typing
from collections.abc import Callable, Iterator, Mapping
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

from .compiler.monograph import MonographCompiler, MonographSpec
from .edition import (
    OUTPUT,
    Book,
    Edition,
    VisualLimits,
    facsimile_edition,
    monograph_edition,
)
from .facsimile import FacsimileStyle

BOOKS_DIR = Path(__file__).resolve().parent.parent / "books"
REPO_TOKEN = "@REPO@"
BOOK_TOKEN = "@BOOK@"
BOOK_TOML = "book.toml"
BOOK_PY = "book.py"
HOOKS_PY = "hooks.py"
PACKAGE = "polytypst_books"


class BookFileError(ValueError):
    """A `book.toml` that does not describe a book; the message names the file and the key."""


class BookLoadError(RuntimeError):
    """A book that failed to load; the message names its key."""


def book_folders() -> dict[str, Path]:
    """Every book folder by key, without loading any book. The key is the folder name."""
    return {
        p.name: p
        for p in sorted(BOOKS_DIR.iterdir())
        if p.is_dir() and ((p / BOOK_TOML).is_file() or (p / BOOK_PY).is_file())
    }


def _package_name(key: str) -> str:
    name = key if key.isidentifier() else "b_" + hashlib.sha1(key.encode()).hexdigest()[:10]
    return f"{PACKAGE}.{name}"


def _package(key: str, folder: Path) -> str:
    """Register the book folder as a package, so that its files can import each other with `from .x import y`."""
    if PACKAGE not in sys.modules:
        root = types.ModuleType(PACKAGE)
        root.__path__ = []
        sys.modules[PACKAGE] = root
    name = _package_name(key)
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, folder / "__init__.py", submodule_search_locations=[str(folder)])
        if spec is None or spec.loader is None:
            raise BookLoadError(f"{key}: cannot import {folder}")
        package = importlib.util.module_from_spec(spec)
        sys.modules[name] = package
        if (folder / "__init__.py").is_file():
            spec.loader.exec_module(package)
    return name


def module(key: str, name: str | None = "book") -> types.ModuleType:
    """The module `books/<key>/<name>.py`, imported as part of its book's package; `None` names the package itself."""
    package = _package(key, book_folders()[key])
    return importlib.import_module(package if name is None else f"{package}.{name}")


def _is_callable(tp: object) -> bool:
    if typing.get_origin(tp) in (types.UnionType, typing.Union):
        return any(_is_callable(a) for a in typing.get_args(tp))
    return tp is Callable or typing.get_origin(tp) is Callable


def _hook_fields(cls: type) -> tuple[str, ...]:
    return tuple(name for name, tp in typing.get_type_hints(cls).items() if _is_callable(tp))


class _Hooks:
    """The functions of `books/<key>/hooks.py`. Each public function must fill a field, or loading fails."""

    def __init__(self, key: str, folder: Path) -> None:
        self.path = folder / HOOKS_PY
        self.module = importlib.import_module(f"{_package(key, folder)}.hooks") if self.path.is_file() else None
        self.used: set[str] = set()

    def named(self, name: object, where: str) -> Callable[..., Any]:
        if not isinstance(name, str) or self.module is None or not callable(fn := getattr(self.module, name, None)):
            raise BookFileError(f"{where}: {HOOKS_PY} defines no function {name!r}")
        self.used.add(name)
        return fn

    def bind(
        self, fields: tuple[str, ...], names: object, where: str, by_name: bool = True
    ) -> dict[str, Callable[..., Any]]:
        """Each field named in the `hooks` table; with `by_name`, also the hooks.py function named after a field."""
        if not isinstance(names, dict):
            raise BookFileError(f"{where}hooks: expected a table, got {names!r}")
        if unknown := sorted(set(names) - set(fields)):
            raise BookFileError(f"{where}hooks: unknown key {', '.join(unknown)}")
        bound = {field: self.named(fn, f"{where}hooks.{field}") for field, fn in names.items()}
        for field in fields if by_name else ():
            if field not in bound and self.module is not None and callable(getattr(self.module, field, None)):
                bound[field] = self.named(field, field)
        return bound

    def check_all_bound(self) -> None:
        if self.module is None:
            return
        public = {
            name for name, value in vars(self.module).items()
            if not name.startswith("_") and callable(value) and not isinstance(value, type)
            and getattr(value, "__module__", None) == self.module.__name__
        }
        if unbound := sorted(public - self.used):
            raise BookFileError(f"{self.path}: {', '.join(unbound)} fill no field; make them private with a leading _")


def _coerce(tp: object, value: object, where: str, folder: Path) -> object:
    origin, args = typing.get_origin(tp), typing.get_args(tp)
    if origin is typing.Literal:
        if value not in args:
            raise BookFileError(f"{where}: {value!r} is not one of {', '.join(map(repr, args))}")
        return value
    if origin in (types.UnionType, typing.Union):
        options = [a for a in args if a is not type(None)]
        if len(options) != 1:
            raise BookFileError(f"{where}: unsupported type {tp}")
        return _coerce(options[0], value, where, folder)
    if origin is Callable or tp is Callable:
        raise BookFileError(f"{where}: a function cannot be set in {BOOK_TOML}")
    if isinstance(tp, type) and dataclasses.is_dataclass(tp):
        return _dataclass(tp, value, where, folder)
    if origin in (list, tuple, frozenset):
        if not isinstance(value, list):
            raise BookFileError(f"{where}: expected an array, got {value!r}")
        if origin is tuple and not (len(args) == 2 and args[1] is Ellipsis):
            if len(value) != len(args):
                raise BookFileError(f"{where}: expected {len(args)} items, got {len(value)}")
            return tuple(_coerce(a, v, f"{where}[{i}]", folder) for i, (a, v) in enumerate(zip(args, value, strict=True)))
        items = [_coerce(args[0], v, f"{where}[{i}]", folder) for i, v in enumerate(value)]
        return origin(items)
    if origin is dict:
        if not isinstance(value, dict):
            raise BookFileError(f"{where}: expected a table, got {value!r}")
        key_type, value_type = args
        out = {}
        for k, v in value.items():
            if key_type is int:
                if not k.lstrip("-").isdigit():
                    raise BookFileError(f"{where}: key {k!r} is not an integer")
                k = int(k)
            out[k] = _coerce(value_type, v, f"{where}.{k}", folder)
        return out
    if tp is float and isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    if tp is str and isinstance(value, str):
        return value.replace(REPO_TOKEN, str(BOOKS_DIR.parent))
    if tp is Path and isinstance(value, str):
        return Path(value.replace(BOOK_TOKEN, str(folder)).replace(REPO_TOKEN, str(BOOKS_DIR.parent)))
    if tp in (int, bool) and type(value) is tp:
        return value
    raise BookFileError(f"{where}: expected {getattr(tp, '__name__', tp)}, got {value!r}")


def _fields(cls: type[DataclassInstance], table: object, where: str, folder: Path) -> dict[str, Any]:
    if not isinstance(table, dict):
        raise BookFileError(f"{where}: expected a table, got {table!r}")
    hints = typing.get_type_hints(cls)
    known = {f.name for f in dataclasses.fields(cls) if f.init}
    if unknown := sorted(set(table) - known):
        raise BookFileError(f"{where}: unknown key {', '.join(unknown)}")
    return {k: _coerce(hints[k], v, f"{where}.{k}" if where else k, folder) for k, v in table.items()}


def _dataclass[T: DataclassInstance](cls: type[T], table: object, where: str, folder: Path) -> T:
    try:
        return cls(**_fields(cls, table, where, folder))
    except TypeError as e:
        raise BookFileError(f"{where or cls.__name__}: {e}") from None


def _out_dir(table: dict[str, object], default: Path, where: str) -> Path:
    name = table.pop("legacy_state", None)
    if name is None:
        return default
    if not isinstance(name, str):
        raise BookFileError(f"{where}legacy_state: expected str, got {name!r}")
    return OUTPUT / name


SPEC_HOOKS = _hook_fields(MonographSpec)
FACSIMILE_HOOKS = _hook_fields(FacsimileStyle)
TITLE_PAGE_TOKEN = "@ENGINE_TITLE_PAGE@"
PREAMBLE_TOKEN = "@ENGINE_PREAMBLE@"
STYLE_TOKEN = re.compile(r"@STYLE:([\w-]+)@")


def _style_file(match: re.Match[str]) -> str:
    path = BOOKS_DIR / "styles" / f"{match.group(1)}.typ"
    if not path.is_file():
        raise BookFileError(f"{match.group(0)}: no style file at {path}")
    return path.read_text(encoding="utf-8")


def _engine_text(spec: MonographSpec) -> MonographSpec:
    """Put the compiler's own title page and preamble where the spec's Typst names their tokens."""
    if STYLE_TOKEN.search(spec.typst_front_matter):
        spec = dataclasses.replace(spec, typst_front_matter=STYLE_TOKEN.sub(_style_file, spec.typst_front_matter))
    if TITLE_PAGE_TOKEN in spec.typst_front_matter:
        own = MonographCompiler(dataclasses.replace(spec, typst_front_matter="")).build_typst_title_page()
        spec = dataclasses.replace(spec, typst_front_matter=spec.typst_front_matter.replace(TITLE_PAGE_TOKEN, own))
    if PREAMBLE_TOKEN in spec.typst_preamble:
        own = MonographCompiler(dataclasses.replace(spec, typst_preamble="")).build_typst_preamble()
        spec = dataclasses.replace(spec, typst_preamble=spec.typst_preamble.replace(PREAMBLE_TOKEN, own))
    return spec


def _edition(
    name: str, table: object, spec: MonographSpec, out_dir: Path, hooks: _Hooks, folder: Path
) -> Edition:
    """One `[editions.<name>]` table: a `monograph` edition by default, or `kind = "facsimile"`."""
    where = f"editions.{name}."
    if not isinstance(table, dict):
        raise BookFileError(f"{where[:-1]}: expected a table, got {table!r}")
    table = dict(table)
    edition_dir = _out_dir(table, out_dir, where)
    kind = table.pop("kind", "monograph")
    summary = table.pop("summary", None)
    if summary is not None and not isinstance(summary, str):
        raise BookFileError(f"{where}summary: expected str, got {summary!r}")
    overrides = _fields(MonographSpec, table.pop("spec", {}), f"{where}spec", folder)
    names = table.pop("hooks", {})

    def edition_spec() -> MonographSpec:
        if table:
            raise BookFileError(f"{where[:-1]}: unknown key {', '.join(sorted(table))}")
        return _engine_text(dataclasses.replace(spec, **overrides)) if overrides else spec

    if kind == "monograph":
        overrides |= hooks.bind(SPEC_HOOKS, names, where, by_name=False)
        prepare = table.pop("prepare", None)
        prepare_fn = None if prepare is None else hooks.named(prepare, f"{where}prepare")
        return monograph_edition(edition_spec(), edition_dir, summary or "", prepare_fn)
    if kind == "facsimile":
        style_table = table.pop("facsimile", None)
        if style_table is None:
            raise BookFileError(f"{where}facsimile: a facsimile edition needs a [{where}facsimile] table")
        style_fields = _fields(FacsimileStyle, style_table, f"{where}facsimile", folder)
        style_fields |= hooks.bind(FACSIMILE_HOOKS, names, where)
        try:
            style = FacsimileStyle(**style_fields)
        except TypeError as e:
            raise BookFileError(f"{where}facsimile: {e}") from None
        visual = table.pop("visual", None)
        limits = None if visual is None else _dataclass(VisualLimits, visual, f"{where}visual", folder)
        extra = {} if summary is None else {"summary": summary}
        return facsimile_edition(edition_spec(), edition_dir, style, visual=limits, **extra)
    raise BookFileError(f"{where}kind: {kind!r} is not one of 'monograph', 'facsimile'")


def load_toml(key: str, folder: Path) -> Book:
    """The book that `books/<key>/book.toml` describes. Its top-level keys are `MonographSpec` fields;
    `hooks.py` beside it fills the fields that take functions."""
    path = folder / BOOK_TOML
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    data.pop("aliases", None)
    out_dir = _out_dir(data, OUTPUT / key, "")
    tables = data.pop("editions", {})
    names = data.pop("hooks", {})
    hooks = _Hooks(key, folder)
    try:
        bound = hooks.bind((*SPEC_HOOKS, "figures"), names, "")
        figures = bound.pop("figures", None)
        spec = _dataclass(MonographSpec, data, "", folder)
        spec = _engine_text(dataclasses.replace(spec, **bound) if bound else spec)
        editions = {name: _edition(name, table, spec, out_dir, hooks, folder) for name, table in tables.items()}
        hooks.check_all_bound()
    except BookFileError as e:
        raise BookFileError(f"{path}: {e}") from None
    return Book(spec, out_dir, editions or {"monograph": monograph_edition(spec, out_dir, "monograph")}, figures)


def load_book(key: str, folder: Path) -> Book:
    if (folder / BOOK_PY).is_file():
        return module(key).BOOK
    return load_toml(key, folder)


class _Books(Mapping[str, Book]):
    """Every book by key. Listing the keys loads nothing; each book loads on first lookup."""

    def __init__(self) -> None:
        self._folders = book_folders()
        self._loaded: dict[str, Book] = {}

    def __getitem__(self, key: str) -> Book:
        if key not in self._loaded:
            folder = self._folders[key]
            try:
                self._loaded[key] = load_book(key, folder)
            except Exception as e:
                raise BookLoadError(f"book {key!r} failed to load: {e}") from e
        return self._loaded[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._folders)

    def __len__(self) -> int:
        return len(self._folders)


@cache
def books() -> Mapping[str, Book]:
    """Every book by key. The key is its folder name under books/."""
    return _Books()


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


def _aliases(folder: Path) -> list[str]:
    toml = folder / BOOK_TOML
    if not toml.is_file():
        return []
    aliases = tomllib.loads(toml.read_text(encoding="utf-8")).get("aliases", [])
    if not (isinstance(aliases, list) and all(isinstance(a, str) for a in aliases)):
        raise BookFileError(f"{toml}: aliases: expected an array of strings, got {aliases!r}")
    return aliases


def book_by_key(key: str) -> Book:
    """The book with key `key`, which may spell underscores as hyphens or be an alias; raises KeyError naming the keys."""
    known = books()
    folders = book_folders()
    names = {k: k for k in known}
    names |= {k.replace("_", "-"): k for k in known}
    names |= {alias: k for k in known if k in folders for alias in _aliases(folders[k])}
    if key not in names:
        raise KeyError(f"unknown book {key!r}; known: {', '.join(known)}")
    return known[names[key]]


def book_for_scan(source: Path, key: str | None = None) -> Book | None:
    """The book named by `key`, else the book whose specs match the scan's file name."""
    if key is not None:
        return book_by_key(key)
    for book in books().values():
        specs = [book.spec, *(e.spec for e in book.editions.values() if e.spec is not None)]
        if any(_names(spec, source) for spec in specs):
            return book
    return None
