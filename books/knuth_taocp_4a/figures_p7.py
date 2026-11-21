from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

from .figures_common import SvgCanvas, Theme, emit_dual_figure, fmt, rich_label

USA_COORDS: dict[str, tuple[int, int]] = {
    "ND": (3, 0), "VT": (9, 0), "NH": (10, 0), "ME": (11, 0),
    "WA": (0, 1), "MT": (2, 1), "SD": (3, 1), "MN": (4, 1), "WI": (5, 1), "MI": (6, 1), "NY": (9, 1), "MA": (10, 1),
    "OR": (0, 2), "ID": (1, 2), "WY": (2, 2), "NE": (3, 2), "IA": (4, 2), "IL": (5, 2), "IN": (6, 2), "OH": (7, 2), "PA": (8, 2), "NJ": (9, 2), "CT": (10, 2), "RI": (11, 2),
    "CA": (-1, 3), "NV": (0, 3), "UT": (1, 3), "CO": (2, 3), "KS": (3, 3), "MO": (4, 3), "KY": (6, 3), "WV": (7, 3), "MD": (8, 3), "DE": (9, 3),
    "AZ": (1, 4), "NM": (2, 4), "OK": (3, 4), "AR": (4, 4), "TN": (6, 4), "VA": (7, 4), "DC": (8, 4),
    "TX": (3, 5), "LA": (4, 5), "MS": (5, 5), "AL": (6, 5), "GA": (7, 5), "NC": (8, 5),
    "FL": (7, 6), "SC": (8, 6),
}

USA_EDGES: list[tuple[str, str]] = sorted({
    tuple(sorted(e))
    for e in [
        ("WA", "OR"), ("WA", "ID"), ("OR", "CA"), ("OR", "NV"), ("OR", "ID"),
        ("CA", "NV"), ("CA", "AZ"), ("NV", "ID"), ("NV", "UT"), ("NV", "AZ"),
        ("ID", "MT"), ("ID", "WY"), ("ID", "UT"), ("MT", "ND"), ("MT", "SD"), ("MT", "WY"),
        ("WY", "SD"), ("WY", "NE"), ("WY", "CO"), ("WY", "UT"), ("UT", "CO"), ("UT", "AZ"),
        ("AZ", "NM"), ("ND", "SD"), ("ND", "MN"), ("SD", "MN"), ("SD", "IA"), ("SD", "NE"),
        ("NE", "IA"), ("NE", "MO"), ("NE", "KS"), ("NE", "CO"), ("CO", "KS"), ("CO", "OK"), ("CO", "NM"),
        ("NM", "OK"), ("NM", "TX"), ("OK", "KS"), ("OK", "MO"), ("OK", "AR"), ("OK", "TX"),
        ("TX", "AR"), ("TX", "LA"), ("MN", "WI"), ("MN", "IA"), ("IA", "WI"), ("IA", "IL"), ("IA", "MO"),
        ("MO", "IL"), ("MO", "KY"), ("MO", "TN"), ("MO", "AR"), ("MO", "KS"),
        ("AR", "TN"), ("AR", "MS"), ("AR", "LA"), ("LA", "MS"), ("WI", "MI"), ("WI", "IL"),
        ("IL", "IN"), ("IL", "KY"), ("MI", "IN"), ("MI", "OH"), ("IN", "OH"), ("IN", "KY"),
        ("OH", "PA"), ("OH", "WV"), ("OH", "KY"), ("KY", "WV"), ("KY", "VA"), ("KY", "TN"),
        ("TN", "VA"), ("TN", "NC"), ("TN", "GA"), ("TN", "AL"), ("TN", "MS"),
        ("MS", "AL"), ("AL", "GA"), ("AL", "FL"), ("GA", "NC"), ("GA", "SC"), ("GA", "FL"),
        ("NC", "VA"), ("NC", "SC"), ("VA", "WV"), ("VA", "MD"), ("VA", "DC"),
        ("WV", "PA"), ("WV", "MD"), ("MD", "PA"), ("MD", "DE"), ("MD", "DC"),
        ("PA", "NY"), ("PA", "NJ"), ("PA", "DE"), ("DE", "NJ"), ("NJ", "NY"),
        ("NY", "VT"), ("NY", "MA"), ("NY", "CT"), ("CT", "MA"), ("CT", "RI"),
        ("MA", "VT"), ("MA", "NH"), ("MA", "RI"), ("VT", "NH"), ("NH", "ME"),
    ]
})


def _pill_node(
    c: SvgCanvas,
    cx: float,
    cy: float,
    w: float,
    h: float,
    label: str,
    stroke: str | None = None,
    fill: str | None = None,
    font_size: float = 10.0,
    italic: bool = False,
    rich: bool = True,
) -> None:
    st = stroke or (c.theme.gold if c.theme.is_dark else c.theme.fg)
    fl = fill or c.theme.node_fill
    c.rect(cx - w * 0.5, cy - h * 0.5, w, h, fill=fl, stroke=st, stroke_width=1.4, rx=h * 0.5)
    c.text(cx, cy, label, font_size=font_size, fill=c.theme.fg, italic=italic, rich=rich)


def _draw_usa_submap(
    c: SvgCanvas,
    x0: float,
    y0: float,
    step: float,
    black_set: set[str] | None = None,
    gray_set: set[str] | None = None,
    thick_edges: set[tuple[str, str]] | None = None,
    thick_color: str | None = None,
    omit_dc: bool = False,
    r_dot: float = 3.1,
) -> None:
    theme = c.theme
    blk = black_set or set()
    gry = gray_set or set()
    thk = {tuple(sorted(e)) for e in (thick_edges or set())}
    base_edge = "#2C3E5A" if theme.is_dark else "#94A3B8"
    hi_edge = thick_color or (theme.gold if theme.is_dark else "#0F172A")

    for u, v in USA_EDGES:
        if omit_dc and ("DC" in (u, v)):
            continue
        key = (u, v) if u < v else (v, u)
        if key in thk:
            continue
        cu, ru = USA_COORDS[u]
        cv, rv = USA_COORDS[v]
        c.line(x0 + cu * step, y0 + ru * step, x0 + cv * step, y0 + rv * step, stroke=base_edge, stroke_width=0.75)

    for u, v in sorted(thk):
        if omit_dc and ("DC" in (u, v)):
            continue
        cu, ru = USA_COORDS[u]
        cv, rv = USA_COORDS[v]
        c.line(x0 + cu * step, y0 + ru * step, x0 + cv * step, y0 + rv * step, stroke=hi_edge, stroke_width=2.3)

    for st, (col, row) in USA_COORDS.items():
        if omit_dc and st == "DC":
            continue
        px = x0 + col * step
        py = y0 + row * step
        if st in blk:
            fl = theme.cyan if theme.is_dark else "#0F172A"
            sk = theme.cyan if theme.is_dark else "#0F172A"
        elif st in gry:
            fl = theme.gold if theme.is_dark else "#94A3B8"
            sk = theme.gold if theme.is_dark else "#0F172A"
        else:
            fl = theme.bg
            sk = "#64748B" if theme.is_dark else "#334155"
        c.circle(px, py, r_dot, fill=fl, stroke=sk, stroke_width=1.0)


def fig_p564_inline_1(theme: Theme) -> str:
    w, h = 156.0, 96.0
    c = SvgCanvas(w, h, theme)
    r = 10.5
    pts: dict[str, tuple[float, float, str]] = {
        "w": (24.0, 20.0, "w"),
        "zb": (78.0, 20.0, "z"),
        "xb": (132.0, 20.0, "x"),
        "y": (51.0, 48.0, "y"),
        "yb": (105.0, 48.0, "y"),
        "x": (24.0, 76.0, "x"),
        "z": (78.0, 76.0, "z"),
        "wb": (132.0, 76.0, "w"),
    }
    edges = [
        ("w", "zb"), ("zb", "xb"),
        ("x", "z"), ("z", "wb"),
        ("w", "y"), ("x", "y"),
        ("yb", "xb"), ("yb", "wb"),
    ]
    ecol = theme.gold if theme.is_dark else theme.fg
    for u, v in edges:
        x1, y1, _ = pts[u]
        x2, y2, _ = pts[v]
        c.graph_edge(x1, y1, x2, y2, r1=r, r2=r + 1.0, stroke=ecol, stroke_width=1.4, directed=True)
    for key, (px, py, lbl) in pts.items():
        ncol = (theme.coral if "b" in key else theme.cyan) if theme.is_dark else theme.fg
        c.graph_node(px, py + (1.0 if "b" in key else 0.0), lbl, r=r, stroke=ncol, font_size=10.6, italic=True, rich=False)
        if "b" in key:
            hw = 4.2 if lbl == "w" else 3.3
            c.line(px - hw + 0.4, py - 4.7, px + hw + 0.4, py - 4.7, stroke=theme.fg, stroke_width=0.95)
    return c.to_svg()


def fig_p564_inline_2(theme: Theme) -> str:
    w, h = 446.0, 88.0
    c = SvgCanvas(w, h, theme)
    x_left, x_right = 14.0, 432.0
    y0, dy = 14.0, 10.0
    wire_col = "#475569" if theme.is_dark else theme.fg
    for i in range(7):
        yw = y0 + i * dy
        c.line(x_left, yw, x_right, yw, stroke=wire_col, stroke_width=1.1)

    clusters = [
        (6, 7, False, True, 28.0),
        (5, 7, False, True, 46.0),
        (4, 7, False, True, 64.0),
        (5, 6, False, True, 80.0),
        (2, 7, False, True, 98.0),
        (2, 6, False, True, 116.0),
        (1, 7, True, True, 136.0),
        (2, 5, False, True, 156.0),
        (1, 6, True, True, 176.0),
        (2, 4, False, True, 196.0),
        (3, 7, True, True, 216.0),
        (1, 5, True, True, 236.0),
        (2, 3, False, True, 254.0),
        (3, 6, True, True, 274.0),
        (1, 4, True, True, 294.0),
        (4, 6, True, True, 314.0),
        (3, 5, True, True, 334.0),
        (1, 3, True, True, 354.0),
        (4, 5, True, True, 374.0),
        (3, 4, True, True, 394.0),
        (1, 2, True, True, 414.0),
    ]
    r_dot = 2.35
    dx_inv = 5.4
    cmp_col = theme.cyan if theme.is_dark else theme.fg
    inv_col = theme.coral if theme.is_dark else theme.fg

    for wi, wj, inv_i, inv_j, xc in clusters:
        yi = y0 + (wi - 1) * dy
        yj = y0 + (wj - 1) * dy
        c.line(xc, yi + r_dot, xc, yj - r_dot, stroke=cmp_col, stroke_width=1.25)
        c.circle(xc, yi, r_dot, fill=theme.bg, stroke=cmp_col, stroke_width=1.25)
        c.circle(xc, yj, r_dot, fill=theme.bg, stroke=cmp_col, stroke_width=1.25)
        if inv_i:
            c.circle(xc - dx_inv, yi, r_dot, fill=theme.bg, stroke=inv_col, stroke_width=1.2)
            c.circle(xc + dx_inv, yi, r_dot, fill=theme.bg, stroke=inv_col, stroke_width=1.2)
        if inv_j:
            c.circle(xc - dx_inv, yj, r_dot, fill=theme.bg, stroke=inv_col, stroke_width=1.2)
            c.circle(xc + dx_inv, yj, r_dot, fill=theme.bg, stroke=inv_col, stroke_width=1.2)
    return c.to_svg()


def fig_p565_inline_1(theme: Theme) -> str:
    w, h = 112.0, 62.0
    c = SvgCanvas(w, h, theme)
    y0, dy = 13.0, 12.0
    wire_col = "#475569" if theme.is_dark else theme.fg
    for i in range(4):
        c.line(14.0, y0 + i * dy, 98.0, y0 + i * dy, stroke=wire_col, stroke_width=1.15)
    r_dot = 2.6
    cmp_col = theme.cyan if theme.is_dark else theme.fg
    inv_col = theme.coral if theme.is_dark else theme.fg
    for xc, wi, wj in [(28.0, 1, 4), (47.0, 1, 2), (66.0, 3, 4), (84.0, 1, 3)]:
        yi = y0 + (wi - 1) * dy
        yj = y0 + (wj - 1) * dy
        c.line(xc, yi + r_dot, xc, yj - r_dot, stroke=cmp_col, stroke_width=1.35)
        c.circle(xc, yi, r_dot, fill=theme.bg, stroke=cmp_col, stroke_width=1.35)
        c.circle(xc, yj, r_dot, fill=theme.bg, stroke=cmp_col, stroke_width=1.35)
    c.circle(47.0, y0 + 3 * dy, r_dot, fill=theme.bg, stroke=inv_col, stroke_width=1.35)
    return c.to_svg()


