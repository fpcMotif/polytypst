from dataclasses import replace
import os
from pathlib import Path
import re

import pymupdf

from polytypst.vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    load_figures_manifest,
    write_figures_manifest,
)

_CROP_DPI = 300
_FALLBACK_SCAN = Path(
    "/Users/martinfan/Downloads/An Introduction to the Theory of Numbers, Sixth Edition (G. H. Hardy, E. M. Wright) .pdf"
)
_SOURCE_NAME = "An Introduction to the Theory of Numbers, Sixth Edition (G. H. Hardy, E. M. Wright) .pdf"

_FIGURE_BOXES: dict[str, tuple[int, tuple[float, float, float, float]]] = {
    "1": (44, (304.0, 402.0, 452.0, 639.0)),
    "2a": (47, (167.0, 136.0, 257.0, 265.0)),
    "2b": (47, (308.0, 136.0, 436.0, 265.0)),
    "2c": (47, (258.0, 281.0, 344.0, 371.0)),
    "3a": (52, (137.0, 137.0, 297.0, 226.5)),
    "3b": (52, (307.0, 137.0, 456.0, 227.5)),
    "4": (64, (138.0, 297.0, 457.0, 320.0)),
    "5": (88, (204.0, 310.0, 390.0, 466.0)),
    "6": (108, (166.0, 291.0, 430.0, 443.0)),
    "7": (310, (146.0, 293.0, 450.0, 641.0)),
    "8": (361, (185.0, 136.0, 410.0, 359.0)),
    "9": (518, (174.0, 136.0, 436.0, 433.0)),
    "10": (520, (322.0, 498.0, 464.0, 638.0)),
    "11": (564, (144.0, 136.0, 451.0, 255.0)),
}

_ROMAN_CHAPTER_RE = re.compile(r"^(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|XXI|XXII|XXIII|XXIV|XXV)$")

_CHAPTER_TITLE_DROP_RE = re.compile(
    r"^(?:"
    r"THE SERIES OF PRIMES \([123]\)"
    r"|FAREY SERIES AND A THEOREM OF MINKOWSKI"
    r"|IRRATIONAL NUMBERS"
    r"|CONGRUENCES AND RESIDUES"
    r"|FERMAT['’]S THEOREM AND ITS CONSEQUENCES"
    r"|GENERAL PROPERTIES OF CONGRUENCES"
    r"|CONGRUENCES TO COMPOSITE MODULI"
    r"|THE REPRESENTATION OF NUMBERS BY DECIMALS"
    r"|CONTINUED FRACTIONS"
    r"|APPROXIMATION OF IRRATIONALS BY RATIONALS"
    r"|THE FUNDAMENTAL THEOREM OF ARITHMETIC"
    r"|IN \$k\(1\)\$, \$k\(i\)\$, AND \$k\(\\rho\)\$"
    r"|SOME DIOPHANTINE EQUATIONS"
    r"|QUADRATIC FIELDS \([12]\)"
    r"|THE ARITHMETICAL FUNCTIONS \$\\phi\(n\)\$, \$\\mu\(n\)\$,"
    r"|\$d\(n\), \\sigma\(n\)\$, \$r\(n\)\$"
    r"|GENERATING FUNCTIONS OF ARITHMETICAL FUNCTIONS"
    r"|THE ORDER OF MAGNITUDE OF ARITHMETICAL FUNCTIONS"
    r"|PARTITIONS"
    r"|THE REPRESENTATION OF A NUMBER BY TWO OR FOUR SQUARES"
    r"|REPRESENTATION BY CUBES AND HIGHER POWERS"
    r"|KRONECKER['’]S THEOREM"
    r"|GEOMETRY OF NUMBERS"
    r"|ELLIPTIC CURVES"
    r")$"
)

_FRONT_BACK_DROP_RE = re.compile(
    r"^(?:"
    r"FOREWORD BY ANDREW WILES"
    r"|PREFACE TO THE (?:SIXTH|FIFTH|FIRST) EDITION"
    r"|REMARKS ON NOTATION"
    r"|A\s*LIST OF BOOKS"
    r"|APPENDIX"
    r")$"
)

