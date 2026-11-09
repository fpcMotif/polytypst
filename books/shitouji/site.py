"""Shitouji on the website: the vertical volumes built in the assets folder, and each 回 read from the source PDF's glyphs."""

import shutil
from pathlib import Path

from polytypst.parity.source import sources_dir
from polytypst.web_exporter import SiteContent, SitePage, SiteSource

from .vertical import extract_chapters


def _page_count(pdf: Path) -> int:
    import pymupdf

    with pymupdf.open(pdf) as doc:
        return doc.page_count


def content(page: SitePage, source: SiteSource, dest: Path, web_base: str) -> SiteContent:
    layout = page.layout
    volumes = sorted(source.folder.glob(layout["volumes"]))
    if not volumes:
        return SiteContent([])
    if len(volumes) > len(layout["volume_labels"]):
        raise ValueError(f"{page.toml}: {len(volumes)} volumes but {len(layout['volume_labels'])} volume_labels")
    editions: list[dict[str, str]] = []
    pages = 0
    for label, pdf in zip(layout["volume_labels"], volumes, strict=False):
        files: dict[str, str] = {}
        for src, key in ((pdf, "pdf"), (pdf.with_suffix(".typ"), "typst"), (source.folder / layout["latex"] / f"{pdf.stem}.tex", "latex")):
            if src.exists():
                shutil.copy2(src, dest / src.name)
                files[key] = f"{web_base}/{src.name}"
        pages += _page_count(pdf)
        editions.append({"name": pdf.stem, "label": label, **files})
    scan = sources_dir(layout["source_pdf"]) / layout["source_pdf"]
    return SiteContent(extract_chapters(scan, layout["first_page"]), editions=editions, pages=pages)