def fig_p565_inline_2(theme: Theme) -> str:
    w, h = 128.0, 78.0
    c = SvgCanvas(w, h, theme)
    y0, dy = 12.0, 10.8
    wire_col = "#475569" if theme.is_dark else theme.fg
    for i in range(6):
        c.line(12.0, y0 + i * dy, 116.0, y0 + i * dy, stroke=wire_col, stroke_width=1.15)
    r_dot = 2.5
    cmp_col = theme.cyan if theme.is_dark else theme.fg
    ops = [
        (24.0, 1, 3),
        (40.0, 2, 4),
        (56.0, 3, 5),
        (72.0, 1, 3),
        (75.5, 4, 6),
        (90.0, 2, 4),
        (104.0, 1, 2),
        (104.0, 5, 6),
    ]
    for xc, wi, wj in ops:
        yi = y0 + (wi - 1) * dy
        yj = y0 + (wj - 1) * dy
        c.line(xc, yi + r_dot, xc, yj - r_dot, stroke=cmp_col, stroke_width=1.35)
        c.circle(xc, yi, r_dot, fill=theme.bg, stroke=cmp_col, stroke_width=1.35)
        c.circle(xc, yj, r_dot, fill=theme.bg, stroke=cmp_col, stroke_width=1.35)
    return c.to_svg()


def _draw_chain_tree(
    c: SvgCanvas,
    ox: float,
    oy: float,
    gates: list[tuple[float, float, str]],
    leaves: list[tuple[float, float, str]],
    edges: list[tuple[int, str, int, float]],
    r: float = 5.4,
) -> None:
    theme = c.theme
    ecol = theme.muted if theme.is_dark else theme.fg
    for gi, kind, ti, curve in edges:
        gx, gy, _ = gates[gi]
        if kind == "g":
            tx, ty, _ = gates[ti]
            r2 = r
        else:
            tx, ty, _ = leaves[ti]
            r2 = 5.5
        c.graph_edge(ox + gx, oy + gy, ox + tx, oy + ty, r1=r, r2=r2, curve=curve, stroke=ecol, stroke_width=1.2)
    palette = {
        "": theme.cyan,
        "+": theme.cyan,
        "or": theme.mint,
        "and": theme.gold,
        "<": theme.coral,
    }
    for gx, gy, op in gates:
        st = palette.get(op, theme.cyan) if theme.is_dark else theme.fg
        c.circle(ox + gx, oy + gy, r, fill=theme.node_fill, stroke=st, stroke_width=1.35)
        if op == "+":
            d = r * 0.56
            c.line(ox + gx - d, oy + gy, ox + gx + d, oy + gy, stroke=st, stroke_width=1.15)
            c.line(ox + gx, oy + gy - d, ox + gx, oy + gy + d, stroke=st, stroke_width=1.15)
        elif op in ("or", "and"):
            d = r * 0.44
            sgn = 1.0 if op == "or" else -1.0
            pts = [
                (ox + gx - d, oy + gy - sgn * d * 0.78),
                (ox + gx, oy + gy + sgn * d * 0.88),
                (ox + gx + d, oy + gy - sgn * d * 0.78),
            ]
            c.polyline(pts, stroke=st, stroke_width=1.15)
        elif op == "<":
            d = r * 0.44
            pts = [
                (ox + gx + d * 0.75, oy + gy - d * 0.82),
                (ox + gx - d * 0.85, oy + gy),
                (ox + gx + d * 0.75, oy + gy + d * 0.82),
            ]
            c.polyline(pts, stroke=st, stroke_width=1.15)
    lcol = theme.gold if theme.is_dark else theme.fg
    for lx, ly, lbl in leaves:
        c.text(ox + lx, oy + ly, lbl, font_size=9.6, fill=lcol)


def fig_p578_inline_1(theme: Theme) -> str:
    w, h = 392.0, 96.0
    c = SvgCanvas(w, h, theme)
    r = 4.9

    _draw_chain_tree(
        c, 42.0, 14.0,
        [(0, 0, ""), (-14, 15, ""), (14, 15, ""), (-2, 31, ""), (22, 31, ""), (2, 47, "")],
        [(-23, 32, "4"), (-9, 48, "3"), (15, 48, "1"), (28, 48, "2"), (-4, 64, "1"), (9, 64, "2")],
        [
            (0, "g", 1, 0), (0, "g", 2, 0),
            (1, "l", 0, 0), (1, "g", 3, 0),
            (2, "g", 3, 0), (2, "g", 4, 0),
            (3, "l", 1, 0), (3, "g", 5, 0),
            (4, "l", 2, 0), (4, "l", 3, 0),
            (5, "l", 4, 0), (5, "l", 5, 0),
        ],
        r=r,
    )

    _draw_chain_tree(
        c, 118.0, 14.0,
        [(0, 0, ""), (-14, 15, ""), (14, 15, ""), (4, 31, ""), (-6, 47, ""), (14, 47, "")],
        [(-24, 32, "3"), (24, 32, "4"), (-12, 64, "1"), (-1, 64, "2"), (9, 64, "1"), (20, 64, "2")],
        [
            (0, "g", 1, 0), (0, "g", 2, 0),
            (1, "l", 0, 0), (1, "g", 4, 0),
            (2, "g", 3, 0), (2, "l", 1, 0),
            (3, "g", 4, 0), (3, "g", 5, 0),
            (4, "l", 2, 0), (4, "l", 3, 0),
            (5, "l", 4, 0), (5, "l", 5, 0),
        ],
        r=r,
    )

    _draw_chain_tree(
        c, 194.0, 14.0,
        [(0, 0, ""), (-14, 15, ""), (14, 15, ""), (0, 31, ""), (-11, 47, ""), (11, 47, "")],
        [(-24, 32, "3"), (24, 32, "4"), (-17, 64, "1"), (-5, 64, "2"), (5, 64, "1"), (17, 64, "2")],
        [
            (0, "g", 1, 0), (0, "g", 2, 0),
            (1, "l", 0, 0), (1, "g", 3, 0),
            (2, "g", 3, 0), (2, "l", 1, 0),
            (3, "g", 4, 0), (3, "g", 5, 0),
            (4, "l", 2, 0), (4, "l", 3, 0),
            (5, "l", 4, 0), (5, "l", 5, 0),
        ],
        r=r,
    )

    _draw_chain_tree(
        c, 272.0, 14.0,
        [(0, 0, ""), (-12, 15, ""), (-4, 30, ""), (5, 45, ""), (-6, 60, ""), (16, 60, "")],
        [(-22, 31, "4"), (-14, 46, "3"), (-12, 76, "1"), (0, 76, "2"), (10, 76, "1"), (22, 76, "2")],
        [
            (0, "g", 1, 0), (0, "g", 5, 16.0),
            (1, "l", 0, 0), (1, "g", 2, 0),
            (2, "l", 1, 0), (2, "g", 3, 0),
            (3, "g", 4, 0), (3, "g", 5, 0),
            (4, "l", 2, 0), (4, "l", 3, 0),
            (5, "l", 4, 0), (5, "l", 5, 0),
        ],
        r=r,
    )

    _draw_chain_tree(
        c, 350.0, 14.0,
        [(0, 0, ""), (-12, 15, ""), (-3, 30, ""), (8, 45, ""), (-3, 60, ""), (19, 60, "")],
        [(-22, 31, "4"), (-13, 46, "3"), (-9, 76, "1"), (3, 76, "2"), (13, 76, "1"), (25, 76, "2")],
        [
            (0, "g", 1, 0), (0, "g", 3, 14.0),
            (1, "l", 0, 0), (1, "g", 2, 0),
            (2, "l", 1, 0), (2, "g", 3, 0),
            (3, "g", 4, 0), (3, "g", 5, 0),
            (4, "l", 2, 0), (4, "l", 3, 0),
            (5, "l", 4, 0), (5, "l", 5, 0),
        ],
        r=r,
    )

    return c.to_svg()


def fig_p578_inline_2(theme: Theme) -> str:
    w, h = 196.0, 112.0
    c = SvgCanvas(w, h, theme)
    c.text(32.0, 16.0, "S_2 =", font_size=11.5, fill=theme.fg, italic=True, rich=True)
    _draw_chain_tree(
        c,
        106.0,
        16.0,
        [
            (0, 0, "<"),
            (-24, 17, "+"),
            (24, 17, "+"),
            (-40, 35, "+"),
            (-8, 35, "+"),
            (14, 35, "or"),
            (42, 35, "and"),
            (-18, 54, "+"),
            (24, 54, "+"),
        ],
        [
            (-48, 54, "4"),
            (-32, 54, "5"),
            (-1, 54, "3"),
            (35, 54, "1"),
            (50, 54, "2"),
            (-25, 73, "1"),
            (-11, 73, "2"),
            (17, 73, "3"),
            (31, 73, "4"),
        ],
        [
            (0, "g", 1, 0), (0, "g", 2, 0),
            (1, "g", 3, 0), (1, "g", 4, 0),
            (2, "g", 5, 0), (2, "g", 6, 0),
            (3, "l", 0, 0), (3, "l", 1, 0),
            (4, "g", 7, 0), (4, "l", 2, 0),
            (5, "g", 4, 0), (5, "g", 8, 0),
            (6, "l", 3, 0), (6, "l", 4, 0),
            (7, "l", 5, 0), (7, "l", 6, 0),
            (8, "l", 7, 0), (8, "l", 8, 0),
        ],
        r=6.4,
    )
    c.text(174.0, 88.0, ".", font_size=12.0, fill=theme.fg)
    return c.to_svg()


def _draw_prefix_net(
    c: SvgCanvas,
    x_left: float,
    x_right: float,
    y0: float,
    dy: float,
    n_wires: int,
    ops: list[tuple[float, int, int]],
    r_dot: float = 2.35,
) -> None:
    theme = c.theme
    wire_col = "#475569" if theme.is_dark else theme.fg
    for i in range(n_wires):
        yw = y0 + i * dy
        c.line(x_left, yw, x_right, yw, stroke=wire_col, stroke_width=1.05)
    op_col = theme.cyan if theme.is_dark else theme.fg
    dot_col = theme.gold if theme.is_dark else theme.fg
    for xc, wi, wj in ops:
        yi = y0 + (wi - 1) * dy
        yj = y0 + (wj - 1) * dy
        c.line(xc, yi, xc, yj - r_dot, stroke=op_col, stroke_width=1.25)
        c.circle(xc, yj, r_dot, fill=theme.bg, stroke=dot_col, stroke_width=1.3)


def fig_p580_inline_1(theme: Theme) -> str:
    w, h = 360.0, 92.0
    c = SvgCanvas(w, h, theme)
    y0, dy = 13.0, 9.2
    c.text(21.0, y0 + 3.5 * dy, "P_8 =", font_size=10.5, fill=theme.fg, italic=True, rich=True)
    p8_ops = [
        (46.0, 1, 2), (46.0, 5, 6),
        (56.0, 3, 4), (56.0, 7, 8),
        (66.0, 2, 4), (66.0, 6, 7),
        (76.0, 2, 3), (76.0, 6, 8),
        (86.0, 4, 5),
        (95.0, 4, 6),
        (104.0, 4, 7),
        (113.0, 4, 8),
    ]
    _draw_prefix_net(c, 38.0, 122.0, y0, dy, 8, p8_ops, r_dot=2.2)
    p8_delays = [0, 1, 2, 2, 3, 3, 3, 3]
    dcol = theme.muted if theme.is_dark else theme.fg
    for i, dv in enumerate(p8_delays):
        c.text(127.0, y0 + i * dy, f"(delay {dv})", font_size=7.6, fill=dcol, anchor="start")
    c.text(173.0, y0 + 3.5 * dy, ";", font_size=11.0, fill=theme.fg)

    c.text(201.0, y0 + 3.5 * dy, "Q_8 =", font_size=10.5, fill=theme.fg, italic=True, rich=True)
    q8_ops = [
        (226.0, 1, 2), (226.0, 3, 4), (226.0, 5, 6), (226.0, 7, 8),
        (238.0, 2, 4), (238.0, 6, 8),
        (250.0, 4, 5),
        (260.0, 4, 6),
        (270.0, 4, 8),
        (282.0, 2, 3), (282.0, 6, 7),
    ]
    _draw_prefix_net(c, 218.0, 292.0, y0, dy, 8, q8_ops, r_dot=2.2)
    q8_delays = [0, 1, 2, 2, 3, 3, 4, 3]
    for i, dv in enumerate(q8_delays):
        c.text(297.0, y0 + i * dy, f"(delay {dv})", font_size=7.6, fill=dcol, anchor="start")
    c.text(344.0, y0 + 3.5 * dy, ".", font_size=11.0, fill=theme.fg)
    return c.to_svg()


