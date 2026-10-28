import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_source_folder_ships_as_a_package() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    listed = set(config["tool"]["setuptools"]["packages"])
    data_globs = config["tool"]["setuptools"]["package-data"].get("polytypst", [])
    src = ROOT / "src"
    folders = [src, *(p for p in src.rglob("*") if p.is_dir())]
    sources = [d for d in folders if "__pycache__" not in d.parts and any(d.glob("*.py"))]
    expected = {
        ".".join(("polytypst", *d.relative_to(src).parts))
        for d in sources
        if all(part.isidentifier() for part in d.relative_to(src).parts)
    }
    shipped_as_data = {p for pattern in data_globs for p in src.glob(pattern)}
    unshipped = [
        py.relative_to(src).as_posix()
        for d in sources
        if not all(part.isidentifier() for part in d.relative_to(src).parts)
        for py in d.glob("*.py")
        if py not in shipped_as_data
    ]
    assert sorted(expected - listed) == []
    assert unshipped == []