_SECTION_LINE_RE = re.compile(r"^(?:#{1,4}\s*|\*\*)?(?P<c>\d{1,2})\.(?P<s>\d{1,2})\.?\s+(?P<rest>.+)$")
_APPENDIX_ITEM_RE = re.compile(r"^(?:#{1,4}\s*|\*\*)(?P<n>[123])\.\s+(?P<rest>.+)$")
_NOTES_RE = re.compile(r"^(?:#{1,4}\s*)?NOTES$")
_DOT_SPLIT_RE = re.compile(r"^((?:[^.$]|\$[^$]*\$)+?)\.(?:\s+(.*))?$")


def _split_title_and_tail(rest: str, bolded: bool) -> tuple[str, str]:
    tail = ""
    raw = rest.strip()
    if bolded and "**" in raw:
        raw, after = raw.split("**", 1)
        tail = after.strip()
    m_dot = _DOT_SPLIT_RE.match(raw.strip())
    if m_dot:
        title = m_dot.group(1).strip()
        extra = (m_dot.group(2) or "").strip()
        if extra:
            tail = f"{extra} {tail}".strip() if tail else extra
    else:
        title = raw.rstrip(".*").strip()
    title = title.rstrip(".*").strip()
    return title, tail


def hardy_heading_hook(lt: str, chapter: int) -> str | None:
    stripped = lt.strip()
    plain = re.sub(r"^#+\s*", "", stripped).strip()
    if chapter == 0:
        if _FRONT_BACK_DROP_RE.match(plain):
            return ""
        if m_app := _APPENDIX_ITEM_RE.match(stripped):
            title, tail = _split_title_and_tail(m_app.group("rest"), stripped.startswith("**"))
            return f"### {m_app.group('n')}. {title}\n\n{tail}" if tail else f"### {m_app.group('n')}. {title}"
        return None

    if _ROMAN_CHAPTER_RE.match(plain) or _CHAPTER_TITLE_DROP_RE.match(plain):
        return ""
    if _NOTES_RE.match(plain):
        return "## Notes"
    if m_sec := _SECTION_LINE_RE.match(stripped):
        c = int(m_sec.group("c"))
        s = int(m_sec.group("s"))
        if c == chapter:
            title, tail = _split_title_and_tail(m_sec.group("rest"), stripped.startswith("**"))
            if tail == "(continued)":
                title = f"{title} (continued)"
                tail = ""
            heading = f"## {c}.{s}. {title}"
            return f"{heading}\n\n{tail}" if tail else heading
    return None


def _scan_path() -> Path:
    if src_env := os.environ.get("POLYTYPST_SOURCES"):
        cand = Path(src_env) / _SOURCE_NAME
        if cand.is_file():
            return cand
    return _FALLBACK_SCAN


def draw_figures(out_dir: Path) -> list[Path]:
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    scan_path = _scan_path()
    written: list[Path] = []
    crops: dict[str, tuple[tuple[float, float, float, float], int, int]] = {}
    with pymupdf.open(scan_path) as doc:
        for fid, (page_no, rect_pt) in _FIGURE_BOXES.items():
            page = doc[page_no - 1]
            r = page.rect
            clip = pymupdf.Rect(*rect_pt)
            pix = page.get_pixmap(dpi=_CROP_DPI, clip=clip, colorspace=pymupdf.csGRAY)
            dest = fig_dir / f"fig_{fid}.png"
            pix.save(dest)
            written.append(dest)
            norm_box = (
                round(rect_pt[0] / r.width, 4),
                round(rect_pt[1] / r.height, 4),
                round(rect_pt[2] / r.width, 4),
                round(rect_pt[3] / r.height, 4),
            )
            crops[fid] = (norm_box, pix.width, pix.height)

    manifest = out_dir / FIGURES_MANIFEST_NAME
    if manifest.exists():
        entries = load_figures_manifest(manifest)
        updated = [
            replace(
                f,
                box=crops[f.figure_id][0],
                width_px=crops[f.figure_id][1],
                height_px=crops[f.figure_id][2],
            )
            if f.figure_id in crops
            else f
            for f in entries
        ]
        write_figures_manifest(manifest, updated)
    return written
