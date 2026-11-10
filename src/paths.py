import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTPUT_ENV = "POLYTYPST_OUTPUT"
ASSETS_ENV = "POLYTYPST_ASSETS"


def _root(env: str, sibling: str) -> Path:
    value = os.environ.get(env)
    return Path(value).expanduser() if value else REPO.parent / sibling


OUTPUT = _root(OUTPUT_ENV, "polytypst-output")
ASSETS = _root(ASSETS_ENV, "polytypst-assets")
FONTS = ASSETS / "fonts"
