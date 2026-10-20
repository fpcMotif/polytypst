import json
import subprocess
from pathlib import Path

from ..compiler.monograph import REPO_FONTS_DIR


def query_marks(typ: Path, inputs: dict[str, str] | None = None) -> list[dict]:
    """Source-page position markers (kind, key, page, y) from a compiled vintage Typst source."""
    flags = [arg for k, v in (inputs or {}).items() for arg in ("--input", f"{k}={v}")]
    res = subprocess.run(
        ["typst", "query", "--font-path", str(REPO_FONTS_DIR), *flags, str(typ), "<src-mark>", "--field", "value"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(res.stdout)
