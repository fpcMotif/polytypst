from __future__ import annotations

import math
from collections.abc import Callable
from itertools import combinations, product
from pathlib import Path

from .figures_common import SvgCanvas, Theme, emit_dual_figure, fmt

USA_PTS: list[tuple[float, float]] = [
    (47.8, 0.0), (119.5, 0.0), (131.45, 0.0), (143.4, 0.0),
    (11.95, 11.95), (35.85, 11.95), (47.8, 11.95), (59.75, 11.95), (71.7, 11.95), (83.65, 11.95), (119.5, 11.95), (131.45, 11.95),
    (11.95, 23.9), (23.9, 23.9), (35.85, 23.9), (47.8, 23.9), (59.75, 23.9), (71.7, 23.9), (83.65, 23.9), (95.6, 23.9), (107.55, 23.9), (119.5, 23.9), (131.45, 23.9), (143.4, 23.9),
    (0.0, 35.85), (11.95, 35.85), (23.9, 35.85), (35.85, 35.85), (47.8, 35.85), (59.75, 35.85), (83.65, 35.85), (95.6, 35.85), (107.55, 35.85), (119.5, 35.85),
    (23.9, 47.8), (35.85, 47.8), (47.8, 47.8), (59.75, 47.8), (83.65, 47.8), (95.6, 47.8), (107.55, 47.8),
    (47.8, 59.75), (59.75, 59.75), (71.7, 59.75), (83.65, 59.75), (95.6, 59.75), (107.55, 59.75),
    (95.6, 71.7), (107.55, 71.7),
]

USA_EDGES: list[tuple[int, int]] = [
    (0, 5), (0, 6), (0, 7), (1, 2), (1, 10), (1, 11), (2, 3), (2, 11), (4, 12), (4, 13),
    (5, 6), (5, 13), (5, 14), (6, 7), (6, 14), (6, 15), (6, 16), (7, 8), (7, 16), (8, 9),
    (8, 16), (8, 17), (9, 18), (9, 19), (10, 11), (10, 20), (10, 21), (10, 22), (11, 22), (11, 23),
    (12, 13), (12, 24), (12, 25), (13, 14), (13, 25), (13, 26), (14, 15), (14, 26), (14, 27), (15, 16),
    (15, 27), (15, 28), (15, 29), (16, 17), (16, 29), (17, 18), (17, 29), (17, 30), (18, 19), (18, 30),
    (19, 20), (19, 30), (19, 31), (20, 21), (20, 31), (20, 32), (20, 33), (21, 33), (22, 23), (24, 25),
    (24, 34), (25, 26), (25, 34), (26, 27), (26, 34), (27, 28), (27, 35), (27, 36), (28, 29), (28, 36),
    (29, 30), (29, 36), (29, 37), (29, 38), (30, 31), (30, 38), (30, 39), (31, 32), (31, 39), (32, 33),
    (32, 39), (32, 40), (34, 35), (35, 36), (35, 41), (36, 37), (36, 41), (37, 38), (37, 41), (37, 42),
    (37, 43), (38, 39), (38, 43), (38, 44), (38, 45), (38, 46), (39, 40), (39, 46), (41, 42), (42, 43),
    (43, 44), (44, 45), (44, 47), (45, 46), (45, 47), (45, 48), (46, 48),
]

USA_K1 = {3, 4, 6, 8, 11, 18, 20, 24, 26, 36, 38, 40, 42, 47, 48}
USA_K2 = {3, 4, 6, 9, 11, 17, 20, 25, 28, 35, 38, 40, 42, 47, 48}


def _level_color(theme: Theme, level: int) -> str:
    if not theme.is_dark:
        return theme.fg
    palette = [theme.cyan, theme.mint, theme.gold, theme.violet, theme.coral]
    return palette[(level - 1) % len(palette)]


def _draw_extracted_bdd(
    c: SvgCanvas,
    ox: float,
    oy: float,
    scale: float,
    nodes: list[tuple[float, float, int | str]],
    sinks: list[tuple[float, float, int | str]],
    edges: list[tuple[int, tuple[str, int, float], tuple[str, int, float]]],
    node_r: float = 8.2,
    sink_sz: float = 11.8,
    font_size: float = 8.8,
) -> None:
    theme = c.theme
    n_pos = [(ox + x * scale, oy + y * scale, lbl) for x, y, lbl in nodes]
    s_pos = [(ox + x * scale, oy + y * scale, val) for x, y, val in sinks]
    sr = sink_sz * 0.56
    for idx, (lo_spec, hi_spec) in enumerate((e[1], e[2]) for e in edges):
        x1, y1, _ = n_pos[idx]
        for is_hi, (kind, tidx, curve) in ((False, lo_spec), (True, hi_spec)):
            if kind == "C":
                x2, y2, _ = n_pos[tidx]
                r2 = node_r
            else:
                x2, y2, _ = s_pos[tidx]
                r2 = sr
            c.bdd_edge(x1, y1, x2, y2, is_hi=is_hi, r1=node_r, r2=r2, curve=curve * scale)
    for x, y, lbl in n_pos:
        lv = int(lbl) if isinstance(lbl, int) or (isinstance(lbl, str) and lbl.isdigit()) else 1
        c.bdd_node(x, y, str(lbl), r=node_r, accent=_level_color(theme, lv), font_size=font_size)
    for x, y, val in s_pos:
        s_lbl = "⊤" if val in (1, "1", "⊤") else ("⊥" if val in (0, "0", "⊥") else str(val))
        is_t = val in (1, "1", "⊤")
        c.bdd_sink(x, y, s_lbl, size=sink_sz, is_true=is_t)


def build_fig_23(theme: Theme) -> str:
    w, h = 500.0, 146.0
    c = SvgCanvas(w, h, theme)
    mod_x = [26.0, 108.0, 190.0, 272.0, 384.0]
    mod_lbl = ["M_1", "M_2", "M_3", "M_4", "M_n"]
    in_lbl = ["x_1", "x_2", "x_3", "x_4", "x_n"]
    mw, mh = 36.0, 44.0
    my = 72.0
    top_y = 24.0
    accents = [theme.cyan, theme.mint, theme.gold, theme.violet, theme.coral]

    for idx, mx in enumerate(mod_x):
        cx = mx + mw * 0.5
        col = accents[idx % len(accents)] if theme.is_dark else theme.fg
        c.graph_node(cx, top_y, in_lbl[idx], r=11.0, stroke=col, font_size=10.5, italic=True)
        c.line(cx, top_y + 11.0, cx, my - 1.0, stroke=col, stroke_width=1.35, arrow_end=True)
        fill = theme.panel if theme.is_dark else "#FFFFFF"
        c.rect(mx, my, mw, mh, fill=fill, stroke=col, stroke_width=1.5, rx=3.0)
        c.text(cx, my + mh * 0.5, mod_lbl[idx], font_size=12.0, fill=theme.fg, italic=True, rich=True)

    def draw_bundle(x1: float, x2: float, n_fwd: int, n_bwd: int) -> None:
        f_col = theme.cyan if theme.is_dark else theme.fg
        b_col = theme.gold if theme.is_dark else theme.secondary
        for k in range(n_fwd):
            yy = my + 6.0 + k * 4.5
            c.line(x1, yy, x2, yy, stroke=f_col, stroke_width=1.2, arrow_end=True)
        for k in range(n_bwd):
            yy = my + mh - 6.0 - k * 4.8
            c.line(x2, yy, x1, yy, stroke=b_col, stroke_width=1.2, arrow_end=True)

    draw_bundle(mod_x[0] + mw, mod_x[1], 2, 1)
    draw_bundle(mod_x[1] + mw, mod_x[2], 3, 2)
    draw_bundle(mod_x[2] + mw, mod_x[3], 4, 2)

    f_col = theme.cyan if theme.is_dark else theme.fg
    b_col = theme.gold if theme.is_dark else theme.secondary
    m4_r = mod_x[3] + mw
    for k in range(5):
        yy = my + 5.0 + k * 4.2
        c.line(m4_r, yy, m4_r + 22.0, yy, stroke=f_col, stroke_width=1.15, arrow_end=True)
    for k in range(2):
        yy = my + mh - 6.0 - k * 5.0
        c.line(m4_r + 22.0, yy, m4_r, yy, stroke=b_col, stroke_width=1.15, arrow_end=True)
    c.text(m4_r + 27.0, my + 13.5, "} a_4", font_size=9.5, fill=f_col, anchor="start", italic=True, rich=True)
    c.text(m4_r + 27.0, my + mh - 8.5, "} b_4", font_size=9.5, fill=b_col, anchor="start", italic=True, rich=True)

    mn_l = mod_x[4]
    for k in range(4):
        yy = my + 7.0 + k * 4.4
        c.line(mn_l - 22.0, yy, mn_l, yy, stroke=f_col, stroke_width=1.15, arrow_end=True)
    for k in range(3):
        yy = my + mh - 5.5 - k * 4.6
        c.line(mn_l, yy, mn_l - 22.0, yy, stroke=b_col, stroke_width=1.15, arrow_end=True)
    c.text(mn_l - 25.0, my + 13.5, "a_{n-1} {", font_size=9.5, fill=f_col, anchor="end", italic=True, rich=True)
    c.text(mn_l - 25.0, my + mh - 10.0, "b_{n-1} {", font_size=9.5, fill=b_col, anchor="end", italic=True, rich=True)

    dots_x = 346.0
    for ry in (my + 8.0, my + 19.0, my + 30.0, my + 40.0):
        c.text(dots_x, ry, "⋯", font_size=11.0, fill=theme.muted)

    mn_r = mod_x[4] + mw
    out_col = theme.mint if theme.is_dark else theme.fg
    c.line(mn_r, my + mh * 0.5, mn_r + 24.0, my + mh * 0.5, stroke=out_col, stroke_width=1.45, arrow_end=True)
    c.text(mn_r + 28.0, my + mh * 0.5, "Output", font_size=11.5, fill=out_col, anchor="start")
    return c.to_svg()


ADD_NODES: list[tuple[float, float, int | str]] = [
    (39.2, 12.1, 1), (55.2, 12.1, 1),
    (15.3, 24.8, 2), (31.3, 24.8, 2), (47.2, 24.8, 2), (63.1, 24.8, 2),
    (39.2, 37.6, 3), (55.2, 37.6, 3), (71.1, 37.6, 3),
    (15.3, 50.3, 4), (31.3, 50.3, 4), (47.2, 50.3, 4), (63.1, 50.3, 4), (79.1, 50.3, 4), (95.0, 50.3, 4),
    (39.2, 63.1, 5), (55.2, 63.1, 5), (71.1, 63.1, 5),
    (15.3, 75.9, 6), (31.3, 75.9, 6), (47.2, 75.9, 6), (63.1, 75.9, 6), (79.1, 75.9, 6), (95.0, 75.9, 6),
    (39.2, 88.6, 7), (55.2, 88.6, 7), (71.1, 88.6, 7),
    (47.2, 101.4, 8), (63.1, 101.4, 8),
]

ADD_SINKS: list[tuple[float, float, int | str]] = [
    (7.4, 37.6, 0), (23.3, 37.6, 1),
    (7.4, 63.1, 0), (23.3, 63.1, 1), (87.1, 63.1, 0), (103.0, 63.1, 1),
    (7.4, 88.6, 0), (23.3, 88.6, 1), (87.1, 88.6, 0), (103.0, 88.6, 1),
    (23.3, 101.4, 0), (87.1, 101.4, 1),
    (39.2, 114.1, 0), (71.1, 114.1, 1),
]

ADD_EDGES: list[tuple[int, tuple[str, int, float], tuple[str, int, float]]] = [
    (0, ("C", 2, 0.0), ("C", 3, 0.0)), (1, ("C", 4, 0.0), ("C", 5, 0.0)),
    (2, ("B", 0, 0.0), ("C", 6, 0.0)), (3, ("C", 6, 0.0), ("B", 1, 0.0)),
    (4, ("C", 6, 0.0), ("C", 8, 0.0)), (5, ("C", 8, 0.0), ("C", 6, 0.0)),
    (6, ("C", 9, 0.0), ("C", 10, 0.0)), (7, ("C", 11, 0.0), ("C", 12, 0.0)), (8, ("C", 14, 0.0), ("C", 13, 0.0)),
    (9, ("B", 2, 0.0), ("C", 15, 0.0)), (10, ("C", 15, 0.0), ("B", 3, 0.0)),
    (11, ("C", 15, 0.0), ("C", 17, 0.0)), (12, ("C", 17, 0.0), ("C", 15, 0.0)),
    (13, ("C", 17, 0.0), ("B", 4, 0.0)), (14, ("B", 5, 0.0), ("C", 17, 0.0)),
    (15, ("C", 18, 0.0), ("C", 19, 0.0)), (16, ("C", 20, 0.0), ("C", 21, 0.0)), (17, ("C", 23, 0.0), ("C", 22, 0.0)),
    (18, ("B", 6, 0.0), ("C", 24, 0.0)), (19, ("C", 24, 0.0), ("B", 7, 0.0)),
    (20, ("C", 24, 0.0), ("C", 26, 0.0)), (21, ("C", 26, 0.0), ("C", 24, 0.0)),
    (22, ("C", 26, 0.0), ("B", 8, 0.0)), (23, ("B", 9, 0.0), ("C", 26, 0.0)),
    (24, ("B", 10, 0.0), ("C", 27, 0.0)), (25, ("C", 27, 0.0), ("C", 28, 0.0)), (26, ("B", 11, 0.0), ("C", 28, 0.0)),
    (27, ("B", 12, 0.0), ("B", 13, 0.0)), (28, ("B", 13, 0.0), ("B", 12, 0.0)),
]


def build_fig_p230_inline(theme: Theme) -> str:
    sc = 1.85
    ox, oy = 46.0, 10.0
    w, h = 290.0, 238.0
    c = SvgCanvas(w, h, theme)
    _draw_extracted_bdd(c, ox, oy, sc, ADD_NODES, ADD_SINKS, ADD_EDGES, node_r=8.2, sink_sz=11.5, font_size=8.8)

    pcol = theme.gold if theme.is_dark else theme.fg
    fx5, fy5 = ox + ADD_NODES[0][0] * sc, oy + ADD_NODES[0][1] * sc
    c.text(ox - 24.0, fy5 - 11.0, "F_5", font_size=11.0, fill=pcol, italic=True, rich=True)
    c.line(ox - 12.0, fy5 - 10.0, fx5 - 6.8, fy5 - 5.2, stroke=pcol, stroke_width=1.25, arrow_end=True)

    for lbl, nidx in (("F_4", 1), ("F_3", 7), ("F_2", 16), ("F_1", 25)):
        nx, ny = ox + ADD_NODES[nidx][0] * sc, oy + ADD_NODES[nidx][1] * sc
        rx = ox + 118.0 * sc
        ry = ny - 10.5
        c.text(rx + 4.0, ry, lbl, font_size=11.0, fill=pcol, anchor="start", italic=True, rich=True)
        c.line(rx, ry + 1.0, nx + 7.2, ny - 4.8, stroke=pcol, stroke_width=1.25, arrow_end=True)
    return c.to_svg()


