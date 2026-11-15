from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from html import escape
from pathlib import Path

import pymupdf


@dataclass(frozen=True)
class Theme:
    is_dark: bool
    bg: str
    panel: str
    panel_stroke: str
    fg: str
    muted: str
    grid: str
    primary: str
    secondary: str
    cyan: str
    gold: str
    coral: str
    mint: str
    violet: str
    node_fill: str
    node_alt: str
    sink_true_fill: str
    sink_false_fill: str
    lo_stroke: str
    hi_stroke: str
    cell_light: str
    cell_dark: str


MONO_THEME = Theme(
    is_dark=False,
    bg="#FFFFFF",
    panel="#F8FAFC",
    panel_stroke="#CBD5E1",
    fg="#0F172A",
    muted="#475569",
    grid="#CBD5E1",
    primary="#0F172A",
    secondary="#334155",
    cyan="#0F172A",
    gold="#1E293B",
    coral="#334155",
    mint="#1E293B",
    violet="#475569",
    node_fill="#FFFFFF",
    node_alt="#E2E8F0",
    sink_true_fill="#F1F5F9",
    sink_false_fill="#FFFFFF",
    lo_stroke="#475569",
    hi_stroke="#0F172A",
    cell_light="#FFFFFF",
    cell_dark="#CBD5E1",
)

DARK_3B1B_THEME = Theme(
    is_dark=True,
    bg="#090D16",
    panel="#101827",
    panel_stroke="#263449",
    fg="#F8FAFC",
    muted="#94A3B8",
    grid="#1E293B",
    primary="#58C4DD",
    secondary="#83C167",
    cyan="#58C4DD",
    gold="#F4D03F",
    coral="#FF6B6B",
    mint="#83C167",
    violet="#C792EA",
    node_fill="#111A2E",
    node_alt="#1D2B44",
    sink_true_fill="#2B2612",
    sink_false_fill="#2B1419",
    lo_stroke="#FF6B6B",
    hi_stroke="#58C4DD",
    cell_light="#131C2E",
    cell_dark="#263B59",
)

SERIF_FONT = "Georgia, 'Times New Roman', serif"
SANS_FONT = "'Helvetica Neue', Arial, sans-serif"
MONO_FONT = "'Menlo', 'Courier New', monospace"


def fmt(v: float) -> str:
    if abs(v - round(v)) < 1e-4:
        return str(round(v))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def rich_label(raw: str, font_size: float = 12.0) -> str:
    out: list[str] = []
    i = 0
    n = len(raw)
    sub_sz = fmt(font_size * 0.74)
    sub_dy = fmt(font_size * 0.26)
    sup_dy = fmt(-font_size * 0.34)
    while i < n:
        ch = raw[i]
        if ch in ("_", "^") and i + 1 < n:
            is_sub = ch == "_"
            i += 1
            if raw[i] == "{":
                end = raw.find("}", i + 1)
                if end == -1:
                    end = n
                seg = raw[i + 1 : end]
                i = end + 1
            else:
                seg = raw[i]
                i += 1
            dy = sub_dy if is_sub else sup_dy
            back = fmt(-float(dy))
            out.append(
                f'<tspan dy="{dy}" font-size="{sub_sz}" font-style="normal">{escape(seg)}</tspan>'
                f'<tspan dy="{back}">\u200b</tspan>'
            )
        elif raw.startswith("\\bar{", i):
            end = raw.find("}", i + 5)
            if end == -1:
                end = n
            seg = raw[i + 5 : end]
            i = end + 1
            out.append(f'<tspan text-decoration="overline">{escape(seg)}</tspan>')
        else:
            out.append(escape(ch))
            i += 1
    return "".join(out)


