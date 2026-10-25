from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Literal

import pymupdf

ThemeMode = Literal["mono", "color", "dark"]
FONT_STACK = "'Songti SC', 'STIX Two Text', 'PingFang SC', 'Noto Serif CJK SC', serif"
SANS_STACK = "'PingFang SC', 'Helvetica Neue', 'STIX Two Text', sans-serif"
PRINT_SCALE = 0.6


@dataclass(frozen=True)
class Palette:
    mode: ThemeMode
    bg: str
    panel_bg: str
    fg: str
    muted: str
    axis: str
    grid: str
    zero: str
    border: str
    series: tuple[str, ...]
    fills: tuple[str, ...]
    band_fills: tuple[str, ...]
    span_fills: tuple[str, ...]


PALETTES: dict[ThemeMode, Palette] = {
    "mono": Palette(
        mode="mono",
        bg="#ffffff",
        panel_bg="#ffffff",
        fg="#0f172a",
        muted="#475569",
        axis="#1e293b",
        grid="#e2e8f0",
        zero="#334155",
        border="#cbd5e1",
        series=(
            "#0f172a",
            "#334155",
            "#64748b",
            "#1e293b",
            "#475569",
            "#94a3b8",
        ),
        fills=(
            "#1e293b",
            "#94a3b8",
            "#cbd5e1",
            "#475569",
            "#e2e8f0",
            "#64748b",
        ),
        band_fills=(
            "rgba(15, 23, 42, 0.10)",
            "rgba(71, 85, 105, 0.12)",
            "rgba(100, 116, 139, 0.10)",
        ),
        span_fills=(
            "rgba(148, 163, 184, 0.22)",
            "rgba(203, 213, 225, 0.28)",
            "rgba(100, 116, 139, 0.16)",
        ),
    ),
    "color": Palette(
        mode="color",
        bg="#ffffff",
        panel_bg="#f8fafc",
        fg="#0f172a",
        muted="#475569",
        axis="#334155",
        grid="#e2e8f0",
        zero="#64748b",
        border="#cbd5e1",
        series=(
            "#2563eb",
            "#e11d48",
            "#059669",
            "#d97706",
            "#7c3aed",
            "#0891b2",
        ),
        fills=(
            "#3b82f6",
            "#f43f5e",
            "#10b981",
            "#f59e0b",
            "#8b5cf6",
            "#06b6d4",
        ),
        band_fills=(
            "rgba(37, 99, 235, 0.14)",
            "rgba(225, 29, 72, 0.13)",
            "rgba(5, 150, 105, 0.13)",
        ),
        span_fills=(
            "rgba(59, 130, 246, 0.11)",
            "rgba(245, 158, 11, 0.13)",
            "rgba(16, 185, 129, 0.11)",
        ),
    ),
    "dark": Palette(
        mode="dark",
        bg="#090d16",
        panel_bg="#0f1624",
        fg="#f8fafc",
        muted="#94a3b8",
        axis="#64748b",
        grid="#1e293b",
        zero="#475569",
        border="#1e293b",
        series=(
            "#38bdf8",
            "#fb7185",
            "#34d399",
            "#facc15",
            "#a78bfa",
            "#fb923c",
        ),
        fills=(
            "#0284c7",
            "#e11d48",
            "#059669",
            "#ca8a04",
            "#7c3aed",
            "#ea580c",
        ),
        band_fills=(
            "rgba(56, 189, 248, 0.18)",
            "rgba(251, 113, 133, 0.16)",
            "rgba(52, 211, 153, 0.16)",
        ),
        span_fills=(
            "rgba(56, 189, 248, 0.12)",
            "rgba(250, 204, 21, 0.12)",
            "rgba(167, 139, 250, 0.12)",
        ),
    ),
}

DASH_PATTERNS: dict[str, str] = {
    "solid": "",
    "dashed": "7,4.5",
    "dotted": "2.2,3.4",
    "dashdot": "8,3.5,2,3.5",
    "longdash": "12,5",
}


def get_palette(mode: ThemeMode = "mono") -> Palette:
    return PALETTES[mode]


@dataclass
class LineSeries:
    x: Sequence[float]
    y: Sequence[float | None]
    label: str = ""
    color_idx: int = 0
    style: str = "solid"
    marker: str | None = None
    width: float = 2.2
    axis: Literal["y1", "y2"] = "y1"
    area_fill: bool = False
    fixed_style: bool = False


@dataclass
class BarSeries:
    x: Sequence[float]
    y: Sequence[float]
    label: str = ""
    color_idx: int = 0
    width: float = 0.6
    bottom: Sequence[float] | None = None
    axis: Literal["y1", "y2"] = "y1"
    hatch: bool = False
    opacity: float = 0.85


@dataclass
class BandSeries:
    x: Sequence[float]
    y_low: Sequence[float]
    y_high: Sequence[float]
    label: str = ""
    color_idx: int = 0
    show_edges: bool = True
    edge_style: str = "dashed"


@dataclass
class VSpan:
    x0: float
    x1: float
    label: str = ""
    color_idx: int = 0


@dataclass
class Annotation:
    x: float
    y: float
    text: str
    dx: float = 0.0
    dy: float = -18.0
    arrow: bool = True
    axis: Literal["y1", "y2"] = "y1"
    color_idx: int | None = None
    fontsize: float = 11.5
    align: Literal["start", "middle", "end"] = "middle"