def build_fig_24(theme: Theme) -> str:
    w, h = 530.0, 198.0
    c = SvgCanvas(w, h, theme)
    ys = [28.0, 62.0, 96.0, 130.0, 166.0]
    r = 10.2
    ssz = 14.5

    def tagged_node(x: float, y: float, lv: int, tag: str, side: str = "left") -> None:
        c.bdd_node(x, y, str(lv), r=r, accent=_level_color(theme, lv), font_size=9.8)
        dx = -(r + 5.0) if side == "left" else (r + 5.0)
        anc = "end" if side == "left" else "start"
        tcol = theme.muted if theme.is_dark else theme.secondary
        c.text(x + dx, y - 2.0, tag, font_size=9.5, fill=tcol, anchor=anc, italic=True, rich=True)

    ax = {"a": 54.0, "b": 34.0, "g": 68.0, "d": 54.0, "s0": 32.0, "s1": 76.0}
    c.bdd_edge(ax["a"], ys[0], ax["b"], ys[1], is_hi=False, r1=r, r2=r)
    c.bdd_edge(ax["a"], ys[0], ax["g"], ys[2], is_hi=True, r1=r, r2=r)
    c.bdd_edge(ax["b"], ys[1], ax["s0"], ys[4], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(ax["b"], ys[1], ax["g"], ys[2], is_hi=True, r1=r, r2=r)
    c.bdd_edge(ax["g"], ys[2], ax["d"], ys[3], is_hi=False, r1=r, r2=r)
    c.bdd_edge(ax["g"], ys[2], ax["s1"], ys[4], is_hi=True, r1=r, r2=ssz * 0.55)
    c.bdd_edge(ax["d"], ys[3], ax["s0"], ys[4], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(ax["d"], ys[3], ax["s1"], ys[4], is_hi=True, r1=r, r2=ssz * 0.55)
    tagged_node(ax["a"], ys[0], 1, "α", "left")
    tagged_node(ax["b"], ys[1], 2, "β", "left")
    tagged_node(ax["g"], ys[2], 3, "γ", "right")
    tagged_node(ax["d"], ys[3], 4, "δ", "left")
    c.bdd_sink(ax["s0"], ys[4], "⊥", size=ssz, is_true=False)
    c.bdd_sink(ax["s1"], ys[4], "⊤", size=ssz, is_true=True)

    gx = {"w": 168.0, "chi": 144.0, "psi": 192.0, "phi": 168.0, "tau": 144.0, "ups": 192.0, "s0": 144.0, "s1": 192.0}
    c.bdd_edge(gx["w"], ys[0], gx["chi"], ys[1], is_hi=False, r1=r, r2=r)
    c.bdd_edge(gx["w"], ys[0], gx["psi"], ys[1], is_hi=True, r1=r, r2=r)
    c.bdd_edge(gx["chi"], ys[1], gx["phi"], ys[2], is_hi=False, r1=r, r2=r)
    c.bdd_edge(gx["chi"], ys[1], gx["s1"], ys[4], is_hi=True, r1=r, r2=ssz * 0.55, curve=36.0)
    c.bdd_edge(gx["psi"], ys[1], gx["s1"], ys[4], is_hi=False, r1=r, r2=ssz * 0.55, curve=-24.0)
    c.bdd_edge(gx["psi"], ys[1], gx["phi"], ys[2], is_hi=True, r1=r, r2=r)
    c.bdd_edge(gx["phi"], ys[2], gx["tau"], ys[3], is_hi=False, r1=r, r2=r)
    c.bdd_edge(gx["phi"], ys[2], gx["ups"], ys[3], is_hi=True, r1=r, r2=r)
    c.bdd_edge(gx["tau"], ys[3], gx["s0"], ys[4], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(gx["tau"], ys[3], gx["s1"], ys[4], is_hi=True, r1=r, r2=ssz * 0.55)
    c.bdd_edge(gx["ups"], ys[3], gx["s1"], ys[4], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(gx["ups"], ys[3], gx["s0"], ys[4], is_hi=True, r1=r, r2=ssz * 0.55)
    tagged_node(gx["w"], ys[0], 1, "ω", "left")
    tagged_node(gx["chi"], ys[1], 2, "χ", "left")
    tagged_node(gx["psi"], ys[1], 2, "ψ", "right")
    tagged_node(gx["phi"], ys[2], 3, "φ", "left")
    tagged_node(gx["tau"], ys[3], 4, "τ", "left")
    tagged_node(gx["ups"], ys[3], 4, "υ", "right")
    c.bdd_sink(gx["s0"], ys[4], "⊥", size=ssz, is_true=False)
    c.bdd_sink(gx["s1"], ys[4], "⊤", size=ssz, is_true=True)

    mr = 9.4
    mssz = 13.5
    m_pos = {
        "aw": (376.0, ys[0], 1, "α⋄ω"),
        "bchi": (336.0, ys[1], 2, "β⋄χ"),
        "gpsi": (416.0, ys[1], 2, "γ⋄ψ"),
        "0phi": (300.0, ys[2], 3, "⊥⋄φ"),
        "g1": (376.0, ys[2], 3, "γ⋄⊤"),
        "gphi": (448.0, ys[2], 3, "γ⋄φ"),
        "0tau": (272.0, ys[3], 4, "⊥⋄τ"),
        "0ups": (324.0, ys[3], 4, "⊥⋄υ"),
        "d1": (376.0, ys[3], 4, "δ⋄⊤"),
        "dtau": (430.0, ys[3], 4, "δ⋄τ"),
        "1ups": (486.0, ys[3], 4, "⊤⋄υ"),
    }
    m_sinks = {
        "01": (300.0, ys[4], "⊥⋄⊤", False),
        "00": (356.0, ys[4], "⊥⋄⊥", False),
        "11": (416.0, ys[4], "⊤⋄⊤", True),
        "10": (476.0, ys[4], "⊤⋄⊥", True),
    }
    m_edges = [
        ("aw", "bchi", False, 0.0), ("aw", "gpsi", True, 0.0),
        ("bchi", "0phi", False, 0.0), ("bchi", "g1", True, 0.0),
        ("gpsi", "g1", False, 0.0), ("gpsi", "gphi", True, 0.0),
        ("0phi", "0tau", False, 0.0), ("0phi", "0ups", True, 0.0),
        ("g1", "d1", False, 0.0), ("g1", "11", True, 8.0),
        ("gphi", "dtau", False, 0.0), ("gphi", "1ups", True, 0.0),
        ("0tau", "00", False, 0.0), ("0tau", "01", True, 0.0),
        ("0ups", "01", False, 0.0), ("0ups", "00", True, 0.0),
        ("d1", "01", False, 0.0), ("d1", "11", True, 0.0),
        ("dtau", "00", False, 0.0), ("dtau", "11", True, 0.0),
        ("1ups", "11", False, 0.0), ("1ups", "10", True, 0.0),
    ]
    for src, dst, is_hi, cv in m_edges:
        x1, y1, _, _ = m_pos[src]
        if dst in m_pos:
            x2, y2, _, _ = m_pos[dst]
            r2 = mr
        else:
            x2, y2, _, _ = m_sinks[dst]
            r2 = mssz * 0.55
        c.bdd_edge(x1, y1, x2, y2, is_hi=is_hi, r1=mr, r2=r2, curve=cv)
    tcol = theme.muted if theme.is_dark else theme.secondary
    for key, (x, y, lv, tag) in m_pos.items():
        c.bdd_node(x, y, str(lv), r=mr, accent=_level_color(theme, lv), font_size=9.2)
        if key in ("aw", "0phi", "0tau"):
            c.text(x - mr - 3.5, y - 2.0, tag, font_size=8.3, fill=tcol, anchor="end", italic=True)
        elif key in ("gpsi", "gphi", "1ups"):
            c.text(x + mr + 3.5, y - 2.0, tag, font_size=8.3, fill=tcol, anchor="start", italic=True)
        else:
            c.text(x, y - mr - 6.5, tag, font_size=8.0, fill=tcol, italic=True)
    for x, y, slbl, ist in m_sinks.values():
        c.bdd_sink(x, y, "", size=mssz, is_true=ist)
        scol = (theme.gold if ist else theme.coral) if theme.is_dark else theme.fg
        c.text(x, y + mssz * 0.5 + 8.5, slbl, font_size=8.6, fill=scol)
    return c.to_svg()


MU3_NODES: list[tuple[float, float, int | str]] = [
    (71.3, 0.0, 1), (41.6, 20.9, 2), (100.9, 20.9, 2),
    (29.9, 41.8, 3), (53.3, 41.8, 3), (93.4, 41.8, 3),
    (7.5, 62.8, 4), (37.4, 62.8, 4), (52.3, 62.8, 4), (69.2, 62.8, 4), (86.0, 62.8, 4),
    (0.0, 83.7, 5), (15.0, 83.7, 5), (29.9, 83.7, 5), (59.8, 83.7, 5), (78.5, 83.7, 5),
    (15.0, 104.6, 6), (29.9, 104.6, 6), (69.2, 104.6, 6),
    (15.0, 125.5, 7), (52.5, 125.5, 7),
    (35.9, 146.4, 8),
]

MU3_SINKS: list[tuple[float, float, int | str]] = [
    (108.4, 41.8, 0), (100.9, 62.8, 0), (44.9, 83.7, 0), (93.4, 83.7, 0),
    (86.0, 104.6, 0), (76.6, 125.5, 0), (60.0, 146.4, 0), (28.4, 167.4, 1), (43.4, 167.4, 0),
]

MU3_EDGES: list[tuple[int, tuple[str, int, float], tuple[str, int, float]]] = [
    (0, ("C", 1, 0.0), ("C", 2, 0.0)), (1, ("C", 3, 0.0), ("C", 4, 0.0)), (2, ("B", 0, 0.0), ("C", 5, 0.0)),
    (3, ("C", 6, 0.0), ("C", 8, 0.0)), (4, ("C", 7, 0.0), ("C", 9, 0.0)), (5, ("B", 1, 0.0), ("C", 10, 0.0)),
    (6, ("C", 12, 0.0), ("C", 11, 0.0)), (7, ("B", 2, 0.0), ("C", 13, 0.0)), (8, ("B", 2, 0.0), ("C", 14, 0.0)),
    (9, ("B", 2, 0.0), ("C", 18, 0.0)), (10, ("B", 3, 0.0), ("C", 15, 0.0)),
    (11, ("C", 21, 22.0), ("C", 18, 10.0)), (12, ("C", 16, 0.0), ("C", 18, -7.0)),
    (13, ("C", 17, 0.0), ("C", 18, -7.0)), (14, ("C", 20, 8.0), ("C", 18, 0.0)), (15, ("B", 4, 0.0), ("C", 18, 0.0)),
    (16, ("C", 19, 0.0), ("C", 21, 0.0)), (17, ("B", 5, 0.0), ("C", 21, 0.0)), (18, ("B", 5, 0.0), ("C", 20, 0.0)),
    (19, ("B", 7, 0.0), ("C", 21, 0.0)), (20, ("B", 6, 0.0), ("C", 21, 0.0)), (21, ("B", 8, 0.0), ("B", 7, 0.0)),
]


def build_fig_25(theme: Theme) -> str:
    sc = 1.32
    w, h = 548.0, 260.0
    c = SvgCanvas(w, h, theme)

    def draw_mu2(bx: float, vars_4: tuple[int, int, int, int]) -> None:
        v1, v2, v3, v4 = vars_4
        ns: list[tuple[float, float, int | str]] = [
            (22.4, 41.8, v1), (7.5, 62.7, v2), (37.3, 62.7, v2),
            (0.0, 83.6, v3), (29.9, 83.6, v3), (22.4, 104.6, v4),
        ]
        sk: list[tuple[float, float, int | str]] = [
            (44.8, 83.6, 0), (0.0, 104.6, 1), (37.3, 104.6, 0), (14.9, 125.5, 1), (29.9, 125.5, 0),
        ]
        ed: list[tuple[int, tuple[str, int, float], tuple[str, int, float]]] = [
            (0, ("C", 1, 0.0), ("C", 2, 0.0)),
            (1, ("C", 3, 0.0), ("C", 5, 0.0)),
            (2, ("B", 0, 0.0), ("C", 4, 0.0)),
            (3, ("B", 1, 0.0), ("C", 5, 0.0)),
            (4, ("B", 2, 0.0), ("C", 5, 0.0)),
            (5, ("B", 4, 0.0), ("B", 3, 0.0)),
        ]
        _draw_extracted_bdd(c, bx, 18.0, sc, ns, sk, ed, node_r=7.6, sink_sz=10.8, font_size=8.4)

    draw_mu2(20.0, (1, 3, 5, 7))
    c.text(105.0, 132.0, "∧", font_size=15.0, fill=theme.gold if theme.is_dark else theme.fg, bold=True)
    draw_mu2(128.0, (2, 4, 6, 8))
    c.text(215.0, 132.0, "∧", font_size=15.0, fill=theme.gold if theme.is_dark else theme.fg, bold=True)

    g8_ns: list[tuple[float, float, int | str]] = [
        (0.0, 0.0, 1), (7.5, 20.9, 2), (0.0, 41.8, 3), (7.5, 62.7, 4),
        (0.0, 83.6, 5), (7.5, 104.5, 6), (0.0, 125.4, 7), (7.5, 146.3, 8),
    ]
    g8_sk: list[tuple[float, float, int | str]] = [
        (15.0, 41.8, 0), (15.0, 83.6, 0), (15.0, 125.4, 0), (0.0, 167.2, 1), (15.0, 167.2, 0),
    ]
    g8_ed: list[tuple[int, tuple[str, int, float], tuple[str, int, float]]] = [
        (0, ("C", 2, 0.0), ("C", 1, 0.0)), (1, ("B", 0, 0.0), ("C", 2, 0.0)),
        (2, ("C", 4, 0.0), ("C", 3, 0.0)), (3, ("B", 1, 0.0), ("C", 4, 0.0)),
        (4, ("C", 6, 0.0), ("C", 5, 0.0)), (5, ("B", 2, 0.0), ("C", 6, 0.0)),
        (6, ("B", 3, 0.0), ("C", 7, 0.0)), (7, ("B", 4, 0.0), ("B", 3, 0.0)),
    ]
    _draw_extracted_bdd(c, 244.0, 18.0, sc, g8_ns, g8_sk, g8_ed, node_r=7.6, sink_sz=10.8, font_size=8.4)

    c.text(298.0, 132.0, "=", font_size=16.0, fill=theme.gold if theme.is_dark else theme.fg, bold=True)
    _draw_extracted_bdd(c, 330.0, 18.0, sc, MU3_NODES, MU3_SINKS, MU3_EDGES, node_r=7.6, sink_sz=10.8, font_size=8.4)
    return c.to_svg()


MUL_NODES: list[tuple[float, float, int | str]] = [
    (35.3, 16.4, 1), (99.0, 16.4, 1), (143.7, 16.4, 1), (162.8, 16.4, 1),
    (16.2, 29.1, 2), (35.3, 29.1, 2), (86.3, 29.1, 2), (111.8, 29.1, 2), (137.3, 29.1, 2), (150.0, 29.1, 2), (162.8, 29.1, 2),
    (9.8, 41.9, 3), (22.6, 41.9, 3), (35.3, 41.9, 3), (79.9, 41.9, 3), (92.7, 41.9, 3), (105.4, 41.9, 3), (118.2, 41.9, 3), (130.9, 41.9, 3), (143.7, 41.9, 3), (156.4, 41.9, 3), (169.2, 41.9, 3), (181.9, 41.9, 3), (194.6, 41.9, 3),
    (9.8, 54.6, 4), (35.3, 54.6, 4), (48.0, 54.6, 4), (60.8, 54.6, 4), (73.5, 54.6, 4), (86.3, 54.6, 4), (99.0, 54.6, 4), (124.5, 54.6, 4), (137.3, 54.6, 4), (150.0, 54.6, 4), (162.8, 54.6, 4), (175.5, 54.6, 4), (188.3, 54.6, 4), (201.0, 54.6, 4), (213.8, 54.6, 4), (226.5, 54.6, 4),
    (9.8, 67.4, 5), (54.4, 67.4, 5), (124.5, 67.4, 5), (137.3, 67.4, 5), (150.0, 67.4, 5), (169.2, 67.4, 5), (181.9, 67.4, 5), (207.4, 67.4, 5),
    (86.3, 80.1, 6), (169.2, 80.1, 6),
]

MUL_SINKS: list[tuple[float, float, int | str]] = [
    (48.0, 29.1, 0), (48.0, 41.9, 0), (22.6, 54.6, 0), (111.8, 54.6, 0),
    (22.6, 67.4, 1), (220.1, 67.4, 0), (232.9, 67.4, 1),
    (9.8, 80.1, 1), (22.6, 80.1, 0), (113.9, 80.1, 0), (141.5, 80.1, 1), (207.4, 80.1, 0),
    (73.5, 92.9, 0), (99.0, 92.9, 1), (150.0, 92.9, 0), (181.9, 92.9, 1),
]

MUL_EDGES: list[tuple[int, tuple[str, int, float], tuple[str, int, float]]] = [
    (0, ("B", 0, 0.0), ("C", 5, 0.0)), (1, ("C", 7, 0.0), ("C", 6, 0.0)),
    (2, ("C", 8, 0.0), ("C", 9, 0.0)), (3, ("C", 4, -7.7), ("C", 10, 0.0)),
    (4, ("C", 12, 0.0), ("C", 11, 0.0)), (5, ("B", 1, 0.0), ("C", 13, 0.0)),
    (6, ("C", 15, 0.0), ("C", 14, 0.0)), (7, ("B", 3, 0.0), ("C", 19, -4.5)),
    (8, ("C", 16, 0.0), ("C", 21, 0.0)), (9, ("C", 17, 0.0), ("C", 22, 0.0)), (10, ("C", 23, -4.6), ("C", 18, 0.0)),
    (11, ("B", 2, 0.0), ("C", 24, 0.0)), (12, ("B", 2, 0.0), ("C", 26, 0.0)), (13, ("C", 26, 0.0), ("C", 25, 0.0)),
    (14, ("C", 30, 0.0), ("C", 27, 0.0)), (15, ("B", 3, 0.0), ("C", 29, 0.0)),
    (16, ("B", 3, 0.0), ("C", 31, 0.0)), (17, ("C", 48, -25.5), ("C", 32, 0.0)),
    (18, ("C", 28, -6.1), ("C", 35, 5.4)), (19, ("B", 3, 0.0), ("C", 34, 0.0)),
    (20, ("C", 34, 0.0), ("C", 36, 0.0)), (21, ("C", 45, 0.0), ("C", 33, 0.0)),
    (22, ("C", 46, 0.0), ("C", 37, 0.0)), (23, ("C", 39, -6.0), ("C", 38, 0.0)),
    (24, ("B", 4, 0.0), ("C", 40, 0.0)), (25, ("C", 41, 0.0), ("B", 4, 0.0)),
    (26, ("B", 8, 0.0), ("C", 41, 0.0)), (27, ("C", 42, 13.5), ("C", 41, 0.0)),
    (28, ("C", 41, 0.0), ("C", 42, 4.5)), (29, ("B", 9, 0.0), ("C", 48, 0.0)),
    (30, ("B", 13, 0.0), ("C", 42, 0.0)), (31, ("B", 9, 0.0), ("C", 42, 0.0)),
    (32, ("C", 48, 0.0), ("C", 43, 0.0)), (33, ("C", 45, 0.0), ("C", 44, 0.0)),
    (34, ("B", 14, 0.0), ("C", 45, 0.0)), (35, ("C", 42, 7.5), ("C", 46, 0.0)),
    (36, ("C", 48, 18.7), ("C", 46, 0.0)), (37, ("C", 46, 0.0), ("C", 47, 0.0)),
    (38, ("B", 5, 0.0), ("C", 49, -4.5)), (39, ("B", 5, 0.0), ("B", 6, 0.0)),
    (40, ("B", 7, 0.0), ("B", 8, 0.0)), (41, ("B", 8, 0.0), ("C", 48, 0.0)),
    (42, ("B", 10, 0.0), ("C", 49, 5.2)), (43, ("C", 49, 0.0), ("B", 10, 0.0)),
    (44, ("B", 10, 0.0), ("C", 48, 8.1)), (45, ("B", 14, 0.0), ("B", 10, 0.0)),
    (46, ("C", 48, -8.9), ("C", 49, -2.8)), (47, ("C", 49, -8.4), ("B", 11, 0.0)),
    (48, ("B", 12, 0.0), ("B", 13, 0.0)), (49, ("B", 15, 0.0), ("B", 14, 0.0)),
]


def build_fig_p242_inline(theme: Theme) -> str:
    sc = 1.92
    ox, oy = 14.0, 24.0
    w, h = 486.0, 220.0
    c = SvgCanvas(w, h, theme)
    _draw_extracted_bdd(c, ox, oy, sc, MUL_NODES, MUL_SINKS, MUL_EDGES, node_r=7.0, sink_sz=9.8, font_size=7.9)

    pcol = theme.gold if theme.is_dark else theme.fg
    roots = [
        ("F_6", 0, 0.0),
        ("F_1", 41, 0.0),
        ("F_5", 1, 0.0),
        ("F_3", 2, -2.0),
        ("F_2", 20, -4.5),
        ("F_4", 3, 5.5),
    ]
    for lbl, nidx, dx in roots:
        nx, ny = ox + MUL_NODES[nidx][0] * sc, oy + MUL_NODES[nidx][1] * sc
        lx = nx + dx
        c.text(lx, 13.5, lbl, font_size=10.0, fill=pcol, italic=True, rich=True)
        c.line(lx, 21.5, nx, ny - 7.4, stroke=pcol, stroke_width=1.15, arrow_end=True)
    return c.to_svg()


def build_fig_p246_inline(theme: Theme) -> str:
    sc = 1.32
    w, h = 456.0, 128.0
    c = SvgCanvas(w, h, theme)
    ecol = "#334A6B" if theme.is_dark else "#94A3B8"
    for idx, (ox, kset, kcol) in enumerate(((18.0, USA_K1, theme.gold), (242.0, USA_K2, theme.cyan))):
        oy = 16.0
        for u, v in USA_EDGES:
            x1, y1 = ox + USA_PTS[u][0] * sc, oy + USA_PTS[u][1] * sc
            x2, y2 = ox + USA_PTS[v][0] * sc, oy + USA_PTS[v][1] * sc
            c.line(x1, y1, x2, y2, stroke=ecol, stroke_width=1.15)
        for vi, (px, py) in enumerate(USA_PTS):
            vx, vy = ox + px * sc, oy + py * sc
            if vi in kset:
                fill = kcol if theme.is_dark else "#0F172A"
                stroke = "#FFFFFF" if theme.is_dark else "#0F172A"
                c.circle(vx, vy, 3.8, fill=fill, stroke=stroke, stroke_width=1.0, glow=True)
            else:
                fill = theme.node_fill if theme.is_dark else "#FFFFFF"
                stroke = theme.muted if theme.is_dark else "#334155"
                c.circle(vx, vy, 2.9, fill=fill, stroke=stroke, stroke_width=1.1)
        if idx == 0:
            c.text(224.0, 92.0, ",", font_size=15.0, fill=theme.fg)
    return c.to_svg()


def build_fig_p250_inline_1(theme: Theme) -> str:
    w, h = 328.0, 166.0
    c = SvgCanvas(w, h, theme)
    r = 9.5
    ssz = 13.5
    ys = [24.0, 52.0, 82.0, 112.0, 144.0]

    c.text(20.0, 84.0, "f :", font_size=12.5, fill=theme.fg, italic=True)
    fn = {
        "1": (88.0, ys[0], 1),
        "2L": (62.0, ys[1], 2), "2R": (114.0, ys[1], 2),
        "3A": (44.0, ys[2], 3), "3B": (88.0, ys[2], 3), "3C": (132.0, ys[2], 3),
        "4B": (88.0, ys[3], 4), "4A": (124.0, ys[3], 4),
    }
    fs = {"0": (66.0, ys[4], False), "1": (110.0, ys[4], True)}
    fe = [
        ("1", "2L", False, 0.0), ("1", "2R", True, 0.0),
        ("2L", "3A", False, 0.0), ("2L", "3B", True, 0.0),
        ("2R", "3C", False, 0.0), ("2R", "3B", True, 0.0),
        ("3A", "0", False, 0.0), ("3A", "1", True, 12.0),
        ("3B", "0", False, -6.0), ("3B", "4B", True, 0.0),
        ("3C", "4A", False, 0.0), ("3C", "1", True, 16.0),
        ("4B", "1", False, 0.0), ("4B", "0", True, 0.0),
        ("4A", "0", False, 6.0), ("4A", "1", True, 0.0),
    ]
    for u, v, hi, cv in fe:
        x1, y1, _ = fn[u]
        if v in fn:
            x2, y2, _ = fn[v]
            r2 = r
        else:
            x2, y2, _ = fs[v]
            r2 = ssz * 0.55
        c.bdd_edge(x1, y1, x2, y2, is_hi=hi, r1=r, r2=r2, curve=cv)
    for x, y, lv in fn.values():
        c.bdd_node(x, y, str(lv), r=r, accent=_level_color(theme, lv), font_size=9.5)
    c.bdd_sink(fs["0"][0], fs["0"][1], "⊥", size=ssz, is_true=False)
    c.bdd_sink(fs["1"][0], fs["1"][1], "⊤", size=ssz, is_true=True)

    c.text(162.0, 96.0, ",", font_size=14.0, fill=theme.fg)
    c.text(192.0, 84.0, "f^π :", font_size=12.5, fill=theme.fg, italic=True, rich=True)
    pn = {"1": (254.0, ys[0], 1), "2": (276.0, ys[1], 2), "3": (258.0, ys[2], 3), "4": (238.0, ys[3], 4)}
    ps = {"0": (284.0, ys[4], False), "1": (238.0, ys[4], True)}
    pe = [
        ("1", "4", False, -8.0), ("1", "2", True, 0.0),
        ("2", "3", False, 0.0), ("2", "0", True, 8.0),
        ("3", "4", False, 0.0), ("3", "1", True, -4.0),
        ("4", "0", False, 0.0), ("4", "1", True, 0.0),
    ]
    for u, v, hi, cv in pe:
        x1, y1, _ = pn[u]
        if v in pn:
            x2, y2, _ = pn[v]
            r2 = r
        else:
            x2, y2, _ = ps[v]
            r2 = ssz * 0.55
        c.bdd_edge(x1, y1, x2, y2, is_hi=hi, r1=r, r2=r2, curve=cv)
    for x, y, lv in pn.values():
        c.bdd_node(x, y, str(lv), r=r, accent=_level_color(theme, lv), font_size=9.5)
    c.bdd_sink(ps["0"][0], ps["0"][1], "⊥", size=ssz, is_true=False)
    c.bdd_sink(ps["1"][0], ps["1"][1], "⊤", size=ssz, is_true=True)
    return c.to_svg()


def build_fig_p250_inline_2(theme: Theme) -> str:
    w, h = 160.0, 166.0
    c = SvgCanvas(w, h, theme)
    r = 9.5
    ssz = 13.5
    ys = [24.0, 52.0, 82.0, 112.0, 144.0]
    c.text(32.0, 84.0, "f :", font_size=12.5, fill=theme.fg, italic=True)
    pn = {"4": (92.0, ys[0], 4), "2": (114.0, ys[1], 2), "1": (96.0, ys[2], 1), "3": (76.0, ys[3], 3)}
    ps = {"0": (122.0, ys[4], False), "1": (76.0, ys[4], True)}
    pe = [
        ("4", "3", False, -8.0), ("4", "2", True, 0.0),
        ("2", "1", False, 0.0), ("2", "0", True, 8.0),
        ("1", "3", False, 0.0), ("1", "1", True, -4.0),
        ("3", "0", False, 0.0), ("3", "1", True, 0.0),
    ]
    for u, v, hi, cv in pe:
        x1, y1, _ = pn[u]
        if v in pn:
            x2, y2, _ = pn[v]
            r2 = r
        else:
            x2, y2, _ = ps[v]
            r2 = ssz * 0.55
        c.bdd_edge(x1, y1, x2, y2, is_hi=hi, r1=r, r2=r2, curve=cv)
    for x, y, lv in pn.values():
        c.bdd_node(x, y, str(lv), r=r, accent=_level_color(theme, lv), font_size=9.5)
    c.bdd_sink(ps["0"][0], ps["0"][1], "⊥", size=ssz, is_true=False)
    c.bdd_sink(ps["1"][0], ps["1"][1], "⊤", size=ssz, is_true=True)
    return c.to_svg()


def build_fig_p253_inline(theme: Theme) -> str:
    w, h = 420.0, 212.0
    c = SvgCanvas(w, h, theme)

    def f_func(x1: int, x2: int, x3: int, x4: int) -> int:
        return (x3 | (x1 & x4)) & ((1 - x2) | (1 - x4))

    rows: list[list[tuple[int, ...]]] = [
        [()],
        [(1,), (2,), (3,), (4,)],
        [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)],
        [(1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4)],
        [(1, 2, 3, 4)],
    ]
    ys = [24.0, 65.0, 106.0, 147.0, 188.0]
    pos: dict[tuple[int, ...], tuple[float, float]] = {}
    for r_i, r_sets in enumerate(rows):
        cnt = len(r_sets)
        span = 320.0 if cnt == 6 else (228.0 if cnt == 4 else 0.0)
        for idx, s in enumerate(r_sets):
            xx = 210.0 if cnt == 1 else (210.0 - span * 0.5 + idx * (span / (cnt - 1)))
            pos[s] = (xx, ys[r_i])

    vars_all = (1, 2, 3, 4)
    for k in range(4):
        for X in combinations(vars_all, k):
            Xset = set(X)
            rem = [v for v in vars_all if v not in Xset]
            for x in rem:
                other = [v for v in rem if v != x]
                dep = set()
                for vx in product((0, 1), repeat=len(X)):
                    base = dict(zip(X, vx))
                    tt0 = []
                    tt1 = []
                    for vo in product((0, 1), repeat=len(other)):
                        a0 = dict(base)
                        a0.update(zip(other, vo))
                        a1 = dict(a0)
                        a0[x] = 0
                        a1[x] = 1
                        tt0.append(f_func(a0[1], a0[2], a0[3], a0[4]))
                        tt1.append(f_func(a1[1], a1[2], a1[3], a1[4]))
                    if tt0 != tt1:
                        dep.add((tuple(tt0), tuple(tt1)))
                mult = len(dep)
                Y = tuple(sorted(Xset | {x}))
                x1, y1 = pos[X]
                x2, y2 = pos[Y]
                dx, dy = x2 - x1, y2 - y1
                dist = math.hypot(dx, dy) or 1.0
                nx, ny = -dy / dist, dx / dist
                col = (
                    (theme.gold if mult == 3 else (theme.cyan if mult == 2 else theme.muted))
                    if theme.is_dark
                    else theme.fg
                )
                offsets = [0.0] if mult == 1 else ([-1.5, 1.5] if mult == 2 else [-2.5, 0.0, 2.5])
                for off in offsets:
                    c.line(x1 + nx * off, y1 + ny * off, x2 + nx * off, y2 + ny * off, stroke=col, stroke_width=1.15)

    for s, (xx, yy) in pos.items():
        lbl = "∅" if not s else "".join(str(v) for v in s)
        pw = max(24.0, 10.0 + 7.2 * len(lbl))
        ph = 18.0
        stroke = _level_color(theme, len(s) + 1) if theme.is_dark else theme.fg
        c.rect(xx - pw * 0.5, yy - ph * 0.5, pw, ph, fill=theme.node_fill, stroke=stroke, stroke_width=1.4, rx=9.0)
        c.text(xx, yy, lbl, font_size=9.8, fill=theme.fg)
    return c.to_svg()


def _draw_swap_pair(c: SvgCanvas, truth_mode: bool) -> None:
    theme = c.theme
    y_top, y_l1, y_l2, y_bot = 16.0, 48.0, 92.0, 136.0
    pcol = theme.gold if theme.is_dark else theme.fg

    lx = [34.0, 82.0, 130.0, 178.0]
    lb = [34.0, 82.0, 130.0, 178.0]
    lt = [34.0, 82.0, 130.0, 178.0]

    l_top_lbl = ["1224", "2324", "1324", "3344"] if truth_mode else ["s_1", "s_2", "s_3", "s_4"]
    l_n1_lbl = ["1224", "2324", "1324", "3344"] if truth_mode else ["1", "1", "1", "1"]
    l_n2_lbl = ["12", "13", "24", "23"] if truth_mode else ["2", "2", "2", "2"]
    l_bot_lbl = ["1", "2", "3", "4"] if truth_mode else ["t_1", "t_2", "t_3", "t_4"]

    r1 = 10.5
    l_edges = [
        ((lx[0], y_l1), (lb[0], y_l2), False, 0.0), ((lx[0], y_l1), (lb[2], y_l2), True, 0.0),
        ((lx[1], y_l1), (lb[3], y_l2), False, 0.0), ((lx[1], y_l1), (lb[2], y_l2), True, 0.0),
        ((lx[2], y_l1), (lb[1], y_l2), False, 0.0), ((lx[2], y_l1), (lb[2], y_l2), True, 0.0),
        ((lx[3], y_l1), (lt[2], y_bot), False, 14.0), ((lx[3], y_l1), (lt[3], y_bot), True, 8.0),
        ((lb[0], y_l2), (lt[0], y_bot), False, 0.0), ((lb[0], y_l2), (lt[1], y_bot), True, 0.0),
        ((lb[1], y_l2), (lt[0], y_bot), False, 0.0), ((lb[1], y_l2), (lt[2], y_bot), True, 0.0),
        ((lb[2], y_l2), (lt[1], y_bot), False, 0.0), ((lb[2], y_l2), (lt[3], y_bot), True, 0.0),
        ((lb[3], y_l2), (lt[1], y_bot), False, 0.0), ((lb[3], y_l2), (lt[2], y_bot), True, 0.0),
    ]
    for (x1, y1), (x2, y2), hi, cv in l_edges:
        c.bdd_edge(x1, y1, x2, y2, is_hi=hi, r1=r1, r2=r1, curve=cv)
    for i in range(4):
        c.text(lx[i], y_top, l_top_lbl[i], font_size=10.0, fill=pcol, italic=not truth_mode, rich=True)
        c.line(lx[i], y_top + 8.0, lx[i], y_l1 - 10.5, stroke=pcol, stroke_width=1.2, arrow_end=True)
        if truth_mode:
            c.rect(lx[i] - 18.0, y_l1 - 9.5, 36.0, 19.0, fill=theme.node_fill, stroke=_level_color(theme, 1), stroke_width=1.4, rx=9.5)
            c.text(lx[i], y_l1, l_n1_lbl[i], font_size=9.2, fill=theme.fg)
            c.rect(lb[i] - 13.5, y_l2 - 9.5, 27.0, 19.0, fill=theme.node_fill, stroke=_level_color(theme, 2), stroke_width=1.4, rx=9.5)
            c.text(lb[i], y_l2, l_n2_lbl[i], font_size=9.2, fill=theme.fg)
            c.bdd_sink(lt[i], y_bot, l_bot_lbl[i], size=16.0, is_true=(i % 2 == 1))
        else:
            c.bdd_node(lx[i], y_l1, "1", r=10.0, accent=_level_color(theme, 1), font_size=10.0)
            c.bdd_node(lb[i], y_l2, "2", r=10.0, accent=_level_color(theme, 2), font_size=10.0)
            c.rect(lt[i] - 13.0, y_bot - 9.5, 26.0, 19.0, fill=theme.sink_true_fill if theme.is_dark else "#F1F5F9", stroke=theme.mint if theme.is_dark else theme.fg, stroke_width=1.4, rx=9.5)
            c.text(lt[i], y_bot, l_bot_lbl[i], font_size=9.8, fill=theme.fg, italic=True, rich=True)

    c.line(214.0, 88.0, 246.0, 88.0, stroke=pcol, stroke_width=1.6, arrow_end=True, arrow_start=True)

    rsx = [280.0, 328.0, 376.0, 424.0]
    rn1 = [280.0, 328.0, 376.0]
    rn2 = [292.0, 346.0, 404.0]
    rt = [280.0, 328.0, 376.0, 424.0]
    r_top_lbl = ["1224", "2234", "1234", "3434"] if truth_mode else ["s_1", "s_2", "s_3", "s_4"]
    r_n1_lbl = ["1224", "2234", "1234"] if truth_mode else ["2", "2", "2"]
    r_n2_lbl = ["12", "24", "34"] if truth_mode else ["1", "1", "1"]

    r_edges = [
        ((rn1[0], y_l1), (rn2[0], y_l2), False, 0.0), ((rn1[0], y_l1), (rn2[1], y_l2), True, 0.0),
        ((rn1[1], y_l1), (rt[1], y_bot), False, -12.0), ((rn1[1], y_l1), (rn2[2], y_l2), True, 0.0),
        ((rn1[2], y_l1), (rn2[0], y_l2), False, 0.0), ((rn1[2], y_l1), (rn2[2], y_l2), True, 0.0),
        ((rn2[0], y_l2), (rt[0], y_bot), False, 0.0), ((rn2[0], y_l2), (rt[1], y_bot), True, 0.0),
        ((rn2[1], y_l2), (rt[1], y_bot), False, 0.0), ((rn2[1], y_l2), (rt[3], y_bot), True, 0.0),
        ((rn2[2], y_l2), (rt[2], y_bot), False, 0.0), ((rn2[2], y_l2), (rt[3], y_bot), True, 0.0),
    ]
    for (x1, y1), (x2, y2), hi, cv in r_edges:
        c.bdd_edge(x1, y1, x2, y2, is_hi=hi, r1=r1, r2=r1, curve=cv)

    for i in range(3):
        c.text(rsx[i], y_top, r_top_lbl[i], font_size=10.0, fill=pcol, italic=not truth_mode, rich=True)
        c.line(rsx[i], y_top + 8.0, rn1[i], y_l1 - 10.5, stroke=pcol, stroke_width=1.2, arrow_end=True)
        if truth_mode:
            c.rect(rn1[i] - 18.0, y_l1 - 9.5, 36.0, 19.0, fill=theme.node_fill, stroke=_level_color(theme, 2), stroke_width=1.4, rx=9.5)
            c.text(rn1[i], y_l1, r_n1_lbl[i], font_size=9.2, fill=theme.fg)
        else:
            c.bdd_node(rn1[i], y_l1, "2", r=10.0, accent=_level_color(theme, 2), font_size=10.0)

    c.text(rsx[3], y_top, r_top_lbl[3], font_size=10.0, fill=pcol, italic=not truth_mode, rich=True)
    c.line(rsx[3], y_top + 8.0, rn2[2] + 4.0, y_l2 - 10.5, stroke=pcol, stroke_width=1.2, arrow_end=True)

    for i in range(3):
        if truth_mode:
            c.rect(rn2[i] - 13.5, y_l2 - 9.5, 27.0, 19.0, fill=theme.node_fill, stroke=_level_color(theme, 1), stroke_width=1.4, rx=9.5)
            c.text(rn2[i], y_l2, r_n2_lbl[i], font_size=9.2, fill=theme.fg)
        else:
            c.bdd_node(rn2[i], y_l2, "1", r=10.0, accent=_level_color(theme, 1), font_size=10.0)

    for i in range(4):
        if truth_mode:
            c.bdd_sink(rt[i], y_bot, l_bot_lbl[i], size=16.0, is_true=(i % 2 == 1))
        else:
            c.rect(rt[i] - 13.0, y_bot - 9.5, 26.0, 19.0, fill=theme.sink_true_fill if theme.is_dark else "#F1F5F9", stroke=theme.mint if theme.is_dark else theme.fg, stroke_width=1.4, rx=9.5)
            c.text(rt[i], y_bot, l_bot_lbl[i], font_size=9.8, fill=theme.fg, italic=True, rich=True)


def build_fig_26(theme: Theme) -> str:
    c = SvgCanvas(460.0, 158.0, theme)
    _draw_swap_pair(c, truth_mode=False)
    return c.to_svg()


def build_fig_27(theme: Theme) -> str:
    c = SvgCanvas(460.0, 158.0, theme)
    _draw_swap_pair(c, truth_mode=True)
    return c.to_svg()


def build_fig_p263_inline(theme: Theme) -> str:
    sc = 1.45
    w, h = 440.0, 212.0
    c = SvgCanvas(w, h, theme)

    ind_nodes: list[tuple[float, float, int | str]] = [
        (19.9, 0.0, 1), (10.0, 17.9, 2), (0.0, 35.8, 3), (34.8, 35.8, 3),
        (0.0, 53.7, 4), (34.8, 53.7, 4), (0.0, 71.6, 5), (34.8, 71.6, 5), (0.0, 89.5, 6),
    ]
    ind_sinks: list[tuple[float, float, int | str]] = [(19.9, 107.4, 1)]
    ind_edges: list[tuple[int, tuple[str, int, float], tuple[str, int, float]]] = [
        (0, ("C", 1, 0.0), ("C", 3, 0.0)),
        (1, ("C", 2, 0.0), ("C", 4, -5.0)),
        (2, ("C", 4, 0.0), ("C", 6, -12.0)),
        (3, ("C", 5, 0.0), ("C", 7, -12.0)),
        (4, ("C", 6, 0.0), ("C", 8, -12.0)),
        (5, ("C", 7, 0.0), ("B", 0, -24.0)),
        (6, ("C", 8, 0.0), ("B", 0, -16.0)),
        (7, ("B", 0, 9.0), ("B", 0, 0.0)),
        (8, ("B", 0, 9.0), ("B", 0, 0.0)),
    ]
    _draw_extracted_bdd(c, 38.0, 18.0, sc, ind_nodes, ind_sinks, ind_edges, node_r=8.2, sink_sz=12.0, font_size=8.8)
    c.text(64.0, 196.0, "Independent sets", font_size=10.5, fill=theme.fg)

    cx, cy, hr = 194.0, 98.0, 32.0
    hex_pts = [
        (cx + hr * math.sin(k * math.pi / 3.0), cy - hr * math.cos(k * math.pi / 3.0))
        for k in range(6)
    ]
    ecol = theme.mint if theme.is_dark else theme.fg
    for k in range(6):
        x1, y1 = hex_pts[k]
        x2, y2 = hex_pts[(k + 1) % 6]
        c.graph_edge(x1, y1, x2, y2, r1=8.8, r2=8.8, stroke=ecol, stroke_width=1.4)
    for k, (px, py) in enumerate(hex_pts):
        c.bdd_node(px, py, str(k + 1), r=8.8, accent=ecol, font_size=9.2)
    c.text(cx, 154.0, "The cycle C_6", font_size=10.5, fill=theme.fg, rich=True)

    ker_nodes: list[tuple[float, float, int | str]] = [
        (44.9, 0.0, 1), (29.9, 18.0, 2), (15.0, 35.9, 3), (44.9, 35.9, 3),
        (29.9, 53.8, 4), (74.7, 53.8, 4), (44.9, 71.7, 5), (15.0, 89.7, 6),
    ]
    ker_sinks: list[tuple[float, float, int | str]] = [
        (0.0, 53.8, 0), (64.8, 71.7, 0), (84.7, 71.7, 1),
        (34.9, 89.7, 0), (54.8, 89.7, 1), (5.0, 107.6, 0), (24.9, 107.6, 1),
    ]
    ker_edges: list[tuple[int, tuple[str, int, float], tuple[str, int, float]]] = [
        (0, ("C", 1, 0.0), ("C", 3, 0.0)), (1, ("C", 2, 0.0), ("C", 4, 0.0)),
        (2, ("B", 0, 0.0), ("C", 7, 0.0)), (3, ("C", 5, 0.0), ("C", 6, 0.0)),
        (4, ("C", 6, 0.0), ("C", 7, 0.0)), (5, ("B", 1, 0.0), ("B", 2, 0.0)),
        (6, ("B", 3, 0.0), ("B", 4, 0.0)), (7, ("B", 5, 0.0), ("B", 6, 0.0)),
    ]
    _draw_extracted_bdd(c, 286.0, 18.0, sc, ker_nodes, ker_sinks, ker_edges, node_r=8.2, sink_sz=12.0, font_size=8.8)
    c.text(350.0, 196.0, "Kernels", font_size=10.5, fill=theme.fg)
    return c.to_svg()


P265_A = [
    ((c, r), (c + 1, r)) for c in (0, 2, 4, 6) for r in range(8)
]

P265_B = [
    ((0, 0), (1, 0)), ((0, 1), (0, 2)), ((0, 3), (0, 4)), ((0, 5), (0, 6)), ((0, 7), (1, 7)),
    ((1, 1), (2, 1)), ((1, 2), (1, 3)), ((1, 4), (2, 4)), ((1, 5), (1, 6)), ((2, 0), (3, 0)),
    ((2, 2), (2, 3)), ((2, 5), (3, 5)), ((2, 6), (2, 7)), ((3, 1), (3, 2)), ((3, 3), (3, 4)),
    ((3, 6), (3, 7)), ((4, 0), (5, 0)), ((4, 1), (5, 1)), ((4, 2), (5, 2)), ((4, 3), (4, 4)),
    ((4, 5), (4, 6)), ((4, 7), (5, 7)), ((5, 3), (5, 4)), ((5, 5), (5, 6)), ((6, 0), (7, 0)),
    ((6, 1), (6, 2)), ((6, 3), (6, 4)), ((6, 5), (6, 6)), ((6, 7), (7, 7)), ((7, 1), (7, 2)),
    ((7, 3), (7, 4)), ((7, 5), (7, 6)),
]

P265_C = [
    ((0, 0), (0, 1)), ((0, 2), (1, 2)), ((0, 3), (0, 4)), ((0, 5), (1, 5)), ((0, 6), (0, 7)),
    ((1, 0), (1, 1)), ((1, 3), (2, 3)), ((1, 4), (2, 4)), ((1, 6), (1, 7)), ((2, 0), (3, 0)),
    ((2, 1), (2, 2)), ((2, 5), (2, 6)), ((2, 7), (3, 7)), ((3, 1), (4, 1)), ((3, 2), (3, 3)),
    ((3, 4), (3, 5)), ((3, 6), (4, 6)), ((4, 0), (5, 0)), ((4, 2), (4, 3)), ((4, 4), (4, 5)),
    ((4, 7), (5, 7)), ((5, 1), (5, 2)), ((5, 3), (6, 3)), ((5, 4), (6, 4)), ((5, 5), (5, 6)),
    ((6, 0), (6, 1)), ((6, 2), (7, 2)), ((6, 5), (7, 5)), ((6, 6), (6, 7)), ((7, 0), (7, 1)),
    ((7, 3), (7, 4)), ((7, 6), (7, 7)),
]


def _polyomino_outline(cells: tuple[tuple[int, int], ...], ox: float, oy: float, cell: float, inset: float) -> list[tuple[float, float]]:
    cset = set(cells)
    directed: dict[tuple[int, int], tuple[int, int]] = {}
    for cx, cy in cset:
        if (cx, cy - 1) not in cset:
            directed[(cx, cy)] = (cx + 1, cy)
        if (cx + 1, cy) not in cset:
            directed[(cx + 1, cy)] = (cx + 1, cy + 1)
        if (cx, cy + 1) not in cset:
            directed[(cx + 1, cy + 1)] = (cx, cy + 1)
        if (cx - 1, cy) not in cset:
            directed[(cx, cy + 1)] = (cx, cy)
    start = min(directed.keys())
    ring = [start]
    cur = directed[start]
    while cur != start:
        ring.append(cur)
        cur = directed[cur]
    n = len(ring)
    pts: list[tuple[float, float]] = []
    for i in range(n):
        p_prev = ring[(i - 1) % n]
        p_cur = ring[i]
        p_next = ring[(i + 1) % n]
        dx1, dy1 = p_cur[0] - p_prev[0], p_cur[1] - p_prev[1]
        dx2, dy2 = p_next[0] - p_cur[0], p_next[1] - p_cur[1]
        n1x, n1y = -dy1, dx1
        n2x, n2y = -dy2, dx2
        pts.append((ox + p_cur[0] * cell + (n1x + n2x) * inset, oy + p_cur[1] * cell + (n1y + n2y) * inset))
    return pts


def _draw_domino_board(c: SvgCanvas, ox: float, oy: float, cell: float, dominoes: list[tuple[tuple[int, int], tuple[int, int]]]) -> None:
    theme = c.theme
    inset = 0.9
    for (c1, r1), (c2, r2) in dominoes:
        horiz = r1 == r2
        c0, r0 = min(c1, c2), min(r1, r2)
        pw = (2.0 if horiz else 1.0) * cell - 2.0 * inset
        ph = (1.0 if horiz else 2.0) * cell - 2.0 * inset
        if theme.is_dark:
            fill = "#162942" if horiz else "#1F2A44"
            stroke = theme.cyan if horiz else theme.gold
        else:
            fill = "#E2E8F0"
            stroke = "#0F172A"
        c.rect(ox + c0 * cell + inset, oy + r0 * cell + inset, pw, ph, fill=fill, stroke=stroke, stroke_width=1.1, rx=1.4)


def build_fig_p265_inline(theme: Theme) -> str:
    cell = 13.0
    w, h = 416.0, 132.0
    c = SvgCanvas(w, h, theme)
    _draw_domino_board(c, 16.0, 14.0, cell, P265_A)
    c.text(129.0, 114.0, ",", font_size=14.0, fill=theme.fg)
    _draw_domino_board(c, 140.0, 14.0, cell, P265_B)
    c.text(268.0, 68.0, ",  or", font_size=12.5, fill=theme.fg)
    _draw_domino_board(c, 296.0, 14.0, cell, P265_C)
    return c.to_svg()


P266_1: list[tuple[tuple[tuple[int, int], ...], float]] = [
    (((0, 0),), 1.0), (((0, 1), (1, 0), (1, 1)), 0.8), (((0, 2), (1, 2), (2, 2)), 0.7),
    (((0, 3), (0, 4)), 0.9), (((0, 5),), 1.0), (((0, 6), (0, 7), (1, 6)), 0.8),
    (((1, 3),), 1.0), (((1, 4), (2, 3), (2, 4)), 0.8), (((1, 5), (2, 5)), 0.9),
    (((1, 7), (2, 7), (3, 7)), 0.7), (((2, 0), (2, 1)), 0.9), (((2, 6),), 1.0),
    (((3, 0), (3, 1), (4, 1)), 0.8), (((3, 2), (4, 2)), 0.9), (((3, 3), (3, 4), (3, 5)), 0.7),
    (((3, 6), (4, 6), (4, 7)), 0.8), (((4, 0), (5, 0)), 0.9), (((4, 3),), 1.0),
    (((4, 4), (4, 5)), 0.9), (((5, 1), (5, 2), (5, 3)), 0.7), (((5, 4), (5, 5), (6, 5)), 0.8),
    (((5, 6), (5, 7)), 0.9), (((6, 0),), 1.0), (((6, 1), (6, 2)), 0.9),
    (((6, 3), (7, 3), (7, 4)), 0.8), (((6, 4),), 1.0), (((6, 6),), 1.0),
    (((6, 7), (7, 6), (7, 7)), 0.8), (((7, 0), (7, 1), (7, 2)), 0.7), (((7, 5),), 1.0),
]


def build_fig_p266_inline_1(theme: Theme) -> str:
    cell = 15.0
    ox, oy = 18.0, 14.0
    c = SvgCanvas(156.0, 148.0, theme)
    for cells, shade in P266_1:
        pts = _polyomino_outline(cells, ox, oy, cell, inset=1.0)
        if theme.is_dark:
            if shade >= 0.98:
                fill, stroke = "#2A2414", theme.gold
            elif shade >= 0.88:
                fill, stroke = "#142A3B", theme.cyan
            elif shade >= 0.78:
                fill, stroke = "#1B2E22", theme.mint
            else:
                fill, stroke = "#281C38", theme.violet
        else:
            fill = "#FFFFFF" if shade >= 0.98 else ("#E2E8F0" if shade >= 0.88 else ("#CBD5E1" if shade >= 0.78 else "#94A3B8"))
            stroke = "#0F172A"
        c.polyline(pts, stroke=stroke, stroke_width=1.25, fill=fill, closed=True, linejoin="miter")
    return c.to_svg()


P266_2 = [
    ((0, 0), (0, 1)), ((0, 2), (1, 2)), ((0, 3), (1, 3)), ((0, 4), (1, 4)), ((0, 5), (1, 5)),
    ((0, 6), (1, 6)), ((1, 0), (2, 0)), ((1, 1), (2, 1)), ((1, 7), (2, 7)), ((2, 2), (3, 2)),
    ((2, 3), (3, 3)), ((2, 4), (3, 4)), ((2, 5), (2, 6)), ((3, 0), (4, 0)), ((3, 1), (4, 1)),
    ((3, 5), (4, 5)), ((3, 6), (4, 6)), ((3, 7), (4, 7)), ((4, 2), (5, 2)), ((4, 3), (5, 3)),
    ((4, 4), (5, 4)), ((5, 0), (6, 0)), ((5, 1), (6, 1)), ((5, 5), (5, 6)), ((6, 2), (6, 3)),
    ((6, 4), (6, 5)), ((6, 6), (6, 7)), ((7, 1), (7, 2)), ((7, 3), (7, 4)), ((7, 5), (7, 6)),
]


def build_fig_p266_inline_2(theme: Theme) -> str:
    cell = 15.0
    ox, oy = 18.0, 14.0
    c = SvgCanvas(156.0, 148.0, theme)
    _draw_domino_board(c, ox, oy, cell, P266_2)
    inset = 0.9
    for uc, ur in ((5, 7), (7, 7)):
        fill = "#2B1419" if theme.is_dark else "#FFFFFF"
        stroke = theme.coral if theme.is_dark else "#0F172A"
        c.rect(ox + uc * cell + inset, oy + ur * cell + inset, cell - 2 * inset, cell - 2 * inset, fill=fill, stroke=stroke, stroke_width=1.35, rx=1.4)
    return c.to_svg()


def build_fig_28(theme: Theme) -> str:
    w, h = 324.0, 206.0
    c = SvgCanvas(w, h, theme)

    dv = {
        "s1": (44.0, 24.0), "s2": (106.0, 24.0),
        "v2": (44.0, 64.0), "v3": (106.0, 64.0),
        "v4": (44.0, 106.0),
        "v5": (44.0, 148.0), "v6": (106.0, 148.0),
        "t1": (44.0, 188.0), "t2": (106.0, 188.0),
    }
    darcs = [
        ("s1", "v2", "1", 0.0, (-8.0, 0.0)),
        ("s2", "v3", "2", 0.0, (8.0, 0.0)),
        ("v2", "v5", "3", 24.0, (-22.0, 0.0)),
        ("v2", "v4", "4", 0.0, (7.5, 0.0)),
        ("v2", "v6", "5", 0.0, (-7.0, -8.0)),
        ("v4", "v5", "6", 0.0, (7.5, 0.0)),
        ("v3", "v5", "7", 0.0, (8.0, -8.0)),
        ("v3", "v6", "8", 0.0, (8.5, 0.0)),
        ("v5", "t1", "9", 0.0, (-8.0, 0.0)),
        ("v6", "t2", "10", 0.0, (10.5, 0.0)),
    ]
    acol = theme.cyan if theme.is_dark else theme.fg
    lcol = theme.gold if theme.is_dark else theme.fg
    for u, v, lbl, cv, (lx, ly) in darcs:
        x1, y1 = dv[u]
        x2, y2 = dv[v]
        c.graph_edge(x1, y1, x2, y2, r1=5.2, r2=5.2, curve=cv, stroke=acol, stroke_width=1.4, directed=True)
        c.text(0.5 * (x1 + x2) + lx, 0.5 * (y1 + y2) + ly, lbl, font_size=9.5, fill=lcol, bold=theme.is_dark)
    for px, py in dv.values():
        c.circle(px, py, 4.8, fill=theme.node_fill, stroke=acol, stroke_width=1.5)

    zn: dict[str, tuple[float, float]] = {
        "1": (200.0, 22.0), "2": (244.0, 38.0),
        "3": (176.0, 56.0), "4": (204.0, 74.0), "5": (232.0, 92.0),
        "6": (204.0, 114.0), "7": (262.0, 78.0), "8": (288.0, 102.0),
        "9": (204.0, 152.0), "10": (268.0, 152.0),
    }
    zs: dict[str, tuple[float, float]] = {"t1": (204.0, 188.0), "t2": (268.0, 188.0)}
    zr = 9.2
    ze = [
        ("1", "2", False, 0.0), ("1", "3", True, 0.0),
        ("3", "4", False, 0.0), ("3", "9", True, 18.0),
        ("4", "5", False, 0.0), ("4", "6", True, 0.0),
        ("5", "10", True, 0.0), ("6", "9", True, 0.0),
        ("2", "7", True, 0.0), ("7", "8", False, 0.0),
        ("7", "9", True, 0.0), ("8", "10", True, 0.0),
        ("9", "t1", True, 0.0), ("10", "t2", True, 0.0),
    ]
    for u, v, hi, cv in ze:
        x1, y1 = zn[u]
        if v in zn:
            x2, y2 = zn[v]
            r2 = zr
        else:
            x2, y2 = zs[v]
            r2 = 7.0
        c.bdd_edge(x1, y1, x2, y2, is_hi=hi, r1=zr, r2=r2, curve=cv)
    for lbl, (px, py) in zn.items():
        c.bdd_node(px, py, lbl, r=zr, accent=_level_color(theme, int(lbl)), font_size=8.8)
    for px, py in zs.values():
        c.bdd_sink(px, py, "⊤", size=13.0, is_true=True)
    return c.to_svg()


def build_fig_p269_inline_1(theme: Theme) -> str:
    c = SvgCanvas(112.0, 92.0, theme)
    r, ssz = 8.8, 12.2
    n1, n2, n3 = (60.0, 20.0), (42.0, 46.0), (60.0, 62.0)
    s0a, s1a, s0b, s1b = (24.0, 72.0), (80.0, 46.0), (44.0, 78.0), (78.0, 78.0)
    c.bdd_edge(n1[0], n1[1], n2[0], n2[1], is_hi=False, r1=r, r2=r)
    c.bdd_edge(n1[0], n1[1], s1a[0], s1a[1], is_hi=True, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n2[0], n2[1], s0a[0], s0a[1], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n2[0], n2[1], n3[0], n3[1], is_hi=True, r1=r, r2=r)
    c.bdd_edge(n3[0], n3[1], s0b[0], s0b[1], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n3[0], n3[1], s1b[0], s1b[1], is_hi=True, r1=r, r2=ssz * 0.55)
    c.bdd_node(n1[0], n1[1], "1", r=r, accent=_level_color(theme, 1), font_size=9.2)
    c.bdd_node(n2[0], n2[1], "2", r=r, accent=_level_color(theme, 2), font_size=9.2)
    c.bdd_node(n3[0], n3[1], "3", r=r, accent=_level_color(theme, 3), font_size=9.2)
    c.bdd_sink(s0a[0], s0a[1], "⊥", size=ssz, is_true=False)
    c.bdd_sink(s1a[0], s1a[1], "⊤", size=ssz, is_true=True)
    c.bdd_sink(s0b[0], s0b[1], "⊥", size=ssz, is_true=False)
    c.bdd_sink(s1b[0], s1b[1], "⊤", size=ssz, is_true=True)
    return c.to_svg()


def build_fig_p269_inline_2(theme: Theme) -> str:
    c = SvgCanvas(128.0, 96.0, theme)
    r, ssz = 8.8, 12.2
    n1 = (64.0, 18.0)
    n2l, n2r = (38.0, 44.0), (90.0, 44.0)
    n3 = (76.0, 64.0)
    s0l, s1l = (24.0, 70.0), (52.0, 70.0)
    s1r = (106.0, 70.0)
    s0b, s1b = (64.0, 82.0), (88.0, 82.0)
    c.bdd_edge(n1[0], n1[1], n2l[0], n2l[1], is_hi=False, r1=r, r2=r)
    c.bdd_edge(n1[0], n1[1], n2r[0], n2r[1], is_hi=True, r1=r, r2=r)
    c.bdd_edge(n2l[0], n2l[1], s0l[0], s0l[1], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n2l[0], n2l[1], s1l[0], s1l[1], is_hi=True, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n2r[0], n2r[1], n3[0], n3[1], is_hi=False, r1=r, r2=r)
    c.bdd_edge(n2r[0], n2r[1], s1r[0], s1r[1], is_hi=True, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n3[0], n3[1], s0b[0], s0b[1], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n3[0], n3[1], s1b[0], s1b[1], is_hi=True, r1=r, r2=ssz * 0.55)
    c.bdd_node(n1[0], n1[1], "1", r=r, accent=_level_color(theme, 1), font_size=9.2)
    c.bdd_node(n2l[0], n2l[1], "2", r=r, accent=_level_color(theme, 2), font_size=9.2)
    c.bdd_node(n2r[0], n2r[1], "2", r=r, accent=_level_color(theme, 2), font_size=9.2)
    c.bdd_node(n3[0], n3[1], "3", r=r, accent=_level_color(theme, 3), font_size=9.2)
    for sx, sy, st in ((s0l[0], s0l[1], False), (s1l[0], s1l[1], True), (s1r[0], s1r[1], True), (s0b[0], s0b[1], False), (s1b[0], s1b[1], True)):
        c.bdd_sink(sx, sy, "⊤" if st else "⊥", size=ssz, is_true=st)
    return c.to_svg()


def build_fig_p269_inline_3(theme: Theme) -> str:
    c = SvgCanvas(124.0, 86.0, theme)
    r, ssz = 8.8, 12.2
    n1 = (62.0, 18.0)
    n2, n3 = (38.0, 44.0), (86.0, 44.0)
    sinks = [(24.0, 70.0, False), (52.0, 70.0, True), (72.0, 70.0, False), (100.0, 70.0, True)]
    c.bdd_edge(n1[0], n1[1], n2[0], n2[1], is_hi=False, r1=r, r2=r)
    c.bdd_edge(n1[0], n1[1], n3[0], n3[1], is_hi=True, r1=r, r2=r)
    c.bdd_edge(n2[0], n2[1], sinks[0][0], sinks[0][1], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n2[0], n2[1], sinks[1][0], sinks[1][1], is_hi=True, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n3[0], n3[1], sinks[2][0], sinks[2][1], is_hi=False, r1=r, r2=ssz * 0.55)
    c.bdd_edge(n3[0], n3[1], sinks[3][0], sinks[3][1], is_hi=True, r1=r, r2=ssz * 0.55)
    c.bdd_node(n1[0], n1[1], "1", r=r, accent=_level_color(theme, 1), font_size=9.2)
    c.bdd_node(n2[0], n2[1], "2", r=r, accent=_level_color(theme, 2), font_size=9.2)
    c.bdd_node(n3[0], n3[1], "3", r=r, accent=_level_color(theme, 3), font_size=9.2)
    for sx, sy, st in sinks:
        c.bdd_sink(sx, sy, "⊤" if st else "⊥", size=ssz, is_true=st)
    return c.to_svg()


FIG29_A = [
    ((0, 0), (0, 1)), ((0, 2), (0, 3)), ((0, 4), (0, 5)), ((1, 0), (2, 0)), ((1, 1), (1, 2)),
    ((1, 3), (1, 4)), ((1, 5), (2, 5)), ((2, 1), (3, 1)), ((2, 2), (2, 3)), ((2, 4), (3, 4)),
    ((3, 0), (4, 0)), ((3, 2), (3, 3)), ((3, 5), (4, 5)), ((4, 1), (4, 2)), ((4, 3), (4, 4)),
]

FIG29_B: list[tuple[tuple[tuple[int, int], tuple[int, int]], float]] = [
    (((0, 0), (0, 1)), 1.0), (((0, 2), (1, 2)), 0.9), (((0, 3), (0, 4)), 0.8), (((0, 5), (0, 6)), 1.0), (((0, 7), (1, 7)), 0.8),
    (((1, 0), (2, 0)), 0.9), (((1, 1), (2, 1)), 0.8), (((1, 3), (1, 4)), 1.0), (((1, 5), (1, 6)), 0.9), (((2, 2), (3, 2)), 1.0),
    (((2, 3), (3, 3)), 0.9), (((2, 4), (2, 5)), 0.8), (((2, 6), (2, 7)), 1.0), (((3, 0), (4, 0)), 1.0), (((3, 1), (4, 1)), 0.9),
    (((3, 4), (3, 5)), 1.0), (((3, 6), (4, 6)), 0.9), (((3, 7), (4, 7)), 0.8), (((4, 2), (4, 3)), 0.8), (((4, 4), (5, 4)), 0.9),
    (((4, 5), (5, 5)), 0.8), (((5, 0), (5, 1)), 0.8), (((5, 2), (5, 3)), 1.0), (((5, 6), (6, 6)), 1.0), (((5, 7), (6, 7)), 0.9),
    (((6, 0), (7, 0)), 1.0), (((6, 1), (6, 2)), 0.9), (((6, 3), (6, 4)), 0.8), (((6, 5), (7, 5)), 0.9), (((7, 1), (7, 2)), 0.8),
    (((7, 3), (7, 4)), 1.0), (((7, 6), (7, 7)), 0.8),
]


def build_fig_29(theme: Theme) -> str:
    cell = 14.5
    w, h = 252.0, 162.0
    c = SvgCanvas(w, h, theme)
    _draw_domino_board(c, 20.0, 28.0, cell, FIG29_A)
    c.text(56.0, 144.0, "(a)", font_size=11.0, fill=theme.fg)

    bx, by = 118.0, 14.0
    inset = 0.9
    for ((c1, r1), (c2, r2)), shade in FIG29_B:
        horiz = r1 == r2
        c0, r0 = min(c1, c2), min(r1, r2)
        pw = (2.0 if horiz else 1.0) * cell - 2.0 * inset
        ph = (1.0 if horiz else 2.0) * cell - 2.0 * inset
        if theme.is_dark:
            if shade >= 0.98:
                fill, stroke = "#2A2414", theme.gold
            elif shade >= 0.88:
                fill, stroke = "#142A3B", theme.cyan
            else:
                fill, stroke = "#2B1822", theme.coral
        else:
            fill = "#FFFFFF" if shade >= 0.98 else ("#D8E0EA" if shade >= 0.88 else "#94A3B8")
            stroke = "#0F172A"
        c.rect(bx + c0 * cell + inset, by + r0 * cell + inset, pw, ph, fill=fill, stroke=stroke, stroke_width=1.1, rx=1.4)
    c.text(bx + 4.0 * cell, 144.0, "(b)", font_size=11.0, fill=theme.fg)
    return c.to_svg()


def _annular_sector_d(cx: float, cy: float, r_in: float, r_out: float, a0_deg: float, a1_deg: float) -> str:
    a0 = math.radians(a0_deg)
    a1 = math.radians(a1_deg)
    x0o, y0o = cx + r_out * math.cos(a0), cy + r_out * math.sin(a0)
    x1o, y1o = cx + r_out * math.cos(a1), cy + r_out * math.sin(a1)
    x1i, y1i = cx + r_in * math.cos(a1), cy + r_in * math.sin(a1)
    x0i, y0i = cx + r_in * math.cos(a0), cy + r_in * math.sin(a0)
    lg = 1 if (a1_deg - a0_deg) > 180.0 else 0
    return (
        f"M {fmt(x0o)} {fmt(y0o)} "
        f"A {fmt(r_out)} {fmt(r_out)} 0 {lg} 1 {fmt(x1o)} {fmt(y1o)} "
        f"L {fmt(x1i)} {fmt(y1i)} "
        f"A {fmt(r_in)} {fmt(r_in)} 0 {lg} 0 {fmt(x0i)} {fmt(y0i)} Z"
    )


def _draw_encoder_pair(
    theme: Theme,
    codes_a: list[str],
    cap_a: str,
    codes_b: list[str],
    cap_b: str,
) -> str:
    w, h = 446.0, 224.0
    c = SvgCanvas(w, h, theme)
    radii = [18.0, 29.0, 40.0, 51.0, 62.0]
    track_cols = [theme.cyan, theme.mint, theme.gold, theme.coral]

    for idx, (codes, cap) in enumerate(((codes_a, cap_a), (codes_b, cap_b))):
        cx = 114.0 if idx == 0 else 332.0
        cy = 102.0
        c.circle(cx, cy, radii[-1], fill=theme.panel if theme.is_dark else "#FFFFFF", stroke="none")
        for s_i, code in enumerate(codes):
            a0 = -45.0 + s_i * 22.5
            a1 = a0 + 22.5
            for t_i in range(4):
                if code[t_i] == "1":
                    r_in = radii[3 - t_i]
                    r_out = radii[4 - t_i]
                    fill = track_cols[t_i] if theme.is_dark else "#1E293B"
                    c.path(_annular_sector_d(cx, cy, r_in, r_out, a0, a1), stroke="none", fill=fill, opacity=0.88 if theme.is_dark else 1.0)
        gcol = "#334A6B" if theme.is_dark else "#0F172A"
        for rr in radii:
            c.circle(cx, cy, rr, fill="none", stroke=gcol, stroke_width=1.0)
        c.circle(cx, cy, radii[0], fill=theme.bg, stroke=gcol, stroke_width=1.1)
        for s_i in range(16):
            ang = math.radians(-45.0 + s_i * 22.5)
            c.line(
                cx + radii[0] * math.cos(ang),
                cy + radii[0] * math.sin(ang),
                cx + radii[-1] * math.cos(ang),
                cy + radii[-1] * math.sin(ang),
                stroke=gcol,
                stroke_width=0.85,
            )

        for k in range(32):
            ang_deg = -45.0 + k * 11.25
            ang = math.radians(ang_deg)
            if k % 2 == 1:
                lbl = codes[k // 2]
                col = theme.fg
                fsz = 7.4
            else:
                u = codes[(k // 2 - 1) % 16]
                v = codes[(k // 2) % 16]
                lbl = "".join(u[b] if u[b] == v[b] else "*" for b in range(4))
                col = theme.gold if (theme.is_dark and lbl.count("*") > 1) else (theme.muted if theme.is_dark else "#475569")
                fsz = 6.9
            lr = 76.5
            lx = cx + lr * math.cos(ang)
            ly = cy + lr * math.sin(ang)
            rot = ang_deg
            if 90.0 < (ang_deg % 360.0) < 270.0:
                rot += 180.0
            c.text(lx, ly, lbl, font_size=fsz, fill=col, mono=True, rotate=rot)

        c.text(cx, 204.0, cap, font_size=10.5, fill=theme.fg)
    return c.to_svg()


def build_fig_30(theme: Theme) -> str:
    lex = [f"{k:04b}" for k in range(16)]
    gray = [f"{(k ^ (k >> 1)):04b}" for k in range(16)]
    return _draw_encoder_pair(theme, lex, "(a) Lexicographic binary code.", gray, "(b) Gray binary code.")


def build_fig_31(theme: Theme) -> str:
    w, h = 320.0, 152.0
    c = SvgCanvas(w, h, theme)
    bar_col = theme.cyan if theme.is_dark else "#0F172A"
    bar_fill = "#162840" if theme.is_dark else "#FFFFFF"
    guide_fill = "#1E293B" if theme.is_dark else "#E2E8F0"
    guide_stroke = theme.muted if theme.is_dark else "#0F172A"
    stem_col = theme.muted if theme.is_dark else "#334155"

    ring_specs = [
        (92.0, 42.0, 24.0, 26.0, -34.0, "on"),
        (118.0, 26.5, 22.0, 18.5, -34.0, "up"),
        (146.0, 42.0, 24.0, 26.0, -34.0, "on"),
        (172.0, 43.0, 24.0, 26.0, -34.0, "on"),
        (202.0, 62.0, 24.0, 26.0, -34.0, "off"),
        (224.0, 82.0, 24.0, 26.0, -34.0, "off"),
        (252.0, 86.0, 24.0, 26.0, -34.0, "off"),
    ]
    stems = [
        (76.0, 32.0, 96.0),
        (104.0, 42.0, 98.0),
        (132.0, 35.0, 99.0),
        (160.0, 35.0, 99.0),
        (190.0, 40.0, 103.0),
        (212.0, 64.0, 124.0),
        (240.0, 74.0, 134.0),
    ]

    def rot_ellipse_arc(cx: float, cy: float, rx: float, ry: float, deg: float, t0: float, t1: float, steps: int = 28) -> str:
        phi = math.radians(deg)
        cp, sp = math.cos(phi), math.sin(phi)
        pts = []
        for s in range(steps + 1):
            t = math.radians(t0 + (t1 - t0) * s / steps)
            ex, ey = rx * math.cos(t), ry * math.sin(t)
            px = cx + ex * cp - ey * sp
            py = cy + ex * sp + ey * cp
            pts.append((px, py))
        return "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in pts)

    def draw_ring_half(idx: int, front: bool) -> None:
        cx, cy, rx, ry, tilt, state = ring_specs[idx]
        t0, t1 = (15.0, 195.0) if front else (195.0, 375.0)
        d_str = rot_ellipse_arc(cx, cy, rx, ry, tilt, t0, t1)
        if theme.is_dark:
            rcol = theme.gold if state == "on" else (theme.cyan if state == "up" else theme.coral)
        else:
            rcol = "#0F172A"
        c.path(d_str, stroke=theme.bg, stroke_width=6.2, fill="none")
        c.path(d_str, stroke=rcol, stroke_width=3.6, fill="none")
        if not theme.is_dark:
            c.path(d_str, stroke="#FFFFFF", stroke_width=1.6, fill="none")

    for idx in range(7):
        draw_ring_half(idx, front=False)

    c.path(
        "M 56 26 L 246 29 A 11 11 0 0 1 246 51 L 56 48",
        stroke=bar_col,
        stroke_width=5.4,
        fill="none",
    )
    c.path(
        "M 56 26 L 246 29 A 11 11 0 0 1 246 51 L 56 48",
        stroke=bar_fill,
        stroke_width=2.8,
        fill="none",
    )
    c.ellipse(34.0, 37.0, 18.0, 14.0, fill=bar_fill, stroke=bar_col, stroke_width=2.0)
    c.ellipse(34.0, 37.0, 10.5, 7.5, fill=theme.bg, stroke=bar_col, stroke_width=1.6)
    c.rect(48.0, 31.5, 16.0, 11.0, fill=bar_fill, stroke=bar_col, stroke_width=1.6, rx=2.0)

    c.rect(58.0, 74.0, 198.0, 15.0, fill=guide_fill, stroke=guide_stroke, stroke_width=1.5, rx=7.5)
    for sx, _, _ in stems:
        c.ellipse(sx, 81.5, 4.2, 2.3, fill=theme.bg, stroke=guide_stroke, stroke_width=1.1)

    for sx, sy_top, sy_bot in stems:
        c.line(sx, sy_top + 4.5, sx, sy_bot - 4.5, stroke=theme.bg, stroke_width=4.4)
        c.line(sx, sy_top + 4.5, sx, sy_bot - 4.5, stroke=stem_col, stroke_width=2.2)
        c.circle(sx, sy_top, 4.6, fill=theme.node_fill if theme.is_dark else "#FFFFFF", stroke=stem_col, stroke_width=1.6)
        c.circle(sx, sy_top, 1.8, fill=theme.bg, stroke=stem_col, stroke_width=1.0)
        c.circle(sx, sy_bot, 4.2, fill=theme.node_fill if theme.is_dark else "#FFFFFF", stroke=stem_col, stroke_width=1.5)

    draw_ring_half(1, front=True)
    c.line(62.0, 48.2, 212.0, 50.6, stroke=bar_col, stroke_width=5.4)
    c.line(62.0, 48.2, 212.0, 50.6, stroke=bar_fill, stroke_width=2.8)
    for idx in (0, 2, 3, 4, 5, 6):
        draw_ring_half(idx, front=True)
    return c.to_svg()


def build_fig_32(theme: Theme) -> str:
    w, h = 340.0, 344.0
    c = SvgCanvas(w, h, theme)
    x0, x1 = 62.0, 312.0
    pw = x1 - x0
    y_first = 28.0
    row_gap = 38.0
    amp = 11.5

    gcol = theme.grid if theme.is_dark else "#CBD5E1"
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        gx = x0 + frac * pw
        c.line(gx, y_first - 16.0, gx, y_first + 7 * row_gap + 16.0, stroke=gcol, stroke_width=0.9)

    accents = [theme.cyan, theme.gold, theme.mint, theme.coral, theme.violet, theme.cyan, theme.gold, theme.mint]
    for k in range(8):
        cy = y_first + k * row_gap
        c.line(x0, cy, x1, cy, stroke=gcol, stroke_width=0.9)
        c.text(x0 - 10.0, cy, f"w_{k}(x)", font_size=10.5, fill=theme.fg, anchor="end", italic=True, rich=True)

        if k > 0:
            cos_pts = []
            for s in range(121):
                u = s / 120.0
                val = math.sqrt(2.0) * math.cos(k * math.pi * u)
                cos_pts.append((x0 + u * pw, cy - val * amp))
            ccol = "#475569" if theme.is_dark else "#94A3B8"
            c.polyline(cos_pts, stroke=ccol, stroke_width=1.0)

        scol = accents[k] if theme.is_dark else "#0F172A"
        breaks = [0.0] + [j / (2.0 * k) for j in range(1, 2 * k, 2)] + [1.0]
        for seg_i in range(len(breaks) - 1):
            u_a, u_b = breaks[seg_i], breaks[seg_i + 1]
            sgn = 1.0 if seg_i % 2 == 0 else -1.0
            sy = cy - sgn * amp
            xa, xb = x0 + u_a * pw, x0 + u_b * pw
            c.line(xa, sy, xb, sy, stroke=scol, stroke_width=1.8)
            c.circle(xa, sy, 2.2, fill=scol, stroke="none")
        if k % 2 == 0:
            c.circle(x1, cy - amp, 2.2, fill=scol, stroke="none")
        else:
            c.circle(x1, cy + amp, 2.2, fill=scol, stroke="none")
            c.circle(x1, cy - amp, 2.3, fill=theme.bg, stroke=scol, stroke_width=1.3)

    by = y_first + 7 * row_gap + 28.0
    for frac, lbl in ((0.0, "x = 0"), (0.25, "x = 1/4"), (0.5, "x = 1/2"), (0.75, "x = 3/4"), (1.0, "x = 1")):
        c.text(x0 + frac * pw, by, lbl, font_size=9.5, fill=theme.fg, italic=True)
    return c.to_svg()


def build_fig_33(theme: Theme) -> str:
    comp = [
        "0000", "0001", "0011", "0010", "0110", "0100", "0101", "0111",
        "1111", "1110", "1100", "1101", "1001", "1011", "1010", "1000",
    ]
    bal = [
        "0000", "0001", "0011", "0010", "0110", "0111", "1111", "1110",
        "1010", "1011", "1001", "1101", "0101", "0100", "1100", "1000",
    ]
    return _draw_encoder_pair(theme, comp, "(a) Complementary Gray code.", bal, "(b) Balanced Gray code.")


def _deltas_to_codes(deltas: list[int], start: int = 0) -> list[int]:
    out = [start]
    cur = start
    for d in deltas:
        cur ^= 1 << d
        out.append(cur)
    return out


def _magic_pi(n: int) -> list[int]:
    if n == 1:
        return [0]
    prev = _magic_pi(n - 1)
    p2 = [prev[prev[j]] for j in range(n - 1)]
    return [(n - 1 if (j - 1) % n == n - 1 else p2[(j - 1) % n]) for j in range(n)]


def _sw_p(n: int, j: int) -> list[int]:
    if j < 0 or j >= n:
        return []
    if n == 1 and j == 0:
        return [0, 1]
    pi = _magic_pi(n - 1)
    part1 = []
    for w in _sw_p(n - 1, j - 1):
        rw = 0
        for b in range(n - 1):
            if (w >> b) & 1:
                rw |= 1 << pi[b]
        part1.append((1 << (n - 1)) | rw)
    return part1 + _sw_p(n - 1, j)


def _sw_s(n: int) -> list[int]:
    out: list[int] = []
    for j in range(n):
        sub = _sw_p(n, j)
        out.extend(reversed(sub) if j % 2 == 1 else sub)
    return out


def _theorem_d(deltas: list[int], n: int, picks: list[int]) -> list[int]:
    alphas: list[list[int]] = []
    js: list[int] = []
    prev = 0
    for idx in picks:
        alphas.append(deltas[prev:idx])
        js.append(deltas[idx])
        prev = idx + 1
    m = len(js)
    res: list[int] = []
    for k in range(m):
        ak = alphas[k]
        akr = list(reversed(ak))
        res.extend(ak + ([n + 1] + akr + [n] if k % 2 == 0 else [n] + akr + [n + 1]) + ak)
        if k < m - 1:
            res.append(js[k])
    res.append(n + 1)
    for k in range(m - 1, -1, -1):
        res.extend(reversed(alphas[k]))
        if k > 0:
            res.append(js[k - 1])
    res.append(n)
    return res


def _gray34_sequences() -> list[tuple[str, list[int]]]:
    ca = [k ^ (k >> 1) for k in range(256)]

    d4 = [int(ch) for ch in "0102303132101232"]
    rot = d4.index(0, 1)
    d4 = d4[rot + 1 :] + d4[: rot + 1]

    def lift_bal(dn: list[int], n: int) -> list[int]:
        if dn[-1] != 0:
            idx0 = max(i for i, x in enumerate(dn) if x == 0)
            dn = dn[idx0 + 1 :] + dn[: idx0 + 1]
        cnt = [dn.count(j) for j in range(n)]
        cp = [2 * (((1 << (n + 1)) + j) // (n + 2)) for j in range(n + 2)]
        rem = [2 * cnt[j] - cp[(j + 2) % (n + 2)] // 2 - (2 if j == 0 else 0) for j in range(n)]
        picks: list[int] = []
        for i in range(len(dn) - 1):
            v = dn[i]
            if rem[v] > 0:
                picks.append(i)
                rem[v] -= 1
        picks.append(len(dn) - 1)
        return _theorem_d(dn, n, picks)

    cb = _deltas_to_codes(lift_bal(lift_bal(d4, 4), 6)[:-1], 0)

    p7 = _sw_s(7)
    cc = p7 + [128 | (x ^ 127) for x in p7]

    v5 = _deltas_to_codes([int(ch) for ch in "0123042103210423" * 2], 0)[:-1]
    u2 = [0, 1, 3, 2]
    alpha = [0, 1, 1, 1]
    iu = jv = 0
    w7: list[int] = []
    for k in range(128):
        w7.append((u2[iu % 4] << 5) | v5[jv % 32])
        if alpha[k % 4] == 0:
            iu += 1
        else:
            jv += 1
    d7 = [(w7[k] ^ w7[(k + 1) % 128]).bit_length() - 1 for k in range(128)]
    cd_d8 = d7 + d7
    for pos in range(128):
        if d7[pos] == 0:
            beta = list(d7)
            beta[pos] = 7
            cand = beta + beta
            min_r = min(
                (idxs[(ai + 1) % len(idxs)] - idxs[ai]) % 256
                for coord in range(8)
                for idxs in [[i for i, x in enumerate(cand) if x == coord]]
                for ai in range(len(idxs))
            )
            if min_r >= 5:
                cd_d8 = cand
                break
    cd = _deltas_to_codes(cd_d8[:-1], 0)

    swap = {0: 1, 1: 0, 2: 2, 3: 3, 4: 4}
    dn = [swap[int(ch)] for ch in "0123042103210423" * 2]
    for n_idx in (5, 6, 7):
        zeros = [i for i, x in enumerate(dn) if x == 0]
        beta = list(dn)
        for p in (zeros[0], zeros[len(zeros) // 3], zeros[(2 * len(zeros)) // 3]):
            beta[p] = n_idx
        dn = beta + beta
    ce = _deltas_to_codes(dn[:-1], 0)

    cf = _sw_s(8)

    half = 32
    gamma = [k ^ (k >> 1) for k in range(1, half + 1)]
    gh = half ^ (half >> 1)
    gh1 = (half + 1) ^ ((half + 1) >> 1)
    gp = [x ^ 1 for x in gamma]
    gpp = [x ^ gh for x in gamma]
    gppp = [x ^ gh1 for x in gamma]
    seq = (
        [x for x in reversed(gpp)]
        + [64 | x for x in reversed(gp)]
        + [192 | x for x in gp]
        + [128 | x for x in gpp]
        + [128 | x for x in gamma]
        + [192 | x for x in gppp]
        + [64 | x for x in reversed(gppp)]
        + [x for x in reversed(gamma)]
    )
    cg = seq
    for shift in range(256):
        cand = seq[shift:] + seq[:shift]
        for rev in (False, True):
            c2 = list(reversed(cand)) if rev else cand
            if c2[0] == 0 and all(sum(k * (-1 if (c2[k] >> j) & 1 else 1) for k in range(256)) == 0 for j in range(8)):
                cg = c2
                break
        if cg[0] == 0 and all(sum(k * (-1 if (cg[k] >> j) & 1 else 1) for k in range(256)) == 0 for j in range(8)):
            break

    return [("(a)", ca), ("(b)", cb), ("(c)", cc), ("(d)", cd), ("(e)", ce), ("(f)", cf), ("(g)", cg)]


def build_fig_34(theme: Theme) -> str:
    strips = _gray34_sequences()
    cw, rh = 3.6, 1.95
    sw = 8.0 * cw
    sh = 256.0 * rh
    gap = 18.0
    ox, oy = 18.0, 14.0
    w = ox * 2.0 + 7 * sw + 6 * gap
    h = oy + sh + 30.0
    c = SvgCanvas(w, h, theme)
    palette = [theme.cyan, theme.gold, theme.mint, theme.coral, theme.violet, theme.cyan, theme.gold]

    for s_idx, (lbl, seq) in enumerate(strips):
        sx = ox + s_idx * (sw + gap)
        c.rect(sx, oy, sw, sh, fill=theme.panel if theme.is_dark else "#FFFFFF", stroke="none")
        fill = palette[s_idx] if theme.is_dark else "#0F172A"
        for col in range(8):
            bit_idx = 7 - col
            r = 0
            while r < 256:
                if (seq[r] >> bit_idx) & 1:
                    r_start = r
                    while r < 256 and ((seq[r] >> bit_idx) & 1):
                        r += 1
                    c.rect(sx + col * cw, oy + r_start * rh, cw, (r - r_start) * rh, fill=fill, stroke="none")
                else:
                    r += 1
        gcol = "#283A52" if theme.is_dark else "#475569"
        for col in range(1, 8):
            c.line(sx + col * cw, oy, sx + col * cw, oy + sh, stroke=gcol, stroke_width=0.45)
        bcol = palette[s_idx] if theme.is_dark else "#0F172A"
        c.rect(sx, oy, sw, sh, fill="none", stroke=bcol, stroke_width=0.95)
        c.text(sx + sw * 0.5, oy + sh + 14.0, lbl, font_size=10.5, fill=theme.fg)
    return c.to_svg()


def _koda_ruskey_visits() -> list[tuple[int, ...]]:
    n = 7
    ch = [2, 0, 1, 0, 0, 0, 4, 3]
    le = [0] * (n + 1)
    ri = [0] * (n + 1)
    ri[2], le[7] = 7, 2
    ri[3], le[6] = 6, 3
    ri[4], le[5] = 5, 4
    a = [0] * (n + 1)
    f = list(range(n + 1))
    le[0], ri[n] = n, 0
    ri[0], le[ch[0]] = ch[0], 0
    visits: list[tuple[int, ...]] = []
    while True:
        visits.append(tuple(a[1:]))
        q = le[0]
        p = f[q]
        f[q] = q
        if p == 0:
            break
        if a[p] == 0:
            a[p] = 1
            if ch[p] != 0:
                q = ri[p]
                le[q] = p - 1
                ri[p - 1] = q
                ri[p] = ch[p]
                le[ch[p]] = p
        else:
            a[p] = 0
            if ch[p] != 0:
                q = ri[p - 1]
                ri[p] = q
                le[q] = p
        f[p] = f[le[p]]
        f[le[p]] = le[p]
    return visits


def build_fig_p314_inline_1(theme: Theme) -> str:
    visits = _koda_ruskey_visits()
    cell_w, cell_h = 40.0, 34.0
    ox, oy = 18.0, 16.0
    w = ox * 2.0 + 11 * cell_w
    h = oy * 2.0 + 3 * cell_h
    c = SvgCanvas(w, h, theme)

    rel_pts = {
        2: (5.0, 5.0),
        1: (5.0, 14.5),
        7: (21.5, 5.0),
        3: (15.5, 14.5),
        6: (27.5, 14.5),
        4: (23.0, 24.0),
        5: (32.0, 24.0),
    }
    tree_edges = [(2, 1), (7, 3), (7, 6), (6, 4), (6, 5)]

    for idx, state in enumerate(visits):
        row = idx // 11
        col_in_row = idx % 11
        col = (10 - col_in_row) if row == 1 else col_in_row
        bx = ox + col * cell_w
        by = oy + row * cell_h

        for u, v in tree_edges:
            ux, uy = bx + rel_pts[u][0], by + rel_pts[u][1]
            vx, vy = bx + rel_pts[v][0], by + rel_pts[v][1]
            both = state[u - 1] == 1 and state[v - 1] == 1
            ecol = (theme.cyan if both else "#334155") if theme.is_dark else ("#0F172A" if both else "#94A3B8")
            c.line(ux, uy, vx, vy, stroke=ecol, stroke_width=1.25 if both else 0.95)

        for nid, (rx, ry) in rel_pts.items():
            px, py = bx + rx, by + ry
            on = state[nid - 1] == 1
            if on:
                fill = theme.gold if theme.is_dark else "#0F172A"
                stroke = theme.gold if theme.is_dark else "#0F172A"
                c.circle(px, py, 2.7, fill=fill, stroke=stroke, stroke_width=1.0)
            else:
                fill = theme.bg if theme.is_dark else "#FFFFFF"
                stroke = theme.muted if theme.is_dark else "#334155"
                c.circle(px, py, 2.5, fill=fill, stroke=stroke, stroke_width=1.05)
    return c.to_svg()


def build_fig_p314_inline_2(theme: Theme) -> str:
    c = SvgCanvas(128.0, 62.0, theme)
    cols = [(26.0, 2), (52.0, 1), (78.0, 3), (104.0, 1)]
    r = 4.2
    stroke = theme.cyan if theme.is_dark else theme.fg
    for cx, cnt in cols:
        for k in range(cnt - 1):
            y1 = 16.0 + k * 15.0
            y2 = 16.0 + (k + 1) * 15.0
            c.line(cx, y1 + r, cx, y2 - r, stroke=stroke, stroke_width=1.35)
        for k in range(cnt):
            yy = 16.0 + k * 15.0
            c.circle(cx, yy, r, fill=theme.node_fill if theme.is_dark else "#FFFFFF", stroke=stroke, stroke_width=1.4)
    return c.to_svg()


def build_fig_35(theme: Theme) -> str:
    w, h = 232.0, 232.0
    c = SvgCanvas(w, h, theme)
    cx, cy = 116.0, 116.0
    r_ring = 68.0
    r_lbl = 86.0

    seq = "00000100011001010011101011011111"
    words = [(seq + seq)[i : i + 5] for i in range(32)]
    idx_11111 = words.index("11111")
    words = words[idx_11111:] + words[:idx_11111]

    c.circle(cx, cy, r_ring, fill="none", stroke=theme.muted if theme.is_dark else "#64748B", stroke_width=1.2)

    for k, w5 in enumerate(words):
        ang_deg = -90.0 + k * (360.0 / 32.0)
        ang = math.radians(ang_deg)
        bx = cx + r_ring * math.cos(ang)
        by = cy + r_ring * math.sin(ang)
        bit = w5[-1] == "1"
        if bit:
            fill = theme.gold if theme.is_dark else "#0F172A"
            c.circle(bx, by, 3.6, fill=fill, stroke=fill, stroke_width=1.0, glow=True)
        else:
            stroke = theme.cyan if theme.is_dark else "#0F172A"
            c.circle(bx, by, 3.5, fill=theme.bg, stroke=stroke, stroke_width=1.35)

        lx = cx + r_lbl * math.cos(ang)
        ly = cy + r_lbl * math.sin(ang)
        rot = ang_deg
        if 90.0 < (ang_deg % 360.0) < 270.0:
            rot += 180.0
        tcol = (theme.gold if bit else theme.cyan) if theme.is_dark else theme.fg
        c.text(lx, ly, w5, font_size=7.4, fill=tcol, mono=True, rotate=rot)
    return c.to_svg()


def build_fig_36(theme: Theme) -> str:
    w, h = 420.0, 152.0
    c = SvgCanvas(w, h, theme)
    ecol = theme.cyan if theme.is_dark else theme.fg
    dcol = theme.gold if theme.is_dark else theme.fg

    def draw_trie(
        internal: list[tuple[float, float]],
        leaves: list[tuple[float, float, str]],
        segs: list[tuple[tuple[float, float], tuple[float, float]]],
        cap_x: float,
        cap: str,
    ) -> None:
        for (x1, y1), (x2, y2) in segs:
            c.line(x1, y1, x2, y2, stroke=ecol, stroke_width=1.4)
        for px, py in internal:
            c.circle(px, py, 2.8, fill=dcol, stroke="none")
        for lx, ly, lbl in leaves:
            c.text(lx, ly + 8.5, lbl, font_size=9.2, fill=theme.fg, mono=True)
        c.text(cap_x, 136.0, cap, font_size=10.5, fill=theme.fg)

    ia = [(96.0, 20.0), (48.0, 42.0), (66.0, 64.0), (144.0, 42.0), (126.0, 64.0), (144.0, 86.0)]
    la = [
        (30.0, 64.0, "00**"), (48.0, 86.0, "010*"), (84.0, 86.0, "011*"),
        (108.0, 86.0, "100*"), (126.0, 108.0, "1010"), (162.0, 108.0, "1011"), (162.0, 64.0, "11**"),
    ]
    sa = [
        (ia[0], ia[1]), (ia[0], ia[3]),
        (ia[1], (30.0, 64.0)), (ia[1], ia[2]),
        (ia[2], (48.0, 86.0)), (ia[2], (84.0, 86.0)),
        (ia[3], ia[4]), (ia[3], (162.0, 64.0)),
        (ia[4], (108.0, 86.0)), (ia[4], ia[5]),
        (ia[5], (126.0, 108.0)), (ia[5], (162.0, 108.0)),
    ]
    draw_trie(ia, la, sa, 96.0, "(a) Normal binary trie.")

    ib = [(304.0, 20.0), (256.0, 42.0), (274.0, 64.0), (352.0, 42.0), (370.0, 64.0), (352.0, 86.0)]
    lb = [
        (238.0, 64.0, "00**"), (256.0, 86.0, "011*"), (292.0, 86.0, "010*"),
        (334.0, 64.0, "11**"), (334.0, 108.0, "1010"), (370.0, 108.0, "1011"), (388.0, 86.0, "100*"),
    ]
    sb = [
        (ib[0], ib[1]), (ib[0], ib[3]),
        (ib[1], (238.0, 64.0)), (ib[1], ib[2]),
        (ib[2], (256.0, 86.0)), (ib[2], (292.0, 86.0)),
        (ib[3], (334.0, 64.0)), (ib[3], ib[4]),
        (ib[4], ib[5]), (ib[4], (388.0, 86.0)),
        (ib[5], (334.0, 108.0)), (ib[5], (370.0, 108.0)),
    ]
    draw_trie(ib, lb, sb, 304.0, "(b) Gray binary trie.")
    return c.to_svg()


P328_RAW_PATHS: list[str] = [
    "M 24.9 11.0 C 24.7 8.2 23.4 5.5 21.4 3.5 C 19.2 1.3 16.1 0.0 13.0 0.0 C 9.8 0.0 6.8 1.3 4.5 3.5 C 2.3 5.7 1.0 8.8 1.0 11.9 C 1.0 12.3 1.0 12.6 1.1 12.9",
    "M 0.0 11.2 C 0.5 11.7 0.9 12.3 1.1 12.9 C 1.2 12.2 1.6 11.6 2.1 11.2",
    "M 1.1 12.9 C 1.3 15.7 2.5 18.4 4.5 20.4 C 6.8 22.6 9.8 23.9 13.0 23.9 C 16.1 23.9 19.2 22.6 21.4 20.4 C 23.7 18.2 24.9 15.1 24.9 12.0 C 24.9 11.6 24.9 11.3 24.9 11.0",
    "M 26.0 12.7 C 25.5 12.2 25.1 11.6 24.9 11.0 C 24.8 11.7 24.4 12.3 23.8 12.7",
    "M 69.5 23.8 C 72.2 23.5 74.7 22.3 76.6 20.4 C 78.8 18.2 80.1 15.1 80.1 12.0 C 80.1 11.6 80.1 11.3 80.0 11.0",
    "M 81.1 12.7 C 80.6 12.2 80.2 11.6 80.0 11.0 C 79.9 11.7 79.5 12.3 79.0 12.7",
    "M 80.0 11.0 C 79.8 8.2 78.6 5.5 76.6 3.5 C 74.7 1.6 72.2 0.4 69.5 0.1 L 67.0 21.4",
    "M 66.1 19.6 C 66.6 20.1 66.9 20.8 67.0 21.4 C 67.2 20.8 67.7 20.3 68.2 19.9",
    "M 67.0 21.4 L 66.7 23.8 C 64.1 23.5 61.6 22.3 59.7 20.4 C 57.6 18.4 56.4 15.7 56.2 12.9",
    "M 57.5 14.4 C 56.9 14.1 56.4 13.6 56.2 12.9 C 56.1 13.6 55.8 14.2 55.4 14.7",
    "M 56.2 12.9 C 56.2 12.6 56.2 12.3 56.2 12.0 C 56.2 8.8 57.4 5.7 59.7 3.5 C 61.6 1.6 64.1 0.4 66.7 0.1 L 67.3 4.8",
    "M 66.0 3.3 C 66.6 3.6 67.0 4.2 67.3 4.8 C 67.3 4.2 67.6 3.5 68.1 3.0",
    "M 67.3 4.8 L 69.5 23.8",
    "M 125.8 23.9 C 128.6 23.6 131.2 22.4 133.3 20.4 C 133.7 20.0 134.1 19.6 134.4 19.1 L 128.3 8.6",
    "M 130.1 9.6 C 129.4 9.5 128.8 9.1 128.3 8.6 C 128.5 9.3 128.5 10.0 128.3 10.6",
    "M 128.3 8.6 L 123.4 0.1 C 120.8 0.4 118.3 1.6 116.4 3.5 C 115.4 4.5 114.6 5.6 114.0 6.8",
    "M 113.9 4.8 C 114.1 5.5 114.2 6.2 114.0 6.8 C 114.5 6.3 115.1 5.9 115.8 5.9",
    "M 114.0 6.8 C 113.3 8.4 112.9 10.2 112.9 12.0 C 112.9 13.6 113.2 15.2 113.8 16.7 L 125.9 16.7",
    "M 124.2 17.7 C 124.7 17.2 125.2 16.8 125.9 16.7 C 125.2 16.5 124.7 16.1 124.2 15.6",
    "M 125.9 16.7 L 135.8 16.7 C 136.4 15.2 136.8 13.6 136.8 12.0 C 136.8 9.5 136.0 7.2 134.7 5.2",
    "M 136.4 6.1 C 135.8 6.0 135.2 5.6 134.7 5.2 C 134.9 5.8 134.9 6.6 134.6 7.2",
    "M 134.7 5.2 C 134.3 4.6 133.8 4.0 133.3 3.5 C 131.4 1.6 128.9 0.4 126.2 0.1 L 120.2 10.5",
    "M 120.1 8.5 C 120.4 9.2 120.4 9.9 120.2 10.5 C 120.6 10.0 121.3 9.7 121.9 9.6",
    "M 120.2 10.5 L 115.2 19.1 C 115.6 19.6 116.0 20.0 116.4 20.4 C 118.6 22.6 121.6 23.9 124.8 23.9 C 125.1 23.9 125.4 23.9 125.8 23.9",
    "M 124.1 24.9 C 124.5 24.4 125.1 24.1 125.8 23.9 C 125.1 23.8 124.5 23.4 124.1 22.8",
    "M 180.6 23.9 C 177.7 23.6 175.1 22.4 173.1 20.4 C 172.7 20.0 172.3 19.6 171.9 19.1 L 176.4 8.6",
    "M 176.7 10.6 C 176.4 10.0 176.3 9.3 176.4 8.6 C 176.0 9.2 175.4 9.6 174.8 9.8",
    "M 176.4 8.6 L 180.1 0.1 C 177.5 0.4 175.0 1.6 173.1 3.5 C 172.1 4.5 171.3 5.6 170.7 6.8",
    "M 170.7 4.8 C 170.8 5.5 170.9 6.2 170.7 6.8 C 171.2 6.3 171.8 5.9 172.5 5.9",
    "M 170.7 6.8 C 170.0 8.4 169.6 10.2 169.6 12.0 C 169.6 13.6 169.9 15.2 170.5 16.7 L 182.6 16.7",
    "M 180.9 17.7 C 181.4 17.2 181.9 16.8 182.6 16.7 C 181.9 16.5 181.4 16.1 180.9 15.6",
    "M 182.6 16.7 L 192.5 16.7 C 193.1 15.2 193.5 13.6 193.5 12.0 C 193.5 9.5 192.7 7.2 191.4 5.2",
    "M 193.1 6.1 C 192.5 6.0 191.9 5.6 191.4 5.2 C 191.6 5.8 191.6 6.6 191.3 7.2",
    "M 191.4 5.2 C 191.0 4.6 190.5 4.0 190.0 3.5 C 188.1 1.6 185.6 0.4 182.9 0.1 L 187.4 10.5",
    "M 185.8 9.4 C 186.4 9.6 187.0 10.0 187.4 10.5 C 187.3 9.9 187.4 9.2 187.7 8.6",
    "M 187.4 10.5 L 191.1 19.1 C 190.8 19.6 190.4 20.0 190.0 20.4 C 187.7 22.6 184.7 23.9 181.5 23.9 C 181.2 23.9 180.9 23.9 180.6 23.9",
    "M 182.2 22.8 C 181.9 23.4 181.3 23.8 180.6 23.9 C 181.2 24.1 181.8 24.4 182.3 24.9",
    "M 239.2 23.9 C 242.0 23.6 244.6 22.4 246.7 20.4 C 247.1 20.0 247.5 19.6 247.8 19.1 L 243.3 8.6",
    "M 245.0 9.8 C 244.3 9.6 243.7 9.2 243.3 8.6 C 243.4 9.3 243.3 10.0 243.0 10.6",
    "M 243.3 8.6 L 239.6 0.1 C 242.3 0.4 244.8 1.6 246.7 3.5 C 247.6 4.5 248.4 5.6 249.0 6.8",
    "M 247.2 5.9 C 247.9 5.9 248.6 6.3 249.0 6.8 C 248.9 6.2 248.9 5.5 249.1 4.8",
    "M 249.0 6.8 C 249.8 8.4 250.2 10.2 250.2 12.0 C 250.2 13.6 249.8 15.2 249.2 16.7 L 237.1 16.7",
    "M 238.8 15.6 C 238.4 16.1 237.8 16.5 237.1 16.7 C 237.8 16.8 238.4 17.2 238.8 17.7",
    "M 237.1 16.7 L 227.2 16.7 C 226.6 15.2 226.3 13.6 226.3 12.0 C 226.3 9.5 227.0 7.2 228.4 5.2",
    "M 228.5 7.2 C 228.1 6.6 228.1 5.8 228.4 5.2 C 227.9 5.6 227.3 6.0 226.6 6.1",
    "M 228.4 5.2 C 228.8 4.6 229.2 4.0 229.8 3.5 C 231.7 1.6 234.2 0.4 236.8 0.1 L 232.3 10.5",
    "M 232.0 8.6 C 232.3 9.2 232.4 9.9 232.3 10.5 C 232.7 10.0 233.3 9.6 234.0 9.4",
    "M 232.3 10.5 L 228.6 19.1 C 229.0 19.6 229.4 20.0 229.8 20.4 C 232.0 22.6 235.0 23.9 238.2 23.9 C 238.5 23.9 238.8 23.9 239.2 23.9",
    "M 237.5 24.9 C 237.9 24.4 238.5 24.1 239.2 23.9 C 238.5 23.8 237.9 23.4 237.5 22.8",
]


def _transform_svg_path(d_raw: str, ox: float, oy: float, sc: float) -> str:
    tokens = d_raw.split()
    out: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("M", "L"):
            x = ox + float(tokens[i + 1]) * sc
            y = oy + float(tokens[i + 2]) * sc
            out.append(f"{tok} {fmt(x)} {fmt(y)}")
            i += 3
        elif tok == "C":
            coords = []
            for k in range(3):
                px = ox + float(tokens[i + 1 + 2 * k]) * sc
                py = oy + float(tokens[i + 2 + 2 * k]) * sc
                coords.append(f"{fmt(px)} {fmt(py)}")
            out.append("C " + " ".join(coords))
            i += 7
        else:
            out.append(tok)
            i += 1
    return " ".join(out)


def build_fig_p328_inline(theme: Theme) -> str:
    sc = 1.48
    ox, oy = 24.0, 14.0
    w, h = 424.0, 82.0
    c = SvgCanvas(w, h, theme)
    palette = [theme.cyan, theme.gold, theme.mint, theme.coral, theme.violet]
    for p_str in P328_RAW_PATHS:
        first_x = float(p_str.split()[1])
        grp = 0 if first_x < 40 else (1 if first_x < 95 else (2 if first_x < 155 else (3 if first_x < 210 else 4)))
        col = palette[grp] if theme.is_dark else theme.fg
        c.path(_transform_svg_path(p_str, ox, oy, sc), stroke=col, stroke_width=1.35, fill="none")

    labels = [
        (13.0, "Before"),
        (68.0, "After Type 1"),
        (124.8, "After Type 2"),
        (181.5, "After Type 3"),
        (238.2, "After Type 4"),
    ]
    for cx_raw, lbl in labels:
        c.text(ox + cx_raw * sc, 64.0, lbl, font_size=9.6, fill=theme.fg)
    return c.to_svg()


def build_fig_p217_inline_1(theme: Theme) -> str:
    c = SvgCanvas(380.0, 108.0, theme)
    node_stroke = theme.primary if theme.is_dark else theme.fg
    root_col = theme.gold if theme.is_dark else theme.fg
    hi_col = theme.hi_stroke if theme.is_dark else theme.fg
    lo_col = theme.lo_stroke
    true_col = theme.mint if theme.is_dark else theme.fg
    false_col = theme.coral if theme.is_dark else theme.fg

    c.text(146.0, 17.0, "ROOT", font_size=11.0, fill=root_col, mono=True, anchor="start")
    c.line(180.0, 17.0, 199.0, 17.0, stroke=root_col, stroke_width=1.35, arrow_end=True)

    nodes = [
        (202.0, 7.0, "1", ("dot", lo_col), ("dot", hi_col)),
        (145.0, 45.0, "2", ("⊥", false_col), ("dot", hi_col)),
        (260.0, 45.0, "2", ("dot", lo_col), ("⊤", true_col)),
        (202.0, 83.0, "3", ("⊥", false_col), ("⊤", true_col)),
    ]
    for x, y, var_lbl, cell2, cell3 in nodes:
        c.rect(x, y, 54.0, 19.0, fill=theme.node_fill, stroke=node_stroke, stroke_width=1.2)
        c.line(x + 18.0, y, x + 18.0, y + 19.0, stroke=node_stroke, stroke_width=1.0)
        c.line(x + 36.0, y, x + 36.0, y + 19.0, stroke=node_stroke, stroke_width=1.0)
        c.text(x + 9.0, y + 9.5, var_lbl, font_size=11.5, fill=theme.fg)
        for ci, (lbl, col) in enumerate((cell2, cell3)):
            cx = x + 27.0 + ci * 18.0
            cy = y + 9.5
            if lbl == "dot":
                c.circle(cx, cy, 2.2, fill=col, stroke=col, stroke_width=0.6)
            else:
                c.text(cx, cy, lbl, font_size=11.5, fill=col)

    c.path("M 229 17 C 229 34 156 28 154 44", stroke=lo_col, stroke_width=1.15, dashed="2.8,2.2", arrow_end=True)
    c.path("M 247 17 C 247 34 270 28 270 44", stroke=hi_col, stroke_width=1.15, arrow_end=True)
    c.path("M 190 55 C 190 71 210 66 211 82", stroke=hi_col, stroke_width=1.15, arrow_end=True)
    c.path("M 287 55 C 287 71 218 66 214 82", stroke=lo_col, stroke_width=1.15, dashed="2.8,2.2", arrow_end=True)
    c.text(362.0, 55.0, "(1)", font_size=11.5, fill=theme.fg, anchor="end")
    return c.to_svg()


def build_fig_p285_inline(theme: Theme) -> str:
    c = SvgCanvas(408.0, 118.0, theme)
    edge_col = theme.cyan if theme.is_dark else theme.fg
    up_col = theme.mint if theme.is_dark else theme.fg
    dn_col = theme.coral if theme.is_dark else theme.fg
    node_col = theme.fg
    dx = 44.0
    dy = 28.0
    ox = 22.0
    oy = 16.0

    for y in range(4):
        cy = oy + (3 - y) * dy
        x_start = 2 * y + 1
        for x in range(x_start, 9):
            cx = ox + (x - 1) * dx
            c.text(cx, cy, f"({x}, {y})", font_size=9.5, fill=node_col)
            if x < 8:
                c.line(cx + 15.0, cy, cx + dx - 15.0, cy, stroke=edge_col, stroke_width=1.15, arrow_end=True)
            else:
                c.line(cx + 15.0, cy, cx + 28.0, cy, stroke=edge_col, stroke_width=1.15, arrow_end=True)
                c.text(cx + 36.0, cy, "⋯", font_size=11.0, fill=theme.muted if theme.is_dark else theme.fg)
        if y < 3:
            cy_up = oy + (2 - y) * dy
            for x in range(2 * (y + 1) + 1, 9):
                cx = ox + (x - 1) * dx
                if x % 2 == 1:
                    c.line(cx, cy - 8.5, cx, cy_up + 8.5, stroke=up_col, stroke_width=1.15, arrow_end=True)
                else:
                    c.line(cx, cy_up + 8.5, cx, cy - 8.5, stroke=dn_col, stroke_width=1.15, arrow_end=True)
    return c.to_svg()


BUILDERS: dict[str, Callable[[Theme], str]] = {
    "fig_p217_inline_1": build_fig_p217_inline_1,
    "fig_p285_inline": build_fig_p285_inline,
    "fig_23": build_fig_23,
    "fig_p230_inline": build_fig_p230_inline,
    "fig_24": build_fig_24,
    "fig_25": build_fig_25,
    "fig_p242_inline": build_fig_p242_inline,
    "fig_p246_inline": build_fig_p246_inline,
    "fig_p250_inline_1": build_fig_p250_inline_1,
    "fig_p250_inline_2": build_fig_p250_inline_2,
    "fig_p253_inline": build_fig_p253_inline,
    "fig_26": build_fig_26,
    "fig_27": build_fig_27,
    "fig_p263_inline": build_fig_p263_inline,
    "fig_p265_inline": build_fig_p265_inline,
    "fig_p266_inline_1": build_fig_p266_inline_1,
    "fig_p266_inline_2": build_fig_p266_inline_2,
    "fig_28": build_fig_28,
    "fig_p269_inline_1": build_fig_p269_inline_1,
    "fig_p269_inline_2": build_fig_p269_inline_2,
    "fig_p269_inline_3": build_fig_p269_inline_3,
    "fig_29": build_fig_29,
    "fig_30": build_fig_30,
    "fig_31": build_fig_31,
    "fig_32": build_fig_32,
    "fig_33": build_fig_33,
    "fig_34": build_fig_34,
    "fig_p314_inline_1": build_fig_p314_inline_1,
    "fig_p314_inline_2": build_fig_p314_inline_2,
    "fig_35": build_fig_35,
    "fig_36": build_fig_36,
    "fig_p328_inline": build_fig_p328_inline,
}

BUILDERS_P3: dict[str, Callable[[Theme], str]] = BUILDERS


def render_part(out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for fig_id, fn in BUILDERS.items():
        m, c, p = emit_dual_figure(fig_id, fn, out_dir)
        paths.extend((m, c, p))
    return paths
