from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from pathlib import Path

from .figures_common import SvgCanvas, Theme, emit_dual_figure, fmt, rich_label


def _queen_glyph(cv: SvgCanvas, cx: float, cy: float, cell: float, is_black: bool, theme: Theme) -> None:
    s = cell * 0.36
    pts = [
        (cx - 0.85 * s, cy + 0.82 * s),
        (cx - 0.98 * s, cy - 0.42 * s),
        (cx - 0.45 * s, cy + 0.14 * s),
        (cx, cy - 0.78 * s),
        (cx + 0.45 * s, cy + 0.14 * s),
        (cx + 0.98 * s, cy - 0.42 * s),
        (cx + 0.85 * s, cy + 0.82 * s),
    ]
    if theme.is_dark:
        fill = theme.coral if is_black else "#13233A"
        stroke = theme.coral if is_black else theme.gold
        tip_col = theme.coral if is_black else theme.gold
    else:
        fill = "#0F172A" if is_black else "#FFFFFF"
        stroke = "#0F172A"
        tip_col = "#0F172A"
    cv.polyline(pts, stroke=stroke, stroke_width=0.85, fill=fill, closed=True)
    for tx, ty in ((cx - 0.98 * s, cy - 0.48 * s), (cx, cy - 0.84 * s), (cx + 0.98 * s, cy - 0.48 * s)):
        cv.circle(tx, ty, 0.55, fill=tip_col, stroke="none")


def fig_p686_inline(theme: Theme) -> str:
    w, h = 468.0, 214.0
    cv = SvgCanvas(w, h, theme)
    c1_pos = [(0, 2), (1, 5), (2, 7), (3, 1), (4, 3), (5, 0), (6, 6), (7, 4)]
    boards: list[tuple[str, list[tuple[int, int]], list[tuple[int, int]], bool]] = [
        ("(C0)", [(1, 1), (2, 3), (3, 7), (6, 2), (7, 6)], [], False),
        ("(C2)", [(0, 0), (0, 7), (7, 0), (7, 7)], [], False),
        ("(C4)", [(0, 2), (1, 1), (2, 0), (6, 7), (7, 6)], [], True),
        ("(C6)", [(1, 7), (3, 5), (4, 4), (5, 3), (7, 1)], [], False),
        ("(C8)", [(0, 0), (1, 2), (2, 4), (3, 1), (4, 3)], [(0, 1), (1, 3), (2, 0), (3, 2), (4, 4)], False),
        ("(C1)", c1_pos, [], False),
        ("(C3)", [(0, col) for col in range(8)], [], False),
        (
            "(C5)",
            [(0, 0), (0, 3), (0, 4), (0, 6), (1, 0), (1, 2), (1, 3), (1, 6), (2, 0), (2, 3), (2, 6)],
            [],
            False,
        ),
        ("(C7)", [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 7)], [], False),
        ("(C9)", c1_pos, [(r, 7 - col) for r, col in c1_pos], False),
    ]
    cell = 8.4
    bw = cell * 8.0
    x0, y0 = 18.0, 14.0
    dx, dy = 91.0, 98.0
    grid_col = "#263B59" if theme.is_dark else "#94A3B8"
    border_col = theme.cyan if theme.is_dark else "#0F172A"
    board_bg = "#101827" if theme.is_dark else "#FFFFFF"
    dash_col = theme.gold if theme.is_dark else "#0F172A"
    for idx, (lbl, whites, blacks, has_diamond) in enumerate(boards):
        row = idx // 5
        col = idx % 5
        bx = x0 + col * dx
        by = y0 + row * dy
        cv.rect(bx, by, bw, bw, fill=board_bg, stroke=border_col, stroke_width=1.05)
        for k in range(1, 8):
            cv.line(bx + k * cell, by, bx + k * cell, by + bw, stroke=grid_col, stroke_width=0.55)
            cv.line(bx, by + k * cell, bx + bw, by + k * cell, stroke=grid_col, stroke_width=0.55)
        if has_diamond:
            d_pts = [
                (bx + 4.0 * cell, by),
                (bx + 8.0 * cell, by + 4.0 * cell),
                (bx + 4.0 * cell, by + 8.0 * cell),
                (bx, by + 4.0 * cell),
            ]
            cv.polyline(d_pts, stroke=dash_col, stroke_width=1.1, fill="none", closed=True, dashed="2.4,2.0")
        for r_q, c_q in whites:
            _queen_glyph(cv, bx + (c_q + 0.5) * cell, by + (r_q + 0.5) * cell, cell, False, theme)
        for r_q, c_q in blacks:
            _queen_glyph(cv, bx + (c_q + 0.5) * cell, by + (r_q + 0.5) * cell, cell, True, theme)
        cv.text(bx + 0.5 * bw, by + bw + 12.0, lbl, font_size=9.2, fill=theme.fg)
    return cv.to_svg()


def fig_p691_inline(theme: Theme) -> str:
    w, h = 532.0, 102.0
    cv = SvgCanvas(w, h, theme)
    y_top = 12.0
    y_n1 = 31.0
    y_n2 = 53.0
    y_sk = 75.0
    y_cnt = 91.0
    r = 7.0
    sk_sz = 10.6
    sk_half = sk_sz * 0.5
    dot_col = theme.gold if theme.is_dark else "#0F172A"
    hi_col = theme.hi_stroke
    lo_col = theme.lo_stroke
    lo_dash = "2.6,2.0"
    counts = [1, 3, 3, 2, 3, 2, 3, 3, 3, 3, 2, 3, 2, 3, 3, 1]

    def comp_dot(px: float, py: float) -> None:
        cv.circle(px, py, 2.0, fill=dot_col, stroke="none", glow=True)

    for t in range(16):
        xc = 20.5 + t * 32.7
        base = 15 - t if t >= 8 else t
        top_comp = t >= 8
        has_n1 = base in (1, 2, 3, 4, 6, 7)
        has_n2 = base in (1, 2, 4, 5, 6, 7)
        if base == 0:
            cv.line(xc, y_top, xc, y_sk - sk_half, stroke=hi_col, stroke_width=1.25)
        elif base == 5:
            cv.line(xc, y_top, xc, y_n2 - r, stroke=hi_col, stroke_width=1.25)
        else:
            cv.line(xc, y_top, xc, y_n1 - r, stroke=hi_col, stroke_width=1.25)
        if top_comp:
            comp_dot(xc, y_top + 2.5)

        if base in (1, 2):
            d_lo = (
                f"M {fmt(xc - 0.72 * r)} {fmt(y_n1 + 0.68 * r)} "
                f"Q {fmt(xc - 12.5)} {fmt(0.5 * (y_n1 + y_sk))} {fmt(xc - 3.6)} {fmt(y_sk - sk_half)}"
            )
            cv.path(d_lo, stroke=lo_col, stroke_width=1.2, dashed=lo_dash)
            cv.line(xc, y_n1 + r, xc, y_n2 - r, stroke=hi_col, stroke_width=1.25)
            if base == 2:
                comp_dot(xc, 0.5 * (y_n1 + r + y_n2 - r))
        elif base == 3:
            cv.line(xc - 2.6, y_n1 + r - 0.6, xc - 2.6, y_sk - sk_half, stroke=lo_col, stroke_width=1.2, dashed=lo_dash)
            cv.line(xc + 2.6, y_n1 + r - 0.6, xc + 2.6, y_sk - sk_half, stroke=hi_col, stroke_width=1.25)
            comp_dot(xc + 2.6, y_n1 + r + 7.5)
        elif base in (4, 7):
            cv.line(xc, y_n1 + r, xc, y_n2 - r, stroke=lo_col, stroke_width=1.2, dashed=lo_dash)
            d_hi = (
                f"M {fmt(xc + 0.72 * r)} {fmt(y_n1 + 0.68 * r)} "
                f"Q {fmt(xc + 12.5)} {fmt(0.5 * (y_n1 + y_sk))} {fmt(xc + 3.6)} {fmt(y_sk - sk_half)}"
            )
            cv.path(d_hi, stroke=hi_col, stroke_width=1.25)
            if base == 7:
                comp_dot(xc + 6.9, 0.5 * (y_n1 + y_sk) - 4.0)
        elif base == 6:
            cv.line(xc - 2.5, y_n1 + r - 0.5, xc - 2.5, y_n2 - r + 0.5, stroke=lo_col, stroke_width=1.2, dashed=lo_dash)
            cv.line(xc + 2.5, y_n1 + r - 0.5, xc + 2.5, y_n2 - r + 0.5, stroke=hi_col, stroke_width=1.25)
            comp_dot(xc + 2.5, 0.5 * (y_n1 + y_n2))

        if has_n2:
            cv.line(xc - 2.5, y_n2 + r - 0.5, xc - 2.5, y_sk - sk_half, stroke=lo_col, stroke_width=1.2, dashed=lo_dash)
            cv.line(xc + 2.5, y_n2 + r - 0.5, xc + 2.5, y_sk - sk_half, stroke=hi_col, stroke_width=1.25)
            comp_dot(xc + 2.5, 0.5 * (y_n2 + r + y_sk - sk_half))

        if has_n1:
            cv.bdd_node(xc, y_n1, "1", r=r, font_size=8.4)
        if has_n2:
            cv.bdd_node(
                xc,
                y_n2,
                "2",
                r=r,
                accent=theme.mint if theme.is_dark else None,
                font_size=8.4,
            )
        cv.bdd_sink(xc, y_sk, "⊥", size=sk_sz, is_true=False)
        cv.text(xc, y_cnt, str(counts[t]), font_size=8.6, fill=theme.muted)
    return cv.to_svg()


def _loony_tube(cv: SvgCanvas, d: str, outer_col: str, inner_col: str, w_out: float = 3.5, w_in: float = 1.65) -> None:
    cv.path(d, stroke=outer_col, stroke_width=w_out)
    cv.path(d, stroke=inner_col, stroke_width=w_in)


