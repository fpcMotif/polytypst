import json
import re
import tomllib
from pathlib import Path

import pymupdf

from polytypst.parity.source import source_pdf

KEY = Path(__file__).parent.name
BOOK_TOML = tomllib.loads((Path(__file__).parent / "book.toml").read_text(encoding="utf-8"))
RUNNING_HEADER_REGEXES = tuple(BOOK_TOML["running_header_regexes"])
CHAPTER_TITLES = {c["title"] for c in BOOK_TOML["chapters"]}

# The section rule reads `3 20世纪…` as a number and a title only when the title starts with a non-digit.
WORD_JOINER = "⁠"

HEADED_BYLINES = ("伊藤元重", "本间正义", "德丸浩", "佐佐木百合")

FALSE_HEADINGS = (
    r"^(?:#+\s*)?为了政策目标。$",
)


def intl_econ_heading_hook(lt: str, chapter: int) -> str | None:
    for rx in RUNNING_HEADER_REGEXES:
        if re.match(rx, lt, re.IGNORECASE):
            return ""
    for rx in FALSE_HEADINGS:
        if re.match(rx, lt):
            return re.sub(r"^#+\s*", "", lt)
    if re.match(r"^#+\s*(?:（日本）内阁府经济社会综合研究所|作者简介|中文版前言|中文版序言|序\s*国际经济环境的变化与日本经济)$", lt):
        return ""
    if m := re.match(rf"^#+\s*((?:——|{'|'.join(HEADED_BYLINES)}).*)$", lt):
        return m.group(1)
    if m := re.match(r"^#+\s*(\d+\s*世纪.*)$", lt):
        return "### " + re.sub(r"\s+", "", m.group(1))
    if m := re.match(r"^#+\s*(\d+)\s+(\d+世纪.*)$", lt):
        return f"### {m.group(1)} {WORD_JOINER}{m.group(2)}"
    # The cleaner keeps only the first of equal headings across the book, which drops every later `1 前言` and `导 语`.
    if m := re.match(r"^#+\s*(.+?)\s*$", lt):
        inner = m.group(1)
        if re.sub(r"^\d+\s+", "", inner) in CHAPTER_TITLES:
            return None
        return f"### {inner}" if len(inner) <= 90 else inner
    return None


_PREFACE_CHART = "preface_exchange_rate.png"
# The preface's exchange-rate chart has no figure number, so figure extraction skips it.
_PREFACE_CHART_PAGE = 17
_PREFACE_CHART_BOX = (0.15, 0.555, 0.83, 0.835)


def _spec():
    from polytypst.books import book_by_key

    return book_by_key(KEY).spec


def _crop_preface_chart(out_dir: Path) -> None:
    """Crop the uncaptioned preface chart, with its printed title, from the scan at the scan's own size."""
    spec = _spec()
    target = out_dir / spec.figure_dir / _PREFACE_CHART
    if target.exists():
        return
    with pymupdf.open(source_pdf(spec)) as scan:
        page = scan[_PREFACE_CHART_PAGE - 1]
        x0, y0, x1, y1 = _PREFACE_CHART_BOX
        r = page.rect
        clip = pymupdf.Rect(
            r.x0 + r.width * x0,
            r.y0 + r.height * y0,
            r.x0 + r.width * x1,
            r.y0 + r.height * y1,
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        page.get_pixmap(dpi=300, clip=clip).save(target)


# Scan p313 prints two charts, 10-7A (women) and 10-7B (men); figure extraction kept one box as 10-7.
_SPLIT_FIGURES = {
    "10-7A": (
        313,
        (0.1805, 0.372, 0.8301, 0.6052),
        "图 10-7A 新员工各年龄段的薪酬（女性，月收入）",
    ),
    "10-7B": (
        313,
        (0.1805, 0.643, 0.8301, 0.856),
        "图 10-7B 新员工各年龄段的薪酬（男性，月收入）",
    ),
}


def _split_figure_10_7(out_dir: Path) -> None:
    spec = _spec()
    manifest_path = out_dir / "figures_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not any(f["figure_id"] == "10-7" for f in manifest):
        return
    entries = []
    with pymupdf.open(source_pdf(spec)) as scan:
        for figure_id, (page_number, box, caption) in _SPLIT_FIGURES.items():
            page = scan[page_number - 1]
            r = page.rect
            x0, y0, x1, y1 = box
            clip = pymupdf.Rect(
                r.width * x0, r.height * y0, r.width * x1, r.height * y1
            )
            rel = f"{spec.figure_dir}/fig_{figure_id}.png"
            pix = page.get_pixmap(dpi=600, clip=clip)
            pix.save(out_dir / rel)
            entries.append(
                {
                    "figure_id": figure_id,
                    "caption": caption,
                    "image_rel_path": rel,
                    "source_page": page_number,
                    "box": list(box),
                    "width_px": pix.width,
                    "height_px": pix.height,
                }
            )
    at = next(i for i, f in enumerate(manifest) if f["figure_id"] == "10-7")
    (out_dir / manifest[at]["image_rel_path"]).unlink(missing_ok=True)
    manifest[at : at + 1] = entries
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def prepare_figures(out_dir: Path) -> None:
    _crop_preface_chart(out_dir)
    _split_figure_10_7(out_dir)