def fig_p580_inline_2(theme: Theme) -> str:
    w, h = 122.0, 146.0
    c = SvgCanvas(w, h, theme)
    y0, dy = 11.0, 8.2
    snir_ops = [
        (22.0, 1, 2), (22.0, 3, 4), (22.0, 5, 6), (22.0, 7, 8), (22.0, 9, 10), (22.0, 11, 12), (22.0, 13, 14),
        (36.0, 2, 4), (36.0, 6, 8), (36.0, 10, 12), (36.0, 14, 15),
        (50.0, 4, 8), (50.0, 12, 15),
        (64.0, 8, 15),
        (78.0, 8, 12),
        (92.0, 4, 6), (92.0, 8, 10), (92.0, 12, 14),
        (106.0, 2, 3), (106.0, 4, 5), (106.0, 6, 7), (106.0, 8, 9), (106.0, 10, 11), (106.0, 12, 13), (106.0, 15, 16),
    ]
    _draw_prefix_net(c, 12.0, 114.0, y0, dy, 16, snir_ops, r_dot=2.1)
    return c.to_svg()


def _mini_bdd_edge(
    c: SvgCanvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    is_hi: bool,
    r1: float = 4.6,
    r2: float = 4.6,
    curve: float = 0.0,
) -> None:
    col = c.theme.hi_stroke if is_hi else c.theme.lo_stroke
    dash: bool | str = False if is_hi else "2.2,1.7"
    c.graph_edge(x1, y1, x2, y2, r1=r1, r2=r2, curve=curve, stroke=col, stroke_width=1.05, dashed=dash)


def _mini_node(c: SvgCanvas, x: float, y: float, lbl: str, r: float = 4.6) -> None:
    st = (c.theme.cyan if lbl == "1" else c.theme.mint) if c.theme.is_dark else c.theme.fg
    c.circle(x, y, r, fill=c.theme.node_fill, stroke=st, stroke_width=1.05)
    c.text(x, y, lbl, font_size=6.5, fill=c.theme.fg)


def _mini_sink(c: SvgCanvas, x: float, y: float, is_true: bool, sz: float = 7.4) -> None:
    c.bdd_sink(x, y, "⊤" if is_true else "⊥", size=sz, is_true=is_true)


def fig_p635_inline_1(theme: Theme) -> str:
    w, h = 456.0, 66.0
    c = SvgCanvas(w, h, theme)
    y1, y2, ys, ytxt = 13.0, 27.0, 42.0, 55.5
    r = 4.5
    rs = 4.0
    dx = 6.2
    sizes = [1, 4, 4, 3, 4, 3, 5, 4, 4, 5, 3, 4, 3, 4, 4, 1]

    for m in range(16):
        cx = 16.0 + m * 28.2
        c.text(cx, ytxt, str(sizes[m]), font_size=8.2, fill=theme.muted if theme.is_dark else theme.fg)
        if m == 0:
            _mini_sink(c, cx, ys, False)
            continue
        if m == 15:
            _mini_sink(c, cx, ys, True)
            continue

        xl, xr = cx - dx, cx + dx
        _mini_sink(c, xl, ys, False)
        _mini_sink(c, xr, ys, True)

        b0 = (m >> 3) & 1
        b1 = (m >> 2) & 1
        b2 = (m >> 1) & 1
        b3 = m & 1
        lo_sub = (b0, b1)
        hi_sub = (b2, b3)

        if lo_sub == hi_sub:
            _mini_node(c, cx, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y2, xr if b0 else xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y2, xr if b1 else xl, ys, True, r1=r, r2=rs)
            continue

        _mini_node(c, cx, y1, "1", r=r)
        lo_const = b0 == b1
        hi_const = b2 == b3
        if lo_const and hi_const:
            _mini_bdd_edge(c, cx, y1, xr if b0 else xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y1, xr if b2 else xl, ys, True, r1=r, r2=rs)
        elif not lo_const and not hi_const:
            _mini_node(c, xl, y2, "2", r=r)
            _mini_node(c, xr, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, xl, y2, False, r1=r, r2=r)
            _mini_bdd_edge(c, cx, y1, xr, y2, True, r1=r, r2=r)
            _mini_bdd_edge(c, xl, y2, xr if b0 else xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, xl, y2, xr if b1 else xl, ys, True, r1=r, r2=rs)
            _mini_bdd_edge(c, xr, y2, xr if b2 else xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, xr, y2, xr if b3 else xl, ys, True, r1=r, r2=rs)
        elif lo_const:
            _mini_node(c, cx, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, cx, y2, True, r1=r, r2=r)
            sx = xr if b0 else xl
            cv = 5.5 if b0 else -5.5
            _mini_bdd_edge(c, cx, y1, sx, ys, False, r1=r, r2=rs, curve=cv)
            _mini_bdd_edge(c, cx, y2, xr if b2 else xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y2, xr if b3 else xl, ys, True, r1=r, r2=rs)
        else:
            _mini_node(c, cx, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, cx, y2, False, r1=r, r2=r)
            sx = xr if b2 else xl
            cv = 5.5 if b2 else -5.5
            _mini_bdd_edge(c, cx, y1, sx, ys, True, r1=r, r2=rs, curve=cv)
            _mini_bdd_edge(c, cx, y2, xr if b0 else xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y2, xr if b1 else xl, ys, True, r1=r, r2=rs)
    return c.to_svg()


def fig_p635_inline_2(theme: Theme) -> str:
    w, h = 236.0, 148.0
    c = SvgCanvas(w, h, theme)
    cx, cy = w * 0.5, h * 0.5
    r = 7.5
    rs = 8.0

    pos: dict[str, tuple[float, float]] = {
        "top": (cx, cy - 56.0),
        "bot": (cx, cy + 56.0),
        "2L": (cx - 46.0, cy),
        "2R": (cx + 46.0, cy),
        "1_fl": (cx - 96.0, cy),
        "1_fr": (cx + 96.0, cy),
        "1_ul_in": (cx - 26.0, cy - 22.0),
        "1_ul_out": (cx - 56.0, cy - 36.0),
        "1_ur_in": (cx + 26.0, cy - 22.0),
        "1_ur_out": (cx + 56.0, cy - 36.0),
        "1_mid_t": (cx, cy - 15.0),
        "1_mid_b": (cx, cy + 15.0),
        "1_ll_in": (cx - 26.0, cy + 22.0),
        "1_ll_out": (cx - 56.0, cy + 36.0),
        "1_lr_in": (cx + 26.0, cy + 22.0),
        "1_lr_out": (cx + 56.0, cy + 36.0),
    }

    links: list[tuple[str, str, bool, float]] = [
        ("2L", "bot", False, 0.0), ("2L", "top", True, 0.0),
        ("2R", "top", False, 0.0), ("2R", "bot", True, 0.0),
        ("1_fl", "top", True, -24.0), ("1_fl", "bot", False, 24.0),
        ("1_fr", "top", False, 24.0), ("1_fr", "bot", True, -24.0),
        ("1_ul_out", "top", False, -6.0), ("1_ul_out", "2L", True, 4.0),
        ("1_ul_in", "2L", False, 0.0), ("1_ul_in", "top", True, 0.0),
        ("1_ur_out", "top", True, 6.0), ("1_ur_out", "2R", False, -4.0),
        ("1_ur_in", "2R", True, 0.0), ("1_ur_in", "top", False, 0.0),
        ("1_mid_t", "2L", False, 0.0), ("1_mid_t", "2R", True, 0.0),
        ("1_mid_b", "2R", False, 0.0), ("1_mid_b", "2L", True, 0.0),
        ("1_ll_out", "bot", True, 6.0), ("1_ll_out", "2L", False, -4.0),
        ("1_ll_in", "2L", True, 0.0), ("1_ll_in", "bot", False, 0.0),
        ("1_lr_out", "bot", False, -6.0), ("1_lr_out", "2R", True, 4.0),
        ("1_lr_in", "2R", False, 0.0), ("1_lr_in", "bot", True, 0.0),
    ]

    for u, v, is_hi, cv in links:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        r2 = rs if v in ("top", "bot") else r
        c.bdd_edge(x1, y1, x2, y2, is_hi=is_hi, r1=r, r2=r2, curve=cv)

    c.bdd_sink(pos["top"][0], pos["top"][1], "⊤", size=14.5, is_true=True)
    c.bdd_sink(pos["bot"][0], pos["bot"][1], "⊥", size=14.5, is_true=False)
    for k in ("2L", "2R"):
        c.bdd_node(pos[k][0], pos[k][1], "2", r=r, accent=theme.mint if theme.is_dark else theme.fg, font_size=9.2)
    for k, (px, py) in pos.items():
        if k.startswith("1_"):
            c.bdd_node(px, py, "1", r=r, accent=theme.cyan if theme.is_dark else theme.fg, font_size=9.2)
    return c.to_svg()


def fig_p636_inline_1(theme: Theme) -> str:
    w, h = 152.0, 68.0
    c = SvgCanvas(w, h, theme)
    r = 8.2
    c.bdd_edge(30.0, 22.0, 18.0, 50.0, is_hi=False, r1=r, r2=6.5)
    c.bdd_edge(30.0, 22.0, 42.0, 50.0, is_hi=True, r1=r, r2=6.5)
    c.bdd_node(30.0, 22.0, "k", r=r, font_size=9.8, italic=True)
    c.text(18.0, 54.0, "α", font_size=10.2, fill=theme.fg, italic=True)
    c.text(43.0, 54.0, "α'", font_size=10.2, fill=theme.fg, italic=True)

    c.text(68.0, 32.0, "by", font_size=10.2, fill=theme.muted if theme.is_dark else theme.fg)

    c.bdd_edge(112.0, 15.0, 98.0, 35.0, is_hi=False, r1=8.0, r2=r)
    c.bdd_edge(112.0, 15.0, 125.0, 52.0, is_hi=True, r1=8.0, r2=6.5)
    c.bdd_edge(98.0, 35.0, 88.0, 53.0, is_hi=False, r1=r, r2=6.5)
    c.bdd_edge(98.0, 35.0, 122.0, 53.0, is_hi=True, r1=r, r2=6.5)
    _pill_node(c, 112.0, 15.0, 28.0, 15.0, "k-1", font_size=9.2, italic=True)
    c.bdd_node(98.0, 35.0, "k", r=r, font_size=9.8, italic=True)
    c.text(87.0, 56.0, "α", font_size=10.2, fill=theme.fg, italic=True)
    c.text(126.0, 56.0, "α'", font_size=10.2, fill=theme.fg, italic=True)
    c.text(140.0, 36.0, ".", font_size=11.0, fill=theme.fg)
    return c.to_svg()


