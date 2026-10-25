import json
from pathlib import Path

from ..compiler.typst_math import run_typst


def query_marks(typ: Path, inputs: dict[str, str] | None = None) -> list[dict]:
    """Source-page position markers (kind, key, page, y) from a compiled vintage Typst source."""
    flags = [arg for k, v in (inputs or {}).items() for arg in ("--input", f"{k}={v}")]
    res = run_typst("query", *flags, str(typ), "<src-mark>", "--field", "value", capture_output=True)
    return json.loads(res.stdout)
