"""Convert Goursat's Course in Mathematical Analysis: figures, OCR, stitching, and vector art."""

import argparse
import re
from pathlib import Path

from ..book_state import book_state
from ..compiler.monograph import MonographSpec
from ..compiler.page_cleaner import PageCleaner
from ..ocr.backend import Backend, backend_argument
from ..ocr.lines import LineStore, source_ocr_dir
from ..ocr.pages import LinePage, PageImage, Transcriber, page_images
from ..ocr.transcripts import TranscriptStore
from ..tex_markdown import repair_page_math
from ..vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    FigureExtractor,
    load_complete_figures_manifest,
    write_figures_manifest,
)
from .figures import (
    export_goursat_figures,
    export_goursat_web_gallery,
    normalize_goursat_markdown,
)

GOURSAT_LAST_TEXT_PAGE = 553
_DOLLAR_REGEX = re.compile(r"(?<!\\)\$")
GOURSAT_RUNNING_HEADERS = (
    "A COURSE IN MATHEMATICAL ANALYSIS",
    "DERIVATIVES AND DIFFERENTIALS",
    "IMPLICIT FUNCTIONS",
    "FUNCTIONAL DETERMINANTS",
    "CHANGE OF VARIABLE",
    "SERIES",
    "DEFINITE INTEGRALS",
    "APPLICATIONS TO GEOMETRY",
)
SECTION_MARK = r"\[?[IVXLCDM1K]+[\.,]\s*(?:§+\s*[0-9a-z:]*|Ex[a-z]*\.?)\]?"
NAMED_RUNNING_HEADER = (
    rf"^[*\s]*(?:#+\s*)?(?:(?:{SECTION_MARK}|\d{{1,4}})\s+)?"
    rf"(?:{'|'.join(re.escape(h) for h in GOURSAT_RUNNING_HEADERS)})"
    rf"(?:\s+(?:{SECTION_MARK}|\d{{1,4}}))?[*\s]*$"
)
SECTION_RUNNING_HEADER = (
    r"(?-i:^[*\s]*(?:#+\s*)?(?:"
    r"\[?[IVXLCDM1K]+[\.,]\s*(?:§+\s*[0-9a-z:]*|Ex[a-z]*\.?)\]?(?:\s+[A-Z][A-Z\s\.,'\-]*\s*\d{0,4})?"
    r"|"
    r"(?:§?\d{1,4}\s+)?[A-Z][A-Z\s\.,'\-]{3,}\s+\[?[IVXLCDM1K]+[\.,]\s*(?:§+\s*[0-9a-z:]*|Ex[a-z]*\.?)\]?"
    r"|"
    r"[ivxlcdm]+\s+[A-Z][A-Z\s'\-]{3,}"
    r"|"
    r"[A-Z][A-Z\s'\-]{3,}\s+[ivxlcdm]+"
    r")[*\s]*$)"
)
GOURSAT_SPEC = MonographSpec(
    domain="math",
    slug="goursat",
    title="A Course in Mathematical Analysis",
    author="Édouard Goursat",
    folio_pattern=r"^\d{1,4}$",
    running_header_regexes=(SECTION_RUNNING_HEADER, NAMED_RUNNING_HEADER),
    normalize_headings=False,
    equation_numbering="none",
)


def place_figures(page_text: str, figures: list[ExtractedFigure]) -> str:
    """Inject figure markdown images into the text near their captions."""
    modified_text = page_text
    placed: set[str] = set()

    for fig in figures:
        fig_tag = (
            f"\n\n![{fig.caption}]({fig.image_rel_path}){{#fig:{fig.figure_id}}}\n\n"
        )
        alt_id = fig.figure_id.replace("_", ", ")

        standalone_pat = re.compile(
            rf"^[ \t\*]*(?:fig|figure|abbildung|图)\.?\s*(?:{re.escape(fig.figure_id)}|{re.escape(alt_id)})\b[^\n]*$",
            re.IGNORECASE | re.MULTILINE,
        )
        m_standalone = standalone_pat.search(modified_text)
        if m_standalone:
            line_text = m_standalone.group(0).strip().strip("*").strip()
            if len(line_text) <= 24:
                modified_text = (
                    modified_text[: m_standalone.start()]
                    + fig_tag
                    + modified_text[m_standalone.end() :]
                )
            else:
                line_end = modified_text.find("\n", m_standalone.end())
                idx = line_end if line_end != -1 else len(modified_text)
                modified_text = modified_text[:idx] + fig_tag + modified_text[idx:]
            placed.add(fig.figure_id)
            continue

        # Search for exact or loose caption mention (e.g. "FIG. 1", "Figure 1", "Fig. 1-1")
        pattern = re.compile(
            rf"(\b(fig|figure|abbildung|图)\.?\s*(?:{re.escape(fig.figure_id)}|{re.escape(alt_id)})\b)",
            re.IGNORECASE,
        )
        match = pattern.search(modified_text)
        if match:
            # Place immediately after the line containing the caption
            para_end = modified_text.find("\n\n", match.end())
            idx = para_end if para_end != -1 else len(modified_text)
            modified_text = modified_text[:idx] + fig_tag + modified_text[idx:]
            placed.add(fig.figure_id)

    # If any figures for this page were not matched in text, append them at the end of the page
    for fig in figures:
        if fig.figure_id not in placed:
            fig_tag = f"\n\n![{fig.caption}]({fig.image_rel_path}){{#fig:{fig.figure_id}}}\n\n"
            modified_text = modified_text + fig_tag

    return modified_text