def fig_p636_inline_2(theme: Theme) -> str:
    w, h = 396.0, 78.0
    c = SvgCanvas(w, h, theme)
    r = 7.8

    c.bdd_edge(28.0, 26.0, 17.0, 54.0, is_hi=False, r1=r, r2=6.0)
    c.bdd_edge(28.0, 26.0, 39.0, 54.0, is_hi=True, r1=r, r2=6.0)
    c.bdd_node(28.0, 26.0, "k", r=r, font_size=9.5, italic=True)
    c.text(17.0, 58.0, "α", font_size=9.8, italic=True)
    c.text(40.0, 58.0, "α'", font_size=9.8, italic=True)

    c.text(62.0, 38.0, "by", font_size=9.8, fill=theme.muted if theme.is_dark else theme.fg)

    c.bdd_edge(108.0, 16.0, 92.0, 39.0, is_hi=False, r1=7.8, r2=r)
    c.bdd_edge(108.0, 16.0, 124.0, 39.0, is_hi=True, r1=7.8, r2=r)
    c.bdd_edge(92.0, 39.0, 92.0, 59.0, is_hi=False, r1=r, r2=6.0)
    c.bdd_edge(92.0, 39.0, 124.0, 59.0, is_hi=True, r1=r, r2=6.0)
    c.bdd_edge(124.0, 39.0, 124.0, 59.0, is_hi=False, r1=r, r2=6.0)
    c.bdd_edge(124.0, 39.0, 92.0, 59.0, is_hi=True, r1=r, r2=6.0)
    _pill_node(c, 108.0, 16.0, 27.0, 14.5, "k-1", font_size=8.8, italic=True)
    c.bdd_node(92.0, 39.0, "k", r=r, font_size=9.5, italic=True)
    c.bdd_node(124.0, 39.0, "k", r=r, font_size=9.5, italic=True)
    c.text(92.0, 64.0, "α", font_size=9.8, italic=True)
    c.text(125.0, 64.0, "α'", font_size=9.8, italic=True)

    c.text(158.0, 38.0, ";", font_size=12.0, fill=theme.muted)

    c.bdd_edge(196.0, 26.0, 186.0, 54.0, is_hi=False, r1=r, r2=6.0)
    c.bdd_edge(196.0, 26.0, 206.0, 54.0, is_hi=True, r1=r, r2=6.0)
    c.bdd_node(196.0, 26.0, "k", r=r, font_size=9.5, italic=True)
    c.text(186.0, 58.0, "α", font_size=9.8, italic=True)
    c.text(207.0, 58.0, "α'", font_size=9.8, italic=True)

    c.bdd_edge(234.0, 26.0, 224.0, 54.0, is_hi=False, r1=r, r2=6.0)
    c.bdd_edge(234.0, 26.0, 244.0, 54.0, is_hi=True, r1=r, r2=6.0)
    c.bdd_node(234.0, 26.0, "k", r=r, font_size=9.5, italic=True)
    c.text(224.0, 58.0, "α'", font_size=9.8, italic=True)
    c.text(245.0, 58.0, "α", font_size=9.8, italic=True)

    c.text(270.0, 38.0, "by", font_size=9.8, fill=theme.muted if theme.is_dark else theme.fg)

    c.bdd_edge(312.0, 16.0, 312.0, 39.0, is_hi=False, r1=7.5, r2=r)
    c.bdd_edge(312.0, 16.0, 354.0, 39.0, is_hi=True, r1=7.5, r2=r)
    c.bdd_edge(354.0, 16.0, 354.0, 39.0, is_hi=False, r1=7.5, r2=r)
    c.bdd_edge(354.0, 16.0, 312.0, 39.0, is_hi=True, r1=7.5, r2=r)
    c.bdd_edge(312.0, 39.0, 312.0, 59.0, is_hi=False, r1=r, r2=6.0)
    c.bdd_edge(312.0, 39.0, 354.0, 59.0, is_hi=True, r1=r, r2=6.0)
    c.bdd_edge(354.0, 39.0, 354.0, 59.0, is_hi=False, r1=r, r2=6.0)
    c.bdd_edge(354.0, 39.0, 312.0, 59.0, is_hi=True, r1=r, r2=6.0)
    _pill_node(c, 312.0, 16.0, 27.0, 14.5, "k-1", font_size=8.8, italic=True)
    _pill_node(c, 354.0, 16.0, 27.0, 14.5, "k-1", font_size=8.8, italic=True)
    c.bdd_node(312.0, 39.0, "k", r=r, font_size=9.5, italic=True)
    c.bdd_node(354.0, 39.0, "k", r=r, font_size=9.5, italic=True)
    c.text(312.0, 64.0, "α", font_size=9.8, italic=True)
    c.text(355.0, 64.0, "α'", font_size=9.8, italic=True)
    c.text(380.0, 39.0, ".", font_size=11.0, fill=theme.fg)
    return c.to_svg()


def fig_p636_inline_3(theme: Theme) -> str:
    w, h = 424.0, 72.0
    c = SvgCanvas(w, h, theme)
    r = 8.0
    lcol = theme.muted if theme.is_dark else theme.fg

    for ox, b1 in [(12.0, "0"), (218.0, "1")]:
        x_a, x_b = ox + 36.0, ox + 114.0
        y_top, y_bot = 31.0, 56.0
        x_t0, x_t1, x_sk = ox + 36.0, ox + 114.0, ox + 172.0

        c.text(x_a, 13.0, f"(x_1 x_{{j-1}} = {b1}0)", font_size=8.6, fill=lcol, italic=True, rich=True)
        c.text(x_b, 13.0, f"(x_1 x_{{j-1}} = {b1}1)", font_size=8.6, fill=lcol, italic=True, rich=True)

        c.bdd_edge(x_a, y_top, x_t0, y_bot - 6.0, is_hi=False, r1=r, r2=2.0)
        c.bdd_edge(x_a, y_top, x_t1 - 12.0, y_bot - 6.0, is_hi=True, r1=r, r2=2.0)
        c.bdd_edge(x_b, y_top, x_t0 + 14.0, y_bot - 6.0, is_hi=False, r1=r, r2=2.0)
        c.bdd_edge(x_b, y_top, x_sk, y_bot, is_hi=True, r1=r, r2=7.5)

        c.bdd_node(x_a, y_top, "j", r=r, font_size=9.5, italic=True)
        c.bdd_node(x_b, y_top, "j", r=r, font_size=9.5, italic=True)
        c.text(x_t0, y_bot, f"(x_1 x_j = {b1}0)", font_size=8.6, fill=theme.fg, italic=True, rich=True)
        c.text(x_t1, y_bot, f"(x_1 x_j = {b1}1)", font_size=8.6, fill=theme.fg, italic=True, rich=True)
        c.bdd_sink(x_sk, y_bot, "⊥", size=13.5, is_true=False)

    c.text(412.0, 42.0, ".", font_size=11.0, fill=theme.fg)
    return c.to_svg()


def fig_p637_inline(theme: Theme) -> str:
    w, h = 368.0, 74.0
    c = SvgCanvas(w, h, theme)
    r = 8.2
    lcol = theme.muted if theme.is_dark else theme.fg
    y_top, y_bot = 31.0, 57.0
    x1, x2, x3 = 86.0, 184.0, 278.0
    xs_l, xt_00, xt_10, xt_1, xs_r = 24.0, 98.0, 190.0, 272.0, 338.0

    c.text(x1, 13.0, "(x_{j-2}x_{j-1} = 00)", font_size=8.8, fill=lcol, italic=True, rich=True)
    c.text(x2, 13.0, "(x_{j-2}x_{j-1} = 10)", font_size=8.8, fill=lcol, italic=True, rich=True)
    c.text(x3, 13.0, "(x_{j-1} = 1)", font_size=8.8, fill=lcol, italic=True, rich=True)

    c.bdd_edge(x1, y_top, xs_l, y_bot, is_hi=False, r1=r, r2=7.5)
    c.bdd_edge(x1, y_top, xt_1 - 18.0, y_bot - 6.0, is_hi=True, r1=r, r2=2.0)
    c.bdd_edge(x2, y_top, xt_00 + 12.0, y_bot - 6.0, is_hi=False, r1=r, r2=2.0)
    c.bdd_edge(x2, y_top, xt_1 - 8.0, y_bot - 6.0, is_hi=True, r1=r, r2=2.0)
    c.bdd_edge(x3, y_top, xt_10 + 12.0, y_bot - 6.0, is_hi=False, r1=r, r2=2.0)
    c.bdd_edge(x3, y_top, xs_r, y_bot, is_hi=True, r1=r, r2=7.5)

    for px in (x1, x2, x3):
        c.bdd_node(px, y_top, "j", r=r, font_size=9.5, italic=True)
    c.bdd_sink(xs_l, y_bot, "⊥", size=13.5, is_true=False)
    c.bdd_sink(xs_r, y_bot, "⊥", size=13.5, is_true=False)
    c.text(xt_00, y_bot, "(x_{j-1}x_j = 00)", font_size=8.8, fill=theme.fg, italic=True, rich=True)
    c.text(xt_10, y_bot, "(x_{j-1}x_j = 10)", font_size=8.8, fill=theme.fg, italic=True, rich=True)
    c.text(xt_1, y_bot, "(x_j = 1)", font_size=8.8, fill=theme.fg, italic=True, rich=True)
    c.text(356.0, 42.0, ",", font_size=11.0, fill=theme.fg)
    return c.to_svg()


def fig_p640_inline_1(theme: Theme) -> str:
    w, h = 232.0, 148.0
    c = SvgCanvas(w, h, theme)
    r = 7.4
    rs = 7.2
    dy = 19.2
    y0 = 16.0

    lx = 58.0
    dx = 19.0
    lp: dict[str, tuple[float, float]] = {
        "1": (lx, y0),
        "2L": (lx - dx * 0.5, y0 + dy), "2R": (lx + dx * 0.5, y0 + dy),
        "3L": (lx - dx, y0 + 2 * dy), "3M": (lx, y0 + 2 * dy), "3R": (lx + dx, y0 + 2 * dy),
        "4L": (lx - dx, y0 + 3 * dy), "4M": (lx, y0 + 3 * dy), "4R": (lx + dx, y0 + 3 * dy),
        "5L": (lx - dx, y0 + 4 * dy), "5M": (lx, y0 + 4 * dy), "5R": (lx + dx, y0 + 4 * dy),
        "b6": (lx - dx, y0 + 5 * dy), "6": (lx, y0 + 5 * dy), "t6": (lx + dx, y0 + 5 * dy),
        "b7": (lx - dx * 0.5, y0 + 6 * dy), "t7": (lx + dx * 0.5, y0 + 6 * dy),
    }
    l_edges = [
        ("1", "2L", False), ("1", "2R", True),
        ("2L", "3L", False), ("2L", "3M", True),
        ("2R", "3M", False), ("2R", "3R", True),
        ("3L", "4L", False), ("3L", "4M", True),
        ("3M", "4L", False), ("3M", "4R", True),
        ("3R", "4M", False), ("3R", "4R", True),
        ("4L", "5L", False), ("4L", "5M", True),
        ("4M", "5L", False), ("4M", "5R", True),
        ("4R", "5M", False), ("4R", "5R", True),
        ("5L", "b6", False), ("5L", "6", True),
        ("5M", "b6", False), ("5M", "t6", True),
        ("5R", "6", False), ("5R", "t6", True),
        ("6", "b7", False), ("6", "t7", True),
    ]
    for u, v, is_hi in l_edges:
        c.bdd_edge(lp[u][0], lp[u][1], lp[v][0], lp[v][1], is_hi=is_hi, r1=r, r2=rs if v[0] in ("b", "t") else r)
    for k, (px, py) in lp.items():
        if k.startswith("b"):
            c.bdd_sink(px, py, "⊥", size=13.0, is_true=False)
        elif k.startswith("t"):
            c.bdd_sink(px, py, "⊤", size=13.0, is_true=True)
        else:
            c.bdd_node(px, py, k[0], r=r, font_size=9.2)

    rx = 168.0
    rp: dict[str, tuple[float, float]] = {
        "1": (rx, y0),
        "2L": (rx - dx * 0.5, y0 + dy), "2R": (rx + dx * 0.5, y0 + dy),
        "b3": (rx - dx * 1.5, y0 + 2 * dy), "3L": (rx - dx * 0.5, y0 + 2 * dy), "3R": (rx + dx * 0.5, y0 + 2 * dy), "t3": (rx + dx * 1.5, y0 + 2 * dy),
        "b4": (rx - dx * 1.5, y0 + 3 * dy), "4L": (rx - dx * 0.5, y0 + 3 * dy), "4R": (rx + dx * 0.5, y0 + 3 * dy), "t4": (rx + dx * 1.5, y0 + 3 * dy),
        "b5": (rx - dx * 1.5, y0 + 4 * dy), "5L": (rx - dx * 0.5, y0 + 4 * dy), "5R": (rx + dx * 0.5, y0 + 4 * dy), "t5": (rx + dx * 1.5, y0 + 4 * dy),
        "b6": (rx - dx, y0 + 5 * dy), "6": (rx, y0 + 5 * dy), "t6": (rx + dx, y0 + 5 * dy),
        "b7": (rx - dx * 0.5, y0 + 6 * dy), "t7": (rx + dx * 0.5, y0 + 6 * dy),
    }
    r_edges = [
        ("1", "2L", False), ("1", "2R", True),
        ("2L", "b3", False), ("2L", "3L", True),
        ("2R", "3R", False), ("2R", "t3", True),
        ("3L", "b4", False), ("3L", "4R", True),
        ("3R", "4L", False), ("3R", "t4", True),
        ("4L", "b5", False), ("4L", "5R", True),
        ("4R", "5L", False), ("4R", "t5", True),
        ("5L", "b6", False), ("5L", "6", True),
        ("5R", "6", False), ("5R", "t6", True),
        ("6", "b7", False), ("6", "t7", True),
    ]
    for u, v, is_hi in r_edges:
        c.bdd_edge(rp[u][0], rp[u][1], rp[v][0], rp[v][1], is_hi=is_hi, r1=r, r2=rs if v[0] in ("b", "t") else r)
    for k, (px, py) in rp.items():
        if k.startswith("b"):
            c.bdd_sink(px, py, "⊥", size=13.0, is_true=False)
        elif k.startswith("t"):
            c.bdd_sink(px, py, "⊤", size=13.0, is_true=True)
        else:
            c.bdd_node(px, py, k[0], r=r, font_size=9.2)
    return c.to_svg()