def _draw_loony_panel(
    cv: SvgCanvas,
    cx: float,
    cy: float,
    step_num: int,
    a_state: int,
    b_state: int,
    theme: Theme,
) -> None:
    sc = 0.72
    wire_out = theme.cyan if theme.is_dark else "#0F172A"
    wire_in = "#142238" if theme.is_dark else "#FFFFFF"
    cord = theme.gold if theme.is_dark else "#64748B"
    cord_hi = "#FFFBEB" if theme.is_dark else "#CBD5E1"
    bg = theme.bg

    def pt(lx: float, ly: float) -> str:
        return f"{fmt(cx + lx * sc)} {fmt(cy + ly * sc)}"

    outer_l = (
        f"M {pt(-22, -46)} L {pt(-76, -46)} "
        f"Q {pt(-86, -46)} {pt(-86, -36)} L {pt(-86, 36)} "
        f"Q {pt(-86, 46)} {pt(-76, 46)} L {pt(-22, 46)}"
    )
    outer_r = (
        f"M {pt(22, -46)} L {pt(76, -46)} "
        f"Q {pt(86, -46)} {pt(86, -36)} L {pt(86, 36)} "
        f"Q {pt(86, 46)} {pt(76, 46)} L {pt(22, 46)}"
    )
    inner_l = (
        f"M {pt(-21, -26)} Q {pt(-31, -26)} {pt(-31, -17)} "
        f"L {pt(-31, 17)} Q {pt(-31, 26)} {pt(-21, 26)}"
    )
    inner_r = (
        f"M {pt(21, -26)} Q {pt(31, -26)} {pt(31, -17)} "
        f"L {pt(31, 17)} Q {pt(31, 26)} {pt(21, 26)}"
    )

    s_top_fall = (
        f"M {pt(-22, -46)} C {pt(-2, -46)} {pt(8, -42)} {pt(24, -33)} "
        f"C {pt(46, -20)} {pt(62, -9)} {pt(80, -9)} L {pt(100, -9)}"
    )
    s_top_rise = (
        f"M {pt(-100, -9)} L {pt(-80, -9)} C {pt(-62, -9)} {pt(-46, -20)} {pt(-24, -33)} "
        f"C {pt(-8, -42)} {pt(2, -46)} {pt(22, -46)}"
    )
    s_bot_rise = (
        f"M {pt(-22, 46)} C {pt(-2, 46)} {pt(8, 42)} {pt(24, 33)} "
        f"C {pt(46, 20)} {pt(62, 9)} {pt(80, 9)} L {pt(100, 9)}"
    )
    s_bot_fall = (
        f"M {pt(-100, 9)} L {pt(-80, 9)} C {pt(-62, 9)} {pt(-46, 20)} {pt(-24, 33)} "
        f"C {pt(-8, 42)} {pt(2, 46)} {pt(22, 46)}"
    )
    s_in_top_fall = (
        f"M {pt(-21, -26)} C {pt(-5, -26)} {pt(6, -21)} {pt(22, -14)} "
        f"C {pt(44, -6)} {pt(64, -4.5)} {pt(80, -4.5)} L {pt(100, -4.5)}"
    )
    s_in_top_rise = (
        f"M {pt(-100, -4.5)} L {pt(-80, -4.5)} C {pt(-64, -4.5)} {pt(-44, -6)} {pt(-22, -14)} "
        f"C {pt(-6, -21)} {pt(5, -26)} {pt(21, -26)}"
    )
    s_in_bot_rise = (
        f"M {pt(-21, 26)} C {pt(-5, 26)} {pt(6, 21)} {pt(22, 14)} "
        f"C {pt(44, 6)} {pt(64, 4.5)} {pt(80, 4.5)} L {pt(100, 4.5)}"
    )
    s_in_bot_fall = (
        f"M {pt(-100, 4.5)} L {pt(-80, 4.5)} C {pt(-64, 4.5)} {pt(-44, 6)} {pt(-22, 14)} "
        f"C {pt(-6, 21)} {pt(5, 26)} {pt(21, 26)}"
    )
    s_mid = f"M {pt(-100, 0)} L {pt(100, 0)}"

    for d_frame in (outer_l, outer_r, inner_l, inner_r):
        _loony_tube(cv, d_frame, wire_out, wire_in)

    comb_over_curves = [
        s_top_rise,
        s_top_fall,
        s_bot_fall,
        s_bot_rise,
        s_in_top_rise,
        s_in_top_fall,
        s_in_bot_fall,
        s_in_bot_rise,
        s_mid,
    ]
    for d_curve in comb_over_curves:
        cv.path(d_curve, stroke=bg, stroke_width=4.8)
        _loony_tube(cv, d_curve, wire_out, wire_in)

    frame_x_patches = [
        f"M {pt(-8, -45.2)} C {pt(-2, -44.2)} {pt(4, -42.5)} {pt(10, -39.8)}",
        f"M {pt(-10, 39.8)} C {pt(-4, 42.5)} {pt(2, 44.2)} {pt(8, 45.2)}",
        f"M {pt(-8, -24.5)} C {pt(-2, -23.0)} {pt(4, -20.8)} {pt(10, -18.5)}",
        f"M {pt(-10, 18.5)} C {pt(-4, 20.8)} {pt(2, 23.0)} {pt(8, 24.5)}",
    ]
    for fp in frame_x_patches:
        cv.path(fp, stroke=bg, stroke_width=4.9)
        _loony_tube(cv, fp, wire_out, wire_in)

    for sx in (-1.0, 1.0):
        bx = cx + sx * 100.0 * sc
        cv.rect(bx - 2.0, cy - 11.5 * sc, 4.0, 23.0 * sc, fill=wire_in, stroke=wire_out, stroke_width=1.15, rx=1.1)

    rx_c = 16.5 * sc
    y_arc = 44.0 * sc
    cord_d = (
        f"M {fmt(cx - rx_c)} {fmt(cy - y_arc)} "
        f"A {fmt(rx_c)} {fmt(rx_c)} 0 0 1 {fmt(cx + rx_c)} {fmt(cy - y_arc)} "
        f"L {fmt(cx + rx_c)} {fmt(cy + y_arc)} "
        f"A {fmt(rx_c)} {fmt(rx_c)} 0 0 1 {fmt(cx - rx_c)} {fmt(cy + y_arc)} Z"
    )
    cv.path(cord_d, stroke=bg, stroke_width=5.8)
    cv.path(cord_d, stroke=cord, stroke_width=3.8, glow=True)
    cv.path(cord_d, stroke=cord_hi, stroke_width=0.85, opacity=0.45)

    left_patches = [
        f"M {pt(-23, -46)} L {pt(-10, -45.7)}",
        f"M {pt(-23, -33.6)} L {pt(-10, -40.8)}",
        f"M {pt(-23, -26)} L {pt(-10, -25.1)}",
        f"M {pt(-23, -14.4)} L {pt(-10, -19.8)}",
        f"M {pt(-23, 0)} L {pt(-10, 0)}",
        f"M {pt(-23, 14.4)} L {pt(-10, 19.8)}",
        f"M {pt(-23, 26)} L {pt(-10, 25.1)}",
        f"M {pt(-23, 33.6)} L {pt(-10, 40.8)}",
        f"M {pt(-23, 46)} L {pt(-10, 45.7)}",
    ]
    right_patches = [
        f"M {pt(10, -45.7)} L {pt(23, -46)}",
        f"M {pt(10, -40.8)} L {pt(23, -33.6)}",
        f"M {pt(10, -25.1)} L {pt(23, -26)}",
        f"M {pt(10, -19.8)} L {pt(23, -14.4)}",
        f"M {pt(10, 0)} L {pt(23, 0)}",
        f"M {pt(10, 19.8)} L {pt(23, 14.4)}",
        f"M {pt(10, 25.1)} L {pt(23, 26)}",
        f"M {pt(10, 40.8)} L {pt(23, 33.6)}",
        f"M {pt(10, 45.7)} L {pt(23, 46)}",
    ]
    l_mask_map = {
        2: [1, 0, 0, 1, 1, 0, 1, 1, 0],
        1: [1, 1, 0, 1, 1, 0, 1, 1, 1],
        0: [1, 1, 0, 0, 1, 1, 1, 0, 0],
    }
    r_mask_map = {
        2: [0, 1, 1, 0, 0, 1, 0, 0, 1],
        1: [1, 1, 1, 0, 0, 1, 0, 0, 0],
        0: [1, 0, 1, 0, 0, 0, 0, 0, 0],
    }
    for flag, seg in zip(l_mask_map[a_state], left_patches):
        if flag:
            cv.path(seg, stroke=bg, stroke_width=5.2)
            _loony_tube(cv, seg, wire_out, wire_in)
    for flag, seg in zip(r_mask_map[b_state], right_patches):
        if flag:
            cv.path(seg, stroke=bg, stroke_width=5.2)
            _loony_tube(cv, seg, wire_out, wire_in)

    lbl_y = cy + 54.0
    cv.text(cx - 64.0, lbl_y, f"Step {step_num}:", font_size=9.4, anchor="start", fill=theme.fg)
    cv.text(
        cx + 64.0,
        lbl_y,
        f"({a_state}, {b_state})",
        font_size=9.4,
        anchor="end",
        fill=theme.gold if theme.is_dark else theme.fg,
    )


def fig_A_1(theme: Theme) -> str:
    w, h = 540.0, 386.0
    cv = SvgCanvas(w, h, theme)
    grid = [
        [(0, 2, 2), (1, 2, 1), (2, 2, 0)],
        [(5, 1, 2), (4, 1, 1), (3, 1, 0)],
        [(6, 0, 2), (7, 0, 1), (8, 0, 0)],
    ]
    col_xs = [96.0, 270.0, 444.0]
    row_ys = [58.0, 182.0, 306.0]
    for r_i, row in enumerate(grid):
        for c_i, (step_n, a_s, b_s) in enumerate(row):
            _draw_loony_panel(cv, col_xs[c_i], row_ys[r_i], step_n, a_s, b_s, theme)
    return cv.to_svg()


