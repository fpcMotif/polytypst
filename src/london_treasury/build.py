"""`build_london_treasury`: parse the reader PDF and write every output format."""

import shutil
import subprocess
from pathlib import Path

import pymupdf

from ..compiler.monograph import REPO_FONTS_DIR, MonographOutputs, compile_typst
from ..parity.source import source_pdf as resolve_source_pdf
from .reader import parse_reader_pdf
from .render import (
    _write_epub_assets,
    render_epub_markdown,
    render_markdown,
    render_typst,
)
from .spec import LONDON_TREASURY_SPEC

EPUB_CSS = Path(__file__).with_name("epub.css")


EPUB_FONTS = ("SourceSerif4-Regular", "SourceSerif4-It", "SourceSerif4-Bold", "SourceSerif4-BoldIt", "SourceSans3-Regular", "SourceSans3-Bold")


def build_london_treasury(
    source_pdf: Path | None = None, out_dir: Path | None = None
) -> MonographOutputs:
    src = resolve_source_pdf(LONDON_TREASURY_SPEC, source_pdf)
    target_dir = out_dir or Path("output/london_treasury")
    target_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_reader_pdf(src, target_dir)
    md_text = render_markdown(parsed)
    typ_text = render_typst(parsed)

    slug = LONDON_TREASURY_SPEC.slug
    md_path = target_dir / f"{slug}.md"
    typ_path = target_dir / f"{slug}.typ"
    tex_path = target_dir / f"{slug}.tex"
    pdf_path = target_dir / f"{slug}.pdf"
    epub_path = target_dir / f"{slug}.epub"

    md_path.write_text(md_text, encoding="utf-8")
    typ_path.write_text(typ_text, encoding="utf-8")

    compile_typst(typ_path, pdf_path)

    subprocess.run(
        [
            "pandoc",
            str(md_path),
            "-f",
            "markdown-tex_math_dollars-raw_tex-raw_html",
            "-t",
            "latex",
            "-s",
            "--toc",
            "--top-level-division=chapter",
            "-V",
            "documentclass=ctexbook",
            "-V",
            "geometry:margin=2.4cm",
            "-o",
            str(tex_path),
        ],
        check=True,
    )

    asset_dir = target_dir / "epub_assets"
    _write_epub_assets(asset_dir)
    subprocess.run(
        [
            "pandoc",
            "-f",
            "markdown-tex_math_dollars-raw_tex-raw_html",
            "-t",
            "epub3",
            "--toc",
            "--toc-depth=2",
            "--css",
            str(EPUB_CSS),
            "--resource-path",
            str(asset_dir),
            *(f"--epub-embed-font={REPO_FONTS_DIR / f'{name}.otf'}" for name in EPUB_FONTS),
            "--metadata",
            f"title={parsed.title}",
            "--metadata",
            f"author={LONDON_TREASURY_SPEC.author}",
            "--metadata",
            "lang=zh-CN",
            "-o",
            str(epub_path),
        ],
        input=render_epub_markdown(parsed),
        text=True,
        check=True,
    )

    for src_f, alias_name in (
        (md_path, "book.md"),
        (typ_path, "book.typ"),
        (tex_path, "book.tex"),
        (pdf_path, "book.pdf"),
        (epub_path, "book.epub"),
    ):
        shutil.copy2(src_f, target_dir / alias_name)

    with pymupdf.open(pdf_path) as built_doc:
        total_pages = len(built_doc)

    return MonographOutputs(
        markdown_path=md_path,
        latex_path=tex_path,
        typst_path=typ_path,
        pdf_path=pdf_path,
        total_pages=total_pages,
    )