def fig_p640_inline_2(theme: Theme) -> str:
    w, h = 448.0, 178.0
    c = SvgCanvas(w, h, theme)
    cx, cy = w * 0.5, h * 0.5
    r = 6.8
    rs = 7.0

    nodes: dict[str, tuple[float, float, str, float, float, str]] = {
        "0": (cx - 102.0, cy, "⊥", -9.0, 0.0, "end"),
        "1": (cx + 102.0, cy, "⊤", 9.0, 0.0, "start"),
        "01": (cx, cy - 44.0, "3", 0.0, -10.5, "middle"),
        "10": (cx, cy + 44.0, "3", 0.0, 11.0, "middle"),
        "001": (cx - 102.0, cy - 48.0, "2", 0.0, -10.5, "middle"),
        "011": (cx + 102.0, cy - 48.0, "2", 0.0, -10.5, "middle"),
        "010": (cx - 32.0, cy, "2", -9.0, 0.0, "end"),
        "101": (cx + 32.0, cy, "2", 9.0, 0.0, "start"),
        "100": (cx - 102.0, cy + 48.0, "2", 0.0, 11.0, "middle"),
        "110": (cx + 102.0, cy + 48.0, "2", 0.0, 11.0, "middle"),
        "0011": (cx, cy - 72.0, "1", 0.0, -10.5, "middle"),
        "1100": (cx, cy + 72.0, "1", 0.0, 11.0, "middle"),
        "1010": (cx, cy - 15.0, "1", 0.0, -10.0, "middle"),
        "0101": (cx, cy + 15.0, "1", 0.0, 10.5, "middle"),
        "1001": (cx - 186.0, cy, "1", -9.0, 0.0, "end"),
        "0110": (cx + 186.0, cy, "1", 9.0, 0.0, "start"),
        "0001": (cx - 138.0, cy - 23.0, "1", -9.0, 0.0, "end"),
        "1000": (cx - 138.0, cy + 23.0, "1", -9.0, 0.0, "end"),
        "0010": (cx - 68.0, cy - 23.0, "1", -9.0, 0.0, "end"),
        "0100": (cx - 68.0, cy + 23.0, "1", -9.0, 0.0, "end"),
        "1011": (cx + 68.0, cy - 23.0, "1", 9.0, 0.0, "start"),
        "1101": (cx + 68.0, cy + 23.0, "1", 9.0, 0.0, "start"),
        "0111": (cx + 138.0, cy - 23.0, "1", 9.0, 0.0, "start"),
        "1110": (cx + 138.0, cy + 23.0, "1", 9.0, 0.0, "start"),
    }

    def reduce_sym(tt: str) -> str:
        if all(ch == "0" for ch in tt):
            return "0"
        if all(ch == "1" for ch in tt):
            return "1"
        return tt

    curves: dict[tuple[str, str, bool], float] = {
        ("1001", "100", False): 16.0,
        ("1001", "001", True): -16.0,
        ("0110", "011", False): 16.0,
        ("0110", "110", True): -16.0,
    }

    for tt, (x1, y1, kind, _, _, _) in nodes.items():
        if len(tt) <= 1:
            continue
        lo_t = reduce_sym(tt[:-1])
        hi_t = reduce_sym(tt[1:])
        for is_hi, tgt in [(False, lo_t), (True, hi_t)]:
            x2, y2, tkind, _, _, _ = nodes[tgt]
            r2 = rs if tkind in ("⊥", "⊤") else r
            cv = curves.get((tt, tgt, is_hi), 0.0)
            c.bdd_edge(x1, y1, x2, y2, is_hi=is_hi, r1=r, r2=r2, curve=cv)

    tcol = theme.muted if theme.is_dark else theme.fg
    lvl_col = {"1": theme.cyan, "2": theme.mint, "3": theme.violet}
    for tt, (px, py, kind, ox, oy, anc) in nodes.items():
        if kind == "⊥":
            c.bdd_sink(px, py, "⊥", size=12.8, is_true=False)
        elif kind == "⊤":
            c.bdd_sink(px, py, "⊤", size=12.8, is_true=True)
        else:
            acc = lvl_col[kind] if theme.is_dark else theme.fg
            c.bdd_node(px, py, kind, r=r, accent=acc, font_size=8.6)
        c.text(px + ox, py + oy, tt, font_size=6.8, fill=tcol, anchor=anc, mono=True)
    return c.to_svg()


def fig_p641_inline(theme: Theme) -> str:
    w, h = 382.0, 124.0
    c = SvgCanvas(w, h, theme)
    r = 7.0
    rs = 7.0
    y0, dy = 26.0, 21.0
    dx = 26.0
    lcol = theme.gold if theme.is_dark else theme.fg

    c.text(16.0, y0 + 2 * dy, "(a)", font_size=9.8, fill=theme.fg)
    ax0 = 56.0
    ap: dict[str, tuple[float, float]] = {
        "1_0": (ax0, y0), "1_1": (ax0 + dx, y0), "1_2": (ax0 + 2 * dx, y0), "1_3": (ax0 + 3 * dx, y0),
        "b2": (ax0 - 0.5 * dx, y0 + dy), "2_0": (ax0 + 0.5 * dx, y0 + dy), "2_1": (ax0 + 1.5 * dx, y0 + dy), "2_2": (ax0 + 2.5 * dx, y0 + dy), "t2": (ax0 + 3.5 * dx, y0 + dy),
        "b3": (ax0, y0 + 2 * dy), "3_0": (ax0 + dx, y0 + 2 * dy), "3_1": (ax0 + 2 * dx, y0 + 2 * dy), "t3": (ax0 + 3 * dx, y0 + 2 * dy),
        "b4": (ax0 + 0.5 * dx, y0 + 3 * dy), "4_0": (ax0 + 1.5 * dx, y0 + 3 * dy), "t4": (ax0 + 2.5 * dx, y0 + 3 * dy),
        "b5": (ax0 + dx, y0 + 4 * dy), "t5": (ax0 + 2 * dx, y0 + 4 * dy),
    }
    a_edges = [
        ("1_0", "b2", False), ("1_0", "2_0", True),
        ("1_1", "2_0", False), ("1_1", "2_1", True),
        ("1_2", "2_1", False), ("1_2", "2_2", True),
        ("1_3", "2_2", False), ("1_3", "t2", True),
        ("2_0", "b3", False), ("2_0", "3_0", True),
        ("2_1", "3_0", False), ("2_1", "3_1", True),
        ("2_2", "3_1", False), ("2_2", "t3", True),
        ("3_0", "b4", False), ("3_0", "4_0", True),
        ("3_1", "4_0", False), ("3_1", "t4", True),
        ("4_0", "b5", False), ("4_0", "t5", True),
    ]
    for u, v, is_hi in a_edges:
        c.bdd_edge(ap[u][0], ap[u][1], ap[v][0], ap[v][1], is_hi=is_hi, r1=r, r2=rs if v[0] in ("b", "t") else r)
    for k, (px, py) in ap.items():
        if k.startswith("b"):
            c.bdd_sink(px, py, "⊥", size=12.4, is_true=False)
        elif k.startswith("t"):
            c.bdd_sink(px, py, "⊤", size=12.4, is_true=True)
        else:
            c.bdd_node(px, py, k[0], r=r, font_size=8.8)
    for idx, sub in enumerate(["≥4", "≥3", "≥2", "≥1"]):
        c.text(ax0 + idx * dx, y0 - 13.0, f"s_{{{sub}}}", font_size=8.5, fill=lcol, italic=True, rich=True)

    c.text(165.0, y0 + 2 * dy, ";", font_size=10.5, fill=theme.fg)
    c.text(196.0, y0 + 2 * dy, "(b)", font_size=9.8, fill=theme.fg)

    bx0 = 236.0
    bp: dict[str, tuple[float, float]] = {
        "1_0": (bx0, y0), "1_1": (bx0 + dx, y0), "1_2": (bx0 + 2 * dx, y0), "1_3": (bx0 + 3 * dx, y0), "1_4": (bx0 + 4 * dx, y0),
        "bl2": (bx0 - 0.5 * dx, y0 + dy), "2_0": (bx0 + 0.5 * dx, y0 + dy), "2_1": (bx0 + 1.5 * dx, y0 + dy), "2_2": (bx0 + 2.5 * dx, y0 + dy), "2_3": (bx0 + 3.5 * dx, y0 + dy), "br2": (bx0 + 4.5 * dx, y0 + dy),
        "bl3": (bx0, y0 + 2 * dy), "3_0": (bx0 + dx, y0 + 2 * dy), "3_1": (bx0 + 2 * dx, y0 + 2 * dy), "3_2": (bx0 + 3 * dx, y0 + 2 * dy), "br3": (bx0 + 4 * dx, y0 + 2 * dy),
        "bl4": (bx0 + 0.5 * dx, y0 + 3 * dy), "4_0": (bx0 + 1.5 * dx, y0 + 3 * dy), "4_1": (bx0 + 2.5 * dx, y0 + 3 * dy), "br4": (bx0 + 3.5 * dx, y0 + 3 * dy),
        "bl5": (bx0 + dx, y0 + 4 * dy), "t5": (bx0 + 2 * dx, y0 + 4 * dy), "br5": (bx0 + 3 * dx, y0 + 4 * dy),
    }
    b_edges = [
        ("1_0", "bl2", False), ("1_0", "2_0", True),
        ("1_1", "2_0", False), ("1_1", "2_1", True),
        ("1_2", "2_1", False), ("1_2", "2_2", True),
        ("1_3", "2_2", False), ("1_3", "2_3", True),
        ("1_4", "2_3", False), ("1_4", "br2", True),
        ("2_0", "bl3", False), ("2_0", "3_0", True),
        ("2_1", "3_0", False), ("2_1", "3_1", True),
        ("2_2", "3_1", False), ("2_2", "3_2", True),
        ("2_3", "3_2", False), ("2_3", "br3", True),
        ("3_0", "bl4", False), ("3_0", "4_0", True),
        ("3_1", "4_0", False), ("3_1", "4_1", True),
        ("3_2", "4_1", False), ("3_2", "br4", True),
        ("4_0", "bl5", False), ("4_0", "t5", True),
        ("4_1", "t5", False), ("4_1", "br5", True),
    ]
    for u, v, is_hi in b_edges:
        c.bdd_edge(bp[u][0], bp[u][1], bp[v][0], bp[v][1], is_hi=is_hi, r1=r, r2=rs if v[0] in ("b", "t") else r)
    for k, (px, py) in bp.items():
        if k.startswith("b"):
            c.bdd_sink(px, py, "⊥", size=12.4, is_true=False)
        elif k.startswith("t"):
            c.bdd_sink(px, py, "⊤", size=12.4, is_true=True)
        else:
            c.bdd_node(px, py, k[0], r=r, font_size=8.8)
    for idx, sub in enumerate(["4", "3", "2", "1", "0"]):
        c.text(bx0 + idx * dx, y0 - 13.0, f"s_{sub}", font_size=8.5, fill=lcol, italic=True, rich=True)
    c.text(370.0, y0 + 2 * dy, ".", font_size=10.5, fill=theme.fg)
    return c.to_svg()


def fig_p650_inline_1(theme: Theme) -> str:
    w, h = 468.0, 92.0
    c = SvgCanvas(w, h, theme)
    step = 11.2
    maps = [
        (
            22.0,
            {"DC", "FL", "IL", "KS", "LA", "MI", "NH", "NM", "NV", "PA", "SC", "SD", "TN", "WA"},
            {"CT", "RI"},
        ),
        (
            174.0,
            {"CA", "DC", "FL", "IN", "LA", "ME", "OK", "PA", "SC", "SD", "TN", "UT", "VT", "WA", "WI"},
            {"CT", "RI"},
        ),
        (
            326.0,
            {"CA", "DC", "FL", "IL", "LA", "MA", "ME", "MI", "OK", "SC", "SD", "TN", "UT", "WA", "WV"},
            {"DE", "NJ"},
        ),
    ]
    for x0, blk, gry in maps:
        _draw_usa_submap(c, x0, 12.0, step, black_set=blk, gray_set=gry, r_dot=2.7)
    return c.to_svg()