def fig_p738_inline(theme: Theme) -> str:
    w, h = 152.0, 128.0
    cv = SvgCanvas(w, h, theme)
    s = 9.0
    nx, ny = 13, 11
    x0, y0 = 17.5, 14.5
    gw, gh = nx * s, ny * s
    g_col = "#283D5C" if theme.is_dark else "#94A3B8"
    cv.rect(x0, y0, gw, gh, fill="#0E1729" if theme.is_dark else "#FFFFFF", stroke=g_col, stroke_width=0.9)
    for ix in range(1, nx):
        cv.line(x0 + ix * s, y0, x0 + ix * s, y0 + gh, stroke=g_col, stroke_width=0.65)
    for iy in range(1, ny):
        cv.line(x0, y0 + iy * s, x0 + gw, y0 + iy * s, stroke=g_col, stroke_width=0.65)
    bits = "011001001000011111101101"
    px, py = 0, 0
    pts = [(x0, y0 + gh)]
    for ch in bits:
        if ch == "0":
            py += 1
        else:
            px += 1
        pts.append((x0 + px * s, y0 + (ny - py) * s))
    p_col = theme.gold if theme.is_dark else "#0F172A"
    d = "M " + " L ".join(f"{fmt(qx)} {fmt(qy)}" for qx, qy in pts)
    cv.path(d, stroke=p_col, stroke_width=2.7, glow=True)
    for ex, ey in (pts[0], pts[-1]):
        cv.circle(ex, ey, 2.3, fill=theme.cyan if theme.is_dark else "#0F172A", stroke="none")
    return cv.to_svg()


def fig_p759_inline(theme: Theme) -> str:
    w, h = 196.0, 38.0
    cv = SvgCanvas(w, h, theme)
    cell = 15.0
    y = 11.5
    cv.domino(16.0, y, 0, 0, vertical=False, cell=cell)
    cv.text(52.5, y + cell * 0.72, ",", font_size=12.5, fill=theme.fg)
    cv.domino(61.0, y, 1, 1, vertical=False, cell=cell)
    cv.text(97.5, y + cell * 0.72, ",", font_size=12.5, fill=theme.fg)
    cv.text(119.0, y + cell * 0.62, "…", font_size=13.0, fill=theme.muted if theme.is_dark else theme.fg)
    cv.text(139.0, y + cell * 0.72, ",", font_size=12.5, fill=theme.fg)
    cv.domino(148.0, y, 6, 6, vertical=False, cell=cell)
    return cv.to_svg()


def fig_p762_inline(theme: Theme) -> str:
    w, h = 268.0, 178.0
    cv = SvgCanvas(w, h, theme)
    cx = 134.0
    y0 = 20.0
    step = 13.4
    half_widths = [8, 7, 7, 4, 4, 4, 4, 2, 2, 1, 1]

    def gpos(gx: int, gy: int) -> tuple[float, float]:
        return cx + gx * step, y0 + gy * step

    rx0, ry0 = gpos(-4, 0)
    rx1, ry1 = gpos(4, 4)
    pad = 6.2
    cv.rect(
        rx0 - pad,
        ry0 - pad,
        (rx1 - rx0) + 2.0 * pad,
        (ry1 - ry0) + 2.0 * pad,
        fill="none",
        stroke=theme.muted,
        stroke_width=1.1,
        dashed="1.5,3.2",
    )

    hooks: list[list[tuple[int, int]]] = [
        [(0, 10), (0, 0), (8, 0)],
        [(-1, 10), (-1, 0), (-8, 0)],
        [(1, 10), (1, 1), (7, 1)],
        [(-2, 8), (-2, 1), (-7, 1)],
        [(2, 8), (2, 2), (7, 2)],
        [(-3, 6), (-3, 2), (-7, 2)],
        [(3, 6), (3, 3), (4, 3)],
        [(-4, 6), (-4, 3)],
        [(4, 6), (4, 4)],
    ]
    pal = (
        [theme.gold, theme.cyan, theme.coral, theme.mint, theme.violet]
        if theme.is_dark
        else ["#0F172A"]
    )
    for hi, hk in enumerate(hooks):
        col = pal[hi % len(pal)]
        cv.polyline([gpos(gx, gy) for gx, gy in hk], stroke=col, stroke_width=1.55)

    dot_stroke = theme.fg if theme.is_dark else "#0F172A"
    for r_i, hw in enumerate(half_widths):
        for gx in range(-hw, hw + 1):
            px, py = gpos(gx, r_i)
            cv.circle(px, py, 2.35, fill=theme.bg, stroke=dot_stroke, stroke_width=1.2)
    return cv.to_svg()


def fig_p763_inline(theme: Theme) -> str:
    w, h = 142.0, 106.0
    cv = SvgCanvas(w, h, theme)
    rows = [(9, True), (8, False), (8, False), (7, True), (5, False), (5, True), (2, True)]
    x0, y0 = 19.0, 17.0
    step = 11.8
    for r_i, (cnt, is_b) in enumerate(rows):
        col = (theme.gold if is_b else theme.cyan) if theme.is_dark else "#0F172A"
        for c_i in range(cnt):
            px = x0 + c_i * step
            py = y0 + r_i * step
            cv.circle(px, py, 2.6, fill=col, stroke="none")
            if is_b and c_i == cnt - 1:
                arm = 5.2
                cv.line(px - arm, py, px + arm, py, stroke=col, stroke_width=1.15)
                cv.line(px, py - arm, px, py + arm, stroke=col, stroke_width=1.15)
    return cv.to_svg()


def fig_p777_inline(theme: Theme) -> str:
    w, h = 532.0, 74.0
    cv = SvgCanvas(w, h, theme)
    parts_15 = [
        [[1, 2, 3, 4]],
        [[1, 2, 3], [4]],
        [[1, 2, 4], [3]],
        [[1, 2], [3, 4]],
        [[1, 2], [3], [4]],
        [[1, 3, 4], [2]],
        [[1, 3], [2, 4]],
        [[1, 3], [2], [4]],
        [[1, 4], [2, 3]],
        [[1], [2, 3, 4]],
        [[1], [2, 3], [4]],
        [[1, 4], [2], [3]],
        [[1], [2, 4], [3]],
        [[1], [2], [3, 4]],
        [[1], [2], [3], [4]],
    ]
    edge_col = theme.cyan if theme.is_dark else "#0F172A"
    dot_col = theme.cyan if theme.is_dark else "#0F172A"
    lbl_col = theme.gold if theme.is_dark else "#0F172A"

    def depth_of(children: dict[int, list[int]], u: int) -> int:
        if not children[u]:
            return 0
        return 1 + max(depth_of(children, v) for v in children[u])

    def assign_x(
        children: dict[int, list[int]],
        xc: float,
        span: float,
        leaf_xs: dict[int, float],
        u: int,
        cur_leaf: list[int],
    ) -> float:
        if not children[u]:
            lx = xc - 0.5 * span + cur_leaf[0] * 7.6
            cur_leaf[0] += 1
            leaf_xs[u] = lx
            return lx
        cxs = [assign_x(children, xc, span, leaf_xs, v, cur_leaf) for v in children[u]]
        val = cxs[0] if len(cxs) == 1 else 0.5 * (cxs[0] + cxs[-1])
        leaf_xs[u] = val
        return val

    def draw_sub(
        children: dict[int, list[int]],
        leaf_xs: dict[int, float],
        leaf_lbl: dict[int, str],
        y_top: float,
        dy: float,
        u: int,
        lv: int,
    ) -> None:
        ux = leaf_xs[u]
        uy = y_top + lv * dy
        for v in children[u]:
            vx = leaf_xs[v]
            vy = y_top + (lv + 1) * dy
            if children[v]:
                cv.line(ux, uy, vx, vy, stroke=edge_col, stroke_width=1.2)
            else:
                dx_e = vx - ux
                dy_e = vy - uy
                ln = math.hypot(dx_e, dy_e) or 1.0
                ex = vx - (dx_e / ln) * 4.8
                ey = vy - (dy_e / ln) * 4.8
                cv.line(ux, uy, ex, ey, stroke=edge_col, stroke_width=1.2)
            draw_sub(children, leaf_xs, leaf_lbl, y_top, dy, v, lv + 1)
        if children[u]:
            cv.circle(ux, uy, 2.0, fill=dot_col, stroke="none")
        else:
            cv.text(ux, uy + 0.5, leaf_lbl[u], font_size=8.4, fill=lbl_col)

    for idx, blocks in enumerate(parts_15):
        children: dict[int, list[int]] = {u: [] for u in range(5)}
        for blk in blocks:
            par = min(blk) - 1
            for m in sorted(blk):
                children[par].append(m)
        leaves = sorted(u for u in range(1, 5) if not children[u])
        leaf_lbl = {old: str(i_l) for i_l, old in enumerate(leaves, 1)}
        max_d = depth_of(children, 0)
        xc = 22.0 + idx * 34.9
        y_top = 13.0
        dy = min(15.0, 44.0 / max(1, max_d))
        leaf_xs: dict[int, float] = {}
        span = (len(leaves) - 1) * 7.6
        assign_x(children, xc, span, leaf_xs, 0, [0])
        draw_sub(children, leaf_xs, leaf_lbl, y_top, dy, 0, 0)
    return cv.to_svg()


