"""3Blue1Brown-styled SVG geometry primitives and colors for Algebra I."""

FONT = '"New Computer Modern", "Latin Modern Math", "STIX Two Math", "Times New Roman", serif'
INK = "#0f172a"
SLATE = "#475569"
MUTED = "#94a3b8"

# 3Blue1Brown palette
BLUE = "#2563eb"
BLUE_BG = "#eff6ff"
AMBER = "#d97706"
AMBER_BG = "#fffbeb"
GREEN = "#059669"
GREEN_BG = "#f0fdf4"
RED = "#e11d48"
RED_BG = "#fff1f2"
PURPLE = "#7c3aed"
PURPLE_BG = "#f5f3ff"
TEAL = "#0891b2"


def marker_defs() -> str:
    return f"""
    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="{INK}" />
    </marker>
    <marker id="arr-rev" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
      <path d="M 9 1.5 L 0 5 L 9 8.5 L 7 5 z" fill="{INK}" />
    </marker>
    <marker id="arr-axis" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="{SLATE}" />
    </marker>
    <marker id="arr-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="{BLUE}" />
    </marker>
    <marker id="arr-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="{RED}" />
    </marker>
    <marker id="arr-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="{GREEN}" />
    </marker>
    <marker id="arr-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="{AMBER}" />
    </marker>
"""


_SUB_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_SUP_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def _clean_svg_scripts(s: str) -> str:
    import re
    s = re.sub(
        r"[₀₁₂₃₄₅₆₇₈₉]+",
        lambda m: f'<tspan baseline-shift="sub" font-size="75%">{m.group(0).translate(_SUB_MAP)}</tspan>',
        s,
    )
    return re.sub(
        r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+",
        lambda m: f'<tspan baseline-shift="super" font-size="75%">{m.group(0).translate(_SUP_MAP)}</tspan>',
        s,
    )


def svg_wrap(w: int, h: int, content: str) -> str:
    content = _clean_svg_scripts(content)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h + 16}" width="{w}" height="{h + 16}">
  <defs>
{marker_defs()}  </defs>
  <rect width="100%" height="100%" fill="#ffffff" />
  <g font-family='{FONT}' font-size="15" fill="{INK}">
{content}
  </g>
</svg>"""


def point(x: float, y: float, r: float = 3.6, fill: str = INK, stroke: str = "#ffffff", stroke_width: float = 1.2) -> str:
    s = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ""
    return f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"{s} />'


def pt_labeled(
    x: float,
    y: float,
    label: str,
    dx: float = 6.0,
    dy: float = -6.0,
    r: float = 3.6,
    fill: str = INK,
    font_size: int = 15,
) -> str:
    return (
        f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="#ffffff" stroke-width="1.2" />\n'
        f'    <text x="{x + dx:.1f}" y="{y + dy:.1f}" font-style="italic" font-size="{font_size}">{label}</text>'
    )


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str = INK,
    width: float = 1.6,
    dash: str = "",
) -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d} stroke-linecap="round" />'


def arrow(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str = INK,
    width: float = 1.6,
    marker: str = "arr",
) -> str:
    m = f' marker-end="url(#{marker})"' if marker else ""
    return f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{m} stroke-linecap="round" />'


def resolve_scan_pdf() -> str:
    import os
    from pathlib import Path
    sources = os.environ.get("POLYTYPST_SOURCES") or str(Path.home() / "Downloads")
    fallback = str(Path(sources) / "Algebra I Basic Notions Of Algebra (Kostrikin A I, Shafarevich I R).pdf")
    try:
        from polytypst.books import BookLoadError, book_by_key
        from polytypst.ocr.scan import SourceScanError
        from polytypst.parity.source import source_pdf
    except ImportError:
        return fallback
    try:
        return str(source_pdf(book_by_key("algebra1").spec))
    except (KeyError, BookLoadError, SourceScanError):
        return fallback


def scan_crop_svg(pdf_path: str, page_num: int, clip_fraction: tuple[float, float, float, float], dpi: int = 250) -> str:
    """Extract a clean high-resolution crop from the scan PDF and wrap in SVG."""
    import base64

    import pymupdf

    doc = pymupdf.open(pdf_path)
    page = doc[page_num - 1]
    r = page.rect
    x0, y0, x1, y1 = clip_fraction
    clip = pymupdf.Rect(r.width * x0, r.height * y0, r.width * x1, r.height * y1)
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    b64_png = base64.b64encode(pix.tobytes("png")).decode("ascii")
    w, h = pix.width, pix.height
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <image href="data:image/png;base64,{b64_png}" width="{w}" height="{h}" />
</svg>"""