@dataclass
class PanelSpec:
    title: str = ""
    xlim: tuple[float, float] = (0.0, 10.0)
    ylim: tuple[float, float] = (0.0, 10.0)
    xticks: Sequence[float | tuple[float, str]] = field(default_factory=list)
    yticks: Sequence[float | tuple[float, str]] = field(default_factory=list)
    y2lim: tuple[float, float] | None = None
    y2ticks: Sequence[float | tuple[float, str]] = field(default_factory=list)
    xlabel: str = ""
    ylabel: str = ""
    y2label: str = ""
    zero_line: bool = True
    hlines: Sequence[tuple[float, str, str]] = field(default_factory=list)
    vlines: Sequence[tuple[float, str, str]] = field(default_factory=list)
    vspans: Sequence[VSpan] = field(default_factory=list)
    bands: Sequence[BandSeries] = field(default_factory=list)
    bars: Sequence[BarSeries] = field(default_factory=list)
    lines: Sequence[LineSeries] = field(default_factory=list)
    annotations: Sequence[Annotation] = field(default_factory=list)
    scatters: Sequence[tuple[Sequence[float], Sequence[float], Sequence[str], int, bool]] = field(
        default_factory=list
    )
    legend_loc: Literal["top", "bottom", "none"] = "top"


@dataclass
class FigureSpec:
    fig_id: str
    title: str
    panels: Sequence[PanelSpec]
    rows: int = 1
    cols: int = 1
    subtitle: str = ""
    note: str = ""
    width: int = 860
    height: int = 520


def _fmt_num(v: float) -> str:
    if abs(v - round(v)) < 1e-6:
        return str(round(v))
    if abs(v * 10 - round(v * 10)) < 1e-6:
        return f"{v:.1f}"
    return f"{v:.2f}"


def _norm_ticks(ticks: Sequence[float | tuple[float, str]], lim: tuple[float, float], n: int = 5) -> list[tuple[float, str]]:
    if ticks:
        out: list[tuple[float, str]] = []
        for t in ticks:
            if isinstance(t, tuple):
                out.append((float(t[0]), str(t[1])))
            else:
                out.append((float(t), _fmt_num(float(t))))
        return out
    lo, hi = lim
    if hi <= lo:
        return [(lo, _fmt_num(lo))]
    step = (hi - lo) / max(1, n - 1)
    return [(lo + i * step, _fmt_num(lo + i * step)) for i in range(n)]


def _dashed_path_d(pts: Sequence[tuple[float, float]], dash_str: str) -> str:
    if len(pts) < 2:
        return ""
    if not dash_str:
        return "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    pattern = [float(p) for p in dash_str.split(",") if p.strip()]
    if not pattern:
        return "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    out: list[str] = []
    pat_idx = 0
    pat_rem = pattern[0]
    draw = True
    cur_x, cur_y = pts[0]
    out.append(f"M {cur_x:.2f},{cur_y:.2f}")
    for nx, ny in pts[1:]:
        dx, dy = nx - cur_x, ny - cur_y
        seg_len = math.hypot(dx, dy)
        if seg_len < 1e-6:
            continue
        ux, uy = dx / seg_len, dy / seg_len
        rem = seg_len
        while rem > 1e-6:
            step = min(rem, pat_rem)
            cur_x += ux * step
            cur_y += uy * step
            rem -= step
            pat_rem -= step
            if draw:
                out.append(f"L {cur_x:.2f},{cur_y:.2f}")
            if pat_rem <= 1e-6:
                pat_idx = (pat_idx + 1) % len(pattern)
                pat_rem = pattern[pat_idx]
                draw = not draw
                if draw:
                    out.append(f"M {cur_x:.2f},{cur_y:.2f}")
    return " ".join(out)


