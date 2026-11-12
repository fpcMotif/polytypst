import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTPUT_ENV = "POLYTYPST_OUTPUT"
ASSETS_ENV = "POLYTYPST_ASSETS"
BUILD_ENV = "POLYTYPST_BUILD"


def _root(env: str, sibling: str) -> Path:
    value = os.environ.get(env)
    return Path(value).expanduser() if value else REPO.parent / sibling


def build_root() -> Path | None:
    """The folder that holds each book's build sources, `$POLYTYPST_BUILD`, read at each call so `--build-dir` can set it."""
    value = os.environ.get(BUILD_ENV)
    return Path(value).expanduser() if value else None


def set_build_root(folder: Path) -> None:
    os.environ[BUILD_ENV] = str(folder.expanduser().resolve())


OUTPUT = _root(OUTPUT_ENV, "polytypst-output")
ASSETS = _root(ASSETS_ENV, "polytypst-assets")
FONTS = ASSETS / "fonts"