def fig_p650_inline_2(theme: Theme) -> str:
    w, h = 256.0, 142.0
    c = SvgCanvas(w, h, theme)
    step = 18.8
    x0, y0 = 32.0, 14.0
    r_node = 6.9

    color_groups: dict[int, set[str]] = {
        1: {"AL", "AR", "CA", "DE", "IA", "ID", "MA", "ME", "NC", "ND", "NM", "OH"},
        2: {"AZ", "CO", "CT", "GA", "IN", "LA", "MO", "NH", "PA", "SD", "VA", "WA"},
        3: {"FL", "KY", "MD", "MS", "MT", "NE", "NY", "OK", "OR", "SC", "UT", "WI"},
        4: {"IL", "KS", "MI", "MN", "NJ", "NV", "RI", "TN", "TX", "VT", "WV", "WY"},
    }
    state_col = {s: cid for cid, grp in color_groups.items() for s in grp}

    edge_col = "#334155" if theme.is_dark else "#94A3B8"
    for u, v in USA_EDGES:
        if "DC" in (u, v):
            continue
        cu, ru = USA_COORDS[u]
        cv, rv = USA_COORDS[v]
        c.line(x0 + cu * step, y0 + ru * step, x0 + cv * step, y0 + rv * step, stroke=edge_col, stroke_width=0.9)

    for st, (col, row) in USA_COORDS.items():
        if st == "DC":
            continue
        px = x0 + col * step
        py = y0 + row * step
        cid = state_col[st]
        if theme.is_dark:
            styles = {
                1: ("#101A2C", theme.cyan, theme.fg),
                2: ("#2A2310", theme.gold, theme.gold),
                3: ("#2C161D", theme.coral, theme.coral),
                4: ("#152920", theme.mint, theme.mint),
            }
        else:
            styles = {
                1: ("#FFFFFF", "#0F172A", "#0F172A"),
                2: ("#E2E8F0", "#0F172A", "#0F172A"),
                3: ("#94A3B8", "#0F172A", "#0F172A"),
                4: ("#0F172A", "#0F172A", "#FFFFFF"),
            }
        fl, sk, tf = styles[cid]
        c.circle(px, py, r_node, fill=fl, stroke=sk, stroke_width=1.15)
        c.text(px, py + 0.2, st, font_size=5.8, fill=tf, sans=True, bold=True)
    return c.to_svg()


def fig_p653_inline(theme: Theme) -> str:
    w, h = 304.0, 168.0
    c = SvgCanvas(w, h, theme)
    cx = w * 0.5
    r = 7.4
    rs = 7.0
    y0, dy = 16.0, 22.0
    dx = 22.0

    pos: dict[str, tuple[float, float, str, bool]] = {
        "r0_0": (cx, y0, "7", False),
        "r1_0": (cx - 0.5 * dx, y0 + dy, "6", False),
        "r1_1": (cx + 0.5 * dx, y0 + dy, "1", True),
    }
    for i, (lbl, sh) in enumerate([("5", False), ("1", True), ("6", False), ("2", True)]):
        pos[f"r2_{i}"] = (cx + (i - 1.5) * dx, y0 + 2 * dy, lbl, sh)
    for i, (lbl, sh) in enumerate([("4", False), ("1", True), ("5", False), ("2", True), ("6", False), ("3", True)]):
        pos[f"r3_{i}"] = (cx + (i - 2.5) * dx, y0 + 3 * dy, lbl, sh)
    for i, (lbl, sh) in enumerate([("3", False), ("1", True), ("4", False), ("2", True), ("5", False), ("3", True), ("6", False), ("4", True)]):
        pos[f"r4_{i}"] = (cx + (i - 3.5) * dx, y0 + 4 * dy, lbl, sh)

    dx5 = 40.0
    for i in range(6):
        pos[f"r5_{i}"] = (cx + (i - 2.5) * dx5, y0 + 5 * dy, str(i + 1), (i % 2 == 1))

    sinks: list[tuple[float, float, bool]] = []
    for i in range(6):
        bx = pos[f"r5_{i}"][0]
        sinks.append((bx - 10.0, y0 + 6 * dy, False))
        sinks.append((bx + 10.0, y0 + 6 * dy, True))

    edges: list[tuple[str, str, bool]] = [
        ("r0_0", "r1_0", False), ("r0_0", "r1_1", True),
        ("r1_0", "r2_0", False), ("r1_0", "r2_1", True),
        ("r1_1", "r2_2", False), ("r1_1", "r2_3", True),
        ("r2_0", "r3_0", False), ("r2_0", "r3_1", True),
        ("r2_1", "r3_2", False), ("r2_1", "r3_3", True),
        ("r2_2", "r3_2", False), ("r2_2", "r3_3", True),
        ("r2_3", "r3_4", False), ("r2_3", "r3_5", True),
        ("r3_0", "r4_0", False), ("r3_0", "r4_1", True),
        ("r3_1", "r4_2", False), ("r3_1", "r4_3", True),
        ("r3_2", "r4_2", False), ("r3_2", "r4_3", True),
        ("r3_3", "r4_4", False), ("r3_3", "r4_5", True),
        ("r3_4", "r4_4", False), ("r3_4", "r4_5", True),
        ("r3_5", "r4_6", False), ("r3_5", "r4_7", True),
        ("r4_0", "r5_0", False), ("r4_0", "r5_1", True),
        ("r4_1", "r5_1", False), ("r4_1", "r5_2", True),
        ("r4_2", "r5_1", False), ("r4_2", "r5_2", True),
        ("r4_3", "r5_2", False), ("r4_3", "r5_3", True),
        ("r4_4", "r5_2", False), ("r4_4", "r5_3", True),
        ("r4_5", "r5_3", False), ("r4_5", "r5_4", True),
        ("r4_6", "r5_3", False), ("r4_6", "r5_4", True),
        ("r4_7", "r5_4", False), ("r4_7", "r5_5", True),
    ]
    for u, v, is_hi in edges:
        c.bdd_edge(pos[u][0], pos[u][1], pos[v][0], pos[v][1], is_hi=is_hi, r1=r, r2=r)
    for i in range(6):
        ux, uy, _, _ = pos[f"r5_{i}"]
        lx_s, ly_s, _ = sinks[2 * i]
        rx_s, ry_s, _ = sinks[2 * i + 1]
        c.bdd_edge(ux, uy, lx_s, ly_s, is_hi=False, r1=r, r2=rs)
        c.bdd_edge(ux, uy, rx_s, ry_s, is_hi=True, r1=r, r2=rs)

    for px, py, lbl, shaded in pos.values():
        if shaded:
            fl = "#2A243B" if theme.is_dark else "#CBD5E1"
            sk = theme.violet if theme.is_dark else theme.fg
        else:
            fl = theme.node_fill
            sk = theme.cyan if theme.is_dark else theme.fg
        c.circle(px, py, r, fill=fl, stroke=sk, stroke_width=1.4)
        c.text(px, py, lbl, font_size=9.2, fill=theme.fg)

    for sx, sy, is_t in sinks:
        c.bdd_sink(sx, sy, "⊤" if is_t else "⊥", size=12.6, is_true=is_t)
    c.text(292.0, y0 + 3 * dy, ",", font_size=11.0, fill=theme.fg)
    return c.to_svg()


def fig_p657_inline(theme: Theme) -> str:
    w, h = 436.0, 154.0
    c = SvgCanvas(w, h, theme)
    cx = w * 0.5
    ys = [18.0, 48.0, 78.0, 108.0, 138.0]

    nodes: dict[tuple[int, ...], tuple[float, float, str, float]] = {
        (): (cx, ys[0], "∅", 20.0),
        (1,): (cx - 120.0, ys[1], "{1}", 26.0),
        (2,): (cx - 40.0, ys[1], "{2}", 26.0),
        (3,): (cx + 40.0, ys[1], "{3}", 26.0),
        (4,): (cx + 120.0, ys[1], "{4}", 26.0),
        (1, 2): (cx - 180.0, ys[2], "{1, 2}", 36.0),
        (1, 3): (cx - 108.0, ys[2], "{1, 3}", 36.0),
        (1, 4): (cx - 36.0, ys[2], "{1, 4}", 36.0),
        (2, 3): (cx + 36.0, ys[2], "{2, 3}", 36.0),
        (2, 4): (cx + 108.0, ys[2], "{2, 4}", 36.0),
        (3, 4): (cx + 180.0, ys[2], "{3, 4}", 36.0),
        (1, 2, 3): (cx - 126.0, ys[3], "{1, 2, 3}", 46.0),
        (1, 2, 4): (cx - 42.0, ys[3], "{1, 2, 4}", 46.0),
        (1, 3, 4): (cx + 42.0, ys[3], "{1, 3, 4}", 46.0),
        (2, 3, 4): (cx + 126.0, ys[3], "{2, 3, 4}", 46.0),
        (1, 2, 3, 4): (cx, ys[4], "{1, 2, 3, 4}", 56.0),
    }

    mults: list[tuple[tuple[int, ...], tuple[int, ...], int]] = [
        ((), (1,), 1), ((), (2,), 1), ((), (3,), 1), ((), (4,), 1),
        ((1,), (1, 2), 2), ((1,), (1, 3), 2), ((1,), (1, 4), 2),
        ((2,), (1, 2), 2), ((2,), (2, 3), 2), ((2,), (2, 4), 2),
        ((3,), (1, 3), 2), ((3,), (2, 3), 2), ((3,), (3, 4), 2),
        ((4,), (1, 4), 2), ((4,), (2, 4), 2), ((4,), (3, 4), 2),
        ((1, 2), (1, 2, 3), 3), ((1, 2), (1, 2, 4), 3),
        ((1, 3), (1, 2, 3), 3), ((1, 3), (1, 3, 4), 4),
        ((1, 4), (1, 2, 4), 3), ((1, 4), (1, 3, 4), 4),
        ((2, 3), (1, 2, 3), 4), ((2, 3), (2, 3, 4), 4),
        ((2, 4), (1, 2, 4), 4), ((2, 4), (2, 3, 4), 4),
        ((3, 4), (1, 3, 4), 2), ((3, 4), (2, 3, 4), 2),
        ((1, 2, 3), (1, 2, 3, 4), 2),
        ((1, 2, 4), (1, 2, 3, 4), 2),
        ((1, 3, 4), (1, 2, 3, 4), 1),
        ((2, 3, 4), (1, 2, 3, 4), 2),
    ]

    m_col = {
        1: theme.muted if theme.is_dark else theme.fg,
        2: theme.cyan if theme.is_dark else theme.fg,
        3: theme.mint if theme.is_dark else theme.fg,
        4: theme.gold if theme.is_dark else theme.fg,
    }

    for u, v, k in mults:
        x1, y1, _, _ = nodes[u]
        x2, y2, _, _ = nodes[v]
        dx = x2 - x1
        dy = y2 - y1
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln
        col = m_col[k]
        for i in range(k):
            off = (i - 0.5 * (k - 1)) * 2.1
            c.line(x1 + nx * off, y1 + ny * off, x2 + nx * off, y2 + ny * off, stroke=col, stroke_width=0.95)

    lvl_stroke = [theme.gold, theme.cyan, theme.mint, theme.violet, theme.coral]
    for s_key, (px, py, lbl, pw) in nodes.items():
        st = lvl_stroke[len(s_key)] if theme.is_dark else theme.fg
        _pill_node(c, px, py, pw, 14.2, lbl, stroke=st, font_size=8.0, rich=False)
    return c.to_svg()