class SvgCanvas:
    def __init__(self, width: float, height: float, theme: Theme, pad_bg: bool = True) -> None:
        self.width = width
        self.height = height
        self.theme = theme
        self.defs: list[str] = []
        self.elements: list[str] = []
        self._marker_ids: set[str] = set()
        if theme.is_dark:
            self.defs.append(
                '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">'
                '<feGaussianBlur stdDeviation="1.6" result="blur"/>'
                '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
                "</filter>"
            )
        if pad_bg:
            rx = "8" if theme.is_dark else "0"
            self.elements.append(
                f'<rect x="0" y="0" width="{fmt(width)}" height="{fmt(height)}" rx="{rx}" fill="{theme.bg}"/>'
            )

    def ensure_arrow(self, color: str, size: float = 6.0) -> str:
        clean = re.sub(r"[^a-zA-Z0-9]", "", color)
        mid = f"arr_{clean}_{int(size * 10)}"
        if mid not in self._marker_ids:
            self._marker_ids.add(mid)
            w = fmt(size)
            h = fmt(size * 0.78)
            rx = fmt(size * 0.85)
            ry = fmt(size * 0.39)
            self.defs.append(
                f'<marker id="{mid}" viewBox="0 0 {w} {h}" refX="{rx}" refY="{ry}" '
                f'markerWidth="{w}" markerHeight="{h}" orient="auto-start-reverse">'
                f'<path d="M 0 0 L {w} {ry} L 0 {h} z" fill="{color}"/>'
                f"</marker>"
            )
        return mid

    def add(self, raw_svg: str) -> None:
        self.elements.append(raw_svg)

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str | None = None,
        stroke_width: float = 1.5,
        dashed: bool | str = False,
        arrow_end: bool = False,
        arrow_start: bool = False,
        opacity: float = 1.0,
        linecap: str = "round",
    ) -> None:
        col = stroke or self.theme.fg
        attrs = [
            f'x1="{fmt(x1)}"',
            f'y1="{fmt(y1)}"',
            f'x2="{fmt(x2)}"',
            f'y2="{fmt(y2)}"',
            f'stroke="{col}"',
            f'stroke-width="{fmt(stroke_width)}"',
            f'stroke-linecap="{linecap}"',
        ]
        if dashed:
            dash_str = dashed if isinstance(dashed, str) else "4,3"
            attrs.append(f'stroke-dasharray="{dash_str}"')
        if opacity < 1.0:
            attrs.append(f'opacity="{fmt(opacity)}"')
        if arrow_end:
            mid = self.ensure_arrow(col)
            attrs.append(f'marker-end="url(#{mid})"')
        if arrow_start:
            mid = self.ensure_arrow(col)
            attrs.append(f'marker-start="url(#{mid})"')
        self.elements.append(f"<line {' '.join(attrs)}/>")

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "none",
        stroke: str | None = None,
        stroke_width: float = 1.3,
        rx: float = 0.0,
        dashed: bool | str = False,
        opacity: float = 1.0,
    ) -> None:
        attrs = [
            f'x="{fmt(x)}"',
            f'y="{fmt(y)}"',
            f'width="{fmt(w)}"',
            f'height="{fmt(h)}"',
            f'fill="{fill}"',
        ]
        if rx > 0:
            attrs.append(f'rx="{fmt(rx)}"')
        if stroke and stroke != "none":
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{fmt(stroke_width)}"')
        if dashed:
            dash_str = dashed if isinstance(dashed, str) else "4,3"
            attrs.append(f'stroke-dasharray="{dash_str}"')
        if opacity < 1.0:
            attrs.append(f'opacity="{fmt(opacity)}"')
        self.elements.append(f"<rect {' '.join(attrs)}/>")

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: str = "none",
        stroke: str | None = None,
        stroke_width: float = 1.4,
        dashed: bool | str = False,
        glow: bool = False,
    ) -> None:
        attrs = [
            f'cx="{fmt(cx)}"',
            f'cy="{fmt(cy)}"',
            f'r="{fmt(r)}"',
            f'fill="{fill}"',
        ]
        if stroke and stroke != "none":
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{fmt(stroke_width)}"')
        if dashed:
            dash_str = dashed if isinstance(dashed, str) else "3,2.5"
            attrs.append(f'stroke-dasharray="{dash_str}"')
        if glow and self.theme.is_dark:
            attrs.append('filter="url(#glow)"')
        self.elements.append(f"<circle {' '.join(attrs)}/>")

    def ellipse(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        fill: str = "none",
        stroke: str | None = None,
        stroke_width: float = 1.4,
        dashed: bool | str = False,
        rotate: float = 0.0,
        opacity: float = 1.0,
    ) -> None:
        attrs = [
            f'cx="{fmt(cx)}"',
            f'cy="{fmt(cy)}"',
            f'rx="{fmt(rx)}"',
            f'ry="{fmt(ry)}"',
            f'fill="{fill}"',
        ]
        if stroke and stroke != "none":
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{fmt(stroke_width)}"')
        if dashed:
            dash_str = dashed if isinstance(dashed, str) else "4,3"
            attrs.append(f'stroke-dasharray="{dash_str}"')
        if abs(rotate) > 1e-3:
            attrs.append(f'transform="rotate({fmt(rotate)} {fmt(cx)} {fmt(cy)})"')
        if opacity < 1.0:
            attrs.append(f'opacity="{fmt(opacity)}"')
        self.elements.append(f"<ellipse {' '.join(attrs)}/>")

    def polyline(
        self,
        pts: list[tuple[float, float]],
        stroke: str | None = None,
        stroke_width: float = 1.5,
        fill: str = "none",
        closed: bool = False,
        dashed: bool | str = False,
        arrow_end: bool = False,
        linejoin: str = "round",
    ) -> None:
        col = stroke or self.theme.fg
        pstr = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in pts)
        tag = "polygon" if closed else "polyline"
        attrs = [
            f'points="{pstr}"',
            f'fill="{fill}"',
            f'stroke="{col}"',
            f'stroke-width="{fmt(stroke_width)}"',
            f'stroke-linejoin="{linejoin}"',
            'stroke-linecap="round"',
        ]
        if dashed:
            dash_str = dashed if isinstance(dashed, str) else "4,3"
            attrs.append(f'stroke-dasharray="{dash_str}"')
        if arrow_end and not closed:
            mid = self.ensure_arrow(col)
            attrs.append(f'marker-end="url(#{mid})"')
        self.elements.append(f"<{tag} {' '.join(attrs)}/>")

    def path(
        self,
        d: str,
        stroke: str | None = None,
        stroke_width: float = 1.5,
        fill: str = "none",
        dashed: bool | str = False,
        arrow_end: bool = False,
        arrow_start: bool = False,
        opacity: float = 1.0,
        glow: bool = False,
    ) -> None:
        col = stroke if stroke is not None else self.theme.fg
        attrs = [f'd="{d}"', f'fill="{fill}"']
        if col != "none":
            attrs.append(f'stroke="{col}"')
            attrs.append(f'stroke-width="{fmt(stroke_width)}"')
            attrs.append('stroke-linecap="round"')
            attrs.append('stroke-linejoin="round"')
        if dashed:
            dash_str = dashed if isinstance(dashed, str) else "4,3"
            attrs.append(f'stroke-dasharray="{dash_str}"')
        if arrow_end and col != "none":
            mid = self.ensure_arrow(col)
            attrs.append(f'marker-end="url(#{mid})"')
        if arrow_start and col != "none":
            mid = self.ensure_arrow(col)
            attrs.append(f'marker-start="url(#{mid})"')
        if opacity < 1.0:
            attrs.append(f'opacity="{fmt(opacity)}"')
        if glow and self.theme.is_dark:
            attrs.append('filter="url(#glow)"')
        self.elements.append(f"<path {' '.join(attrs)}/>")

    def text(
        self,
        x: float,
        y: float,
        content: str,
        font_size: float = 12.0,
        fill: str | None = None,
        anchor: str = "middle",
        italic: bool = False,
        bold: bool = False,
        mono: bool = False,
        sans: bool = False,
        rich: bool = False,
        baseline: str = "central",
        rotate: float | None = None,
    ) -> None:
        col = fill or self.theme.fg
        fam = MONO_FONT if mono else (SANS_FONT if sans else SERIF_FONT)
        attrs = [
            f'x="{fmt(x)}"',
            f'y="{fmt(y)}"',
            f'fill="{col}"',
            f'font-family="{fam}"',
            f'font-size="{fmt(font_size)}"',
            f'text-anchor="{anchor}"',
            f'dominant-baseline="{baseline}"',
        ]
        if italic:
            attrs.append('font-style="italic"')
        if bold:
            attrs.append('font-weight="bold"')
        if rotate is not None:
            attrs.append(f'transform="rotate({fmt(rotate)} {fmt(x)} {fmt(y)})"')
        inner = rich_label(content, font_size) if rich else escape(content)
        self.elements.append(f"<text {' '.join(attrs)}>{inner}</text>")

    def graph_edge(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        r1: float = 0.0,
        r2: float = 0.0,
        curve: float = 0.0,
        stroke: str | None = None,
        stroke_width: float = 1.5,
        dashed: bool | str = False,
        directed: bool = False,
    ) -> None:
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist < 1e-3:
            return
        ux, uy = dx / dist, dy / dist
        nx, ny = -uy, ux
        if abs(curve) < 1e-3:
            sx = x1 + ux * r1
            sy = y1 + uy * r1
            ex = x2 - ux * r2
            ey = y2 - uy * r2
            self.line(sx, sy, ex, ey, stroke=stroke, stroke_width=stroke_width, dashed=dashed, arrow_end=directed)
        else:
            mx = 0.5 * (x1 + x2) + nx * curve
            my = 0.5 * (y1 + y2) + ny * curve
            d1 = math.hypot(mx - x1, my - y1) or 1.0
            d2 = math.hypot(x2 - mx, y2 - my) or 1.0
            sx = x1 + (mx - x1) / d1 * r1
            sy = y1 + (my - y1) / d1 * r1
            ex = x2 - (x2 - mx) / d2 * r2
            ey = y2 - (y2 - my) / d2 * r2
            d = f"M {fmt(sx)} {fmt(sy)} Q {fmt(mx)} {fmt(my)} {fmt(ex)} {fmt(ey)}"
            self.path(d, stroke=stroke, stroke_width=stroke_width, dashed=dashed, arrow_end=directed)

    def graph_node(
        self,
        x: float,
        y: float,
        label: str = "",
        r: float = 11.5,
        fill: str | None = None,
        stroke: str | None = None,
        text_fill: str | None = None,
        font_size: float = 11.0,
        italic: bool = False,
        rich: bool = True,
        filled_dot: bool = False,
    ) -> None:
        if filled_dot:
            col = stroke or (self.theme.cyan if self.theme.is_dark else self.theme.fg)
            self.circle(x, y, r, fill=col, stroke="none")
            return
        nf = fill or self.theme.node_fill
        ns = stroke or (self.theme.cyan if self.theme.is_dark else self.theme.fg)
        self.circle(x, y, r, fill=nf, stroke=ns, stroke_width=1.5)
        if label:
            self.text(x, y, label, font_size=font_size, fill=text_fill or self.theme.fg, italic=italic, rich=rich)

    def bdd_node(
        self,
        x: float,
        y: float,
        label: str,
        r: float = 12.5,
        accent: str | None = None,
        font_size: float = 11.5,
        italic: bool = False,
    ) -> None:
        st = accent or (self.theme.cyan if self.theme.is_dark else self.theme.fg)
        self.circle(x, y, r, fill=self.theme.node_fill, stroke=st, stroke_width=1.5)
        self.text(x, y, label, font_size=font_size, fill=self.theme.fg, italic=italic, rich=True)

    def bdd_sink(self, x: float, y: float, label: str, size: float = 18.0, is_true: bool | None = None) -> None:
        if is_true is None:
            is_true = label in ("1", "⊤", "T")
        fill = self.theme.sink_true_fill if is_true else self.theme.sink_false_fill
        stroke = (
            (self.theme.gold if is_true else self.theme.coral)
            if self.theme.is_dark
            else self.theme.fg
        )
        tcol = stroke if self.theme.is_dark else self.theme.fg
        half = size / 2.0
        self.rect(x - half, y - half, size, size, fill=fill, stroke=stroke, stroke_width=1.5, rx=2.0)
        self.text(x, y, label, font_size=size * 0.64, fill=tcol, bold=True)

    def bdd_edge(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        is_hi: bool = True,
        r1: float = 12.5,
        r2: float = 12.5,
        curve: float = 0.0,
        directed: bool = False,
    ) -> None:
        col = self.theme.hi_stroke if is_hi else self.theme.lo_stroke
        dash: bool | str = False if is_hi else "3.2,2.4"
        self.graph_edge(
            x1, y1, x2, y2, r1=r1, r2=r2, curve=curve, stroke=col, stroke_width=1.45, dashed=dash, directed=directed
        )

    def domino(
        self,
        x: float,
        y: float,
        pips_a: int,
        pips_b: int,
        vertical: bool = True,
        cell: float = 20.0,
        inverted: bool = True,
    ) -> None:
        w = cell if vertical else cell * 2.0
        h = cell * 2.0 if vertical else cell
        if self.theme.is_dark:
            body_fill = "#182438" if inverted else "#0F172A"
            border = self.theme.cyan
            pip_col = self.theme.gold
        else:
            body_fill = "#111827" if inverted else "#FFFFFF"
            border = "#111827"
            pip_col = "#FFFFFF" if inverted else "#111827"
        self.rect(x, y, w, h, fill=body_fill, stroke=border, stroke_width=1.3, rx=2.2)
        if vertical:
            self.line(x + 2, y + cell, x + w - 2, y + cell, stroke=pip_col, stroke_width=1.0)
            centers = [(x + cell * 0.5, y + cell * 0.5, pips_a), (x + cell * 0.5, y + cell * 1.5, pips_b)]
        else:
            self.line(x + cell, y + 2, x + cell, y + h - 2, stroke=pip_col, stroke_width=1.0)
            centers = [(x + cell * 0.5, y + cell * 0.5, pips_a), (x + cell * 1.5, y + cell * 0.5, pips_b)]
        d = cell * 0.26
        pip_r = max(1.3, cell * 0.085)
        offsets: dict[int, list[tuple[float, float]]] = {
            0: [],
            1: [(0, 0)],
            2: [(-d, -d), (d, d)],
            3: [(-d, -d), (0, 0), (d, d)],
            4: [(-d, -d), (d, -d), (-d, d), (d, d)],
            5: [(-d, -d), (d, -d), (0, 0), (-d, d), (d, d)],
            6: [(-d, -d), (d, -d), (-d, 0), (d, 0), (-d, d), (d, d)]
            if vertical
            else [(-d, -d), (0, -d), (d, -d), (-d, d), (0, d), (d, d)],
        }
        for cx, cy, count in centers:
            for ox, oy in offsets.get(count, []):
                self.circle(cx + ox, cy + oy, pip_r, fill=pip_col, stroke="none")

    def genjiko(
        self,
        x: float,
        y: float,
        blocks: list[list[int]],
        n: int = 5,
        w: float = 26.0,
        h: float = 28.0,
        stroke_width: float = 1.6,
        right_to_left: bool = False,
    ) -> None:
        step = w / max(1, n - 1)
        xs = [
            (x + w - (i - 1) * step) if right_to_left else (x + (i - 1) * step)
            for i in range(1, n + 1)
        ]
        multi = [sorted(b) for b in blocks if len(b) >= 2]
        multi.sort(key=lambda b: (b[-1] - b[0], b[0]))
        levels: list[int] = []
        spans: list[tuple[float, float, int]] = []
        for b in multi:
            lo = min(xs[idx - 1] for idx in b)
            hi = max(xs[idx - 1] for idx in b)
            lvl = 0
            for slo, shi, slvl in spans:
                if not (hi < slo - 0.1 or lo > shi + 0.1) and slvl >= lvl:
                    lvl = slvl + 1
            levels.append(lvl)
            spans.append((lo, hi, lvl))
        max_lvl = max(levels, default=0)
        palette = (
            [self.theme.cyan, self.theme.gold, self.theme.coral, self.theme.mint, self.theme.violet]
            if self.theme.is_dark
            else [self.theme.fg]
        )
        bar_top_base = y + 3.5 * max_lvl
        member_top: dict[int, float] = {i: y for i in range(1, n + 1)}
        for bi, (b, lvl) in enumerate(zip(multi, levels)):
            col = palette[bi % len(palette)]
            top_y = bar_top_base - 3.5 * lvl
            lo = min(xs[idx - 1] for idx in b)
            hi = max(xs[idx - 1] for idx in b)
            self.line(lo, top_y, hi, top_y, stroke=col, stroke_width=stroke_width)
            for idx in b:
                member_top[idx] = top_y
                self.line(xs[idx - 1], top_y, xs[idx - 1], y + h, stroke=col, stroke_width=stroke_width)
        singletons = {b[0] for b in blocks if len(b) == 1}
        for i in range(1, n + 1):
            if i in singletons or i not in {m for b in multi for m in b}:
                col = self.theme.muted if self.theme.is_dark else self.theme.fg
                self.line(xs[i - 1], y, xs[i - 1], y + h, stroke=col, stroke_width=stroke_width)

    def to_svg(self) -> str:
        defs_str = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        body = "\n".join(self.elements)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {fmt(self.width)} {fmt(self.height)}" '
            f'width="{fmt(self.width)}" height="{fmt(self.height)}">\n'
            f"{defs_str}\n{body}\n</svg>\n"
        )


