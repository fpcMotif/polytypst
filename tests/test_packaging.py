import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_source_folder_ships_as_a_package() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    listed = set(config["tool"]["setuptools"]["packages"])
    src = ROOT / "src"
    folders = [src, *(p for p in src.rglob("*") if p.is_dir())]
    expected = {
        ".".join(("polytypst", *d.relative_to(src).parts))
        for d in folders
        if "__pycache__" not in d.parts and any(d.glob("*.py"))
    }
    assert sorted(expected - listed) == []
