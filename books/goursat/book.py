import dataclasses
from pathlib import Path

from polytypst.books import load_toml

from .figures import export_goursat_figures, export_goursat_web_gallery


def draw_figures(out_dir: Path) -> list[Path]:
    _ = export_goursat_web_gallery(out_dir / "web_figures")
    return export_goursat_figures(out_dir / "figures")


BOOK = dataclasses.replace(load_toml("goursat", Path(__file__).parent), figures=draw_figures)