def validate_svg(svg_text: str) -> None:
    if "<image" in svg_text.lower():
        raise ValueError("Raster <image> tag forbidden in pure vector SVG")
    ET.fromstring(svg_text)


def render_svg_to_png_300dpi(svg_text: str, png_path: Path) -> None:
    doc = pymupdf.open(stream=svg_text.encode("utf-8"), filetype="svg")
    try:
        page = doc[0]
        scale = 300.0 / 72.0
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        pix.set_dpi(300, 300)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(png_path))
    finally:
        doc.close()


def _frame_inline_svg(svg_text: str, stem: str, theme: Theme) -> str:
    if not stem.startswith("fig_p"):
        return svg_text
    m = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)" width="[0-9.]+" height="[0-9.]+"', svg_text)
    if not m:
        return svg_text
    vw = float(m.group(1))
    vh = float(m.group(2))
    min_w = 280.0
    if vw >= min_w:
        return svg_text
    pad = round((min_w - vw) / 2.0, 2)
    rx = "8" if theme.is_dark else "0"
    old_head = m.group(0)
    new_head = f'viewBox="{fmt(-pad)} 0 {fmt(min_w)} {fmt(vh)}" width="{fmt(min_w)}" height="{fmt(vh)}"'
    svg_text = svg_text.replace(old_head, new_head, 1)
    old_bg = f'<rect x="0" y="0" width="{fmt(vw)}" height="{fmt(vh)}" rx="{rx}" fill="{theme.bg}"/>'
    new_bg = f'<rect x="{fmt(-pad)}" y="0" width="{fmt(min_w)}" height="{fmt(vh)}" rx="{rx}" fill="{theme.bg}"/>'
    return svg_text.replace(old_bg, new_bg, 1)


def emit_dual_figure(
    fig_id: str,
    builder: Callable[[Theme], str],
    out_dir: Path,
) -> tuple[Path, Path, Path]:
    stem = fig_id if fig_id.startswith("fig_") else f"fig_{fig_id}"
    mono_svg = _frame_inline_svg(builder(MONO_THEME), stem, MONO_THEME)
    dark_svg = _frame_inline_svg(builder(DARK_3B1B_THEME), stem, DARK_3B1B_THEME)
    validate_svg(mono_svg)
    validate_svg(dark_svg)
    mono_dir = out_dir / "figures"
    dark_dir = out_dir / "figures_color"
    mono_dir.mkdir(parents=True, exist_ok=True)
    dark_dir.mkdir(parents=True, exist_ok=True)
    mono_path = mono_dir / f"{stem}.svg"
    dark_path = dark_dir / f"{stem}.svg"
    png_path = mono_dir / f"{stem}.png"
    mono_path.write_text(mono_svg, encoding="utf-8")
    dark_path.write_text(dark_svg, encoding="utf-8")
    render_svg_to_png_300dpi(mono_svg, png_path)
    return mono_path, dark_path, png_path