def fig_p781_inline(theme: Theme) -> str:
    w, h = 230.0, 224.0
    cv = SvgCanvas(w, h, theme)
    s = 19.0
    x0, y0 = 25.0, 23.0
    grid_col = "#263B59" if theme.is_dark else "#94A3B8"
    step_col = theme.cyan if theme.is_dark else "#0F172A"
    rook_col = theme.gold if theme.is_dark else "#0F172A"
    cell_bg = "#101827" if theme.is_dark else "#FFFFFF"

    for r_i in range(8):
        n_cols = 8 - r_i
        cv.rect(x0, y0 + r_i * s, n_cols * s, s, fill=cell_bg, stroke="none")

    cv.line(x0, y0, x0 + 8 * s, y0, stroke=grid_col, stroke_width=0.9)
    cv.line(x0, y0, x0, y0 + 8 * s, stroke=grid_col, stroke_width=0.9)
    for r_i in range(1, 8):
        cv.line(x0, y0 + r_i * s, x0 + (8 - r_i) * s, y0 + r_i * s, stroke=grid_col, stroke_width=0.75)
    for c_i in range(1, 8):
        cv.line(x0 + c_i * s, y0, x0 + c_i * s, y0 + (8 - c_i) * s, stroke=grid_col, stroke_width=0.75)

    stair_pts: list[tuple[float, float]] = [
        (x0 + (k // 2) * s, y0 + (9 - (k + 1) // 2) * s) for k in range(19)
    ]
    cv.polyline(stair_pts, stroke=step_col, stroke_width=1.85)

    for k, (vx, vy) in enumerate(stair_pts):
        if k == 0:
            ox, oy = -5.2, 2.5
        elif k == 1:
            ox, oy = -5.5, 0.0
        elif k == 17:
            ox, oy = -2.0, -5.8
        elif k == 18:
            ox, oy = 6.8, 0.0
        elif k % 2 == 1:
            ox, oy = -3.8, -3.4
        else:
            ox, oy = 4.6, 5.0
        cv.text(vx + ox, vy + oy, str(k), font_size=6.2, fill=theme.muted)

    for row_lbl in range(1, 10):
        r_i = 9 - row_lbl
        n_cols = row_lbl - 1
        cv.text(
            x0 + n_cols * s + 12.0,
            y0 + (r_i + 0.5) * s,
            str(row_lbl),
            font_size=9.0,
            fill=theme.coral if theme.is_dark else theme.fg,
            bold=True,
        )

    rooks = [(1, 3), (3, 5), (2, 7), (4, 8), (8, 9)]
    for col_1, row_lbl in rooks:
        rx = x0 + (col_1 - 0.5) * s
        ry = y0 + (9 - row_lbl + 0.5) * s
        cv.circle(rx, ry, 3.2, fill=rook_col, stroke="none", glow=True)
    return cv.to_svg()


def fig_p794_inline_1(theme: Theme) -> str:
    w, h = 249.0, 52.0
    cv = SvgCanvas(w, h, theme)
    cell = 15.5
    y = 10.5
    yc = y + cell
    x = 14.0
    groups = [[(1, 2), (2, 4), (3, 6)], [(1, 3), (2, 6)], [(2, 3), (4, 6)]]
    for gi, grp in enumerate(groups):
        for di, (pa, pb) in enumerate(grp):
            cv.domino(x, y, pa, pb, vertical=True, cell=cell)
            x += cell
            if di + 1 < len(grp):
                cv.text(x + 9.0, yc, "≡", font_size=12.5, fill=theme.fg)
                x += 18.0
        if gi + 1 < len(groups):
            cv.text(x + 4.5, y + 2.0 * cell - 2.0, ",", font_size=12.5, fill=theme.fg)
            x += 17.0
        else:
            cv.text(x + 4.5, y + 2.0 * cell - 2.0, ".", font_size=12.5, fill=theme.fg)
    return cv.to_svg()


def fig_p794_inline_2(theme: Theme) -> str:
    w, h = 451.0, 50.0
    cv = SvgCanvas(w, h, theme)
    cell = 14.0
    y = 11.0
    yc = y + cell
    groups = [
        [(2, 1), (1, 5), (4, 2), (5, 3), (6, 3)],
        [(1, 3), (6, 1), (2, 5), (2, 6), (4, 5)],
        [(4, 1), (2, 3), (4, 3), (4, 6), (6, 5)],
    ]
    x = 13.0
    for gi, grp in enumerate(groups):
        for di, (pa, pb) in enumerate(grp):
            cv.domino(x, y, pa, pb, vertical=True, cell=cell)
            x += cell
            if di + 1 < len(grp):
                cv.text(x + 7.2, yc, "+", font_size=11.5, fill=theme.muted if theme.is_dark else theme.fg)
                x += 14.4
        if gi + 1 < len(groups):
            cv.text(x + 10.5, yc, "=", font_size=12.5, fill=theme.gold if theme.is_dark else theme.fg, bold=True)
            x += 21.0
    return cv.to_svg()


def fig_p795_inline(theme: Theme) -> str:
    w, h = 168.0, 168.0
    cv = SvgCanvas(w, h, theme)
    cx, cy, r = 84.0, 84.0, 68.0
    ring_col = "#263B59" if theme.is_dark else "#CBD5E1"
    cv.circle(cx, cy, r, fill="none", stroke=ring_col, stroke_width=1.05)

    p_str = "(())((())((()(()))())(()(())))"
    st: list[tuple[int, int]] = []
    chords: list[tuple[int, int, int]] = []
    for idx, ch in enumerate(p_str, 1):
        if ch == "(":
            st.append((idx, len(st)))
        else:
            u, depth = st.pop()
            chords.append((u, idx, depth))

    pts: dict[int, tuple[float, float]] = {}
    for k in range(1, 31):
        ang = math.radians(90.0 - (k - 1) * 12.0)
        pts[k] = (cx + r * math.cos(ang), cy + r * math.sin(ang))

    pal = (
        [theme.gold, theme.cyan, theme.mint, theme.coral, theme.violet]
        if theme.is_dark
        else ["#0F172A"]
    )
    for u, v, depth in chords:
        ux, uy = pts[u]
        vx, vy = pts[v]
        cv.line(ux, uy, vx, vy, stroke=pal[depth % len(pal)], stroke_width=1.45)

    dot_stroke = theme.fg if theme.is_dark else "#0F172A"
    for k in range(1, 31):
        px, py = pts[k]
        cv.circle(px, py, 2.15, fill=theme.bg, stroke=dot_stroke, stroke_width=1.15)
    return cv.to_svg()


def fig_p796_inline_1(theme: Theme) -> str:
    w, h = 320.0, 134.0
    cv = SvgCanvas(w, h, theme)
    r = 9.0
    pos: dict[str, tuple[float, float]] = {
        "12": (152.0, 22.0),
        "21": (292.0, 22.0),
        "3f": (46.0, 48.0),
        "44": (152.0, 48.0),
        "53": (256.0, 48.0),
        "6a": (106.0, 74.0),
        "78": (168.0, 74.0),
        "85": (214.0, 74.0),
        "ce": (82.0, 99.0),
        "db": (118.0, 99.0),
        "b9": (168.0, 99.0),
        "97": (202.0, 99.0),
        "a6": (226.0, 99.0),
        "ed": (106.0, 121.0),
        "fc": (130.0, 121.0),
    }
    edges = [
        ("12", "3f"),
        ("12", "44"),
        ("12", "53"),
        ("44", "6a"),
        ("44", "78"),
        ("44", "85"),
        ("6a", "ce"),
        ("6a", "db"),
        ("db", "ed"),
        ("db", "fc"),
        ("78", "b9"),
        ("85", "97"),
        ("85", "a6"),
    ]
    edge_col = theme.muted if theme.is_dark else "#0F172A"
    for u, v in edges:
        cv.graph_edge(pos[u][0], pos[u][1], pos[v][0], pos[v][1], r1=r, r2=r, stroke=edge_col, stroke_width=1.25)
    for lbl, (nx, ny) in pos.items():
        is_root = lbl in ("12", "21")
        st_col = (theme.gold if is_root else theme.cyan) if theme.is_dark else "#0F172A"
        cv.graph_node(nx, ny, lbl, r=r, stroke=st_col, font_size=8.2, rich=False)
    return cv.to_svg()


def _draw_ortho_forest(
    cv: SvgCanvas,
    x0: float,
    y0: float,
    step: float,
    nodes: dict[str, tuple[int, int]],
    h_edges: list[tuple[str, str]],
    v_edges: list[tuple[str, str]],
    theme: Theme,
) -> None:
    r = 8.8
    h_col = theme.gold if theme.is_dark else "#0F172A"
    v_col = theme.cyan if theme.is_dark else "#0F172A"
    for u, v in h_edges:
        ru, cu = nodes[u]
        rv, cv_i = nodes[v]
        cv.graph_edge(
            x0 + cu * step,
            y0 + ru * step,
            x0 + cv_i * step,
            y0 + rv * step,
            r1=r,
            r2=r,
            stroke=h_col,
            stroke_width=1.25,
        )
    for u, v in v_edges:
        ru, cu = nodes[u]
        rv, cv_i = nodes[v]
        cv.graph_edge(
            x0 + cu * step,
            y0 + ru * step,
            x0 + cv_i * step,
            y0 + rv * step,
            r1=r,
            r2=r,
            stroke=v_col,
            stroke_width=1.25,
        )
    for lbl, (rn, cn) in nodes.items():
        st_col = (theme.gold if lbl == "12" else theme.cyan) if theme.is_dark else "#0F172A"
        cv.graph_node(x0 + cn * step, y0 + rn * step, lbl, r=r, stroke=st_col, font_size=8.0, rich=False)


def fig_p796_inline_2(theme: Theme) -> str:
    w, h = 396.0, 174.0
    cv = SvgCanvas(w, h, theme)
    step = 26.5
    left_nodes: dict[str, tuple[int, int]] = {
        "12": (0, 0),
        "3f": (0, 1),
        "21": (1, 0),
        "44": (1, 1),
        "6a": (1, 2),
        "ce": (1, 4),
        "53": (2, 1),
        "78": (2, 2),
        "b9": (2, 3),
        "db": (2, 4),
        "ed": (2, 5),
        "85": (3, 2),
        "97": (3, 3),
        "fc": (3, 5),
        "a6": (4, 3),
    }
    h_left = [("12", "3f"), ("44", "6a"), ("6a", "ce"), ("78", "b9"), ("db", "ed"), ("85", "97")]
    v_left = [
        ("12", "21"),
        ("3f", "44"),
        ("44", "53"),
        ("6a", "78"),
        ("78", "85"),
        ("97", "a6"),
        ("ce", "db"),
        ("ed", "fc"),
    ]
    _draw_ortho_forest(cv, 22.0, 34.0, step, left_nodes, h_left, v_left, theme)

    right_nodes: dict[str, tuple[int, int]] = {
        "12": (0, 0),
        "21": (0, 1),
        "3f": (1, 0),
        "44": (1, 1),
        "53": (1, 2),
        "6a": (2, 1),
        "78": (2, 2),
        "85": (2, 3),
        "b9": (3, 2),
        "97": (3, 3),
        "a6": (3, 4),
        "ce": (4, 1),
        "db": (4, 2),
        "ed": (5, 2),
        "fc": (5, 3),
    }
    _draw_ortho_forest(cv, 242.0, 21.0, step, right_nodes, v_left, h_left, theme)
    return cv.to_svg()


def _capsule(
    cv: SvgCanvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    lbl: str,
    lbl_pos: str,
    col: str,
    fill_col: str,
) -> None:
    pad = 4.2
    lx = min(x1, x2) - pad
    ly = min(y1, y2) - pad
    rw = abs(x2 - x1) + 2.0 * pad
    rh = abs(y2 - y1) + 2.0 * pad
    cv.rect(lx, ly, rw, rh, fill=fill_col, stroke=col, stroke_width=0.95, rx=pad)
    if lbl_pos == "bottom":
        cv.text(0.5 * (x1 + x2), max(y1, y2) + 10.5, lbl, font_size=8.4, italic=True, fill=col)
    elif lbl_pos == "right":
        cv.text(max(x1, x2) + 9.0, 0.5 * (y1 + y2), lbl, font_size=8.4, italic=True, fill=col)
    elif lbl_pos == "left":
        cv.text(min(x1, x2) - 9.0, 0.5 * (y1 + y2), lbl, font_size=8.4, italic=True, fill=col)


def fig_p797_inline(theme: Theme) -> str:
    w, h = 540.0, 192.0
    cv = SvgCanvas(w, h, theme)
    c_i = theme.cyan if theme.is_dark else "#64748B"
    c_j = theme.gold if theme.is_dark else "#64748B"
    c_k = theme.coral if theme.is_dark else "#64748B"
    f_i = "#102336" if theme.is_dark else "#F8FAFC"
    f_j = "#262210" if theme.is_dark else "#F8FAFC"
    f_k = "#29151B" if theme.is_dark else "#F8FAFC"
    edge_col = theme.fg if theme.is_dark else "#0F172A"
    dot_col = theme.fg if theme.is_dark else "#0F172A"
    dr = 1.65

    def dot(px: float, py: float) -> None:
        cv.circle(px, py, dr, fill=dot_col, stroke="none")

    def edg(x1: float, y1: float, x2: float, y2: float) -> None:
        cv.line(x1, y1, x2, y2, stroke=edge_col, stroke_width=1.05)

    def f_eq(lx: float, ly: float, transpose: bool) -> None:
        cv.text(lx, ly, "F", font_size=10.2, italic=True)
        if transpose:
            cv.text(lx + 6.0, ly - 3.8, "T", font_size=7.0, italic=True)
            cv.text(lx + 14.5, ly, "=", font_size=10.2)
        else:
            cv.text(lx + 10.5, ly, "=", font_size=10.2)

    f_eq(18.0, 52.0, False)
    x1_c = 70.0
    _capsule(cv, x1_c - 26.0, 26.0, x1_c - 16.0, 26.0, "i", "bottom", c_i, f_i)
    _capsule(cv, x1_c + 16.0, 26.0, x1_c + 26.0, 26.0, "i", "bottom", c_i, f_i)
    _capsule(cv, x1_c, 26.0, x1_c, 48.0, "j", "right", c_j, f_j)
    _capsule(cv, x1_c, 74.0, x1_c + 12.0, 74.0, "i", "bottom", c_i, f_i)
    edg(x1_c, 26.0, x1_c, 60.0)
    for lx in (x1_c - 12.0, x1_c, x1_c + 12.0):
        edg(x1_c, 60.0, lx, 74.0)
        dot(lx, 74.0)
    for rx in (x1_c - 26.0, x1_c - 16.0, x1_c + 16.0, x1_c + 26.0):
        dot(rx, 26.0)
    for ry in (26.0, 37.0, 48.0, 60.0):
        dot(x1_c, ry)
    cv.text(106.0, 56.0, ",", font_size=11.0)

    f_eq(16.0, 140.0, True)
    _capsule(cv, x1_c, 108.0, x1_c, 120.0, "i", "right", c_i, f_i)
    _capsule(cv, x1_c - 11.0, 134.0, x1_c + 11.0, 134.0, "j", "bottom", c_j, f_j)
    _capsule(cv, x1_c - 25.0, 146.0, x1_c - 25.0, 158.0, "i", "right", c_i, f_i)
    _capsule(cv, x1_c + 25.0, 146.0, x1_c + 25.0, 158.0, "i", "right", c_i, f_i)
    edg(x1_c, 108.0, x1_c, 120.0)
    for lx in (x1_c - 25.0, x1_c - 11.0, x1_c, x1_c + 11.0, x1_c + 25.0):
        edg(x1_c, 120.0, lx, 134.0)
        dot(lx, 134.0)
    for sx in (-25.0, 25.0):
        edg(x1_c + sx, 134.0, x1_c + sx, 158.0)
        dot(x1_c + sx, 146.0)
        dot(x1_c + sx, 158.0)
    dot(x1_c, 108.0)
    dot(x1_c, 120.0)
    cv.text(106.0, 142.0, ";", font_size=11.0)

    cv.text(129.0, 98.0, "or", font_size=10.0, fill=theme.muted if theme.is_dark else theme.fg)

    f_eq(154.0, 98.0, False)
    xm = 244.0
    _capsule(cv, xm - 38.0, 16.0, xm - 28.0, 16.0, "i", "bottom", c_i, f_i)
    _capsule(cv, xm + 28.0, 16.0, xm + 38.0, 16.0, "i", "bottom", c_i, f_i)
    _capsule(cv, xm, 16.0, xm, 36.0, "j", "right", c_j, f_j)
    _capsule(cv, xm - 25.0, 58.0, xm - 15.0, 58.0, "i", "bottom", c_i, f_i)
    _capsule(cv, xm + 15.0, 58.0, xm + 25.0, 58.0, "i", "bottom", c_i, f_i)
    _capsule(cv, xm - 38.0, 58.0, xm - 38.0, 78.0, "j", "right", c_j, f_j)
    _capsule(cv, xm + 38.0, 58.0, xm + 38.0, 78.0, "j", "right", c_j, f_j)
    _capsule(cv, xm - 43.0, 102.0, xm - 33.0, 102.0, "i", "bottom", c_i, f_i)
    _capsule(cv, xm + 33.0, 102.0, xm + 43.0, 102.0, "i", "bottom", c_i, f_i)
    _capsule(cv, xm, 58.0, xm, 98.0, "k", "right", c_k, f_k)
    _capsule(cv, xm - 24.0, 126.0, xm - 14.0, 126.0, "i", "bottom", c_i, f_i)
    _capsule(cv, xm + 14.0, 126.0, xm + 24.0, 126.0, "i", "bottom", c_i, f_i)
    _capsule(cv, xm, 146.0, xm, 166.0, "j", "right", c_j, f_j)

    for rx in (xm - 38.0, xm - 28.0, xm - 16.0, xm + 16.0, xm + 28.0, xm + 38.0):
        dot(rx, 16.0)
    edg(xm, 16.0, xm, 46.0)
    for ry in (16.0, 26.0, 36.0, 46.0):
        dot(xm, ry)
    for cx_b in (xm - 38.0, xm - 25.0, xm - 15.0, xm, xm + 15.0, xm + 25.0, xm + 38.0):
        edg(xm, 46.0, cx_b, 58.0)
        dot(cx_b, 58.0)
    for arm_x in (xm - 38.0, xm + 38.0):
        edg(arm_x, 58.0, arm_x, 89.0)
        for ay in (68.0, 78.0, 89.0):
            dot(arm_x, ay)
        for leaf_dx in (-15.0, -5.0, 5.0, 15.0):
            edg(arm_x, 89.0, arm_x + leaf_dx, 102.0)
            dot(arm_x + leaf_dx, 102.0)
    edg(xm, 58.0, xm, 112.0)
    for ky in (68.0, 78.0, 88.0, 98.0, 112.0):
        dot(xm, ky)
    for bx_l in (xm - 35.0, xm - 24.0, xm - 14.0, xm, xm + 14.0, xm + 24.0, xm + 35.0):
        edg(xm, 112.0, bx_l, 126.0)
        dot(bx_l, 126.0)
    edg(xm, 126.0, xm, 166.0)
    for by_j in (136.0, 146.0, 156.0, 166.0):
        dot(xm, by_j)
    cv.text(308.0, 102.0, ",", font_size=11.0)

    f_eq(329.0, 98.0, True)
    xr = 434.0
    _capsule(cv, xr, 22.0, xr, 33.0, "i", "right", c_i, f_i)
    _capsule(cv, xr - 36.0, 58.0, xr - 16.0, 58.0, "j", "bottom", c_j, f_j)
    _capsule(cv, xr + 16.0, 58.0, xr + 36.0, 58.0, "j", "bottom", c_j, f_j)
    _capsule(cv, xr - 49.0, 70.0, xr - 49.0, 81.0, "i", "left", c_i, f_i)
    _capsule(cv, xr + 49.0, 70.0, xr + 49.0, 81.0, "i", "right", c_i, f_i)
    _capsule(cv, xr, 58.0, xr, 69.0, "i", "right", c_i, f_i)
    _capsule(cv, xr - 20.0, 94.0, xr + 20.0, 94.0, "k", "bottom", c_k, f_k)
    _capsule(cv, xr - 36.0, 94.0, xr - 36.0, 105.0, "i", "left", c_i, f_i)
    _capsule(cv, xr + 36.0, 94.0, xr + 36.0, 105.0, "i", "right", c_i, f_i)
    _capsule(cv, xr - 45.0, 130.0, xr - 27.0, 130.0, "j", "bottom", c_j, f_j)
    _capsule(cv, xr + 27.0, 130.0, xr + 45.0, 130.0, "j", "bottom", c_j, f_j)
    _capsule(cv, xr - 15.0, 152.0, xr - 15.0, 163.0, "i", "left", c_i, f_i)
    _capsule(cv, xr + 15.0, 152.0, xr + 15.0, 163.0, "i", "right", c_i, f_i)

    edg(xr, 22.0, xr, 45.0)
    for ry in (22.0, 33.0, 45.0):
        dot(xr, ry)
    for tx in (xr - 49.0, xr - 36.0, xr - 26.0, xr - 16.0, xr, xr + 16.0, xr + 26.0, xr + 36.0, xr + 49.0):
        edg(xr, 45.0, tx, 58.0)
        dot(tx, 58.0)
    for sx in (-49.0, 49.0):
        edg(xr + sx, 58.0, xr + sx, 81.0)
        dot(xr + sx, 70.0)
        dot(xr + sx, 81.0)
    edg(xr, 58.0, xr, 81.0)
    dot(xr, 69.0)
    dot(xr, 81.0)
    for mx in (xr - 36.0, xr - 20.0, xr - 10.0, xr, xr + 10.0, xr + 20.0, xr + 36.0):
        edg(xr, 81.0, mx, 94.0)
        dot(mx, 94.0)
    for sgn in (-1.0, 1.0):
        ax = xr + sgn * 36.0
        edg(ax, 94.0, ax, 117.0)
        dot(ax, 105.0)
        dot(ax, 117.0)
        sub_xs = (
            [xr - 56.0, xr - 45.0, xr - 36.0, xr - 27.0, xr - 15.0]
            if sgn < 0
            else [xr + 15.0, xr + 27.0, xr + 36.0, xr + 45.0, xr + 56.0]
        )
        for lx in sub_xs:
            edg(ax, 117.0, lx, 130.0)
            dot(lx, 130.0)
        ix = xr + sgn * 15.0
        edg(ix, 130.0, ix, 163.0)
        for iy in (141.0, 152.0, 163.0):
            dot(ix, iy)
    cv.text(506.0, 102.0, ".", font_size=11.0)
    return cv.to_svg()


def fig_p800_inline(theme: Theme) -> str:
    w, h = 396.0, 174.0
    cv = SvgCanvas(w, h, theme)
    step = 26.5
    left_nodes: dict[str, tuple[int, int]] = {
        "12": (0, 0),
        "3f": (0, 5),
        "21": (1, 0),
        "44": (1, 1),
        "6a": (1, 3),
        "ce": (1, 5),
        "53": (2, 1),
        "78": (2, 2),
        "b9": (2, 3),
        "db": (2, 4),
        "ed": (2, 5),
        "85": (3, 1),
        "97": (3, 2),
        "fc": (3, 5),
        "a6": (4, 2),
    }
    h_left = [("12", "3f"), ("44", "6a"), ("6a", "ce"), ("78", "b9"), ("85", "97"), ("db", "ed")]
    v_left = [
        ("12", "21"),
        ("44", "53"),
        ("6a", "b9"),
        ("78", "97"),
        ("97", "a6"),
        ("3f", "ce"),
        ("ce", "ed"),
        ("ed", "fc"),
    ]
    _draw_ortho_forest(cv, 22.0, 34.0, step, left_nodes, h_left, v_left, theme)

    right_nodes: dict[str, tuple[int, int]] = {lbl: (5 - c, 4 - r) for lbl, (r, c) in left_nodes.items()}
    _draw_ortho_forest(cv, 242.0, 21.0, step, right_nodes, v_left, h_left, theme)
    return cv.to_svg()


BinSpec = int | tuple["BinSpec", "BinSpec"]


def fig_p812_inline_1(theme: Theme) -> str:
    w, h = 546.0, 78.0
    cv = SvgCanvas(w, h, theme)
    trees: list[BinSpec] = [
        (3, (1, (2, 0))),
        ((1, (2, 0)), 3),
        ((3, 1), (2, 0)),
        ((1, 3), (2, 0)),
        (1, (3, (2, 0))),
        (1, ((2, 0), 3)),
        (1, ((3, 2), 0)),
        (1, ((2, 3), 0)),
        (1, (2, (3, 0))),
        (1, (2, (0, 3))),
    ]
    edge_col = theme.muted if theme.is_dark else "#0F172A"
    int_stroke = theme.cyan if theme.is_dark else "#0F172A"

    def get_bin_h(node: BinSpec) -> int:
        if isinstance(node, int):
            return 0
        return 1 + max(get_bin_h(node[0]), get_bin_h(node[1]))

    def assign_bin(
        node: BinSpec,
        xc: float,
        y0: float,
        dy: float,
    ) -> tuple[list[tuple[float, float, float, float]], list[tuple[float, float, int | None]]]:
        leaves_pos: list[float] = []
        edges_acc: list[tuple[float, float, float, float]] = []
        nodes_acc: list[tuple[float, float, int | None]] = []

        def walk(nd: BinSpec, lv: int) -> tuple[float, float]:
            ny = y0 + lv * dy
            if isinstance(nd, int):
                nx = xc - 16.5 + len(leaves_pos) * 11.0
                leaves_pos.append(nx)
                nodes_acc.append((nx, ny, nd))
                return nx, ny
            lx, ly = walk(nd[0], lv + 1)
            rx, ry = walk(nd[1], lv + 1)
            nx = 0.5 * (lx + rx)
            edges_acc.append((nx, ny, lx, ly))
            edges_acc.append((nx, ny, rx, ry))
            nodes_acc.append((nx, ny, None))
            return nx, ny

        walk(node, 0)
        return edges_acc, nodes_acc

    for ti, tr in enumerate(trees):
        xc = 32.0 + ti * 53.5
        max_h = get_bin_h(tr)
        dy = min(15.5, 46.0 / max(1, max_h))
        e_list, n_list = assign_bin(tr, xc, 14.0, dy)
        for x1, y1, x2, y2 in e_list:
            cv.line(x1, y1, x2, y2, stroke=edge_col, stroke_width=1.05)
        for nx, ny, val in n_list:
            if val is None:
                cv.circle(nx, ny, 2.7, fill=theme.node_fill, stroke=int_stroke, stroke_width=1.15)
            else:
                is_new = val == 3
                sq = 8.8
                st = (theme.gold if is_new else theme.cyan) if theme.is_dark else "#0F172A"
                fl = ("#2B2612" if is_new else theme.node_fill) if theme.is_dark else "#FFFFFF"
                tc = (theme.gold if is_new else theme.fg) if theme.is_dark else "#0F172A"
                cv.rect(nx - sq * 0.5, ny - sq * 0.5, sq, sq, fill=fl, stroke=st, stroke_width=1.05, rx=1.0)
                cv.text(nx, ny + 0.3, str(val), font_size=6.8, fill=tc, bold=is_new)
    return cv.to_svg()


SchroderSpec = None | list["SchroderSpec"]


def fig_p812_inline_2(theme: Theme) -> str:
    w, h = 540.0, 72.0
    cv = SvgCanvas(w, h, theme)
    leaf: SchroderSpec = None
    trees: list[SchroderSpec] = [
        [leaf, leaf, leaf, leaf],
        [leaf, leaf, [leaf, leaf]],
        [leaf, [leaf, [leaf, leaf]]],
        [leaf, [leaf, leaf, leaf]],
        [leaf, [[leaf, leaf], leaf]],
        [leaf, [leaf, leaf], leaf],
        [[leaf, leaf, leaf], leaf],
        [[leaf, [leaf, leaf]], leaf],
        [[[leaf, leaf], leaf], leaf],
        [[leaf, leaf], [leaf, leaf]],
        [[leaf, leaf], leaf, leaf],
    ]
    edge_col = theme.muted if theme.is_dark else "#0F172A"
    int_stroke = theme.cyan if theme.is_dark else "#0F172A"
    leaf_stroke = theme.gold if theme.is_dark else "#0F172A"

    def get_sch_h(nd: SchroderSpec) -> int:
        if nd is None:
            return 0
        return 1 + max(get_sch_h(c) for c in nd)

    def assign_sch(
        root: SchroderSpec,
        xc: float,
        y0: float,
        dy: float,
    ) -> tuple[list[tuple[float, float, float, float]], list[tuple[float, float, bool]]]:
        leaf_i = [0]
        e_list: list[tuple[float, float, float, float]] = []
        n_list: list[tuple[float, float, bool]] = []

        def walk(nd: SchroderSpec, lv: int) -> tuple[float, float]:
            ny = y0 + lv * dy
            if nd is None:
                nx = xc - 13.5 + leaf_i[0] * 9.0
                leaf_i[0] += 1
                n_list.append((nx, ny, True))
                return nx, ny
            ch_pts = [walk(c, lv + 1) for c in nd]
            nx = 0.5 * (ch_pts[0][0] + ch_pts[-1][0])
            for cx_p, cy_p in ch_pts:
                e_list.append((nx, ny, cx_p, cy_p))
            n_list.append((nx, ny, False))
            return nx, ny

        walk(root, 0)
        return e_list, n_list

    for ti, tr in enumerate(trees):
        xc = 26.0 + ti * 48.8
        max_h = get_sch_h(tr)
        dy = min(15.5, 44.0 / max(1, max_h))
        e_list, n_list = assign_sch(tr, xc, 14.0, dy)
        for x1, y1, x2, y2 in e_list:
            cv.line(x1, y1, x2, y2, stroke=edge_col, stroke_width=1.05)
        for nx, ny, is_leaf in n_list:
            if is_leaf:
                sq = 5.0
                cv.rect(nx - sq * 0.5, ny - sq * 0.5, sq, sq, fill=theme.node_fill, stroke=leaf_stroke, stroke_width=1.05)
            else:
                cv.circle(nx, ny, 2.5, fill=theme.node_fill, stroke=int_stroke, stroke_width=1.1)
    return cv.to_svg()


def fig_p817_inline(theme: Theme) -> str:
    w, h = 212.0, 96.0
    cv = SvgCanvas(w, h, theme)
    cv.text(24.0, 48.0, "A′ =", font_size=11.0, italic=True, fill=theme.fg)
    r = 3.2
    v0 = (50.0, 48.0)
    v1 = (84.0, 48.0)
    v2 = (116.0, 48.0)
    v3 = (148.0, 48.0)
    v4 = (190.0, 48.0)
    e_col = theme.cyan if theme.is_dark else "#0F172A"
    l_col = theme.gold if theme.is_dark else "#0F172A"

    cv.graph_edge(v0[0], v0[1], v1[0], v1[1], r1=r, r2=r, stroke=e_col, stroke_width=1.35)
    cv.graph_edge(v1[0], v1[1], v2[0], v2[1], r1=r, r2=r, stroke=e_col, stroke_width=1.35)
    cv.graph_edge(v2[0], v2[1], v3[0], v3[1], r1=r, r2=r, stroke=e_col, stroke_width=1.35)
    cv.graph_edge(v1[0], v1[1], v3[0], v3[1], r1=r, r2=r, curve=-34.0, stroke=e_col, stroke_width=1.35)
    cv.graph_edge(v1[0], v1[1], v3[0], v3[1], r1=r, r2=r, curve=34.0, stroke=e_col, stroke_width=1.35)
    cv.graph_edge(v3[0], v3[1], v4[0], v4[1], r1=r, r2=r, curve=-24.0, stroke=e_col, stroke_width=1.35)
    cv.graph_edge(v3[0], v3[1], v4[0], v4[1], r1=r, r2=r, curve=24.0, stroke=e_col, stroke_width=1.35)

    for vx, vy in (v0, v1, v2, v3, v4):
        cv.circle(vx, vy, r, fill=theme.node_fill, stroke=theme.fg if theme.is_dark else "#0F172A", stroke_width=1.3)

    cv.text(67.0, 40.0, "a", font_size=9.5, italic=True, fill=l_col)
    cv.text(116.0, 19.0, "b", font_size=9.5, italic=True, fill=l_col)
    cv.text(100.0, 40.0, "c", font_size=9.5, italic=True, fill=l_col)
    cv.text(132.0, 40.0, "d", font_size=9.5, italic=True, fill=l_col)
    cv.text(116.0, 76.0, "e", font_size=9.5, italic=True, fill=l_col)
    cv.text(169.0, 27.0, "f", font_size=9.5, italic=True, fill=l_col)
    cv.text(169.0, 69.0, "g", font_size=9.5, italic=True, fill=l_col)
    return cv.to_svg()


def fig_p823_inline(theme: Theme) -> str:
    w, h = 136.0, 152.0
    cv = SvgCanvas(w, h, theme)
    cx = 68.0
    sl = (28.0, 81.0)
    sr = (108.0, 81.0)
    u_ys = [29.0, 55.0, 81.0, 107.0, 133.0]
    arc_col = theme.cyan if theme.is_dark else "#0F172A"
    tri_col = theme.mint if theme.is_dark else "#0F172A"
    sq_col = theme.gold if theme.is_dark else "#0F172A"
    r_u = 3.1
    r_pq = 2.6

    for k, uy in enumerate(u_ys):
        if k == 2:
            cv.line(sl[0], sl[1], sr[0], sr[1], stroke=arc_col, stroke_width=1.25)
        else:
            ctrl_dx = 4.0 if k in (0, 4) else 10.0
            d_l = f"M {fmt(sl[0])} {fmt(sl[1])} Q {fmt(sl[0] + ctrl_dx)} {fmt(uy)} {fmt(cx)} {fmt(uy)}"
            d_r = f"M {fmt(sr[0])} {fmt(sr[1])} Q {fmt(sr[0] - ctrl_dx)} {fmt(uy)} {fmt(cx)} {fmt(uy)}"
            cv.path(d_l, stroke=arc_col, stroke_width=1.2)
            cv.path(d_r, stroke=arc_col, stroke_width=1.2)

    for uy in u_ys:
        px_l, py_t = cx - 8.5, uy - 10.5
        px_r = cx + 8.5
        cv.line(cx, uy, px_l, py_t, stroke=tri_col, stroke_width=1.15)
        cv.line(cx, uy, px_r, py_t, stroke=tri_col, stroke_width=1.15)
        cv.line(px_l, py_t, px_r, py_t, stroke=tri_col, stroke_width=1.15)
        cv.circle(cx, uy, r_u, fill=theme.node_fill, stroke=theme.fg if theme.is_dark else "#0F172A", stroke_width=1.2)
        cv.circle(px_l, py_t, r_pq, fill=theme.node_fill, stroke=theme.fg if theme.is_dark else "#0F172A", stroke_width=1.1)
        cv.circle(px_r, py_t, r_pq, fill=theme.node_fill, stroke=theme.fg if theme.is_dark else "#0F172A", stroke_width=1.1)

    sq = 5.8
    for sx, sy in (sl, sr):
        cv.rect(sx - sq * 0.5, sy - sq * 0.5, sq, sq, fill=sq_col, stroke="none")
    return cv.to_svg()


def _draw_codon_hex(
    cv: SvgCanvas,
    x: float,
    y: float,
    rows_top_to_bot: list[str],
    bar_col: str,
    dot_col: str,
    w_bar: float = 17.0,
    row_dy: float = 4.2,
) -> None:
    for ri, kind in enumerate(rows_top_to_bot):
        ry = y + ri * row_dy
        if kind == "1":
            cv.line(x, ry, x + w_bar, ry, stroke=bar_col, stroke_width=1.85, linecap="butt")
        elif kind == "0":
            seg = 6.6
            cv.line(x, ry, x + seg, ry, stroke=bar_col, stroke_width=1.85, linecap="butt")
            cv.line(x + w_bar - seg, ry, x + w_bar, ry, stroke=bar_col, stroke_width=1.85, linecap="butt")
        else:
            cv.circle(x + 3.6, ry, 0.95, fill=dot_col, stroke="none")
            cv.circle(x + w_bar - 3.6, ry, 0.95, fill=dot_col, stroke="none")


def _draw_nucleotide_tuple(theme: Theme, specs: list[list[str]], bar_col_dark: str) -> str:
    w, h = 152.0, 42.0
    cv = SvgCanvas(w, h, theme)
    bar_col = bar_col_dark if theme.is_dark else "#0F172A"
    dot_col = theme.muted if theme.is_dark else "#475569"
    y0 = 10.5
    cv.text(14.5, 21.0, "(", font_size=17.0, fill=theme.fg)
    x = 22.0
    for idx, sp in enumerate(specs):
        _draw_codon_hex(cv, x, y0, sp, bar_col, dot_col)
        x += 17.0
        if idx + 1 < len(specs):
            cv.text(x + 4.8, 28.5, ",", font_size=12.0, fill=theme.fg)
            x += 11.5
    cv.text(x + 6.5, 21.0, ")", font_size=17.0, fill=theme.fg)
    return cv.to_svg()


def fig_p825_inline_1(theme: Theme) -> str:
    specs = [
        ["d", "d", "d", "d", "1", "1"],
        ["d", "d", "d", "d", "0", "1"],
        ["d", "d", "d", "d", "1", "0"],
        ["d", "d", "d", "d", "0", "0"],
    ]
    return _draw_nucleotide_tuple(theme, specs, theme.cyan)


def fig_p825_inline_2(theme: Theme) -> str:
    specs = [
        ["d", "0", "d", "1", "d", "d"],
        ["d", "1", "d", "0", "d", "d"],
        ["d", "1", "d", "1", "d", "d"],
        ["d", "0", "d", "0", "d", "d"],
    ]
    return _draw_nucleotide_tuple(theme, specs, theme.gold)


def fig_p825_inline_3(theme: Theme) -> str:
    specs = [
        ["0", "d", "0", "d", "d", "d"],
        ["0", "d", "1", "d", "d", "d"],
        ["1", "d", "0", "d", "d", "d"],
        ["1", "d", "1", "d", "d", "d"],
    ]
    return _draw_nucleotide_tuple(theme, specs, theme.coral)


def fig_p825_inline_4(theme: Theme) -> str:
    w, h = 166.0, 42.0
    cv = SvgCanvas(w, h, theme)
    dot_col = theme.muted if theme.is_dark else "#475569"
    y0 = 10.5
    c_hex = theme.mint if theme.is_dark else "#0F172A"
    c_1 = theme.cyan if theme.is_dark else "#0F172A"
    c_2 = theme.gold if theme.is_dark else "#0F172A"
    c_3 = theme.coral if theme.is_dark else "#0F172A"
    _draw_codon_hex(cv, 15.0, y0, ["0", "0", "1", "1", "1", "1"], c_hex, dot_col)
    cv.text(43.5, 21.0, "=", font_size=12.5, fill=theme.fg)
    _draw_codon_hex(cv, 55.0, y0, ["d", "d", "d", "d", "1", "1"], c_1, dot_col)
    cv.text(82.5, 21.0, "+", font_size=12.0, fill=theme.fg)
    _draw_codon_hex(cv, 93.0, y0, ["d", "0", "d", "1", "d", "d"], c_2, dot_col)
    cv.text(120.5, 21.0, "+", font_size=12.0, fill=theme.fg)
    _draw_codon_hex(cv, 131.0, y0, ["0", "d", "1", "d", "d", "d"], c_3, dot_col)
    return cv.to_svg()


def _draw_renaissance_staff(theme: Theme, steps_from_bottom: list[int]) -> str:
    w, h = 92.0, 42.0
    cv = SvgCanvas(w, h, theme)
    y_bot = 31.0
    line_gap = 5.0
    staff_col = theme.muted if theme.is_dark else "#334155"
    note_col = theme.gold if theme.is_dark else "#0F172A"
    for li in range(5):
        ly = y_bot - li * line_gap
        cv.line(12.0, ly, 80.0, ly, stroke=staff_col, stroke_width=0.95)
    for idx, st in enumerate(steps_from_bottom):
        nx = 24.0 + idx * 11.0
        ny = y_bot - st * (line_gap * 0.5)
        outer = [
            (nx, ny - 3.9),
            (nx + 3.2, ny),
            (nx, ny + 3.9),
            (nx - 3.2, ny),
        ]
        inner = [
            (nx - 0.5, ny - 2.1),
            (nx + 1.6, ny + 0.5),
            (nx + 0.5, ny + 2.1),
            (nx - 1.6, ny - 0.5),
        ]
        d = (
            f"M {fmt(outer[0][0])} {fmt(outer[0][1])} "
            f"L {fmt(outer[1][0])} {fmt(outer[1][1])} "
            f"L {fmt(outer[2][0])} {fmt(outer[2][1])} "
            f"L {fmt(outer[3][0])} {fmt(outer[3][1])} Z "
            f"M {fmt(inner[0][0])} {fmt(inner[0][1])} "
            f"L {fmt(inner[3][0])} {fmt(inner[3][1])} "
            f"L {fmt(inner[2][0])} {fmt(inner[2][1])} "
            f"L {fmt(inner[1][0])} {fmt(inner[1][1])} Z"
        )
        cv.add(f'<path d="{d}" fill="{note_col}" fill-rule="evenodd"/>')
    return cv.to_svg()


def fig_p826_inline_1(theme: Theme) -> str:
    return _draw_renaissance_staff(theme, [5, 4, 6, 4, 5])


def fig_p826_inline_2(theme: Theme) -> str:
    return _draw_renaissance_staff(theme, [6, 4, 5, 5, 4])


def fig_p827_inline(theme: Theme) -> str:
    w, h = 136.0, 44.0
    cv = SvgCanvas(w, h, theme)
    x0, y0 = 18.0, 11.0
    cw, ch = 25.0, 22.0
    over = 3.2
    rule_col = theme.cyan if theme.is_dark else "#475569"
    cv.line(x0 - over, y0, x0 + 4 * cw + over, y0, stroke=rule_col, stroke_width=1.05)
    cv.line(x0 - over, y0 + ch, x0 + 4 * cw + over, y0 + ch, stroke=rule_col, stroke_width=1.05)
    for k in range(5):
        vx = x0 + k * cw
        cv.line(vx, y0 - over, vx, y0 + ch + over, stroke=rule_col, stroke_width=1.05)
    letters = [("b", False), ("c", False), ("d", False), ("t", True)]
    for idx, (ch_l, is_rubric) in enumerate(letters):
        col = (
            (theme.coral if is_rubric else theme.fg)
            if theme.is_dark
            else ("#64748B" if is_rubric else "#0F172A")
        )
        cv.text(x0 + (idx + 0.5) * cw, y0 + 0.52 * ch, ch_l, font_size=13.5, fill=col, bold=True)
    return cv.to_svg()


def _alg_h_52() -> list[list[list[int]]]:
    n = 5
    res: list[list[list[int]]] = []
    a = [0] * n
    b = [1] * (n - 1)
    m = 1
    while True:
        groups: dict[int, list[int]] = {}
        for idx, val in enumerate(a, 1):
            groups.setdefault(val, []).append(idx)
        res.append([groups[k] for k in sorted(groups)])
        if a[n - 1] != m:
            a[n - 1] += 1
            continue
        j = n - 2
        while j >= 0 and a[j] == b[j]:
            j -= 1
        if j <= 0:
            break
        a[j] += 1
        m = b[j] + (1 if a[j] == b[j] else 0)
        j += 1
        while j < n - 1:
            a[j] = 0
            b[j] = m
            j += 1
        a[n - 1] = 0
    return res


def _honda_52(elems: list[int]) -> list[list[list[int]]]:
    if not elems:
        return [[]]
    n_elem = elems[-1]
    rest = elems[:-1]
    out: list[list[list[int]]] = []
    for k in range(len(rest) + 1):
        combos = list(itertools.combinations(rest, k))
        combos.sort(key=lambda c: tuple(reversed(c)))
        for comb in combos:
            comb_set = set(comb)
            rem = [x for x in rest if x not in comb_set]
            block_n = sorted([*comb, n_elem])
            for sub in _honda_52(rem):
                out.append(sorted([*sub, block_n], key=lambda b: b[0]))
    return out


def _wallis_52() -> list[list[list[int]]]:
    primes = (1, 2, 3, 4, 5)
    all_divs: list[tuple[int, ...]] = []
    for k in range(len(primes) + 1):
        cs = list(itertools.combinations(primes, k))
        cs.sort(key=lambda c: tuple(reversed(c)))
        all_divs.extend(cs)
    rank = {d: i for i, d in enumerate(all_divs)}

    def factor(rem: tuple[int, ...], max_rank: int) -> list[list[list[int]]]:
        if not rem:
            return [[]]
        rem_divs = [d for d in reversed(all_divs) if len(d) > 0 and rank[d] <= max_rank and set(d).issubset(rem)]
        out: list[list[list[int]]] = []
        for d in rem_divs:
            next_rem = tuple(x for x in rem if x not in d)
            for sub in factor(next_rem, rank[d]):
                out.append([list(d), *sub])
        return out

    raw = factor(primes, len(all_divs) - 1)
    return [sorted([sorted(b) for b in p], key=lambda b: b[0]) for p in raw]


def _draw_genjiko_52(theme: Theme, seq: list[list[list[int]]], right_to_left: bool) -> str:
    w, h = 516.0, 146.0
    cv = SvgCanvas(w, h, theme)
    x0, y0 = 18.0, 14.0
    dx, dy = 38.4, 31.5
    for idx, blocks in enumerate(seq):
        row = idx // 13
        col = idx % 13
        cv.genjiko(
            x0 + col * dx,
            y0 + row * dy,
            blocks,
            n=5,
            w=20.0,
            h=22.0,
            stroke_width=1.35,
            right_to_left=right_to_left,
        )
    return cv.to_svg()


def fig_p829_inline_1(theme: Theme) -> str:
    return _draw_genjiko_52(theme, _alg_h_52(), right_to_left=False)


def fig_p829_inline_2(theme: Theme) -> str:
    return _draw_genjiko_52(theme, _honda_52([1, 2, 3, 4, 5]), right_to_left=True)


def fig_p830_inline(theme: Theme) -> str:
    return _draw_genjiko_52(theme, _wallis_52(), right_to_left=True)


BUILDERS: dict[str, Callable[[Theme], str]] = {
    "fig_p686_inline": fig_p686_inline,
    "fig_p691_inline": fig_p691_inline,
    "fig_A-1": fig_A_1,
    "fig_p738_inline": fig_p738_inline,
    "fig_p759_inline": fig_p759_inline,
    "fig_p762_inline": fig_p762_inline,
    "fig_p763_inline": fig_p763_inline,
    "fig_p777_inline": fig_p777_inline,
    "fig_p781_inline": fig_p781_inline,
    "fig_p794_inline_1": fig_p794_inline_1,
    "fig_p794_inline_2": fig_p794_inline_2,
    "fig_p795_inline": fig_p795_inline,
    "fig_p796_inline_1": fig_p796_inline_1,
    "fig_p796_inline_2": fig_p796_inline_2,
    "fig_p797_inline": fig_p797_inline,
    "fig_p800_inline": fig_p800_inline,
    "fig_p812_inline_1": fig_p812_inline_1,
    "fig_p812_inline_2": fig_p812_inline_2,
    "fig_p817_inline": fig_p817_inline,
    "fig_p823_inline": fig_p823_inline,
    "fig_p825_inline_1": fig_p825_inline_1,
    "fig_p825_inline_2": fig_p825_inline_2,
    "fig_p825_inline_3": fig_p825_inline_3,
    "fig_p825_inline_4": fig_p825_inline_4,
    "fig_p826_inline_1": fig_p826_inline_1,
    "fig_p826_inline_2": fig_p826_inline_2,
    "fig_p827_inline": fig_p827_inline,
    "fig_p829_inline_1": fig_p829_inline_1,
    "fig_p829_inline_2": fig_p829_inline_2,
    "fig_p830_inline": fig_p830_inline,
}

BUILDERS_P8 = BUILDERS

_ = rich_label


def render_part(out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for fig_id, fn in BUILDERS.items():
        m, c, p = emit_dual_figure(fig_id, fn, out_dir)
        paths.extend((m, c, p))
    return paths