def fig_p669_pistol(theme: Theme) -> str:
    w, h = 116.0, 64.0
    c = SvgCanvas(w, h, theme)
    cell = 11.0
    x0, y0 = 14.0, 10.0
    poly = [
        (x0, y0),
        (x0 + 8 * cell, y0),
        (x0 + 8 * cell, y0 + cell),
        (x0 + 6 * cell, y0 + cell),
        (x0 + 6 * cell, y0 + 2 * cell),
        (x0 + 4 * cell, y0 + 2 * cell),
        (x0 + 4 * cell, y0 + 3 * cell),
        (x0 + 2 * cell, y0 + 3 * cell),
        (x0 + 2 * cell, y0 + 4 * cell),
        (x0, y0 + 4 * cell),
    ]
    fl = "#131F36" if theme.is_dark else "#FFFFFF"
    st = theme.cyan if theme.is_dark else theme.fg
    c.polyline(poly, stroke=st, stroke_width=1.5, fill=fl, closed=True)
    dots = [(0, 3), (1, 0), (2, 2), (3, 1), (4, 1), (5, 0), (6, 0), (7, 0)]
    dcol = theme.gold if theme.is_dark else "#0F172A"
    for col, row in dots:
        c.circle(x0 + (col + 0.5) * cell, y0 + (row + 0.5) * cell, 3.5, fill=dcol, stroke="none")
    return c.to_svg()


def fig_p669_inline(theme: Theme) -> str:
    w, h = 178.0, 74.0
    c = SvgCanvas(w, h, theme)
    ym = 37.0
    r = 9.2
    rs = 8.5
    xs = [22.0, 56.0, 90.0, 124.0, 156.0]

    c.bdd_edge(xs[0], ym, xs[1], ym, is_hi=True, r1=r, r2=r)
    c.bdd_edge(xs[0], ym, xs[3], ym, is_hi=False, r1=r, r2=rs, curve=24.0)
    c.bdd_edge(xs[1], ym, xs[2], ym, is_hi=False, r1=r, r2=r)
    c.bdd_edge(xs[1], ym, xs[3], ym, is_hi=True, r1=r, r2=rs, curve=-21.0)
    c.bdd_edge(xs[2], ym, xs[3], ym, is_hi=True, r1=r, r2=rs)
    c.bdd_edge(xs[2], ym, xs[4], ym, is_hi=False, r1=r, r2=rs, curve=21.0)

    c.bdd_node(xs[0], ym, "1", r=r, font_size=10.5)
    c.bdd_node(xs[1], ym, "2", r=r, font_size=10.5)
    c.bdd_node(xs[2], ym, "3", r=r, font_size=10.5)
    c.bdd_sink(xs[3], ym, "⊤", size=15.5, is_true=True)
    c.bdd_sink(xs[4], ym, "⊥", size=15.5, is_true=False)
    c.text(170.0, ym + 4.0, ".", font_size=11.5, fill=theme.fg)
    return c.to_svg()


def fig_p671_inline(theme: Theme) -> str:
    w, h = 216.0, 144.0
    c = SvgCanvas(w, h, theme)
    r = 7.4
    rs = 7.0

    p: dict[str, tuple[float, float]] = {
        "1": (68.0, 18.0),
        "b1": (30.0, 36.0),
        "2": (106.0, 36.0),
        "b2": (68.0, 56.0),
        "3": (144.0, 56.0),
        "4L": (106.0, 77.0),
        "4R": (176.0, 77.0),
        "5_1": (86.0, 99.0),
        "5_2": (124.0, 99.0),
        "5_3": (160.0, 99.0),
        "t5": (196.0, 99.0),
        "b6": (76.0, 121.0),
        "6_1": (96.0, 121.0),
        "6_2": (115.0, 121.0),
        "6_3": (134.0, 121.0),
        "6_4": (153.0, 121.0),
        "6_5": (172.0, 121.0),
    }

    edges = [
        ("1", "b1", False), ("1", "2", True),
        ("2", "b2", False), ("2", "3", True),
        ("3", "4L", False), ("3", "4R", True),
        ("4L", "5_1", False), ("4L", "5_2", True),
        ("4R", "5_3", False), ("4R", "t5", True),
        ("5_1", "b6", False), ("5_1", "6_1", True),
        ("5_2", "6_2", False), ("5_2", "6_3", True),
        ("5_3", "6_4", False), ("5_3", "6_5", True),
    ]
    for u, v, is_hi in edges:
        c.bdd_edge(p[u][0], p[u][1], p[v][0], p[v][1], is_hi=is_hi, r1=r, r2=rs if v[0] in ("b", "t") else r)

    for i in range(1, 6):
        gx, gy = p[f"6_{i}"]
        c.bdd_edge(gx, gy, gx - 5.2, gy + 15.0, is_hi=False, r1=r, r2=0.0)
        c.bdd_edge(gx, gy, gx + 5.2, gy + 15.0, is_hi=True, r1=r, r2=0.0)

    for k, (px, py) in p.items():
        if k.startswith("b"):
            c.bdd_sink(px, py, "⊥", size=12.6, is_true=False)
        elif k.startswith("t"):
            c.bdd_sink(px, py, "⊤", size=12.6, is_true=True)
        else:
            c.bdd_node(px, py, k[0], r=r, font_size=9.0)
    return c.to_svg()


def _mini_parallel_legs(c: SvgCanvas, x: float, y1: float, y2: float, r1: float, r2: float) -> None:
    off = 1.45
    c.line(x - off, y1 + r1, x - off, y2 - r2, stroke=c.theme.lo_stroke, stroke_width=1.05, dashed="2.2,1.7")
    c.line(x + off, y1 + r1, x + off, y2 - r2, stroke=c.theme.hi_stroke, stroke_width=1.05)