def _draw_marker(
    cx: float,
    cy: float,
    shape: str,
    color: str,
    bg: str,
    size: float = 4.0,
    hollow: bool = False,
) -> str:
    fill = bg if hollow else color
    stroke = color
    sw = "1.6" if hollow else "1.2"
    if shape == "circle":
        return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{size:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    if shape == "square":
        s = size * 0.9
        return f'<rect x="{cx - s:.2f}" y="{cy - s:.2f}" width="{2 * s:.2f}" height="{2 * s:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    if shape == "triangle":
        s = size * 1.15
        pts = f"{cx:.2f},{cy - s:.2f} {cx - s:.2f},{cy + s * 0.85:.2f} {cx + s:.2f},{cy + s * 0.85:.2f}"
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    if shape == "diamond":
        s = size * 1.15
        pts = f"{cx:.2f},{cy - s:.2f} {cx + s:.2f},{cy:.2f} {cx:.2f},{cy + s:.2f} {cx - s:.2f},{cy:.2f}"
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    if shape == "cross":
        s = size * 0.95
        return (
            f'<line x1="{cx - s:.2f}" y1="{cy - s:.2f}" x2="{cx + s:.2f}" y2="{cy + s:.2f}" stroke="{stroke}" stroke-width="1.8"/>'
            f'<line x1="{cx - s:.2f}" y1="{cy + s:.2f}" x2="{cx + s:.2f}" y2="{cy - s:.2f}" stroke="{stroke}" stroke-width="1.8"/>'
        )
    return ""


LEGEND_ROW_H = 16.0
LegendItem = tuple[str, str, str, str | None, bool]


def _text_w(text: str, size: float) -> float:
    return sum(size if ord(ch) > 0x2E7F else size * 0.56 for ch in text)


def _legend_item_w(item: LegendItem) -> float:
    return 22.0 + _text_w(item[1], 10.8) + 14.0


def _legend_items(panel: PanelSpec, pal: Palette, mode: ThemeMode) -> list[LegendItem]:
    items: list[LegendItem] = []
    for b in panel.bars:
        if b.label:
            bcol = pal.fills[b.color_idx % len(pal.fills)]
            items.append(("bar", b.label, bcol, "hatch" if (mode == "mono" and b.hatch) else None, False))
    for ln in panel.lines:
        if ln.label:
            lcol = pal.series[ln.color_idx % len(pal.series)]
            s_key = ln.style
            if mode == "mono" and s_key == "solid" and ln.color_idx > 0 and len(panel.lines) > 1 and not ln.fixed_style:
                mono_styles = ["solid", "dashed", "dotted", "dashdot", "longdash"]
                s_key = mono_styles[ln.color_idx % len(mono_styles)]
            items.append(("line", ln.label, lcol, s_key, ln.marker is not None))
    for i, bd in enumerate(panel.bands):
        if bd.label and bd.show_edges:
            bcol = pal.series[bd.color_idx % len(pal.series)]
            items.append(("band", bd.label, bcol, "dashed", False))
        elif bd.label:
            layers = "|".join(pal.band_fills[b.color_idx % len(pal.band_fills)] for b in panel.bands[: i + 1])
            items.append(("fill", bd.label, layers, None, False))
    return items


def _wrap_legend(items: list[LegendItem], width: float) -> list[list[LegendItem]]:
    rows: list[list[LegendItem]] = []
    used = 0.0
    for item in items:
        item_w = _legend_item_w(item)
        if not rows or (rows[-1] and used + item_w > width):
            rows.append([])
            used = 0.0
        rows[-1].append(item)
        used += item_w
    return rows


MIN_PLOT_H = 110.0
PLOT_ASPECT = 0.42
TITLE_SIZE = 13.5
TITLE_LINE_H = 17.0
NOTE_SIZE = 10.5
NOTE_LINE_H = 14.0


@dataclass
class PanelFrame:
    pad_l: float
    pw: float
    pad_t: float
    pad_b: float
    leg_rows: list[list[LegendItem]]
    y_label_gap: float
    title_lines: list[str]


def _wrap_title(title: str, width: float, size: float = TITLE_SIZE) -> list[str]:
    """Break text that is wider than its room, after a colon, comma or closing bracket when one fits."""
    if not title or _text_w(title, size) <= width:
        return [title] if title else []
    breaks = [i + 1 for i, ch in enumerate(title) if ch in "：:）)，,、；; " and _text_w(title[: i + 1], size) <= width]
    cut = breaks[-1] if breaks else max(i for i in range(1, len(title)) if _text_w(title[:i], size) <= width)
    return [title[:cut].rstrip(), *_wrap_title(title[cut:].lstrip(), width, size)]


def _panel_frame(panel: PanelSpec, cell_w: float, cols: int, pal: Palette, mode: ThemeMode) -> PanelFrame:
    pad_l = 54.0 if panel.ylabel or cols == 1 else 46.0
    pad_r = 52.0 if panel.y2lim is not None else 22.0
    pw = max(60.0, cell_w - pad_l - pad_r)
    leg_rows = _wrap_legend(_legend_items(panel, pal, mode), pw) if panel.legend_loc != "none" else []
    leg_h = 22.0 + LEGEND_ROW_H * (len(leg_rows) - 1) if leg_rows else 0.0
    top_legend = bool(leg_rows) and panel.legend_loc == "top"
    title_lines = _wrap_title(panel.title, cell_w - abs(2 * pad_l + pw - cell_w) - 6.0)
    y_label_gap = 17.0 if (top_legend or title_lines) and (panel.ylabel or panel.y2label) else 0.0
    title_h = 26.0 + TITLE_LINE_H * (len(title_lines) - 1) if title_lines else 10.0
    pad_t = title_h + (leg_h if top_legend else 8.0) + y_label_gap
    pad_b = 34.0 + (14.0 if panel.xlabel else 0.0) + (leg_h + 6.0 if panel.legend_loc == "bottom" and leg_rows else 0.0)
    return PanelFrame(pad_l, pw, pad_t, pad_b, leg_rows, y_label_gap, title_lines)


def _free_row(placed: list[tuple[float, float, float]], x0: float, x1: float, y: float) -> float:
    """The first label row at or below `y` where x0..x1 clears every label already placed."""
    while any(py == y and x0 < px1 + 4 and px0 < x1 + 4 for px0, px1, py in placed):
        y += 13.0
    placed.append((x0, x1, y))
    return y


POINT_LABEL_SPOTS: tuple[tuple[float, float, str], ...] = (
    (5.0, -4.0, "start"), (-5.0, -4.0, "end"), (5.0, 11.0, "start"), (-5.0, 11.0, "end"),
    (0.0, -8.0, "middle"), (0.0, 16.0, "middle"), (5.0, -14.0, "start"), (-5.0, -14.0, "end"),
    (10.0, 20.0, "start"), (-10.0, 20.0, "end"), (10.0, -20.0, "start"), (-10.0, -20.0, "end"),
)


def _place_point_label(
    placed: list[tuple[float, float, float, float]], px: float, py: float, width: float
) -> tuple[float, float, str]:
    """The first spot around a point whose label box clears the labels already placed."""
    def box(dx: float, dy: float, anchor: str) -> tuple[float, float, float, float]:
        x0 = px + dx - {"start": 0.0, "middle": width / 2, "end": width}[anchor]
        return (x0 - 1.0, py + dy - 10.0, x0 + width + 1.0, py + dy + 3.0)

    def overlap(b: tuple[float, float, float, float]) -> float:
        return sum(
            max(0.0, min(b[2], o[2]) - max(b[0], o[0])) * max(0.0, min(b[3], o[3]) - max(b[1], o[1])) for o in placed
        )

    dx, dy, anchor = min(POINT_LABEL_SPOTS, key=lambda s: overlap(box(*s)))
    placed.append(box(dx, dy, anchor))
    return px + dx, py + dy, anchor


def _thin_ticks(
    ticks: list[tuple[float, str]], to_px: Callable[[float], float], min_gap: float
) -> list[tuple[float, str]]:
    """Drop tick labels that would sit closer than `min_gap` to a kept one, keeping zero first."""
    order = sorted(range(len(ticks)), key=lambda i: (ticks[i][0] != 0.0, i))
    kept: list[int] = []
    for i in order:
        if all(abs(to_px(ticks[i][0]) - to_px(ticks[k][0])) >= min_gap for k in kept):
            kept.append(i)
    return [ticks[i] for i in sorted(kept)]


def render_figure_svg(spec: FigureSpec, mode: ThemeMode = "mono") -> str:
    pal = get_palette(mode)
    W, H = round(spec.width * PRINT_SCALE), round(spec.height * PRINT_SCALE)
    rows = max(1, spec.rows)
    cols = max(1, spec.cols)
    grid_left = 18.0
    grid_right = W - 18.0
    cell_w = (grid_right - grid_left) / cols
    top_y = 16.0
    grid_top = top_y + (16.0 if spec.subtitle else 0.0) + 6.0
    note_lines = _wrap_title(spec.note, grid_right - grid_left - 16.0, NOTE_SIZE)
    bottom_pad = 18.0 + NOTE_LINE_H * len(note_lines)
    frames = [_panel_frame(panel, cell_w, cols, pal, mode) for panel in spec.panels[: rows * cols]]
    cell_h_min = max(f.pad_t + f.pad_b + max(MIN_PLOT_H, PLOT_ASPECT * f.pw) for f in frames)
    H = max(H, math.ceil(grid_top + rows * cell_h_min + bottom_pad))
    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f"<title>{escape(spec.title)}</title>",
        "<defs>",
        (f'<pattern id="hatch_{mode}" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">'
        f'<line x1="0" y1="0" x2="0" y2="6" stroke="{pal.fg}" stroke-width="1.4" stroke-opacity="0.55"/>'
        "</pattern>"),
        (f'<pattern id="crosshatch_{mode}" width="6" height="6" patternUnits="userSpaceOnUse">'
        f'<path d="M 0 0 L 6 6 M 6 0 L 0 6" stroke="{pal.fg}" stroke-width="1.0" stroke-opacity="0.45"/>'
        "</pattern>"),
        (f'<marker id="arrow_{mode}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 1.5 L 8.5 5 L 0 8.5 z" fill="{pal.fg}"/>'
        "</marker>"),
        "</defs>",
        f'<rect width="{W}" height="{H}" fill="{pal.bg}"/>',
    ]

    if spec.subtitle:
        out.append(
            f'<text x="{W / 2:.1f}" y="{top_y:.1f}" text-anchor="middle" '
            f'font-family="{FONT_STACK}" font-size="12.5" fill="{pal.muted}">'
            f"{escape(spec.subtitle)}</text>"
        )

    cell_h = (H - bottom_pad - grid_top) / rows

    for idx, (panel, frame) in enumerate(zip(spec.panels, frames)):
        r = idx // cols
        c = idx % cols
        cx0 = grid_left + c * cell_w
        cy0 = grid_top + r * cell_h

        has_y2 = panel.y2lim is not None
        pad_l, pw, pad_t, pad_b = frame.pad_l, frame.pw, frame.pad_t, frame.pad_b
        leg_rows, y_label_gap = frame.leg_rows, frame.y_label_gap

        px0 = cx0 + pad_l
        py0 = cy0 + pad_t
        ph = max(50.0, cell_h - pad_t - pad_b)
        px1 = px0 + pw
        py1 = py0 + ph

        for line_idx, title_line in enumerate(frame.title_lines):
            out.append(
                f'<text x="{px0 + pw / 2:.1f}" y="{cy0 + 18.0 + TITLE_LINE_H * line_idx:.1f}" text-anchor="middle" '
                f'font-family="{FONT_STACK}" font-size="{TITLE_SIZE}" font-weight="600" fill="{pal.fg}">'
                f"{escape(title_line)}</text>"
            )
        if panel.ylabel:
            yl_anchor = "start" if len(panel.ylabel) > 4 else "end"
            yl_x = (px0 - 28.0) if len(panel.ylabel) > 4 else (px0 - 6.0)
            out.append(
                f'<text x="{max(6.0, yl_x):.1f}" y="{py0 - 11:.1f}" text-anchor="{yl_anchor}" '
                f'font-family="{FONT_STACK}" font-size="11" fill="{pal.muted}">'
                f"{escape(panel.ylabel)}</text>"
            )
        if has_y2 and panel.y2label:
            y2_anchor = "end" if len(panel.y2label) > 4 else "start"
            y2_x = (px1 + 28.0) if len(panel.y2label) > 4 else (px1 + 6.0)
            out.append(
                f'<text x="{min(W - 6.0, y2_x):.1f}" y="{py0 - 11:.1f}" text-anchor="{y2_anchor}" '
                f'font-family="{FONT_STACK}" font-size="11" fill="{pal.muted}">'
                f"{escape(panel.y2label)}</text>"
            )

        out.append(
            f'<rect x="{px0:.2f}" y="{py0:.2f}" width="{pw:.2f}" height="{ph:.2f}" '
            f'fill="{pal.panel_bg}" stroke="{pal.border}" stroke-width="1"/>'
        )

        xlo, xhi = panel.xlim
        ylo, yhi = panel.ylim
        y2lo, y2hi = panel.y2lim if panel.y2lim is not None else (ylo, yhi)

        def map_x(xv: float, _xlo: float = xlo, _xhi: float = xhi, _px0: float = px0, _pw: float = pw) -> float:
            if _xhi == _xlo:
                return _px0 + _pw / 2
            return _px0 + (xv - _xlo) / (_xhi - _xlo) * _pw

        def map_y1(yv: float, _ylo: float = ylo, _yhi: float = yhi, _py0: float = py0, _py1: float = py1, _ph: float = ph) -> float:
            if _yhi == _ylo:
                return _py0 + _ph / 2
            return _py1 - (yv - _ylo) / (_yhi - _ylo) * _ph

        def map_y2(yv: float, _y2lo: float = y2lo, _y2hi: float = y2hi, _py0: float = py0, _py1: float = py1, _ph: float = ph) -> float:
            if _y2hi == _y2lo:
                return _py0 + _ph / 2
            return _py1 - (yv - _y2lo) / (_y2hi - _y2lo) * _ph

        clip_id = f"clip_{spec.fig_id}_{idx}_{mode}"
        out.append(
            f'<clipPath id="{clip_id}"><rect x="{px0:.2f}" y="{py0:.2f}" width="{pw:.2f}" height="{ph:.2f}"/></clipPath>'
        )

        out.append(f'<g clip-path="url(#{clip_id})">')
        placed_labels: list[tuple[float, float, float]] = []
        for vsp in panel.vspans:
            sx0 = max(px0, min(px1, map_x(vsp.x0)))
            sx1 = max(px0, min(px1, map_x(vsp.x1)))
            sfill = pal.span_fills[vsp.color_idx % len(pal.span_fills)]
            out.append(
                f'<rect x="{min(sx0, sx1):.2f}" y="{py0:.2f}" width="{abs(sx1 - sx0):.2f}" height="{ph:.2f}" fill="{sfill}"/>'
            )
            if vsp.label:
                half = _text_w(vsp.label, 10.5) / 2
                vy = _free_row(placed_labels, (sx0 + sx1) / 2 - half, (sx0 + sx1) / 2 + half, py0 + 13)
                out.append(
                    f'<text x="{(sx0 + sx1) / 2:.2f}" y="{vy:.2f}" text-anchor="middle" '
                    f'font-family="{FONT_STACK}" font-size="10.5" fill="{pal.muted}">{escape(vsp.label)}</text>'
                )
        out.append("</g>")

        yticks = _norm_ticks(panel.yticks, panel.ylim, 5)
        if len(yticks) > 1:
            yticks = _thin_ticks(yticks, map_y1, 13.0)
        for yv, ylab in yticks:
            yy = map_y1(yv)
            if py0 - 1.0 <= yy <= py1 + 1.0:
                out.append(
                    f'<line x1="{px0:.2f}" y1="{yy:.2f}" x2="{px1:.2f}" y2="{yy:.2f}" '
                    f'stroke="{pal.grid}" stroke-width="0.9" stroke-dasharray="2.5,2.5"/>'
                )
                out.append(
                    f'<line x1="{px0:.2f}" y1="{yy:.2f}" x2="{px0 + 4.5:.2f}" y2="{yy:.2f}" '
                    f'stroke="{pal.axis}" stroke-width="1.1"/>'
                )
                out.append(
                    f'<text x="{px0 - 6.5:.2f}" y="{yy + 3.8:.2f}" text-anchor="end" '
                    f'font-family="{SANS_STACK}" font-size="10.5" fill="{pal.muted}">{escape(ylab)}</text>'
                )

        if has_y2 and panel.y2lim is not None:
            y2ticks = _norm_ticks(panel.y2ticks, panel.y2lim, len(yticks))
            for yv, ylab in y2ticks:
                yy = map_y2(yv)
                if py0 - 1.0 <= yy <= py1 + 1.0:
                    out.append(
                        f'<line x1="{px1 - 4.5:.2f}" y1="{yy:.2f}" x2="{px1:.2f}" y2="{yy:.2f}" '
                        f'stroke="{pal.axis}" stroke-width="1.1"/>'
                    )
                    out.append(
                        f'<text x="{px1 + 6.5:.2f}" y="{yy + 3.8:.2f}" text-anchor="start" '
                        f'font-family="{SANS_STACK}" font-size="10.5" fill="{pal.muted}">{escape(ylab)}</text>'
                    )

        xticks = _norm_ticks(panel.xticks, panel.xlim, 6)
        if len(xticks) > 1:
            label_w = max(_text_w(lab, 10.5) for _, lab in xticks) + 8.0
            xticks = _thin_ticks(xticks, map_x, label_w)
        for xv, xlab in xticks:
            xx = map_x(xv)
            if px0 - 1.0 <= xx <= px1 + 1.0:
                out.append(
                    f'<line x1="{xx:.2f}" y1="{py1 - 4.5:.2f}" x2="{xx:.2f}" y2="{py1:.2f}" '
                    f'stroke="{pal.axis}" stroke-width="1.1"/>'
                )
                out.append(
                    f'<text x="{xx:.2f}" y="{py1 + 18.0:.2f}" text-anchor="middle" '
                    f'font-family="{SANS_STACK}" font-size="10.5" fill="{pal.muted}">{escape(xlab)}</text>'
                )

        if panel.xlabel:
            out.append(
                f'<text x="{px0 + pw / 2:.1f}" y="{py1 + 34:.1f}" text-anchor="middle" '
                f'font-family="{FONT_STACK}" font-size="11.5" fill="{pal.muted}">{escape(panel.xlabel)}</text>'
            )

        if panel.zero_line and ylo < 0 < yhi:
            zy = map_y1(0.0)
            out.append(
                f'<line x1="{px0:.2f}" y1="{zy:.2f}" x2="{px1:.2f}" y2="{zy:.2f}" '
                f'stroke="{pal.zero}" stroke-width="1.25"/>'
            )

        out.append(f'<g clip-path="url(#{clip_id})">')

        for hy, hlab, hstyle in panel.hlines:
            yy = map_y1(hy)
            dash = DASH_PATTERNS.get(hstyle, "5,4")
            hd_str = _dashed_path_d([(px0, yy), (px1, yy)], dash)
            out.append(
                f'<path d="{hd_str}" fill="none" stroke="{pal.muted}" stroke-width="1.2"/>'
            )
            if hlab:
                out.append(
                    f'<text x="{px1 - 6:.2f}" y="{yy - 4:.2f}" text-anchor="end" '
                    f'font-family="{FONT_STACK}" font-size="10.5" fill="{pal.muted}">{escape(hlab)}</text>'
                )

        for vx, vlab, vstyle in panel.vlines:
            xx = map_x(vx)
            dash = DASH_PATTERNS.get(vstyle, "5,4")
            vd_str = _dashed_path_d([(xx, py0), (xx, py1)], dash)
            out.append(
                f'<path d="{vd_str}" fill="none" stroke="{pal.muted}" stroke-width="1.2"/>'
            )
            if vlab:
                vw = _text_w(vlab, 10.5)
                flip = xx + 4 + vw > px1
                lx0 = xx - 4 - vw if flip else xx + 4
                vy = _free_row(placed_labels, lx0, lx0 + vw, py0 + 13)
                out.append(
                    f'<text x="{xx - 4 if flip else xx + 4:.2f}" y="{vy:.2f}" text-anchor="{"end" if flip else "start"}" '
                    f'font-family="{FONT_STACK}" font-size="10.5" fill="{pal.muted}">{escape(vlab)}</text>'
                )

        for b in panel.bands:
            if len(b.x) < 2:
                continue
            bfill = pal.band_fills[b.color_idx % len(pal.band_fills)]
            bcol = pal.series[b.color_idx % len(pal.series)]
            upper_coords = [(map_x(xv), map_y1(yh)) for xv, yh in zip(b.x, b.y_high)]
            lower_coords = [(map_x(xv), map_y1(yl)) for xv, yl in zip(b.x, b.y_low)]
            upper_pts = [f"{px:.2f},{py:.2f}" for px, py in upper_coords]
            lower_pts = [f"{px:.2f},{py:.2f}" for px, py in reversed(lower_coords)]
            poly = " ".join(upper_pts + lower_pts)
            out.append(f'<polygon points="{poly}" fill="{bfill}" stroke="none"/>')
            if b.show_edges:
                dash = DASH_PATTERNS.get(b.edge_style, "5,3.5")
                u_path = _dashed_path_d(upper_coords, dash)
                l_path = _dashed_path_d(lower_coords, dash)
                out.append(
                    f'<path d="{u_path}" fill="none" stroke="{bcol}" stroke-width="1.25" stroke-opacity="0.75"/>'
                )
                out.append(
                    f'<path d="{l_path}" fill="none" stroke="{bcol}" stroke-width="1.25" stroke-opacity="0.75"/>'
                )

        for b in panel.bars:
            y_fn = map_y2 if b.axis == "y2" else map_y1
            bcol = pal.fills[b.color_idx % len(pal.fills)]
            bw_px = max(2.0, abs(map_x(xlo + b.width) - map_x(xlo)))
            for i, (xv, yv) in enumerate(zip(b.x, b.y)):
                b0 = b.bottom[i] if b.bottom is not None and i < len(b.bottom) else 0.0
                y_top = y_fn(max(b0, b0 + yv))
                y_bot = y_fn(min(b0, b0 + yv))
                bh = max(0.8, abs(y_bot - y_top))
                bx = map_x(xv) - bw_px / 2
                fill_attr = "#cbd5e1" if (mode == "mono" and b.hatch) else bcol
                out.append(
                    f'<rect x="{bx:.2f}" y="{min(y_top, y_bot):.2f}" width="{bw_px:.2f}" height="{bh:.2f}" '
                    f'fill="{fill_attr}" fill-opacity="{b.opacity:.2f}" stroke="{pal.fg if mode == "mono" else bcol}" stroke-width="0.7"/>'
                )

        scatter_boxes = [
            (map_x(xv) - 4.0, map_y1(yv) - 4.0, map_x(xv) + 4.0, map_y1(yv) + 4.0)
            for xs, ys, *_ in panel.scatters
            for xv, yv in zip(xs, ys)
        ]
        for xs, ys, pt_labels, c_idx, connect in panel.scatters:
            scol = pal.series[c_idx % len(pal.series)]
            pts_px = [(map_x(xv), map_y1(yv)) for xv, yv in zip(xs, ys)]
            if connect and len(pts_px) >= 2:
                d_str = "M " + " L ".join(f"{px:.2f},{py:.2f}" for px, py in pts_px)
                out.append(
                    f'<path d="{d_str}" fill="none" stroke="{scol}" stroke-width="1.6" stroke-opacity="0.75"/>'
                )
            for i, (px, py) in enumerate(pts_px):
                out.append(_draw_marker(px, py, "circle", scol, pal.panel_bg, 3.6, hollow=(mode == "mono" and c_idx % 2 == 1)))
                if pt_labels and i < len(pt_labels) and pt_labels[i]:
                    lx, ly, anchor = _place_point_label(scatter_boxes, px, py, _text_w(pt_labels[i], 9.5))
                    out.append(
                        f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="{anchor}" font-family="{SANS_STACK}" '
                        f'font-size="9.5" fill="{pal.fg}">{escape(pt_labels[i])}</text>'
                    )

        for l_idx, ln in enumerate(panel.lines):
            y_fn = map_y2 if ln.axis == "y2" else map_y1
            lcol = pal.series[ln.color_idx % len(pal.series)]
            style_key = ln.style
            if mode == "mono" and style_key == "solid" and ln.color_idx > 0 and len(panel.lines) > 1 and not ln.fixed_style:
                mono_styles = ["solid", "dashed", "dotted", "dashdot", "longdash"]
                style_key = mono_styles[ln.color_idx % len(mono_styles)]
            dash = DASH_PATTERNS.get(style_key, "")

            segments: list[list[tuple[float, float]]] = []
            cur: list[tuple[float, float]] = []
            for xv, yv in zip(ln.x, ln.y):
                if yv is None or math.isnan(yv):
                    if cur:
                        segments.append(cur)
                        cur = []
                else:
                    cur.append((map_x(xv), y_fn(yv)))
            if cur:
                segments.append(cur)

            for seg in segments:
                if len(seg) >= 2 and style_key != "none":
                    if ln.area_fill or (mode in ("color", "dark") and len(panel.lines) == 1 and not panel.bars and not panel.bands):
                        z_py = min(py1, max(py0, y_fn(0.0)))
                        area_pts = (
                            [f"{seg[0][0]:.2f},{z_py:.2f}"]
                            + [f"{px:.2f},{py:.2f}" for px, py in seg]
                            + [f"{seg[-1][0]:.2f},{z_py:.2f}"]
                        )
                        afill = pal.band_fills[ln.color_idx % len(pal.band_fills)]
                        if mode != "mono" or ln.area_fill:
                            out.append(f'<polygon points="{" ".join(area_pts)}" fill="{afill}" stroke="none"/>')
                    d_str = _dashed_path_d(seg, dash)
                    out.append(
                        f'<path d="{d_str}" fill="none" stroke="{lcol}" stroke-width="{ln.width:.2f}" '
                        f'stroke-linecap="round" stroke-linejoin="round"/>'
                    )
                if ln.marker:
                    step = 1 if style_key == "none" else max(1, len(seg) // 18)
                    for m_i, (px, py) in enumerate(seg):
                        if m_i % step == 0 or m_i == len(seg) - 1:
                            out.append(
                                _draw_marker(
                                    px,
                                    py,
                                    ln.marker,
                                    lcol,
                                    pal.panel_bg,
                                    3.6,
                                    hollow=(mode == "mono" and ln.color_idx % 2 == 1),
                                )
                            )

        for ann in panel.annotations:
            y_fn = map_y2 if ann.axis == "y2" else map_y1
            ax = map_x(ann.x)
            ay = y_fn(ann.y)
            tx = ax + ann.dx * PRINT_SCALE
            ty = ay + ann.dy * PRINT_SCALE
            acol = pal.series[ann.color_idx % len(pal.series)] if ann.color_idx is not None else pal.fg
            if ann.arrow and (abs(ann.dx) > 2 or abs(ann.dy) > 2):
                out.append(
                    f'<line x1="{tx:.2f}" y1="{ty:.2f}" x2="{ax:.2f}" y2="{ay:.2f}" '
                    f'stroke="{acol}" stroke-width="1.2" marker-end="url(#arrow_{mode})"/>'
                )
            text_dy = -4.0 if ann.dy <= 0 else 11.0
            ann_w = _text_w(ann.text, ann.fontsize)
            left = {"start": 0.0, "middle": ann_w / 2, "end": ann_w}[ann.align]
            text_x = min(max(tx, 4.0 + left), W - 4.0 - (ann_w - left))
            out.append(
                f'<text x="{text_x:.2f}" y="{ty + text_dy:.2f}" text-anchor="{ann.align}" '
                f'font-family="{FONT_STACK}" font-size="{ann.fontsize:.1f}" font-weight="500" fill="{acol}">'
                f"{escape(ann.text)}</text>"
            )

        out.append("</g>")

        out.append(
            f'<rect x="{px0:.2f}" y="{py0:.2f}" width="{pw:.2f}" height="{ph:.2f}" '
            f'fill="none" stroke="{pal.axis}" stroke-width="1.2"/>'
        )

        if leg_rows:
            for row_idx, row in enumerate(leg_rows):
                if panel.legend_loc == "top":
                    ly = py0 - 10.0 - y_label_gap - LEGEND_ROW_H * (len(leg_rows) - 1 - row_idx)
                else:
                    ly = py1 + (52.0 if panel.xlabel else 36.0) + LEGEND_ROW_H * row_idx
                lx = px0 + max(0.0, (pw - sum(_legend_item_w(it) for it in row)) / 2.0)
                for kind, ltext, lcol, lstyle, has_mk in row:
                    iw = _legend_item_w((kind, ltext, lcol, lstyle, has_mk))
                    if kind == "bar":
                        fill_attr = "#cbd5e1" if lstyle == "hatch" else lcol
                        out.append(
                            f'<rect x="{lx:.2f}" y="{ly - 8.5:.2f}" width="14" height="9" '
                            f'fill="{fill_attr}" stroke="{pal.fg if mode == "mono" else lcol}" stroke-width="0.8"/>'
                        )
                    elif kind == "fill":
                        out.extend(
                            f'<rect x="{lx:.2f}" y="{ly - 9.0:.2f}" width="16" height="10" fill="{layer}" stroke="none"/>'
                            for layer in lcol.split("|")
                        )
                    else:
                        if lstyle != "none":
                            dash = DASH_PATTERNS.get(lstyle or "solid", "")
                            leg_d = _dashed_path_d([(lx, ly - 4.0), (lx + 18.0, ly - 4.0)], dash)
                            out.append(
                                f'<path d="{leg_d}" fill="none" stroke="{lcol}" stroke-width="2.1"/>'
                            )
                        if has_mk:
                            out.append(_draw_marker(lx + 9, ly - 4, "circle", lcol, pal.panel_bg, 3.0))
                    out.append(
                        f'<text x="{lx + 22:.2f}" y="{ly:.2f}" font-family="{FONT_STACK}" '
                        f'font-size="10.8" fill="{pal.fg}">{escape(ltext)}</text>'
                    )
                    lx += iw

    for line_idx, note_line in enumerate(note_lines):
        out.append(
            f'<text x="{grid_left + 8:.1f}" y="{H - 10 - NOTE_LINE_H * (len(note_lines) - 1 - line_idx):.1f}" '
            f'font-family="{FONT_STACK}" font-size="{NOTE_SIZE}" fill="{pal.muted}">{escape(note_line)}</text>'
        )

    out.append("</svg>")
    svg_str = "\n".join(out)
    return _normalize_rgba_fills(svg_str)


def _normalize_rgba_fills(svg_str: str) -> str:
    import re

    def _repl(m: re.Match[str]) -> str:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = float(m.group(4))
        return f'fill="#{r:02x}{g:02x}{b:02x}" fill-opacity="{a:.2f}"'

    return re.sub(
        r'fill="rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)"',
        _repl,
        svg_str,
    )


def svg_to_png(svg_text: str, png_path: Path, dpi: int = 300) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open("svg", svg_text.encode("utf-8"))
    try:
        page = doc[0]
        pix = page.get_pixmap(dpi=dpi)
        pix.save(str(png_path))
    finally:
        doc.close()


def save_figure_outputs(
    fig_id: str,
    svg_by_mode: dict[ThemeMode, str],
    book_dir: Path,
    dpi: int = 300,
) -> None:
    dir_map: list[tuple[ThemeMode, Path]] = [
        ("mono", book_dir / "figures"),
        ("mono", book_dir / "figures_mono"),
        ("color", book_dir / "figures_color"),
        ("dark", book_dir / "figures_3b1b_dark"),
    ]
    png_cache: dict[ThemeMode, bytes] = {}
    for mode, svg_text in svg_by_mode.items():
        doc = pymupdf.open("svg", svg_text.encode("utf-8"))
        try:
            png_cache[mode] = doc[0].get_pixmap(dpi=dpi).tobytes("png")
        finally:
            doc.close()

    for mode, target_dir in dir_map:
        if mode not in svg_by_mode:
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / f"fig_{fig_id}.svg").write_text(svg_by_mode[mode], encoding="utf-8")
        (target_dir / f"fig_{fig_id}.png").write_bytes(png_cache[mode])
