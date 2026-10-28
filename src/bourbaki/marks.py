from pathlib import Path

from ..compiler.typst_math import query_typst


def query_marks(typ: Path, inputs: dict[str, str] | None = None) -> list[dict]:
    """Source-page position markers (kind, key, page, y) from a compiled vintage Typst source."""
    return query_typst(typ, "<src-mark>", "value", inputs or {})