def fig_p672_inline(theme: Theme) -> str:
    w, h = 456.0, 66.0
    c = SvgCanvas(w, h, theme)
    y1, y2, ys, ytxt = 13.0, 27.0, 42.0, 55.5
    r = 4.5
    rs = 4.0
    dx = 6.2
    sizes = [1, 4, 3, 4, 3, 4, 4, 5, 1, 4, 2, 3, 2, 5, 3, 3]

    for m in range(16):
        cx = 16.0 + m * 28.2
        c.text(cx, ytxt, str(sizes[m]), font_size=8.2, fill=theme.muted if theme.is_dark else theme.fg)
        xl, xr = cx - dx, cx + dx

        if m == 0:
            _mini_sink(c, cx, ys, False)
        elif m == 1:
            _mini_sink(c, xl, ys, False)
            _mini_sink(c, xr, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, cx, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, xl, ys, False, r1=r, r2=rs, curve=-5.5)
            _mini_bdd_edge(c, cx, y1, cx, y2, True, r1=r, r2=r)
            _mini_bdd_edge(c, cx, y2, xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y2, xr, ys, True, r1=r, r2=rs)
        elif m == 2:
            _mini_sink(c, xl, ys, False)
            _mini_sink(c, xr, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_bdd_edge(c, cx, y1, xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y1, xr, ys, True, r1=r, r2=rs)
        elif m == 3:
            _mini_sink(c, xl, ys, False)
            _mini_sink(c, xr, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, xr, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, xl, ys, False, r1=r, r2=rs, curve=-4.5)
            _mini_bdd_edge(c, cx, y1, xr, y2, True, r1=r, r2=r)
            _mini_parallel_legs(c, xr, y2, ys, r, rs)
        elif m == 4:
            _mini_sink(c, xl, ys, False)
            _mini_sink(c, xr, ys, True)
            _mini_node(c, cx, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y2, xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y2, xr, ys, True, r1=r, r2=rs)
        elif m == 5:
            _mini_sink(c, xl, ys, False)
            _mini_sink(c, xr, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, cx, y2, "2", r=r)
            _mini_parallel_legs(c, cx, y1, y2, r, r)
            _mini_bdd_edge(c, cx, y2, xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y2, xr, ys, True, r1=r, r2=rs)
        elif m == 6:
            _mini_sink(c, xl, ys, False)
            _mini_sink(c, xr, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, cx, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, cx, y2, False, r1=r, r2=r)
            _mini_bdd_edge(c, cx, y1, xr, ys, True, r1=r, r2=rs, curve=5.5)
            _mini_bdd_edge(c, cx, y2, xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y2, xr, ys, True, r1=r, r2=rs)
        elif m == 7:
            _mini_sink(c, xl, ys, False)
            _mini_sink(c, xr, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, xl, y2, "2", r=r)
            _mini_node(c, xr, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, xl, y2, False, r1=r, r2=r)
            _mini_bdd_edge(c, cx, y1, xr, y2, True, r1=r, r2=r)
            _mini_bdd_edge(c, xl, y2, xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, xl, y2, xr, ys, True, r1=r, r2=rs)
            _mini_parallel_legs(c, xr, y2, ys, r, rs)
        elif m == 8:
            _mini_sink(c, cx, ys, True)
        elif m == 9:
            _mini_sink(c, xl, ys, False)
            _mini_sink(c, xr, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, cx, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, xr, ys, False, r1=r, r2=rs, curve=5.5)
            _mini_bdd_edge(c, cx, y1, cx, y2, True, r1=r, r2=r)
            _mini_bdd_edge(c, cx, y2, xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, cx, y2, xr, ys, True, r1=r, r2=rs)
        elif m == 10:
            _mini_sink(c, cx, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_parallel_legs(c, cx, y1, ys, r, rs)
        elif m == 11:
            _mini_sink(c, cx, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, cx, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, cx, ys, False, r1=r, r2=rs, curve=-6.5)
            _mini_bdd_edge(c, cx, y1, cx, y2, True, r1=r, r2=r)
            _mini_parallel_legs(c, cx, y2, ys, r, rs)
        elif m == 12:
            _mini_sink(c, cx, ys, True)
            _mini_node(c, cx, y2, "2", r=r)
            _mini_parallel_legs(c, cx, y2, ys, r, rs)
        elif m == 13:
            _mini_sink(c, xl, ys, False)
            _mini_sink(c, xr, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, xl, y2, "2", r=r)
            _mini_node(c, xr, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, xl, y2, False, r1=r, r2=r)
            _mini_bdd_edge(c, cx, y1, xr, y2, True, r1=r, r2=r)
            _mini_bdd_edge(c, xl, y2, xr, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, xl, y2, xr, ys, True, r1=r, r2=rs, curve=3.8)
            _mini_bdd_edge(c, xr, y2, xl, ys, False, r1=r, r2=rs)
            _mini_bdd_edge(c, xr, y2, xr, ys, True, r1=r, r2=rs)
        elif m == 14:
            _mini_sink(c, cx, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, cx, y2, "2", r=r)
            _mini_bdd_edge(c, cx, y1, cx, y2, False, r1=r, r2=r)
            _mini_bdd_edge(c, cx, y1, cx, ys, True, r1=r, r2=rs, curve=6.5)
            _mini_parallel_legs(c, cx, y2, ys, r, rs)
        else:
            _mini_sink(c, cx, ys, True)
            _mini_node(c, cx, y1, "1", r=r)
            _mini_node(c, cx, y2, "2", r=r)
            _mini_parallel_legs(c, cx, y1, y2, r, r)
            _mini_parallel_legs(c, cx, y2, ys, r, rs)
    return c.to_svg()


def fig_p682_inline_1(theme: Theme) -> str:
    w, h = 446.0, 114.0
    c = SvgCanvas(w, h, theme)
    step = 13.5
    all48 = {s for s in USA_COORDS if s != "DC"}

    path_min = [
        "ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA", "DE", "MD", "VA",
        "NC", "SC", "GA", "FL", "AL", "MS", "LA", "TX", "OK", "AR", "TN", "KY",
        "WV", "OH", "MI", "IN", "IL", "MO", "KS", "NE", "IA", "WI", "MN", "SD",
        "ND", "MT", "ID", "UT", "WY", "CO", "NM", "AZ", "NV", "CA", "OR", "WA",
    ]
    path_max = [
        "ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "DE", "MD", "WV", "PA",
        "OH", "IN", "MI", "WI", "MN", "ND", "MT", "SD", "IA", "IL", "KY", "VA",
        "TN", "NC", "SC", "GA", "FL", "AL", "MS", "AR", "LA", "TX", "NM", "OK",
        "CO", "KS", "MO", "NE", "WY", "UT", "AZ", "CA", "OR", "NV", "ID", "WA",
    ]

    edges_min = {(path_min[i], path_min[i + 1]) for i in range(47)}
    edges_max = {(path_max[i], path_max[i + 1]) for i in range(47)}

    _draw_usa_submap(
        c, 24.0, 12.0, step,
        black_set=all48,
        thick_edges=edges_min,
        thick_color=theme.mint if theme.is_dark else "#0F172A",
        omit_dc=True,
        r_dot=2.3,
    )
    c.text(104.0, 103.0, "11698 miles;", font_size=9.2, fill=theme.fg)

    _draw_usa_submap(
        c, 244.0, 12.0, step,
        black_set=all48,
        thick_edges=edges_max,
        thick_color=theme.coral if theme.is_dark else "#0F172A",
        omit_dc=True,
        r_dot=2.3,
    )
    c.text(324.0, 103.0, "18040 miles.", font_size=9.2, fill=theme.fg)
    return c.to_svg()


def fig_p682_inline_2(theme: Theme) -> str:
    w, h = 236.0, 106.0
    c = SvgCanvas(w, h, theme)
    cell = 11.2
    y0 = 8.0

    cyc0 = [
        (0, 0), (0, 1), (1, 0), (2, 1), (3, 0), (4, 1), (5, 0), (6, 1),
        (7, 0), (6, 0), (7, 1), (6, 2), (7, 3), (7, 2), (6, 3), (5, 2),
        (4, 3), (3, 2), (2, 3), (1, 2), (0, 3), (0, 2), (1, 3), (2, 2),
        (3, 3), (2, 4), (3, 5), (2, 6), (3, 7), (4, 6), (5, 7), (6, 6),
        (7, 7), (7, 6), (6, 7), (5, 6), (4, 7), (3, 6), (2, 7), (1, 6),
        (0, 7), (1, 7), (0, 6), (1, 5), (0, 4), (0, 5), (1, 4), (2, 5),
        (3, 4), (4, 5), (5, 4), (6, 5), (7, 4), (7, 5), (6, 4), (5, 5),
        (4, 4), (5, 3), (4, 2), (5, 1), (4, 0), (3, 1), (2, 0), (1, 1),
    ]
    cyc1 = [
        (0, 0), (1, 0), (0, 1), (1, 2), (0, 3), (1, 4), (0, 5), (0, 4),
        (1, 5), (0, 6), (1, 7), (0, 7), (1, 6), (2, 7), (3, 6), (2, 5),
        (3, 4), (2, 3), (3, 2), (2, 1), (3, 0), (2, 0), (3, 1), (4, 0),
        (5, 1), (4, 2), (5, 3), (4, 4), (5, 5), (6, 4), (7, 5), (6, 6),
        (7, 7), (6, 7), (7, 6), (6, 5), (7, 4), (6, 3), (7, 2), (7, 3),
        (6, 2), (7, 1), (6, 0), (7, 0), (6, 1), (5, 0), (4, 1), (5, 2),
        (4, 3), (5, 4), (4, 5), (5, 6), (4, 7), (5, 7), (4, 6), (3, 7),
        (2, 6), (3, 5), (2, 4), (3, 3), (2, 2), (1, 3), (0, 2), (1, 1),
    ]

    for idx, (ox, cyc, tcol) in enumerate([(14.0, cyc0, theme.cyan), (126.0, cyc1, theme.gold)]):
        for r_i in range(8):
            for c_i in range(8):
                sq_fl = theme.cell_dark if (r_i + c_i) % 2 == 1 else theme.cell_light
                c.rect(ox + c_i * cell, y0 + r_i * cell, cell, cell, fill=sq_fl, stroke="none")
        c.rect(ox, y0, 8 * cell, 8 * cell, fill="none", stroke=theme.grid, stroke_width=0.9)
        pts = [(ox + (col + 0.5) * cell, y0 + (row + 0.5) * cell) for row, col in cyc]
        stroke = tcol if theme.is_dark else "#0F172A"
        c.polyline(pts, stroke=stroke, stroke_width=1.25, closed=True)
        if idx == 1:
            c.text(ox + 8 * cell + 6.0, y0 + 8 * cell - 2.0, ".", font_size=11.0, fill=theme.fg)
    return c.to_svg()


def fig_p684_inline(theme: Theme) -> str:
    w, h = 472.0, 74.0
    c = SvgCanvas(w, h, theme)
    step = 8.4
    all49 = set(USA_COORDS)
    whites = [
        {"AL", "CA", "CT", "DE", "KS", "KY", "LA", "MI", "MN", "MO", "MT", "NE", "NJ", "NM", "NV", "SC", "TN", "TX", "VA", "VT", "WA", "WI", "WV", "WY"},
        {"AR", "GA", "IA", "KY", "MA", "MS", "ND", "NE", "NV", "OH", "OK", "OR", "PA", "VA", "WY"},
        {"CA", "KS", "MD", "MO", "NM", "WY"},
        {"CA", "OH"},
    ]
    for idx, wset in enumerate(whites):
        _draw_usa_submap(c, 18.0 + idx * 115.0, 11.0, step, black_set=all49 - wset, r_dot=2.25)
    return c.to_svg()


def fig_p685_inline_1(theme: Theme) -> str:
    w, h = 188.0, 96.0
    c = SvgCanvas(w, h, theme)
    blk = {
        "AL", "AR", "AZ", "CT", "FL", "GA", "ID", "LA", "MA", "ME",
        "MI", "MN", "MS", "MT", "NC", "ND", "NH", "NM", "NY", "OR",
        "RI", "SC", "SD", "TN", "TX", "VT", "WA", "WI", "WY",
    }
    _draw_usa_submap(c, 26.0, 12.0, 12.2, black_set=blk, r_dot=2.85)
    return c.to_svg()


def fig_p685_inline_2(theme: Theme) -> str:
    w, h = 188.0, 96.0
    c = SvgCanvas(w, h, theme)
    centers = {"GA", "IN", "MA", "MD", "NV", "OK", "SD"}
    undom = {"LA", "ME", "MS", "NJ", "WA", "WI"}
    blk = set(USA_COORDS) - undom - centers
    star_edges = {(u, v) for u, v in USA_EDGES if (u in centers) ^ (v in centers)}
    _draw_usa_submap(
        c, 26.0, 12.0, 12.2,
        black_set=blk,
        gray_set=centers if theme.is_dark else set(),
        thick_edges=star_edges,
        thick_color=theme.gold if theme.is_dark else "#0F172A",
        r_dot=2.85,
    )
    if not theme.is_dark:
        for st in centers:
            col, row = USA_COORDS[st]
            c.circle(26.0 + col * 12.2, 12.0 + row * 12.2, 2.85, fill="#0F172A", stroke="#0F172A", stroke_width=1.0)
    return c.to_svg()


_P586_INPUTS: tuple[str, ...] = ("1010", "1011", "1100", "1101", "1110", "1111")

_P586_SEGS_1: tuple[tuple[tuple[float, float, float, float], ...], ...] = (
    ((0.0, 6.74, 2.18, 6.01), (0.31, 11.4, 5.1, 1.69), (0.6, 0.73, 2.13, 6.01), (1.51, 0.4, 5.16, 1.69), (5.31, 0.45, 2.18, 6.29)),
    ((0.0, 0.73, 2.13, 6.01), (0.91, 0.4, 5.16, 1.69), (4.16, 6.74, 2.13, 6.29), (4.71, 0.45, 2.18, 6.29)),
    ((0.0, 11.4, 5.1, 1.69), (0.29, 0.73, 2.13, 6.01), (1.2, 0.4, 5.16, 1.69), (4.45, 6.74, 2.13, 6.29)),
    ((0.0, 6.74, 2.13, 6.29), (0.55, 0.45, 2.17, 6.29)),
    ((0.0, 6.74, 2.17, 6.01), (0.3, 11.4, 5.1, 1.69), (1.51, 0.4, 5.16, 1.69), (4.75, 6.74, 2.13, 6.29)),
    ((0.0, 11.4, 5.1, 1.69), (0.68, 5.89, 5.5, 1.69), (1.2, 0.4, 5.16, 1.69), (4.45, 6.74, 2.13, 6.29)),
)

_P586_SEGS_2: tuple[tuple[tuple[float, float, float, float], ...], ...] = (
    ((0.0, 6.62, 2.18, 6.01), (0.31, 11.28, 5.1, 1.69), (1.51, 0.28, 5.16, 1.69), (5.31, 0.33, 2.18, 6.29)),
    ((0.0, 11.28, 5.1, 1.69), (1.2, 0.28, 5.16, 1.69), (5.0, 0.33, 2.18, 6.29)),
    ((0.0, 0.61, 2.13, 6.01), (4.16, 6.62, 2.13, 6.29), (4.71, 0.33, 2.18, 6.29)),
    ((0.0, 0.61, 2.13, 6.01), (4.16, 6.62, 2.13, 6.29), (4.71, 0.33, 2.17, 6.29)),
    ((0.0, 6.62, 2.17, 6.01), (0.3, 11.28, 5.1, 1.69), (0.59, 0.61, 2.13, 6.01), (1.51, 0.28, 5.16, 1.69), (4.75, 6.62, 2.13, 6.29)),
    ((0.0, 11.28, 5.1, 1.69), (0.29, 0.61, 2.13, 6.01), (1.2, 0.28, 5.16, 1.69), (4.45, 6.62, 2.13, 6.29)),
)


def _draw_p586_row(theme: Theme, groups: tuple[tuple[tuple[float, float, float, float], ...], ...]) -> str:
    step_x = 76.0
    w = 6.0 * step_x + 12.0
    h = 34.0
    c = SvgCanvas(w, h, theme)
    inp_col = theme.cyan if theme.is_dark else theme.fg
    seg_col = theme.gold if theme.is_dark else theme.fg
    punct_col = theme.muted if theme.is_dark else theme.fg
    scale = 1.45
    seg_y = 7.0
    for i, (inp, grp) in enumerate(zip(_P586_INPUTS, groups, strict=True)):
        x_base = 8.0 + i * step_x
        c.text(x_base, 18.0, f"{inp} ↦", font_size=11.0, fill=inp_col, mono=True, anchor="start")
        seg_x = x_base + 45.0
        for rx, ry, rw, rh in grp:
            c.rect(
                seg_x + rx * scale,
                seg_y + ry * scale,
                max(1.6, rw * scale),
                max(1.6, rh * scale),
                fill=seg_col,
                rx=0.7,
            )
        punct = "." if i == 5 else ","
        c.text(seg_x + 15.0, 18.0, punct, font_size=12.0, fill=punct_col, anchor="start")
    return c.to_svg()


def fig_p586_inline_1(theme: Theme) -> str:
    return _draw_p586_row(theme, _P586_SEGS_1)


def fig_p586_inline_2(theme: Theme) -> str:
    return _draw_p586_row(theme, _P586_SEGS_2)


BUILDERS_P7: dict[str, Callable[[Theme], str]] = {
    "fig_p564_inline_1": fig_p564_inline_1,
    "fig_p564_inline_2": fig_p564_inline_2,
    "fig_p565_inline_1": fig_p565_inline_1,
    "fig_p565_inline_2": fig_p565_inline_2,
    "fig_p578_inline_1": fig_p578_inline_1,
    "fig_p578_inline_2": fig_p578_inline_2,
    "fig_p580_inline_1": fig_p580_inline_1,
    "fig_p580_inline_2": fig_p580_inline_2,
    "fig_p586_inline_1": fig_p586_inline_1,
    "fig_p586_inline_2": fig_p586_inline_2,
    "fig_p635_inline_1": fig_p635_inline_1,
    "fig_p635_inline_2": fig_p635_inline_2,
    "fig_p636_inline_1": fig_p636_inline_1,
    "fig_p636_inline_2": fig_p636_inline_2,
    "fig_p636_inline_3": fig_p636_inline_3,
    "fig_p637_inline": fig_p637_inline,
    "fig_p640_inline_1": fig_p640_inline_1,
    "fig_p640_inline_2": fig_p640_inline_2,
    "fig_p641_inline": fig_p641_inline,
    "fig_p650_inline_1": fig_p650_inline_1,
    "fig_p650_inline_2": fig_p650_inline_2,
    "fig_p653_inline": fig_p653_inline,
    "fig_p657_inline": fig_p657_inline,
    "fig_p669_pistol": fig_p669_pistol,
    "fig_p669_inline": fig_p669_inline,
    "fig_p671_inline": fig_p671_inline,
    "fig_p672_inline": fig_p672_inline,
    "fig_p682_inline_1": fig_p682_inline_1,
    "fig_p682_inline_2": fig_p682_inline_2,
    "fig_p684_inline": fig_p684_inline,
    "fig_p685_inline_1": fig_p685_inline_1,
    "fig_p685_inline_2": fig_p685_inline_2,
}

BUILDERS: dict[str, Callable[[Theme], str]] = BUILDERS_P7


def render_part(out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for fig_id, fn in BUILDERS_P7.items():
        m, c, p = emit_dual_figure(fig_id, fn, out_dir)
        paths.extend((m, c, p))
    return paths


__all__ = ["BUILDERS", "BUILDERS_P7", "fmt", "render_part", "rich_label"]