def goursat_markdown(pages_md: list[tuple[int, str]], figures: list[ExtractedFigure]) -> str:
    cleaner = PageCleaner.for_spec(GOURSAT_SPEC)
    by_page: dict[int, list[ExtractedFigure]] = {}
    for fig in figures:
        by_page.setdefault(fig.source_page, []).append(fig)
    cleaned_pages: list[str] = []
    for pno, raw in pages_md:
        clean_p = cleaner.clean(repair_page_math(raw), pno).body
        if by_page.get(pno):
            clean_p = place_figures(clean_p, by_page[pno]).strip()
        if clean_p:
            cleaned_pages.append(clean_p)

    if not cleaned_pages:
        return ""

    acc = cleaned_pages[0]
    for cur in cleaned_pages[1:]:
        acc_r = acc.rstrip()
        cur_l = cur.lstrip()
        if not cur_l:
            continue
        if len(_DOLLAR_REGEX.findall(acc_r)) % 2 == 1 and cur_l.startswith("$") and not cur_l.startswith("$$"):
            acc = acc_r + " " + cur_l[1:]
            continue
        if re.search(r"[a-zA-Z]{2,}-$", acc_r) and re.match(r"^[a-z]{2,}", cur_l):
            acc = acc_r[:-1] + cur_l
            continue
        last_line = acc_r.splitlines()[-1].strip() if acc_r else ""
        first_line = cur_l.splitlines()[0].strip()
        ends_complete = (
            last_line.endswith((".", "!", "?", ":", ";", "$$", "*", ")", "]"))
            or last_line.startswith(("#", "!["))
            or bool(re.search(r"\{#fig:[^}]+\}$", last_line))
        )
        starts_new = first_line.startswith(
            ("#", "**", "$$", "![", "* ", "- ", "†", "*")
        ) or bool(re.match(r"^(?:\d+\.|\([0-9a-zA-Z']+\)|[IVXLCDM]+\.)\s", first_line))
        if not ends_complete and not starts_new:
            acc = acc_r + " " + cur_l
        else:
            acc = acc_r + "\n\n" + cur_l

    return acc


def _figures(
    pdf_path: Path, out_dir: Path, renders: list[PageImage]
) -> list[ExtractedFigure]:
    manifest_path = out_dir / FIGURES_MANIFEST_NAME
    cached = load_complete_figures_manifest(manifest_path)
    if cached is not None:
        return cached
    extractor = FigureExtractor(pdf_path)
    lines = LineStore(source_ocr_dir(out_dir)).read(renders, extractor.reader)
    ocr_pages = [LinePage(number, page_lines) for number, page_lines in lines.items()]
    figures = extractor.extract_figures_from_ocr_pages(
        ocr_pages, out_dir / "figures", dpi=300
    )
    write_figures_manifest(manifest_path, figures)
    return figures


def build_goursat(pdf_path: Path, out_dir: Path, transcriber: Transcriber) -> Path:
    """Write `book.md`, the vector figures, and the web gallery into `out_dir`."""
    pages = page_images(out_dir / "page_renders")
    figures = _figures(pdf_path, out_dir, pages)
    print(f"{len(figures)} figures grounded.")

    text_pages = [p for p in pages if p.number <= GOURSAT_LAST_TEXT_PAGE]
    store = TranscriptStore(book_state(out_dir) / "markdown_pages")
    pages_md = store.transcribe(text_pages, transcriber)
    print(f"{len(pages_md)}/{len(text_pages)} pages transcribed.")

    master_md = normalize_goursat_markdown(goursat_markdown(sorted(pages_md.items()), figures))
    master_path = out_dir / "book.md"
    _ = master_path.write_text(master_md, encoding="utf-8")
    svgs = export_goursat_figures(out_dir / "figures")
    gallery = export_goursat_web_gallery(out_dir / "web_figures")
    print(f"{len(svgs)} vector figures; gallery at {gallery}")
    return master_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("pdf", type=Path)
    _ = parser.add_argument("--out", type=Path, default=Path("output/goursat_colab"))
    _ = parser.add_argument(
        "--backend",
        type=backend_argument,
        default=Backend.parse("colab?session=goursat"),
        help="OCR backend as KIND[:MODEL][?KEY=VALUE&...], as in `polytypst --backend`",
    )
    args = parser.parse_args()
    path = build_goursat(args.pdf, args.out, args.backend.transcriber(None))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
