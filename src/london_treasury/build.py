"""`build_london_treasury`: parse the reader PDF and write every output format."""

import subprocess
from pathlib import Path

from ..compiler.monograph import (
    MONOGRAPH_FORMATS,
    MonographOutputs,
    alias_as_book,
    build_outputs,
    compile_typst,
    run_formats,
)
from ..compiler.typst_math import REPO_FONTS_DIR
from ..parity.source import source_pdf as resolve_source_pdf
from .models import ParsedReaderBook
from .reader import parse_reader_pdf
from .render import (
    render_epub_markdown,
    render_markdown,
    render_typst,
    write_epub_assets,
)
from .spec import LONDON_TREASURY_SPEC

EPUB_CSS = Path(__file__).with_name("epub.css")
EPUB_FONTS = ("SourceSerif4-Regular", "SourceSerif4-It", "SourceSerif4-Bold", "SourceSerif4-BoldIt", "SourceSans3-Regular", "SourceSans3-Bold")

LONDON_FORMATS = MONOGRAPH_FORMATS | {"epub"}


def _write_latex(md_path: Path, tex_path: Path) -> None:
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


def _write_epub(parsed: ParsedReaderBook, asset_dir: Path, epub_path: Path) -> None:
    write_epub_assets(asset_dir)
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


def build_london_treasury(
    source_pdf: Path | None = None, out_dir: Path | None = None, formats: frozenset[str] = LONDON_FORMATS
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

    made = run_formats(
        {
            "pdf": (pdf_path, lambda: compile_typst(typ_path, pdf_path)),
            "tex": (tex_path, lambda: _write_latex(md_path, tex_path)),
            "epub": (epub_path, lambda: _write_epub(parsed, target_dir / "epub_assets", epub_path)),
        },
        formats,
    )
    for path in (md_path, typ_path, *made.values()):
        alias_as_book(path)
    return build_outputs(md_path, typ_path, made)
