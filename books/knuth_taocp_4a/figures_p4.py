from __future__ import annotations

import math
from collections.abc import Callable
from itertools import combinations, permutations
from pathlib import Path

from .figures_common import SvgCanvas, Theme, emit_dual_figure, fmt, rich_label

_CAMBRIDGE_48 = "032121202121232121202121312121012121312123212123"
_RJW_42A = (
    "tststsststsssststsssstststsstsssstsssststsstsstsssstsstsstss"
    "sstsssstsstsstsssstsssstsssstststsstsstststsssststsstsstssss"
)
_FIG46_E_STEPS = (
    "546576879843897867566476879865897886988732788968879856897867"
    "466576879853897867758798768997547889688798758997762167799857"
    "897886988745788968879856897867327687986489788698876576688943"
    "988776546557788946977867897835879876899724788968879856897867"
    "466576879810897867566476879865897886988743799867897854869887"
    "657668895798468978673276879865897886988754788965977668578978"
    "438798768997657668895498877665215667788945988667567998678978"
    "328798768779649887766543544667788935988776246779985789788698"
    "8745788968879856897867"
)
_FIG46_F_STEPS = (
    "456783242526727826727524274645256463678546747867476587610203"
    "045056070804030208070504303204535053575030580860807030207282"
    "682082862824520234045032060203080320262707270307054043202720"
    "263604065054320167854674786747658763245256272848725276287276"
    "28584387654"
)
_FIG46_H_STEPS = (
    "061065462432415417034568705185085435132130430682345768407487"
    "432402102832857123465738637632138108172174601235462752652102"
    "708706106358012435164154108168768508524780132405304308705765"
    "748741367802138428328768465463763025678102731721765735435265"
    "28145670816"
)


def _wire_tube(cv: SvgCanvas, d: str, outer_col: str, inner_col: str, w_out: float = 5.4, w_in: float = 2.6) -> None:
    cv.path(d, stroke=outer_col, stroke_width=w_out)
    cv.path(d, stroke=inner_col, stroke_width=w_in)


def fig_37(theme: Theme) -> str:
    w, h = 250.0, 178.0
    cv = SvgCanvas(w, h, theme)
    cx, cy = 125.0, 89.0
    wire_out = theme.cyan if theme.is_dark else "#0F172A"
    wire_in = "#142238" if theme.is_dark else "#FFFFFF"
    cord = theme.gold if theme.is_dark else "#475569"
    cord_hi = "#FFFBEB" if theme.is_dark else "#94A3B8"
    bg = theme.bg

    outer_d = (
        f"M {fmt(cx - 58)} {fmt(cy - 8)} "
        f"L {fmt(cx - 98)} {fmt(cy - 8)} "
        f"C {fmt(cx - 110)} {fmt(cy - 8)} {fmt(cx - 110)} {fmt(cy - 60)} {fmt(cx - 72)} {fmt(cy - 60)} "
        f"L {fmt(cx + 72)} {fmt(cy - 60)} "
        f"C {fmt(cx + 110)} {fmt(cy - 60)} {fmt(cx + 110)} {fmt(cy - 8)} {fmt(cx + 98)} {fmt(cy - 8)} "
        f"L {fmt(cx + 58)} {fmt(cy - 8)}"
    )
    outer_bot_d = (
        f"M {fmt(cx - 58)} {fmt(cy + 8)} "
        f"L {fmt(cx - 98)} {fmt(cy + 8)} "
        f"C {fmt(cx - 110)} {fmt(cy + 8)} {fmt(cx - 110)} {fmt(cy + 60)} {fmt(cx - 72)} {fmt(cy + 60)} "
        f"L {fmt(cx + 72)} {fmt(cy + 60)} "
        f"C {fmt(cx + 110)} {fmt(cy + 60)} {fmt(cx + 110)} {fmt(cy + 8)} {fmt(cx + 98)} {fmt(cy + 8)} "
        f"L {fmt(cx + 58)} {fmt(cy + 8)}"
    )
    inner_top_d = (
        f"M {fmt(cx - 42)} {fmt(cy - 3)} "
        f"C {fmt(cx - 42)} {fmt(cy - 40)} {fmt(cx - 32)} {fmt(cy - 42)} {fmt(cx - 12)} {fmt(cy - 42)} "
        f"L {fmt(cx + 12)} {fmt(cy - 42)} "
        f"C {fmt(cx + 32)} {fmt(cy - 42)} {fmt(cx + 42)} {fmt(cy - 40)} {fmt(cx + 42)} {fmt(cy - 3)}"
    )
    inner_bot_d = (
        f"M {fmt(cx - 42)} {fmt(cy + 3)} "
        f"C {fmt(cx - 42)} {fmt(cy + 40)} {fmt(cx - 32)} {fmt(cy + 42)} {fmt(cx - 12)} {fmt(cy + 42)} "
        f"L {fmt(cx + 12)} {fmt(cy + 42)} "
        f"C {fmt(cx + 32)} {fmt(cy + 42)} {fmt(cx + 42)} {fmt(cy + 40)} {fmt(cx + 42)} {fmt(cy + 3)}"
    )
    mid_bars = [
        f"M {fmt(cx - 98)} {fmt(cy - 8)} L {fmt(cx + 98)} {fmt(cy - 8)}",
        f"M {fmt(cx - 98)} {fmt(cy - 2.7)} L {fmt(cx + 98)} {fmt(cy - 2.7)}",
        f"M {fmt(cx - 98)} {fmt(cy + 2.7)} L {fmt(cx + 98)} {fmt(cy + 2.7)}",
        f"M {fmt(cx - 98)} {fmt(cy + 8)} L {fmt(cx + 98)} {fmt(cy + 8)}",
    ]

    _wire_tube(cv, outer_d, wire_out, wire_in)
    _wire_tube(cv, outer_bot_d, wire_out, wire_in)
    _wire_tube(cv, inner_top_d, wire_out, wire_in)
    _wire_tube(cv, inner_bot_d, wire_out, wire_in)
    for bd in mid_bars:
        _wire_tube(cv, bd, wire_out, wire_in, 4.6, 2.1)

    for sx in (-1.0, 1.0):
        bx = cx + sx * 98.0
        cv.rect(bx - 3.5, cy - 11.0, 7.0, 22.0, fill=wire_in, stroke=wire_out, stroke_width=1.5, rx=1.8)
        for oy in (-5.5, 0.0, 5.5):
            cv.line(bx - 2.5, cy + oy, bx + 2.5, cy + oy, stroke=wire_out, stroke_width=1.1)

    rx_c = 21.0
    top_y = cy - 73.0
    bot_y = cy + 73.0
    cord_d = (
        f"M {fmt(cx - rx_c)} {fmt(cy - 52)} "
        f"A {fmt(rx_c)} {fmt(rx_c)} 0 0 1 {fmt(cx + rx_c)} {fmt(cy - 52)} "
        f"L {fmt(cx + rx_c)} {fmt(cy + 52)} "
        f"A {fmt(rx_c)} {fmt(rx_c)} 0 0 1 {fmt(cx - rx_c)} {fmt(cy + 52)} Z"
    )
    cv.path(cord_d, stroke=bg, stroke_width=7.8)
    cv.path(cord_d, stroke=cord, stroke_width=5.0, glow=True)
    cv.path(cord_d, stroke=cord_hi, stroke_width=1.1, opacity=0.45)

    over_patches = [
        (f"M {fmt(cx - 32)} {fmt(cy - 60)} L {fmt(cx - 10)} {fmt(cy - 60)}", 5.4, 2.6),
        (f"M {fmt(cx + 10)} {fmt(cy + 60)} L {fmt(cx + 32)} {fmt(cy + 60)}", 5.4, 2.6),
        (f"M {fmt(cx + 10)} {fmt(cy - 42)} L {fmt(cx + 30)} {fmt(cy - 42)}", 5.4, 2.6),
        (f"M {fmt(cx - 30)} {fmt(cy + 42)} L {fmt(cx - 10)} {fmt(cy + 42)}", 5.4, 2.6),
        (f"M {fmt(cx - 30)} {fmt(cy - 8)} L {fmt(cx - 12)} {fmt(cy - 8)}", 4.6, 2.1),
        (f"M {fmt(cx - 30)} {fmt(cy + 2.7)} L {fmt(cx - 12)} {fmt(cy + 2.7)}", 4.6, 2.1),
        (f"M {fmt(cx + 12)} {fmt(cy - 2.7)} L {fmt(cx + 30)} {fmt(cy - 2.7)}", 4.6, 2.1),
        (f"M {fmt(cx + 12)} {fmt(cy + 8)} L {fmt(cx + 30)} {fmt(cy + 8)}", 4.6, 2.1),
    ]
    for pd, wo, wi in over_patches:
        cv.path(pd, stroke=bg, stroke_width=wo + 2.2)
        _wire_tube(cv, pd, wire_out, wire_in, wo, wi)

    _ = top_y, bot_y
    return cv.to_svg()


def _algo_p_5_cycle() -> list[tuple[int, ...]]:
    a = [1, 2, 3, 4, 5]
    c = [0] * 6
    o = [1] * 6
    out: list[tuple[int, ...]] = []
    while True:
        out.append(tuple(a))
        j = 5
        s = 0
        while True:
            q = c[j] + o[j]
            if q < 0:
                o[j] = -o[j]
                j -= 1
            elif q == j:
                if j == 1:
                    out.append((1, 2, 3, 4, 5))
                    return out
                s += 1
                o[j] = -o[j]
                j -= 1
            else:
                i1 = j - c[j] + s - 1
                i2 = j - q + s - 1
                a[i1], a[i2] = a[i2], a[i1]
                c[j] = q
                break


def _grandsire_5_cycle() -> list[tuple[int, ...]]:
    p1 = lambda p: (p[0], p[2], p[1], p[4], p[3])
    p3 = lambda p: (p[1], p[0], p[2], p[4], p[3])
    p5 = lambda p: (p[1], p[0], p[3], p[2], p[4])
    ps = lambda p: (p[0], p[1], p[2], p[4], p[3])
    leads = {
        "P": [p3, p1, p5, p1, p5, p1, p5, p1, p5, p1],
        "B": [p3, p1, p5, p1, p5, p1, p5, p1, p3, p1],
        "S": [p3, p1, p5, p1, p5, p1, p5, p1, p3, ps],
    }
    cur = (1, 2, 3, 4, 5)
    out = [cur]
    for ch in "PBPBPSPBPBPS":
        for fn in leads[ch]:
            cur = fn(cur)
            out.append(cur)
    return out


def _stedman_5_cycle() -> list[tuple[int, ...]]:
    p1 = lambda p: (p[0], p[2], p[1], p[4], p[3])
    p3 = lambda p: (p[1], p[0], p[2], p[4], p[3])
    p5 = lambda p: (p[1], p[0], p[3], p[2], p[4])
    p345 = lambda p: (p[1], p[0], p[2], p[3], p[4])
    base12 = [p3, p1, p3, p1, p3, p5, p1, p3, p1, p3, p1, p5]
    half60 = (base12 * 5)[:]
    half60[1 * 6 + 5] = p345
    ops = half60 + half60
    ops = ops[9:] + ops[:9]
    cur = (1, 2, 3, 4, 5)
    out = [cur]
    for fn in ops:
        cur = fn(cur)
        out.append(cur)
    return out


def _cambridge_48_states() -> list[tuple[int, ...]]:
    cur = [1, 2, 3, 4, 5]
    out = [tuple(cur)]
    for ch in _CAMBRIDGE_48:
        r = int(ch)
        cur[r], cur[r + 1] = cur[r + 1], cur[r]
        out.append(tuple(cur))
    return out


def _algo_z_5_cycle() -> list[tuple[int, ...]]:
    big_a = [1, 2, 3, 4, 5]
    a = [2, 4, 5, 3]
    c = [0] * 5
    o = [1] * 5

    def step_p() -> tuple[int, int]:
        j = 4
        s = 0
        while True:
            q = c[j] + o[j]
            if q < 0:
                o[j] = -o[j]
                j -= 1
            elif q == j:
                if j == 1:
                    return 1, 0
                s += 1
                o[j] = -o[j]
                j -= 1
            else:
                i1 = j - c[j] + s - 1
                i2 = j - q + s - 1
                a[i1], a[i2] = a[i2], a[i1]
                c[j] = q
                return j, s

    def get_xy() -> tuple[int, int]:
        while True:
            j, s = step_p()
            if j == 2:
                a[s], a[s + 1] = a[s + 1], a[s]
                continue
            if j == 1:
                return 0, 0
            x = a[j - c[j] + s + (1 if o[j] == 1 else 0) - 1]
            y = a[j - c[j] + s - (1 if o[j] == -1 else 0) - 1]
            return x, y

    out: list[tuple[int, ...]] = []
    x, y = get_xy()
    while True:
        out.append(tuple(big_a))
        if big_a[0] == x and big_a[1] == y:
            big_a[2], big_a[3] = big_a[3], big_a[2]
            out.append(tuple(big_a))
            big_a[1], big_a[2] = big_a[2], big_a[1]
            big_a[3], big_a[4] = big_a[4], big_a[3]
            x, y = get_xy()
        else:
            big_a[0], big_a[1] = big_a[1], big_a[0]
            big_a[2], big_a[3] = big_a[3], big_a[2]
            out.append(tuple(big_a))
            big_a[1], big_a[2] = big_a[2], big_a[1]
            big_a[3], big_a[4] = big_a[4], big_a[3]
            if big_a == [1, 2, 3, 4, 5]:
                out.append(tuple(big_a))
                break
    return out


def _draw_bell_strip(
    cv: SvgCanvas,
    states: list[tuple[int, ...]],
    x0: float,
    y0: float,
    dx: float,
    dy: float,
    theme: Theme,
) -> None:
    if theme.is_dark:
        styles = {
            1: (theme.violet, 0.85, False),
            2: (theme.mint, 1.0, False),
            3: (theme.cyan, 1.15, False),
            4: (theme.coral, 1.4, False),
            5: (theme.gold, 2.1, True),
        }
    else:
        styles = {
            1: ("#94A3B8", 0.65, False),
            2: ("#64748B", 0.85, False),
            3: ("#475569", 1.1, False),
            4: ("#334155", 1.45, False),
            5: ("#0F172A", 2.15, False),
        }
    for bell in (1, 2, 3, 4, 5):
        col, sw, gl = styles[bell]
        pts = [f"{fmt(x0 + k * dx)} {fmt(y0 + st.index(bell) * dy)}" for k, st in enumerate(states)]
        d = "M " + " L ".join(pts)
        cv.path(d, stroke=col, stroke_width=sw, glow=gl)


def fig_38(theme: Theme) -> str:
    w, h = 476.0, 232.0
    cv = SvgCanvas(w, h, theme)
    dx = 3.55
    dy = 4.6
    full_w = 120.0 * dx
    x_left = 0.5 * (w - full_w)

    st_a = _cambridge_48_states()
    st_b = _algo_p_5_cycle()
    st_c = _grandsire_5_cycle()
    st_d = _stedman_5_cycle()

    for r in range(5):
        cv.text(x_left - 8, 66.0 + r * dy, str(r + 1), font_size=6.5, fill=theme.muted)

    xa = x_left + 84.0
    _draw_bell_strip(cv, st_a, xa, 14.0, dx, dy, theme)
    cv.text(xa + 48 * dx + 10.0, 14.0 + 2 * dy, "(incomplete)", font_size=8.5, italic=True, anchor="start", fill=theme.muted)
    cv.text(w * 0.5, 47.0, "(a) The Cambridge Forty-Eight.", font_size=9.2)

    _draw_bell_strip(cv, st_b, x_left, 66.0, dx, dy, theme)
    cv.text(w * 0.5, 99.0, "(b) Plain Changes.", font_size=9.2)

    _draw_bell_strip(cv, st_c, x_left, 118.0, dx, dy, theme)
    cv.text(w * 0.5, 151.0, "(c) Grandsire Doubles.", font_size=9.2)

    _draw_bell_strip(cv, st_d, x_left, 170.0, dx, dy, theme)
    cv.text(w * 0.5, 204.0, "(d) Stedman Doubles.", font_size=9.2)
    return cv.to_svg()


def _draw_algo_g_tree(theme: Theme, pruned: bool) -> str:
    w, h = 468.0, 116.0
    cv = SvgCanvas(w, h, theme)
    thick_col = theme.gold if theme.is_dark else "#0F172A"
    thin_col = theme.cyan if theme.is_dark else "#334155"
    dot_col = theme.coral if theme.is_dark else "#0F172A"

    root_x, root_y = w * 0.5, 12.0
    y1, y2, y3, y4 = 34.0, 62.0, 89.0, 105.0
    leaf_xs = [20.0 + i * 18.6 for i in range(24)]

    cv.circle(root_x, root_y, 2.2, fill=thick_col, stroke="none")
    for a in range(4):
        base = a * 6
        x_a = 0.5 * (leaf_xs[base + 2] + leaf_xs[base + 3])
        sw_a = 2.4 if a == 0 else 1.05
        col_a = thick_col if a == 0 else thin_col
        c_ax = 0.55 * root_x + 0.45 * x_a
        cv.path(f"M {fmt(root_x)} {fmt(root_y)} Q {fmt(c_ax)} {fmt(root_y + 3)} {fmt(x_a)} {fmt(y1)}", stroke=col_a, stroke_width=sw_a)
        cv.text(x_a - 5.5, y1 - 3.5, str(a), font_size=7.8, anchor="end")
        if pruned and a == 2:
            cv.circle(x_a, y1, 2.2, fill=dot_col, stroke="none")
            continue
        for b in range(3):
            idx_ab = base + b * 2
            x_ab = 0.5 * (leaf_xs[idx_ab] + leaf_xs[idx_ab + 1])
            sw_b = 2.4 if b == 0 else 1.05
            col_b = thick_col if b == 0 else thin_col
            cx_b = 0.35 * x_a + 0.65 * x_ab
            cv.path(f"M {fmt(x_a)} {fmt(y1)} Q {fmt(cx_b)} {fmt(y1 + 8)} {fmt(x_ab)} {fmt(y2)}", stroke=col_b, stroke_width=sw_b)
            lbl_ab = f"{a}{b}"
            lx_off = -3.5 if b < 2 else 3.5
            anc_ab = "end" if b < 2 else "start"
            cv.text(x_ab + lx_off, y2 - 3.0, lbl_ab, font_size=7.4, anchor=anc_ab)
            if pruned and lbl_ab in ("00", "11"):
                cv.circle(x_ab, y2, 2.2, fill=dot_col, stroke="none")
                continue
            for c in range(2):
                x_leaf = leaf_xs[idx_ab + c]
                lbl_abc = f"{a}{b}{c}"
                sw_c = 2.4 if c == 0 else 1.05
                col_c = thick_col if c == 0 else thin_col
                cx_c = 0.3 * x_ab + 0.7 * x_leaf
                cv.path(f"M {fmt(x_ab)} {fmt(y2)} Q {fmt(cx_c)} {fmt(y2 + 9)} {fmt(x_leaf)} {fmt(y3)}", stroke=col_c, stroke_width=sw_c)
                if pruned and lbl_abc == "121":
                    cv.circle(x_leaf, y3, 2.2, fill=dot_col, stroke="none")
                    cv.text(x_leaf + 3.5, y3 + 1.0, lbl_abc, font_size=7.0, anchor="start")
                else:
                    cv.line(x_leaf, y3, x_leaf, y4, stroke=thick_col, stroke_width=2.3)
                    cv.text(x_leaf - 2.5, y4 - 4.5, lbl_abc, font_size=6.8, anchor="end")
    return cv.to_svg()


def fig_39(theme: Theme) -> str:
    return _draw_algo_g_tree(theme, pruned=False)


def fig_40(theme: Theme) -> str:
    return _draw_algo_g_tree(theme, pruned=True)


def fig_41(theme: Theme) -> str:
    w, h = 456.0, 122.0
    cv = SvgCanvas(w, h, theme)
    edge_col = theme.cyan if theme.is_dark else "#334155"
    node_stroke = theme.cyan if theme.is_dark else "#0F172A"
    rej_stroke = theme.coral if theme.is_dark else "#0F172A"
    acc_stroke = theme.gold if theme.is_dark else "#0F172A"
    acc_fill = theme.sink_true_fill if theme.is_dark else "#FFFFFF"

    ys = [12.0, 36.0, 62.0, 86.0, 108.0]
    root_x = 216.0

    leaves: list[tuple[str, float, str]] = [
        ("1234", 24.0, "sq"),
        ("1243", 50.0, "sq"),
        ("132", 78.0, "c3"),
        ("1342", 104.0, "sq"),
        ("14", 128.0, "c2"),
        ("2", 162.0, "c1"),
        ("3124", 192.0, "sq"),
        ("314", 216.0, "c3"),
        ("3214", 242.0, "sq"),
        ("3241", 268.0, "sq"),
        ("3412", 294.0, "sq"),
        ("3421", 320.0, "sq"),
        ("4123", 348.0, "sq"),
        ("4132", 374.0, "sq"),
        ("4213", 398.0, "sq"),
        ("4231", 420.0, "sq"),
        ("4312", 436.0, "dot4"),
        ("4321", 448.0, "sq"),
    ]

    pos: dict[str, tuple[float, float]] = {"": (root_x, ys[0])}
    for pfx_len in (4, 3, 2, 1):
        groups: dict[str, list[float]] = {}
        for code, x, _ in leaves:
            if len(code) >= pfx_len:
                p = code[:pfx_len]
                groups.setdefault(p, []).append(x)
        for p, xs in groups.items():
            pos[p] = (sum(xs) / len(xs), ys[pfx_len])

    rej_set = {"2", "14", "132", "314", "4312"}
    sq_set = {code for code, _, kind in leaves if kind == "sq"}

    for p, (px, py) in pos.items():
        if not p:
            continue
        par = p[:-1]
        qx, qy = pos[par]
        r2 = 3.8 if p in sq_set else 2.5
        cv.graph_edge(qx, qy, px, py, r1=2.5, r2=r2, stroke=edge_col, stroke_width=1.15)

    cv.circle(root_x, ys[0], 2.5, fill=theme.node_fill, stroke=node_stroke, stroke_width=1.2)
    for p, (px, py) in pos.items():
        if not p:
            continue
        digit = p[-1]
        if p in sq_set:
            cv.rect(px - 3.6, py - 3.6, 7.2, 7.2, fill=acc_fill, stroke=acc_stroke, stroke_width=1.3)
            cv.text(px - 5.5, py, digit, font_size=8.0, anchor="end")
        elif p == "4312":
            cv.circle(px, py, 2.0, fill=rej_stroke if theme.is_dark else "#FFFFFF", stroke=rej_stroke, stroke_width=1.2)
            cv.text(px - 4.0, py, digit, font_size=7.6, anchor="end")
        elif p in rej_set:
            cv.circle(px, py, 2.5, fill=theme.sink_false_fill if theme.is_dark else "#FFFFFF", stroke=rej_stroke, stroke_width=1.25)
            cv.text(px - 4.8, py, digit, font_size=8.0, anchor="end")
        else:
            cv.circle(px, py, 2.5, fill=theme.node_fill, stroke=node_stroke, stroke_width=1.2)
            cv.text(px - 4.8, py - 1.0, digit, font_size=8.0, anchor="end")
    return cv.to_svg()


def fig_42(theme: Theme) -> str:
    w, h = 476.0, 128.0
    cv = SvgCanvas(w, h, theme)
    dx = 3.55
    dy = 4.6
    x_left = 0.5 * (w - 120.0 * dx)

    sig = lambda p: (p[1], p[2], p[3], p[4], p[0])
    tau = lambda p: (p[1], p[0], p[2], p[3], p[4])
    cur = (1, 2, 3, 4, 5)
    st_a = [cur]
    for ch in _RJW_42A:
        cur = sig(cur) if ch == "s" else tau(cur)
        st_a.append(cur)
    st_b = _algo_z_5_cycle()

    _draw_bell_strip(cv, st_a, x_left, 14.0, dx, dy, theme)
    cv.text(w * 0.5, 48.0, "(a) Using only transitions (1 2 3 4 5) and (1 2).", font_size=9.0)

    _draw_bell_strip(cv, st_b, x_left, 68.0, dx, dy, theme)
    cv.text(w * 0.5, 102.0, "(b) Using only transitions (1 2)(3 4), (2 3)(4 5), and (3 4).", font_size=9.0)
    return cv.to_svg()


def fig_43(theme: Theme) -> str:
    w, h = 236.0, 224.0
    cv = SvgCanvas(w, h, theme)
    cx, cy = 118.0, 112.0

    all_p = sorted(permutations((1, 2, 3, 4)))

    def coords_3d(p: tuple[int, ...]) -> tuple[float, float, float]:
        inv = [0.0] * 4
        for pos_i, val in enumerate(p):
            inv[val - 1] = pos_i + 1.0
        u0, u1, u2, u3 = [v - 2.5 for v in inv]
        yy = (-3.0 * u0 - 1.0 * u1 + 1.0 * u2 + 3.0 * u3) / math.sqrt(20.0)
        xx = (-1.0 * u0 + 2.2 * u1 - 2.2 * u2 + 1.0 * u3) / math.sqrt(11.68)
        zz = (1.0 * u0 - 1.0 * u1 - 1.0 * u2 + 1.0 * u3) * 0.5
        ang = 0.24
        xr = xx * math.cos(ang) + zz * math.sin(ang)
        zr = -xx * math.sin(ang) + zz * math.cos(ang)
        tilt = 0.22
        yr = yy * math.cos(tilt) - zr * math.sin(tilt)
        zf = yy * math.sin(tilt) + zr * math.cos(tilt)
        return xr, yr, zf

    pts3 = {p: coords_3d(p) for p in all_p}
    scale = 40.5
    pts2 = {p: (cx + scale * v[0], cy - scale * v[1]) for p, v in pts3.items()}

    a = [1, 2, 3, 4]
    deltas = [int(ch) for ch in "32131231" * 3]
    ham_edges: set[frozenset[tuple[int, ...]]] = set()
    for d in deltas:
        u = tuple(a)
        a[d - 1], a[d] = a[d], a[d - 1]
        v = tuple(a)
        ham_edges.add(frozenset((u, v)))

    all_edges: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    for i, p in enumerate(all_p):
        for d in range(3):
            q = list(p)
            q[d], q[d + 1] = q[d + 1], q[d]
            qt = tuple(q)
            if p < qt:
                all_edges.append((p, qt))

    back_set = {p for p, v in pts3.items() if v[2] < -0.32}

    thin_vis = theme.muted if theme.is_dark else "#475569"
    thin_hid = theme.grid if theme.is_dark else "#94A3B8"
    ham_col = theme.gold if theme.is_dark else "#0F172A"
    ham_hid = theme.cyan if theme.is_dark else "#334155"

    for pass_ham in (False, True):
        for p, q in all_edges:
            is_ham = frozenset((p, q)) in ham_edges
            if is_ham != pass_ham:
                continue
            is_back = (p in back_set) and (q in back_set)
            if not is_back and (p in back_set or q in back_set) and (pts3[p][2] + pts3[q][2]) < -0.55:
                is_back = True
            x1, y1 = pts2[p]
            x2, y2 = pts2[q]
            if is_ham:
                col = ham_hid if is_back else ham_col
                dash: bool | str = "2.2,2.2" if is_back else False
                cv.line(x1, y1, x2, y2, stroke=col, stroke_width=2.5, dashed=dash)
            else:
                col = thin_hid if is_back else thin_vis
                dash = "1.8,2.2" if is_back else False
                cv.line(x1, y1, x2, y2, stroke=col, stroke_width=0.95, dashed=dash)

    for p in all_p:
        x, y = pts2[p]
        is_b = p in back_set
        r = 2.1 if is_b else 2.5
        vcol = theme.cyan if (theme.is_dark and not is_b) else (theme.muted if is_b else "#0F172A")
        cv.circle(x, y, r, fill=vcol, stroke="none")
        dx_lbl = x - cx
        dy_lbl = y - cy
        nrm = math.hypot(dx_lbl, dy_lbl) or 1.0
        ox = x + 10.5 * (dx_lbl / nrm)
        oy = y + 7.5 * (dy_lbl / nrm)
        tcol = theme.muted if is_b else theme.fg
        cv.text(ox, oy, "".join(str(k) for k in p), font_size=7.2, fill=tcol)
    return cv.to_svg()


def fig_44(theme: Theme) -> str:
    w, h = 312.0, 126.0
    cv = SvgCanvas(w, h, theme)

    r_hex = 19.5
    dx_h = math.sqrt(3.0) * r_hex
    x_start = 38.0
    y_top = 40.0
    y_bot = y_top + 1.5 * r_hex

    edge_col = theme.cyan if theme.is_dark else "#1E293B"
    stub_col = theme.violet if theme.is_dark else "#475569"
    node_stroke = theme.gold if theme.is_dark else "#0F172A"
    ghost_col = theme.muted if theme.is_dark else "#64748B"

    top_pairs = [
        ("4312", "4132"),
        ("3214", "3412"),
        ("4231", "4213"),
        ("3421", "3241"),
        ("4123", "4321"),
        ("3142", "3124"),
    ]
    bot_pairs = [
        ("1432", "1234"),
        ("2413", "2431"),
        ("1243", "1423"),
        ("2341", "2143"),
        ("1324", "1342"),
        ("2134", "2314"),
    ]
    top_ghosts = ["1342", "2314", "1234", "2431", "1423", "2143"]
    bot_ghosts = ["4231", "3421", "4123", "3142", "4312", "3214"]

    v_map: dict[tuple[int, int], tuple[float, float]] = {}
    for c in range(7):
        vx = x_start + c * dx_h
        v_map[(0, c * 2)] = (vx, y_top - 0.5 * r_hex)
        v_map[(0, c * 2 + 1)] = (vx, y_top + 0.5 * r_hex)
    for c in range(6):
        mx = x_start + (c + 0.5) * dx_h
        v_map[(0, c * 2 + 100)] = (mx, y_top - r_hex)
        v_map[(1, c * 2 + 100)] = (mx, y_top + r_hex)
        v_map[(2, c * 2 + 100)] = (mx, y_bot + 0.5 * r_hex)
        v_map[(3, c * 2 + 100)] = (mx, y_bot + 1.5 * r_hex)

    segs: list[tuple[float, float, float, float, bool]] = []
    nodes: list[tuple[float, float, str]] = []

    for c in range(6):
        lx = x_start + c * dx_h
        mx = lx + 0.5 * dx_h
        rx = lx + dx_h
        p_tl = (lx, y_top - 0.5 * r_hex)
        p_bl = (lx, y_top + 0.5 * r_hex)
        p_tc = (mx, y_top - r_hex)
        p_bc = (mx, y_top + r_hex)
        p_tr = (rx, y_top - 0.5 * r_hex)
        p_br = (rx, y_top + 0.5 * r_hex)
        segs.extend([
            (p_tl[0], p_tl[1], p_tc[0], p_tc[1], False),
            (p_tc[0], p_tc[1], p_tr[0], p_tr[1], False),
            (p_tl[0], p_tl[1], p_bl[0], p_bl[1], False),
            (p_bl[0], p_bl[1], p_bc[0], p_bc[1], False),
            (p_bc[0], p_bc[1], p_br[0], p_br[1], False),
            (p_tc[0], p_tc[1], p_tc[0], p_tc[1] - 11.0, True),
        ])
        cv.text(p_tc[0], p_tc[1] - 16.5, top_ghosts[c], font_size=6.8, fill=ghost_col)
        nodes.append((p_tl[0], p_tl[1], top_pairs[c][0]))
        nodes.append((p_bl[0], p_bl[1], top_pairs[c][1]))
        nodes.append((p_tc[0], p_tc[1], ""))

    segs.append((x_start, y_top - 0.5 * r_hex, x_start - 11.0, y_top - 0.82 * r_hex, True))
    cv.text(x_start - 13.0, y_top - 0.85 * r_hex, "3142", font_size=6.8, fill=ghost_col, anchor="end")
    rx_end = x_start + 6 * dx_h
    segs.append((rx_end, y_top - 0.5 * r_hex, rx_end, y_top + 0.5 * r_hex, True))
    cv.text(rx_end + 4.0, y_top - 0.5 * r_hex, "4312", font_size=6.8, fill=ghost_col, anchor="start")
    cv.text(rx_end + 4.0, y_top + 0.5 * r_hex, "4132", font_size=6.8, fill=ghost_col, anchor="start")

    x_b0 = x_start + 0.5 * dx_h
    for c in range(6):
        lx = x_b0 + c * dx_h
        mx = lx + 0.5 * dx_h
        rx = lx + dx_h
        p_tl = (lx, y_top + r_hex)
        p_bl = (lx, y_top + 2.0 * r_hex)
        p_tc = (mx, y_top + 0.5 * r_hex)
        p_bc = (mx, y_top + 2.5 * r_hex)
        p_tr = (rx, y_top + r_hex)
        p_br = (rx, y_top + 2.0 * r_hex)
        segs.extend([
            (p_tl[0], p_tl[1], p_tc[0], p_tc[1], False),
            (p_tc[0], p_tc[1], p_tr[0], p_tr[1], False),
            (p_tl[0], p_tl[1], p_bl[0], p_bl[1], False),
            (p_bl[0], p_bl[1], p_bc[0], p_bc[1], False),
            (p_bc[0], p_bc[1], p_br[0], p_br[1], False),
            (p_bc[0], p_bc[1], p_bc[0], p_bc[1] + 11.0, True),
        ])
        cv.text(p_bc[0], p_bc[1] + 16.5, bot_ghosts[c], font_size=6.8, fill=ghost_col)
        nodes.append((p_tl[0], p_tl[1], bot_pairs[c][0]))
        nodes.append((p_bl[0], p_bl[1], bot_pairs[c][1]))
        nodes.append((p_bc[0], p_bc[1], ""))

    segs.append((x_b0, y_top + 2.0 * r_hex, x_b0 - 11.0, y_top + 2.32 * r_hex, True))
    cv.text(x_b0 - 13.0, y_top + 2.35 * r_hex, "2134", font_size=6.8, fill=ghost_col, anchor="end")
    rx_b_end = x_b0 + 6 * dx_h
    segs.append((rx_b_end, y_top + r_hex, rx_b_end, y_top + 2.0 * r_hex, True))
    cv.text(rx_b_end + 4.0, y_top + r_hex, "1432", font_size=6.8, fill=ghost_col, anchor="start")
    cv.text(rx_b_end + 4.0, y_top + 2.0 * r_hex, "1234", font_size=6.8, fill=ghost_col, anchor="start")

    for x1, y1, x2, y2, is_stub in segs:
        cv.line(x1, y1, x2, y2, stroke=stub_col if is_stub else edge_col, stroke_width=1.0 if is_stub else 1.25, dashed="2.2,2.0" if is_stub else False)

    drawn_pts: set[tuple[int, int]] = set()
    for nx, ny, lbl in nodes:
        key = (round(nx * 10), round(ny * 10))
        if key not in drawn_pts:
            drawn_pts.add(key)
            cv.circle(nx, ny, 2.3, fill=theme.node_fill, stroke=node_stroke, stroke_width=1.2)
        if lbl:
            cv.text(nx + 3.8, ny, lbl, font_size=6.5, anchor="start", fill=theme.fg)
    return cv.to_svg()


def fig_45(theme: Theme) -> str:
    board = [
        [29, 24, 19, 14, 49, 44, 39, 34],
        [58, 53, 48, 43, 38, 9, 4, 63],
        [23, 18, 13, 8, 3, 62, 33, 28],
        [52, 47, 42, 37, 32, 27, 22, 57],
        [17, 12, 7, 2, 61, 56, 51, 46],
        [6, 41, 36, 31, 26, 21, 16, 11],
        [35, 30, 1, 60, 55, 50, 45, 40],
        [0, 59, 54, 25, 20, 15, 10, 5],
    ]
    cell = 22.0
    pad = 14.0
    w = 2 * pad + 8 * cell
    h = 2 * pad + 8 * cell
    cv = SvgCanvas(w, h, theme)

    pos_of: dict[int, tuple[float, float]] = {}
    for r in range(8):
        for c in range(8):
            x = pad + c * cell
            y = pad + r * cell
            val = board[r][c]
            pos_of[val] = (x + 0.5 * cell, y + 0.5 * cell)
            if theme.is_dark:
                fill = "#162238" if (r + c) % 2 == 1 else "#0E1626"
                if val == 0:
                    fill = theme.sink_true_fill
                elif val == 63:
                    fill = theme.sink_false_fill
                cv.rect(x, y, cell, cell, fill=fill, stroke=theme.panel_stroke, stroke_width=0.9)
            else:
                cv.rect(x, y, cell, cell, fill="#FFFFFF", stroke="#0F172A", stroke_width=0.9)

    if theme.is_dark:
        for k in range(63):
            x1, y1 = pos_of[k]
            x2, y2 = pos_of[k + 1]
            if math.hypot(x2 - x1, y2 - y1) < 3.0 * cell:
                cv.line(x1, y1, x2, y2, stroke=theme.cyan, stroke_width=0.85, opacity=0.26)

    cv.rect(pad, pad, 8 * cell, 8 * cell, fill="none", stroke=theme.cyan if theme.is_dark else "#0F172A", stroke_width=1.4)
    for r in range(8):
        for c in range(8):
            val = board[r][c]
            cx, cy = pos_of[val]
            tcol = theme.fg
            if theme.is_dark and val == 0:
                tcol = theme.gold
            elif theme.is_dark and val == 63:
                tcol = theme.coral
            cv.text(cx, cy, str(val), font_size=9.5, fill=tcol, bold=val in (0, 63))
    return cv.to_svg()


def fig_p371_paths(theme: Theme) -> str:
    qs = [
        (3, 0, 0, 0), (2, 1, 0, 0), (2, 0, 1, 0), (2, 0, 0, 1),
        (1, 2, 0, 0), (1, 1, 1, 0), (1, 1, 0, 1), (1, 0, 2, 0),
        (1, 0, 1, 1), (1, 0, 0, 2), (0, 3, 0, 0), (0, 2, 1, 0),
        (0, 2, 0, 1), (0, 1, 2, 0), (0, 1, 1, 1), (0, 1, 0, 2),
        (0, 0, 3, 0), (0, 0, 2, 1), (0, 0, 1, 2), (0, 0, 0, 3),
    ]
    w = 104.0
    row_h = 14.5
    top_y = 28.0
    h = top_y + 20 * row_h + 10.0
    cv = SvgCanvas(w, h, theme)

    rule_col = theme.cyan if theme.is_dark else "#0F172A"
    grid_col = theme.panel_stroke if theme.is_dark else "#CBD5E1"
    path_col = theme.gold if theme.is_dark else "#0F172A"

    cv.line(8.0, 8.0, w - 8.0, 8.0, stroke=rule_col, stroke_width=1.0)
    for j, sub in enumerate(("q_3", "q_2", "q_1", "q_0")):
        cv.text(12.2 + j * 11.5, 16.5, sub, font_size=8.0, anchor="start", italic=True, rich=True)
    cv.text(79.0, 16.5, "path", font_size=8.0)
    cv.line(8.0, 24.0, w - 8.0, 24.0, stroke=rule_col, stroke_width=0.9)

    g_cell = 3.3
    for ri, q in enumerate(qs):
        yc = top_y + ri * row_h + 6.0
        for j in range(4):
            cv.text(16.0 + j * 11.5, yc, str(q[j]), font_size=8.2)
        gx = 74.0
        gy = yc + 1.5 * g_cell
        for k in range(4):
            cv.line(gx, gy - k * g_cell, gx + 3 * g_cell, gy - k * g_cell, stroke=grid_col, stroke_width=0.55)
            cv.line(gx + k * g_cell, gy, gx + k * g_cell, gy - 3 * g_cell, stroke=grid_col, stroke_width=0.55)
        px, py = 0, 0
        pts = [(gx, gy)]
        for step_i in range(4):
            if q[step_i] > 0:
                py += q[step_i]
                pts.append((gx + px * g_cell, gy - py * g_cell))
            if step_i < 3:
                px += 1
                pts.append((gx + px * g_cell, gy - py * g_cell))
        cv.polyline(pts, stroke=path_col, stroke_width=1.55)

    cv.line(8.0, h - 6.0, w - 8.0, h - 6.0, stroke=rule_col, stroke_width=1.0)
    return cv.to_svg()


def fig_p374_inline_1(theme: Theme) -> str:
    w, h = 290.0, 74.0
    cv = SvgCanvas(w, h, theme)
    edge_col = theme.cyan if theme.is_dark else "#1E293B"
    node_stroke = theme.gold if theme.is_dark else "#0F172A"

    cv.text(16.0, 38.0, "T_0 =", font_size=11.0, anchor="start", italic=True, rich=True)
    cv.circle(52.0, 38.0, 3.0, fill=theme.node_fill, stroke=node_stroke, stroke_width=1.3)
    cv.text(60.0, 40.0, ",", font_size=11.0)

    cv.text(104.0, 38.0, "T_n =", font_size=11.0, anchor="start", italic=True, rich=True)
    rx, ry = 198.0, 14.0
    cxs = [148.0, 178.0, 212.0, 250.0]
    cy_bot = 52.0
    elbls = [("0", -5.0), ("1", -4.0), ("", 0.0), ("n − 1", 14.0)]
    blbls = [("T_0", -5.5), ("T_1", -5.5), (". . .", 0.0), ("T_{n-1}", -10.5)]

    for i, cx_i in enumerate(cxs):
        if i != 2:
            cv.graph_edge(rx, ry, cx_i, cy_bot - 6.0, r1=3.0, r2=0.0, stroke=edge_col, stroke_width=1.2)
            mx = 0.5 * (rx + cx_i) + elbls[i][1]
            my = 0.5 * (ry + cy_bot - 6.0) - 2.0
            cv.text(mx, my, elbls[i][0], font_size=8.5)
            cv.text(cx_i + blbls[i][1], cy_bot + 3.0, blbls[i][0], font_size=10.5, anchor="start", italic=True, rich=True)
        else:
            cv.text(cx_i, cy_bot + 3.0, blbls[i][0], font_size=10.5)

    cv.circle(rx, ry, 3.0, fill=theme.node_fill, stroke=node_stroke, stroke_width=1.3)
    cv.text(272.0, 40.0, ".", font_size=11.0)
    return cv.to_svg()


def _t4_layout() -> tuple[dict[str, tuple[float, float]], list[tuple[str, str, str]]]:
    pos = {
        "0000": (146.0, 14.0),
        "0001": (36.0, 40.0),
        "0010": (86.0, 40.0),
        "0100": (152.0, 40.0),
        "1000": (236.0, 40.0),
        "0011": (86.0, 68.0),
        "0101": (128.0, 68.0),
        "0110": (172.0, 68.0),
        "1001": (204.0, 68.0),
        "1010": (236.0, 68.0),
        "1100": (272.0, 68.0),
        "0111": (172.0, 96.0),
        "1011": (236.0, 96.0),
        "1101": (258.0, 96.0),
        "1110": (288.0, 96.0),
        "1111": (288.0, 124.0),
    }
    edges = [
        ("0000", "0001", "0"),
        ("0000", "0010", "1"),
        ("0000", "0100", "2"),
        ("0000", "1000", "3"),
        ("0010", "0011", "0"),
        ("0100", "0101", "0"),
        ("0100", "0110", "1"),
        ("0110", "0111", "0"),
        ("1000", "1001", "0"),
        ("1000", "1010", "1"),
        ("1000", "1100", "2"),
        ("1010", "1011", "0"),
        ("1100", "1101", "0"),
        ("1100", "1110", "1"),
        ("1110", "1111", "0"),
    ]
    return pos, edges


def fig_p374_inline_2(theme: Theme) -> str:
    w, h = 316.0, 138.0
    cv = SvgCanvas(w, h, theme)
    pos, edges = _t4_layout()
    edge_col = theme.cyan if theme.is_dark else "#1E293B"
    node_stroke = theme.gold if theme.is_dark else "#0F172A"

    for u, v, lbl in edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        cv.graph_edge(x1, y1, x2, y2, r1=2.8, r2=2.8, stroke=edge_col, stroke_width=1.2)
        mx = 0.5 * (x1 + x2)
        my = 0.5 * (y1 + y2)
        off_x = -5.5 if x2 <= x1 else 5.5
        cv.text(mx + off_x, my - 1.5, lbl, font_size=7.8, fill=theme.muted if theme.is_dark else theme.fg)

    for nx, ny in pos.values():
        cv.circle(nx, ny, 2.8, fill=theme.node_fill, stroke=node_stroke, stroke_width=1.25)
    return cv.to_svg()


def fig_p378_inline(theme: Theme) -> str:
    w, h = 166.0, 108.0
    cv = SvgCanvas(w, h, theme)
    kx0, ky0 = 18.0, 44.0
    kw, kh = 19.0, 52.0

    key_stroke = theme.cyan if theme.is_dark else "#0F172A"
    pressed = {1, 2, 4}
    for i in range(6):
        kx = kx0 + i * kw
        if theme.is_dark:
            kfill = theme.sink_true_fill if i in pressed else "#131D31"
        else:
            kfill = "#F1F5F9" if i in pressed else "#FFFFFF"
        cv.rect(kx, ky0, kw, kh, fill=kfill, stroke=key_stroke, stroke_width=1.2, rx=1.8)
        if i in pressed:
            dot_col = theme.gold if theme.is_dark else "#94A3B8"
            cv.circle(kx + 0.5 * kw, ky0 + kh - 8.0, 2.2, fill=dot_col, stroke="none")

    hand_stroke = theme.gold if theme.is_dark else "#0F172A"
    hand_fill = "#1D283A" if theme.is_dark else "#FFFFFF"

    f1x = kx0 + 1.5 * kw
    f2x = kx0 + 2.5 * kw
    f3x = kx0 + 4.5 * kw
    f0x = kx0 + 0.55 * kw
    f4x = kx0 + 5.35 * kw

    hand_d = (
        f"M {fmt(f1x - 14)} 10 "
        f"C {fmt(f0x - 6)} 18 {fmt(f0x - 6)} 30 {fmt(f0x - 2)} 38 "
        f"C {fmt(f0x + 1)} 43 {fmt(f0x + 6)} 42 {fmt(f0x + 7)} 35 "
        f"L {fmt(f1x - 5)} 28 "
        f"L {fmt(f1x - 4)} 65 "
        f"C {fmt(f1x - 4)} 71 {fmt(f1x + 4)} 71 {fmt(f1x + 4)} 65 "
        f"L {fmt(f1x + 5)} 31 "
        f"L {fmt(f2x - 4)} 31 "
        f"L {fmt(f2x - 4)} 68 "
        f"C {fmt(f2x - 4)} 74 {fmt(f2x + 4)} 74 {fmt(f2x + 4)} 68 "
        f"L {fmt(f2x + 5)} 30 "
        f"C {fmt(f2x + 9)} 36 {fmt(f2x + 15)} 36 {fmt(f2x + 17)} 29 "
        f"L {fmt(f3x - 4)} 30 "
        f"L {fmt(f3x - 4)} 63 "
        f"C {fmt(f3x - 4)} 69 {fmt(f3x + 4)} 69 {fmt(f3x + 4)} 63 "
        f"L {fmt(f3x + 5)} 31 "
        f"C {fmt(f4x - 2)} 37 {fmt(f4x + 5)} 37 {fmt(f4x + 5)} 29 "
        f"C {fmt(f4x + 6)} 20 {fmt(f3x + 10)} 13 {fmt(f2x + 18)} 10 Z"
    )
    cv.path(hand_d, stroke=hand_stroke, stroke_width=1.45, fill=hand_fill)
    for fx, fy in ((f1x, 65.0), (f2x, 68.0), (f3x, 63.0)):
        cv.path(f"M {fmt(fx - 2.3)} {fmt(fy - 1)} A 2.3 2.3 0 0 0 {fmt(fx + 2.3)} {fmt(fy - 1)}", stroke=hand_stroke, stroke_width=0.9)
    return cv.to_svg()


def _gamma_st(s: int, t: int) -> list[str]:
    if s == 0:
        return ["1" * t]
    if t == 0:
        return ["0" * s]
    return ["0" + x for x in _gamma_st(s - 1, t)] + ["1" + x for x in reversed(_gamma_st(s, t - 1))]


def _k_st(s: int, t: int) -> list[str]:
    if t < 0:
        return []
    if s == 0:
        return ["1" * t]
    if t == 0:
        return ["0" * s]
    return (
        ["0" + x for x in _k_st(s - 1, t)]
        + ["10" + x for x in reversed(_k_st(s - 1, t - 1))]
        + ["11" + x for x in _k_st(s, t - 2)]
    )


def _chase_st(s: int, t: int) -> list[str]:
    n = s + t
    a = [0] * s + [1] * t
    w = [1] * (n + 1)
    r = s if s > 0 else t
    out: list[str] = []
    while True:
        out.append("".join(str(a[i]) for i in range(n - 1, -1, -1)))
        j = r
        while w[j] == 0:
            w[j] = 1
            j += 1
        if j == n:
            return out
        w[j] = 0
        if (j % 2 == 1) and a[j] != 0:
            a[j - 1], a[j] = 1, 0
            if r == j and j > 1:
                r = j - 1
            elif r == j - 1:
                r = j
        elif (j % 2 == 0) and a[j] != 0:
            if a[j - 2] != 0:
                a[j - 1], a[j] = 1, 0
                if r == j and j > 1:
                    r = j - 1
                elif r == j - 1:
                    r = j
            else:
                a[j - 2], a[j] = 1, 0
                if r == j:
                    r = max(j - 2, 1)
                elif r == j - 2:
                    r = j - 1
        elif (j % 2 == 0) and a[j] == 0:
            a[j], a[j - 1] = 1, 0
            if r == j and j > 1:
                r = j - 1
            elif r == j - 1:
                r = j
        else:
            if a[j - 1] != 0:
                a[j], a[j - 1] = 1, 0
                if r == j and j > 1:
                    r = j - 1
                elif r == j - 1:
                    r = j
            else:
                a[j], a[j - 2] = 1, 0
                if r == j - 2:
                    r = j
                elif r == j - 1:
                    r = j - 2


def _ruskey_w(s: int, t: int) -> list[str]:
    n = s + t
    bits = (1 << t) - 1
    out: list[str] = []
    while True:
        out.append(f"{bits:0{n}b}")
        r0 = bits & (bits + 1)
        r1 = r0 ^ (r0 - 1)
        r0 = r1 + 1
        r1 = r1 & bits
        r0 = max(0, (r0 & bits) - 1)
        bits = bits + r1 - r0
        if (bits >> n) & 1:
            return out


def _decode_e_55() -> list[str]:
    cur = list("0000011111")
    out = ["".join(cur)]
    for i in range(0, len(_FIG46_E_STEPS), 2):
        src = int(_FIG46_E_STEPS[i])
        dst = int(_FIG46_E_STEPS[i + 1])
        cur[src], cur[dst] = "0", "1"
        out.append("".join(cur))
    return out


def _decode_f_55() -> list[str]:
    cur = list("1111100000")
    out = ["".join(cur)]
    for ch in _FIG46_F_STEPS:
        p = int(ch)
        cur[p], cur[p + 1] = cur[p + 1], cur[p]
        out.append("".join(cur))
    return out


def _decode_h_55() -> list[str]:
    cur = list("0000011111")
    out = ["".join(cur)]
    for ch in _FIG46_H_STEPS:
        p = int(ch)
        cur[p], cur[9] = cur[9], cur[p]
        out.append("".join(cur))
    return out


def fig_46(theme: Theme) -> str:
    w, h = 396.0, 560.0
    cv = SvgCanvas(w, h, theme)

    seq_a = sorted(["".join("1" if b in c else "0" for b in range(9, -1, -1)) for c in combinations(range(10), 5)])
    seqs = [
        ("(a)", seq_a),
        ("(b)", _gamma_st(5, 5)),
        ("(c)", _k_st(5, 5)),
        ("(d)", _chase_st(5, 5)),
        ("(e)", _decode_e_55()),
        ("(f)", _decode_f_55()),
        ("(g)", _ruskey_w(5, 5)),
        ("(h)", _decode_h_55()),
    ]

    y_top = 18.0
    row_h = 2.02
    body_h = 252.0 * row_h
    ext = 4.5
    col_w = 34.0
    col_gap = 13.0
    x_start = 0.5 * (w - (8 * col_w + 7 * col_gap))
    bit_w = col_w / 10.0

    track_col = theme.panel_stroke if theme.is_dark else "#64748B"
    palette = (
        [theme.cyan, theme.cyan, theme.mint, theme.mint, theme.gold, theme.gold, theme.coral, theme.coral, theme.violet, theme.violet]
        if theme.is_dark
        else ["#0F172A"] * 10
    )

    for ci, (lbl, seq) in enumerate(seqs):
        cx0 = x_start + ci * (col_w + col_gap)
        for b in range(11):
            bx = cx0 + b * bit_w
            cv.line(bx, y_top - ext, bx, y_top + body_h + ext, stroke=track_col, stroke_width=0.45)

        for b in range(10):
            bx = cx0 + b * bit_w
            col = palette[b]
            segs_d: list[str] = []
            r = 0
            while r < 252:
                if seq[r][b] == "1":
                    r0 = r
                    while r < 252 and seq[r][b] == "1":
                        r += 1
                    ya = y_top + r0 * row_h
                    yb = y_top + r * row_h
                    segs_d.append(f"M {fmt(bx + 0.15)} {fmt(ya)} H {fmt(bx + bit_w - 0.15)} V {fmt(yb)} H {fmt(bx + 0.15)} Z")
                else:
                    r += 1
            if segs_d:
                cv.path(" ".join(segs_d), stroke="none", fill=col)

        cv.text(cx0 + 0.5 * col_w, y_top + body_h + 15.0, lbl, font_size=9.2)
    return cv.to_svg()


def _binom_real(x: float, k: int) -> float:
    res = 1.0
    for j in range(1, k + 1):
        res *= (x - k + j) / j
    return res


def _kruskal_5(n: int) -> int:
    if n == 0:
        return 0
    rem = n
    tot = 0
    for k in range(5, 0, -1):
        m = k - 1
        while math.comb(m + 1, k) <= rem:
            m += 1
        rem -= math.comb(m, k)
        tot += math.comb(m, k - 1)
    return tot


def fig_47(theme: Theme) -> str:
    w, h = 420.0, 146.0
    cv = SvgCanvas(w, h, theme)
    grid_col = theme.panel_stroke if theme.is_dark else "#CBD5E1"
    axis_col = theme.muted if theme.is_dark else "#334155"
    main_col = theme.cyan if theme.is_dark else "#0F172A"
    sub_col = theme.gold if theme.is_dark else "#64748B"

    lx0, ly0, lw, lh = 34.0, 26.0, 152.0, 88.0
    cv.rect(lx0, ly0, lw, lh, fill=theme.panel if theme.is_dark else "none", stroke=axis_col, stroke_width=0.9)
    cv.text(lx0 + 0.5 * lw - 19.0, 13.0, "κ_5 N − N", font_size=9.5, anchor="start", italic=True, rich=True)

    for yv in (0, 7, 14, 22):
        yy = ly0 + lh - (yv / 22.0) * lh
        if 0 < yv < 22:
            cv.line(lx0, yy, lx0 + lw, yy, stroke=grid_col, stroke_width=0.6)
        cv.text(lx0 - 5.0, yy, str(yv), font_size=7.6, anchor="end", fill=theme.muted)

    xticks_l = [
        (0, "0"),
        (21, "(7/5)"),
        (56, "(8/5)"),
        (91, "(8/5)+(7/4)"),
        (126, "(9/5)"),
    ]
    for xv, _ in xticks_l:
        xx = lx0 + (xv / 126.0) * lw
        if 0 < xv < 126:
            cv.line(xx, ly0, xx, ly0 + lh, stroke=grid_col, stroke_width=0.6)

    cv.text(lx0, ly0 + lh + 12.0, "0", font_size=7.6, fill=theme.muted)
    for xv, top_n, bot_n in [(21, "7", "5"), (56, "8", "5"), (126, "9", "5")]:
        xx = lx0 + (xv / 126.0) * lw
        cv.text(xx, ly0 + lh + 9.0, top_n, font_size=6.2, fill=theme.muted)
        cv.text(xx, ly0 + lh + 15.5, bot_n, font_size=6.2, fill=theme.muted)
        cv.text(xx - 4.2, ly0 + lh + 12.0, "(", font_size=10.0, fill=theme.muted)
        cv.text(xx + 4.2, ly0 + lh + 12.0, ")", font_size=10.0, fill=theme.muted)
    xx91 = lx0 + (91 / 126.0) * lw
    cv.text(xx91 - 8.5, ly0 + lh + 9.0, "8", font_size=6.0, fill=theme.muted)
    cv.text(xx91 - 8.5, ly0 + lh + 15.5, "5", font_size=6.0, fill=theme.muted)
    cv.text(xx91 - 12.3, ly0 + lh + 12.0, "(", font_size=9.5, fill=theme.muted)
    cv.text(xx91 - 4.7, ly0 + lh + 12.0, ")", font_size=9.5, fill=theme.muted)
    cv.text(xx91, ly0 + lh + 12.2, "+", font_size=6.8, fill=theme.muted)
    cv.text(xx91 + 8.5, ly0 + lh + 9.0, "7", font_size=6.0, fill=theme.muted)
    cv.text(xx91 + 8.5, ly0 + lh + 15.5, "4", font_size=6.0, fill=theme.muted)
    cv.text(xx91 + 4.7, ly0 + lh + 12.0, "(", font_size=9.5, fill=theme.muted)
    cv.text(xx91 + 12.3, ly0 + lh + 12.0, ")", font_size=9.5, fill=theme.muted)

    low_pts: list[tuple[float, float]] = []
    for i in range(121):
        xr = 4.0 + 5.0 * i / 120.0
        nv = _binom_real(xr, 5)
        kv = _binom_real(xr, 4) - nv
        if 0.0 <= nv <= 126.0:
            low_pts.append((lx0 + (nv / 126.0) * lw, ly0 + lh - (kv / 22.0) * lh))
    cv.polyline(low_pts, stroke=sub_col, stroke_width=1.05, dashed="2.5,2.0" if theme.is_dark else False)

    k_pts = [
        (lx0 + (n / 126.0) * lw, ly0 + lh - ((_kruskal_5(n) - n) / 22.0) * lh)
        for n in range(127)
    ]
    cv.polyline(k_pts, stroke=main_col, stroke_width=1.25)

    rx0, ry0, rw, rh = 236.0, 26.0, 156.0, 88.0
    cv.rect(rx0, ry0, rw, rh, fill=theme.panel if theme.is_dark else "none", stroke=axis_col, stroke_width=0.9)
    cv.text(rx0 + 0.5 * rw, 13.0, "τ(x)", font_size=9.5, italic=True)

    for yv, ylbl in ((0.0, "0"), (0.25, "1/4"), (0.5, "1/2"), (2.0 / 3.0, "2/3")):
        yy = ry0 + rh - (yv / (2.0 / 3.0)) * rh
        if 0.0 < yv < 0.66:
            cv.line(rx0, yy, rx0 + rw, yy, stroke=grid_col, stroke_width=0.6)
        cv.text(rx0 - 5.0, yy, ylbl, font_size=7.6, anchor="end", fill=theme.muted)

    for xv, xlbl in ((0.0, "0"), (0.25, "1/4"), (0.5, "1/2"), (0.75, "3/4"), (1.0, "1")):
        xx = rx0 + xv * rw
        if 0.0 < xv < 1.0:
            cv.line(xx, ry0, xx, ry0 + rh, stroke=grid_col, stroke_width=0.6)
        cv.text(xx, ry0 + rh + 12.0, xlbl, font_size=7.6, fill=theme.muted)

    t_pts: list[tuple[float, float]] = []
    for j in range(257):
        xv = j / 256.0
        tv = 0.0
        p2 = 1.0
        for _ in range(10):
            frac = abs((xv * p2) - round(xv * p2))
            tv += frac / p2
            p2 *= 2.0
        t_pts.append((rx0 + xv * rw, ry0 + rh - (tv / (2.0 / 3.0)) * rh))
    cv.polyline(t_pts, stroke=theme.coral if theme.is_dark else main_col, stroke_width=1.2)
    return cv.to_svg()


def fig_p390_inline(theme: Theme) -> str:
    w, h = 292.0, 92.0
    cv = SvgCanvas(w, h, theme)
    m1, m2 = 4, 6
    x_set = {(0, 0), (1, 2), (1, 3), (1, 4), (1, 5), (2, 1), (2, 2), (2, 5)}

    def core_of(s: set[tuple[int, int]]) -> set[tuple[int, int]]:
        return {
            (a, b)
            for a in range(m1)
            for b in range(m2)
            if (a, b) in s and ((a + 1) % m1, b) in s and (a, (b + 1) % m2) in s
        }

    def spread_of(s: set[tuple[int, int]]) -> set[tuple[int, int]]:
        return {
            (a, b)
            for a in range(m1)
            for b in range(m2)
            if (a, b) in s or ((a - 1) % m1, b) in s or (a, (b - 1) % m2) in s
        }

    x_core = core_of(x_set)
    x_spread = spread_of(x_set)
    x_dual = {(a, b) for a in range(m1) for b in range(m2) if (m1 - 1 - a, m2 - 1 - b) not in x_set}
    d_core = core_of(x_dual)
    d_spread = spread_of(x_dual)

    cell = 9.0
    gw, gh = m1 * cell, m2 * cell
    gy = 10.0
    gxs = [22.0, 88.0, 162.0, 228.0]
    grid_col = theme.panel_stroke if theme.is_dark else "#94A3B8"
    border_col = theme.cyan if theme.is_dark else "#0F172A"
    dot_col = theme.cyan if theme.is_dark else "#0F172A"
    core_col = theme.gold if theme.is_dark else "#0F172A"
    plus_col = theme.coral if theme.is_dark else "#334155"

    panels = [
        (gxs[0], "X", -4.5, x_set, set(), set()),
        (gxs[1], "X^◦ and X^+", -20.5, x_set, x_core, x_spread),
        (gxs[2], "X^∼", -6.5, x_dual, set(), set()),
        (gxs[3], "X^{∼◦} and X^{∼+}", -25.0, x_dual, d_core, d_spread),
    ]

    for gx, title, tx_off, s_main, s_c, s_sp in panels:
        for r in range(m2 + 1):
            cv.line(gx, gy + r * cell, gx + gw, gy + r * cell, stroke=grid_col, stroke_width=0.6)
        for c in range(m1 + 1):
            cv.line(gx + c * cell, gy, gx + c * cell, gy + gh, stroke=grid_col, stroke_width=0.6)
        cv.rect(gx, gy, gw, gh, fill="none", stroke=border_col, stroke_width=1.0)
        for a in range(m1):
            for b in range(m2):
                px = gx + (a + 0.5) * cell
                py = gy + (m2 - 1 - b + 0.5) * cell
                if (a, b) in s_c:
                    cv.circle(px, py, 2.3, fill=theme.bg, stroke=core_col, stroke_width=1.2)
                elif (a, b) in s_main:
                    cv.circle(px, py, 2.3, fill=dot_col, stroke="none")
                elif (a, b) in s_sp:
                    cv.line(px - 2.3, py, px + 2.3, py, stroke=plus_col, stroke_width=1.0)
                    cv.line(px, py - 2.3, px, py + 2.3, stroke=plus_col, stroke_width=1.0)
        cv.text(gx + 0.5 * gw + tx_off, gy + gh + 13.0, title, font_size=8.2, anchor="start", italic=True, rich=True)
    return cv.to_svg()


def fig_p395_inline(theme: Theme) -> str:
    w, h = 340.0, 140.0
    cv = SvgCanvas(w, h, theme)
    base_pos, edges = _t4_layout()
    pos = {k: (x * 1.06 + 4.0, y) for k, (x, y) in base_pos.items()}
    edge_col = theme.cyan if theme.is_dark else "#334155"
    pill_stroke = theme.gold if theme.is_dark else "#CBD5E1"

    for u, v, _ in edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        cv.line(x1, y1 + 5.5, x2, y2 - 5.5, stroke=edge_col, stroke_width=1.15)

    for code, (nx, ny) in pos.items():
        cv.rect(nx - 12.0, ny - 5.2, 24.0, 10.4, fill=theme.node_fill if theme.is_dark else "#FFFFFF", stroke=pill_stroke if theme.is_dark else "none", stroke_width=0.9, rx=2.5)
        tcol = theme.gold if (theme.is_dark and code in ("0000", "1111")) else theme.fg
        cv.text(nx, ny, code, font_size=7.6, mono=True, fill=tcol)
    return cv.to_svg()


def fig_p403_inline(theme: Theme) -> str:
    cell = 13.5
    pad = 10.0
    w = 2 * pad + 27 * cell
    h = 2 * pad + 3 * cell
    cv = SvgCanvas(w, h, theme)

    top_doms = [(0, 0), (0, 1), (1, 3), (3, 6), (6, 6), (6, 0), (0, 2), (2, 5), (5, 5), (5, 6), (6, 1), (1, 4), (4, 4)]
    bot_doms = [(0, 5), (3, 0), (3, 3), (4, 3), (6, 4), (2, 6), (2, 2), (3, 2), (5, 3), (1, 5), (1, 1), (2, 1), (4, 2)]

    for i, (pa, pb) in enumerate(top_doms):
        cv.domino(pad + (2 * i) * cell, pad, pa, pb, vertical=False, cell=cell, inverted=True)
    cv.domino(pad + 26 * cell, pad, 4, 5, vertical=True, cell=cell, inverted=True)
    for i, (pa, pb) in enumerate(bot_doms):
        gx = 25 - 2 * i
        cv.domino(pad + gx * cell, pad + 2 * cell, pa, pb, vertical=False, cell=cell, inverted=True)
    cv.domino(pad, pad + cell, 0, 4, vertical=True, cell=cell, inverted=True)
    return cv.to_svg()


def _draw_urn_row(
    groups: list[tuple[list[str], list[str], list[str]]],
    labeled_urns: bool,
    labeled_balls: bool,
    theme: Theme,
) -> str:
    n_g = len(groups)
    urn_w = 10.0
    urn_gap = 2.6
    grp_w = 3 * urn_w + 2 * urn_gap
    grp_gap = 9.5 if n_g >= 8 else 14.0
    pad_x = 12.0
    w = 2 * pad_x + n_g * grp_w + (n_g - 1) * grp_gap
    h = 54.0 if labeled_urns else 46.0
    cv = SvgCanvas(w, h, theme)

    urn_col = theme.cyan if theme.is_dark else "#1E293B"
    ball_cols = {"1": theme.gold, "2": theme.coral, "3": theme.mint, "": theme.gold}

    y_base = 34.0
    y_top = 11.0
    for gi, grp in enumerate(groups):
        gx0 = pad_x + gi * (grp_w + grp_gap)
        for ui in range(3):
            ux = gx0 + ui * (urn_w + urn_gap)
            u_d = (
                f"M {fmt(ux)} {fmt(y_top)} "
                f"L {fmt(ux)} {fmt(y_base - 3)} "
                f"Q {fmt(ux)} {fmt(y_base)} {fmt(ux + 3)} {fmt(y_base)} "
                f"L {fmt(ux + urn_w - 3)} {fmt(y_base)} "
                f"Q {fmt(ux + urn_w)} {fmt(y_base)} {fmt(ux + urn_w)} {fmt(y_base - 3)} "
                f"L {fmt(ux + urn_w)} {fmt(y_top)}"
            )
            cv.path(u_d, stroke=urn_col, stroke_width=1.15)
            cv.line(ux + 2.0, y_base + 2.2, ux + urn_w - 2.0, y_base + 2.2, stroke=urn_col, stroke_width=1.1)
            if labeled_urns:
                cv.text(ux + 0.5 * urn_w, y_base + 10.5, "ABC"[ui], font_size=7.4, fill=theme.muted if theme.is_dark else theme.fg)
            balls = grp[ui]
            for bi, b_lbl in enumerate(balls):
                by = y_base - 4.0 - bi * 7.2
                bx = ux + 0.5 * urn_w
                bcol = ball_cols.get(b_lbl, theme.gold) if theme.is_dark else "#0F172A"
                bfill = theme.node_fill if theme.is_dark else "#FFFFFF"
                cv.circle(bx, by, 3.3, fill=bfill, stroke=bcol, stroke_width=1.05)
                if labeled_balls and b_lbl:
                    cv.text(bx, by + 0.2, b_lbl, font_size=5.6, fill=bcol if theme.is_dark else "#0F172A", bold=True)
    return cv.to_svg()


def fig_p404_inline_1(theme: Theme) -> str:
    groups = [
        (["1", "2"], [], []),
        (["1"], ["2"], []),
        (["1"], [], ["2"]),
        (["2"], ["1"], []),
        ([], ["1", "2"], []),
        ([], ["1"], ["2"]),
        (["2"], [], ["1"]),
        ([], ["2"], ["1"]),
        ([], [], ["1", "2"]),
    ]
    return _draw_urn_row(groups, labeled_urns=True, labeled_balls=True, theme=theme)


def fig_p404_inline_2(theme: Theme) -> str:
    groups = [
        (["", ""], [], []),
        ([""], [""], []),
        ([""], [], [""]),
        ([], ["", ""], []),
        ([], [""], [""]),
        ([], [], ["", ""]),
    ]
    return _draw_urn_row(groups, labeled_urns=True, labeled_balls=False, theme=theme)


def fig_p404_inline_3(theme: Theme) -> str:
    groups = [
        (["1", "2", "3"], [], []),
        (["1", "2"], ["3"], []),
        (["1", "3"], ["2"], []),
        (["1"], ["2", "3"], []),
        (["1"], ["2"], ["3"]),
    ]
    return _draw_urn_row(groups, labeled_urns=False, labeled_balls=True, theme=theme)


def fig_p404_inline_4(theme: Theme) -> str:
    groups = [
        (["", "", ""], [], []),
        (["", ""], [""], []),
        ([""], [""], [""]),
    ]
    return _draw_urn_row(groups, labeled_urns=False, labeled_balls=False, theme=theme)


def fig_48(theme: Theme) -> str:
    w, h = 236.0, 126.0
    cv = SvgCanvas(w, h, theme)
    sp = 10.5
    dot_in = theme.gold if theme.is_dark else "#0F172A"
    dot_out = theme.cyan if theme.is_dark else "#0F172A"
    box_col = theme.coral if theme.is_dark else "#334155"

    parts_a = [8, 8, 8, 7, 2, 1, 1]
    parts_b = [7, 5, 4, 4, 4, 4, 4, 3]

    for x0, y0, parts, cap in [(18.0, 18.0, parts_a, "(a) 8887211"), (132.0, 18.0, parts_b, "(b) 75444443")]:
        cv.rect(x0 - 4.8, y0 - 4.8, 3 * sp + 9.6, 3 * sp + 9.6, fill="none", stroke=box_col, stroke_width=1.05, dashed="1.8,2.0")
        for r, cnt in enumerate(parts):
            for c in range(cnt):
                in_d = r < 4 and c < 4
                cv.circle(x0 + c * sp, y0 + r * sp, 2.3, fill=dot_in if in_d else dot_out, stroke="none")
        cv.text(x0 + 3.5 * sp, 110.0, cap, font_size=9.0)
    return cv.to_svg()


def _partition_table_up_to(n_max: int) -> list[list[int]]:
    dp = [[0] * (n_max + 1) for _ in range(n_max + 1)]
    dp[0][0] = 1
    for ni in range(1, n_max + 1):
        for k in range(1, ni + 1):
            dp[ni][k] = dp[ni - 1][k - 1] + (dp[ni - k][k] if ni >= k else 0)
    return dp


def fig_49(theme: Theme) -> str:
    w, h = 368.0, 148.0
    cv = SvgCanvas(w, h, theme)
    dp = _partition_table_up_to(100)
    counts = [dp[100][m] for m in range(59)]
    max_c = max(counts)

    ax_col = theme.muted if theme.is_dark else "#1E293B"
    fill_col = "#1D3557" if theme.is_dark else "#E2E8F0"
    hi_col = theme.gold if theme.is_dark else "#475569"
    curve_col = theme.cyan if theme.is_dark else "#0F172A"

    x0, y0, pw, ph = 56.0, 12.0, 286.0, 44.0
    bw = pw / 58.0
    cv.text(12.0, y0 + 0.5 * ph, "a)", font_size=8.8, anchor="start")
    cv.text(36.0, y0 + 0.5 * ph - 4.0, "100", font_size=6.8)
    cv.text(36.0, y0 + 0.5 * ph + 3.5, "m", font_size=6.8, italic=True)
    cv.line(27.5, y0 + 0.5 * ph - 9.0, 27.5, y0 + 0.5 * ph + 8.0, stroke=theme.fg, stroke_width=0.8)
    cv.line(44.5, y0 + 0.5 * ph - 9.0, 44.5, y0 + 0.5 * ph + 8.0, stroke=theme.fg, stroke_width=0.8)
    cv.text(48.5, y0 + 0.5 * ph, ":", font_size=8.5)

    hi_ms = {8, 18, 28, 38, 48}
    step_pts: list[tuple[float, float]] = [(x0, y0 + ph)]
    for m in range(1, 59):
        bh = (counts[m] / max_c) * (ph - 2.0)
        bx = x0 + (m - 1) * bw
        by = y0 + ph - bh
        c_fill = hi_col if m in hi_ms else fill_col
        cv.rect(bx, by, bw, bh, fill=c_fill, stroke=ax_col, stroke_width=0.35)
        step_pts.append((bx, by))
        step_pts.append((bx + bw, by))
    step_pts.append((x0 + pw, y0 + ph))
    cv.polyline(step_pts, stroke=curve_col, stroke_width=0.95)
    cv.line(x0, y0 + ph, x0 + pw + 4.0, y0 + ph, stroke=ax_col, stroke_width=0.9)
    for mv in (0, 8, 18, 28, 38, 48, 58):
        tx = x0 + (mv - 0.5 if mv > 0 else 0.0) * bw
        cv.line(tx, y0 + ph, tx, y0 + ph + 2.8, stroke=ax_col, stroke_width=0.8)
        cv.text(tx, y0 + ph + 9.0, str(mv), font_size=7.2, fill=theme.muted)
    cv.text(x0 + pw + 12.0, y0 + ph + 8.0, "m", font_size=8.2, italic=True)

    y1, ph2 = 82.0, 44.0
    cv.text(12.0, y1 + 0.5 * ph2, "b)", font_size=8.8, anchor="start")
    cv.text(38.0, y1 + 0.5 * ph2, "f(x):", font_size=8.5, italic=True)

    c_const = math.pi / math.sqrt(6.0)
    f_max = c_const / math.e
    n_bins = 60
    sw_b = pw / n_bins
    for bi in range(n_bins):
        xm = -2.0 + (bi + 0.5) * 6.0 / n_bins
        fv = math.exp(-c_const * xm - math.exp(-c_const * xm) / c_const)
        bh = (fv / f_max) * (ph2 - 2.0)
        bx = x0 + bi * sw_b
        is_int = bi in (0, 10, 20, 30, 40, 50)
        cv.rect(bx, y1 + ph2 - bh, sw_b, bh, fill=hi_col if is_int else fill_col, stroke=ax_col, stroke_width=0.3)

    f_pts: list[tuple[float, float]] = []
    for i in range(181):
        xv = -2.0 + 6.0 * i / 180.0
        fv = math.exp(-c_const * xv - math.exp(-c_const * xv) / c_const)
        f_pts.append((x0 + ((xv + 2.0) / 6.0) * pw, y1 + ph2 - (fv / f_max) * (ph2 - 2.0)))
    cv.polyline(f_pts, stroke=theme.coral if theme.is_dark else curve_col, stroke_width=1.25)
    cv.line(x0, y1 + ph2, x0 + pw + 4.0, y1 + ph2, stroke=ax_col, stroke_width=0.9)
    for xv in range(-2, 5):
        tx = x0 + ((xv + 2.0) / 6.0) * pw
        cv.line(tx, y1 + ph2, tx, y1 + ph2 + 2.8, stroke=ax_col, stroke_width=0.8)
        lbl = f"−{abs(xv)}" if xv < 0 else str(xv)
        cv.text(tx, y1 + ph2 + 9.0, lbl, font_size=7.2, fill=theme.muted)
    cv.text(x0 + pw + 12.0, y1 + ph2 + 8.0, "x", font_size=8.2, italic=True)
    return cv.to_svg()


def _blend_hex(c0: str, c1: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    r0, g0, b0 = int(c0[1:3], 16), int(c0[3:5], 16), int(c0[5:7], 16)
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r = round(r0 + (r1 - r0) * t)
    g = round(g0 + (g1 - g0) * t)
    b = round(b0 + (b1 - b0) * t)
    return f"#{r:02X}{g:02X}{b:02X}"


def fig_50(theme: Theme) -> str:
    n = 25
    occ = [[0] * n for _ in range(n)]
    total = [0]

    def gen(rem: int, mx: int, row: int) -> None:
        if rem == 0:
            total[0] += 1
            return
        for v in range(min(rem, mx), 0, -1):
            for c in range(v):
                occ[row][c] += 1
            gen(rem - v, v, row + 1)

    gen(n, n, 0)
    tot = float(total[0])

    cell = 6.2
    x0, y0 = 36.0, 24.0
    w = x0 + n * cell + 16.0
    h = y0 + n * cell + 14.0
    cv = SvgCanvas(w, h, theme)

    lo_c = "#10192B" if theme.is_dark else "#FFFFFF"
    hi_c = theme.cyan if theme.is_dark else "#1E293B"
    grid_c = "#1E2D47" if theme.is_dark else "#CBD5E1"

    for r in range(n):
        for c in range(n):
            cnt = occ[r][c]
            if cnt > 0:
                frac = cnt / tot
                fill = _blend_hex(lo_c, hi_c, frac ** 0.78)
                cv.rect(x0 + c * cell, y0 + r * cell, cell, cell, fill=fill, stroke=grid_c, stroke_width=0.35)

    ax_col = theme.muted if theme.is_dark else "#0F172A"
    cv.line(x0, y0, x0 + n * cell, y0, stroke=ax_col, stroke_width=0.9)
    cv.line(x0, y0, x0, y0 + n * cell, stroke=ax_col, stroke_width=0.9)

    for k, lbl in ((0, "0"), (5, "√n"), (10, "2√n")):
        cv.line(x0 + k * cell, y0 - 3.0, x0 + k * cell, y0, stroke=ax_col, stroke_width=0.85)
        cv.text(x0 + k * cell, y0 - 9.0, lbl, font_size=7.6, italic=("n" in lbl))
        if k > 0:
            cv.line(x0 - 3.0, y0 + k * cell, x0, y0 + k * cell, stroke=ax_col, stroke_width=0.85)
            cv.text(x0 - 5.5, y0 + k * cell, lbl, font_size=7.6, anchor="end", italic=True)

    c_const = math.pi / math.sqrt(6.0)
    sq_n = 5.0
    t_pts: list[tuple[float, float]] = []
    for i in range(1, 240):
        yv = 0.08 + (24.8 * i) / 240.0
        ey = math.exp(-c_const * yv / sq_n)
        if ey < 0.999999:
            xv = -sq_n / c_const * math.log(1.0 - ey)
            if xv <= 25.2:
                t_pts.append((x0 + xv * cell, y0 + yv * cell))
    cv.polyline(t_pts, stroke=theme.gold if theme.is_dark else "#0F172A", stroke_width=1.45)
    return cv.to_svg()


def fig_51(theme: Theme) -> str:
    n, m = 50, 5
    max_part = n - m + 1
    occ = [[0] * max_part for _ in range(m)]
    total = [0]

    def gen(rem: int, parts_left: int, mx: int, row: int) -> None:
        if parts_left == 1:
            if 1 <= rem <= mx:
                for c in range(rem):
                    occ[row][c] += 1
                total[0] += 1
            return
        lo = math.ceil(rem / parts_left)
        hi = min(mx, rem - (parts_left - 1))
        for v in range(hi, lo - 1, -1):
            for c in range(v):
                occ[row][c] += 1
            gen(rem - v, parts_left - 1, v, row + 1)

    gen(n, m, max_part, 0)
    tot = float(total[0])

    cw, ch_cell = 7.4, 9.2
    x0, y0 = 26.0, 24.0
    w = x0 + max_part * cw + 14.0
    h = y0 + m * ch_cell + 14.0
    cv = SvgCanvas(w, h, theme)

    lo_c = "#10192B" if theme.is_dark else "#FFFFFF"
    hi_c = theme.cyan if theme.is_dark else "#1E293B"
    grid_c = "#1E2D47" if theme.is_dark else "#CBD5E1"

    for r in range(m):
        for c in range(max_part):
            cnt = occ[r][c]
            if cnt > 0:
                frac = cnt / tot
                fill = _blend_hex(lo_c, hi_c, frac ** 0.8)
                cv.rect(x0 + c * cw, y0 + r * ch_cell, cw, ch_cell, fill=fill, stroke=grid_c, stroke_width=0.35)

    ax_col = theme.muted if theme.is_dark else "#0F172A"
    cv.line(x0, y0, x0 + max_part * cw, y0, stroke=ax_col, stroke_width=0.9)
    cv.line(x0, y0, x0, y0 + m * ch_cell, stroke=ax_col, stroke_width=0.9)

    for k, lbl in ((0, "0"), (10, "n/m"), (20, "2n/m")):
        cv.line(x0 + k * cw, y0 - 3.0, x0 + k * cw, y0, stroke=ax_col, stroke_width=0.85)
        cv.text(x0 + k * cw, y0 - 9.0, lbl, font_size=7.6, italic=(k > 0))
    cv.line(x0 - 3.0, y0 + m * ch_cell, x0, y0 + m * ch_cell, stroke=ax_col, stroke_width=0.85)
    cv.text(x0 - 6.0, y0 + m * ch_cell, "m", font_size=7.8, anchor="end", italic=True)

    c_pts: list[tuple[float, float]] = []
    for i in range(1, 160):
        yv = 5.0 * i / 159.0
        xv = 10.0 * math.log(5.0 / yv)
        if xv <= max_part + 0.2:
            c_pts.append((x0 + xv * cw, y0 + yv * ch_cell))
    cv.polyline(c_pts, stroke=theme.gold if theme.is_dark else "#0F172A", stroke_width=1.45)
    return cv.to_svg()


def _pill_box(cv: SvgCanvas, x: float, y: float, label: str, theme: Theme, font_size: float = 6.8, pad_h: float = 3.2, h: float = 11.2, accent: bool = False) -> None:
    bw = max(12.0, len(label) * (font_size * 0.58) + 2 * pad_h)
    stroke = (theme.gold if accent else theme.cyan) if theme.is_dark else "#334155"
    fill = theme.sink_true_fill if (theme.is_dark and accent) else (theme.node_fill if theme.is_dark else "#FFFFFF")
    cv.rect(x - 0.5 * bw, y - 0.5 * h, bw, h, fill=fill, stroke=stroke, stroke_width=0.95, rx=3.5)
    cv.text(x, y + 0.2, label, font_size=font_size, fill=theme.gold if (theme.is_dark and accent) else theme.fg)


def fig_p422_inline(theme: Theme) -> str:
    w, h = 472.0, 178.0
    cv = SvgCanvas(w, h, theme)
    edge_col = theme.muted if theme.is_dark else "#334155"

    nodes_a = {
        "ϵ": (108.0, 16.0),
        "1": (92.0, 38.0),
        "11": (68.0, 62.0),
        "2": (118.0, 62.0),
        "111": (52.0, 86.0),
        "21": (98.0, 86.0),
        "3": (146.0, 86.0),
        "1111": (38.0, 110.0),
        "211": (78.0, 110.0),
        "22": (112.0, 110.0),
        "31": (142.0, 110.0),
        "4": (176.0, 110.0),
        "11111": (26.0, 134.0),
        "2111": (64.0, 134.0),
        "221": (96.0, 134.0),
        "311": (124.0, 134.0),
        "32": (150.0, 134.0),
        "41": (174.0, 134.0),
        "5": (198.0, 134.0),
    }
    edges_a = [
        ("ϵ", "1"), ("1", "11"), ("1", "2"), ("11", "111"), ("2", "21"), ("2", "3"),
        ("111", "1111"), ("21", "211"), ("21", "22"), ("3", "31"), ("3", "4"),
        ("1111", "11111"), ("211", "2111"), ("22", "221"), ("31", "311"), ("31", "32"), ("4", "41"), ("4", "5"),
    ]
    stubs_a = [
        ("11111", -8.0), ("2111", -7.0),
        ("221", -6.0), ("221", 6.0),
        ("311", -6.0),
        ("32", -6.0), ("32", 6.0),
        ("41", -6.0), ("41", 6.0),
        ("5", -6.0), ("5", 6.0),
    ]
    for u, v in edges_a:
        cv.line(nodes_a[u][0], nodes_a[u][1], nodes_a[v][0], nodes_a[v][1], stroke=edge_col, stroke_width=1.0)
    for u, dx_s in stubs_a:
        ux, uy = nodes_a[u]
        cv.line(ux, uy, ux + dx_s, uy + 14.0, stroke=edge_col, stroke_width=0.95)
    for lbl, (nx, ny) in nodes_a.items():
        _pill_box(cv, nx, ny, lbl, theme, font_size=6.5, h=10.5, accent=(lbl == "ϵ"))
    cv.text(112.0, 164.0, "(a)", font_size=9.2)

    nodes_b = {
        "11111111": (346.0, 14.0),
        "2111111": (332.0, 34.0),
        "221111": (296.0, 54.0),
        "311111": (368.0, 54.0),
        "22211": (272.0, 74.0),
        "32111": (342.0, 74.0),
        "41111": (404.0, 74.0),
        "2222": (254.0, 94.0),
        "3221": (306.0, 94.0),
        "3311": (348.0, 94.0),
        "4211": (388.0, 94.0),
        "5111": (432.0, 94.0),
        "332": (324.0, 114.0),
        "422": (362.0, 114.0),
        "431": (392.0, 114.0),
        "521": (420.0, 114.0),
        "611": (448.0, 114.0),
        "44": (378.0, 134.0),
        "53": (406.0, 134.0),
        "62": (432.0, 134.0),
        "71": (456.0, 134.0),
        "8": (444.0, 154.0),
    }
    edges_b = [
        ("11111111", "2111111"),
        ("2111111", "221111"), ("2111111", "311111"),
        ("221111", "22211"), ("311111", "32111"), ("311111", "41111"),
        ("22211", "2222"), ("32111", "3221"), ("32111", "3311"), ("41111", "4211"), ("41111", "5111"),
        ("3311", "332"), ("4211", "422"), ("4211", "431"), ("5111", "521"), ("5111", "611"),
        ("431", "44"), ("521", "53"), ("611", "62"), ("611", "71"),
        ("71", "8"),
    ]
    for u, v in edges_b:
        cv.line(nodes_b[u][0], nodes_b[u][1], nodes_b[v][0], nodes_b[v][1], stroke=edge_col, stroke_width=1.0)
    for lbl, (nx, ny) in nodes_b.items():
        _pill_box(cv, nx, ny, lbl, theme, font_size=6.2, h=10.2, accent=(lbl in ("11111111", "8")))
    cv.text(352.0, 164.0, "(b)", font_size=9.2)
    return cv.to_svg()


def fig_52(theme: Theme) -> str:
    parts: list[tuple[int, ...]] = []

    def gen(rem: int, mx: int, cur: list[int]) -> None:
        if rem == 0:
            parts.append(tuple(cur))
            return
        for v in range(min(rem, mx), 0, -1):
            gen(rem - v, v, cur + [v])

    gen(12, 12, [])

    def dom_geq(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
        sa = sb = 0
        for i in range(max(len(a), len(b))):
            sa += a[i] if i < len(a) else 0
            sb += b[i] if i < len(b) else 0
            if sa < sb:
                return False
        return True

    edges: list[tuple[int, int]] = []
    for i, a in enumerate(parts):
        for j, b in enumerate(parts):
            if i != j and dom_geq(a, b) and not any(
                k != i and k != j and dom_geq(a, parts[k]) and dom_geq(parts[k], b) for k in range(len(parts))
            ):
                edges.append((i, j))

    top_d = [0] * len(parts)
    for i in range(len(parts)):
        for u, v in edges:
            if v == i:
                top_d[i] = max(top_d[i], top_d[u] + 1)

    w, h = 324.0, 466.0
    cv = SvgCanvas(w, h, theme)

    levels: dict[int, list[int]] = {}
    for i, d in enumerate(top_d):
        levels.setdefault(d, []).append(i)

    def fmt_part(p: tuple[int, ...]) -> str:
        if p[0] >= 10:
            return " ".join(str(x) for x in p)
        return "".join(str(x) for x in p)

    coords: dict[int, tuple[float, float]] = {}
    for d, idxs in levels.items():
        idxs.sort(key=lambda idx: (-len(parts[idx]), -parts[idx][0], parts[idx]))
        yy = 16.0 + d * 15.5
        k = len(idxs)
        if k == 1:
            xs = [w * 0.5]
        else:
            span = min(w - 64.0, (k - 1) * 58.0)
            x_l = 0.5 * (w - span)
            xs = [x_l + j * (span / (k - 1)) for j in range(k)]
        for idx, xx in zip(idxs, xs):
            coords[idx] = (xx, yy)

    edge_col = theme.panel_stroke if theme.is_dark else "#94A3B8"
    for u, v in edges:
        cv.line(coords[u][0], coords[u][1], coords[v][0], coords[v][1], stroke=edge_col, stroke_width=0.85)

    for i, p in enumerate(parts):
        lbl = fmt_part(p)
        nx, ny = coords[i]
        fs = 5.8 if len(lbl) >= 9 else 6.4
        _pill_box(cv, nx, ny, lbl, theme, font_size=fs, pad_h=2.8, h=10.0, accent=(i in (0, len(parts) - 1)))
    return cv.to_svg()


def fig_53(theme: Theme) -> str:
    w, h = 228.0, 172.0
    cv = SvgCanvas(w, h, theme)
    cx = 114.0
    zy = 136.0
    sy = 64.0

    def proj_plane(u: float, v: float) -> tuple[float, float]:
        return cx + 52.0 * u + 22.0 * v, zy - 15.0 * v

    def proj_surf(u: float, v: float) -> tuple[float, float]:
        z_alt = 22.0 * (u * u - v * v)
        return cx + 52.0 * u + 22.0 * v, sy - 15.0 * v - z_alt

    p_corners = [proj_plane(-1, -1), proj_plane(1, -1), proj_plane(1, 1), proj_plane(-1, 1)]
    plane_fill = "#111A2E" if theme.is_dark else "#F8FAFC"
    plane_stroke = theme.panel_stroke if theme.is_dark else "#64748B"
    cv.polyline(p_corners, stroke=plane_stroke, stroke_width=0.9, fill=plane_fill, closed=True)

    pl_l = proj_plane(-1, 0)
    pl_r = proj_plane(1, 0)
    pl_f = proj_plane(0, -1)
    pl_b = proj_plane(0, 1)
    ax_col = theme.muted if theme.is_dark else "#334155"
    cv.line(pl_l[0], pl_l[1], pl_r[0], pl_r[1], stroke=ax_col, stroke_width=0.95)
    cv.line(pl_f[0], pl_f[1], pl_b[0], pl_b[1], stroke=theme.gold if theme.is_dark else "#0F172A", stroke_width=1.25)

    for pt in (pl_l, pl_r, pl_f, pl_b, (cx, zy)):
        cv.circle(pt[0], pt[1], 1.9, fill=theme.cyan if theme.is_dark else "#0F172A", stroke="none")

    cv.text(pl_l[0] - 28.0, pl_l[1], "z_0 − ϵ", font_size=7.8, anchor="start", italic=True, rich=True)
    cv.text(pl_r[0] + 4.0, pl_r[1], "z_0 + ϵ", font_size=7.8, anchor="start", italic=True, rich=True)
    cv.text(pl_f[0] - 15.0, pl_f[1] + 9.5, "z_0 − iϵ", font_size=7.8, anchor="start", italic=True, rich=True)
    cv.text(pl_b[0] + 4.0, pl_b[1] - 6.5, "z_0 + iϵ", font_size=7.8, anchor="start", italic=True, rich=True)
    cv.text(cx + 5.0, zy + 7.5, "z_0", font_size=8.0, anchor="start", italic=True, rich=True)

    cv.line(cx, sy, cx, zy, stroke=plane_stroke, stroke_width=0.8, dashed="2.2,2.2")

    mesh_col = theme.panel_stroke if theme.is_dark else "#CBD5E1"
    for k in (-1.0, -0.5, 0.5, 1.0):
        u_curve = [proj_surf(k, -1.0 + 2.0 * j / 24.0) for j in range(25)]
        v_curve = [proj_surf(-1.0 + 2.0 * j / 24.0, k) for j in range(25)]
        sw = 1.05 if abs(k) == 1.0 else 0.65
        cv.polyline(u_curve, stroke=mesh_col, stroke_width=sw)
        cv.polyline(v_curve, stroke=mesh_col, stroke_width=sw)

    real_arch = [proj_surf(-1.0 + 2.0 * j / 32.0, 0.0) for j in range(33)]
    imag_arch = [proj_surf(0.0, -1.0 + 2.0 * j / 32.0) for j in range(33)]
    cv.polyline(real_arch, stroke=theme.coral if theme.is_dark else "#334155", stroke_width=1.6)
    cv.polyline(imag_arch, stroke=theme.gold if theme.is_dark else "#0F172A", stroke_width=1.85)

    for pt in (proj_surf(-1, 0), proj_surf(1, 0), proj_surf(0, -1), proj_surf(0, 1)):
        cv.circle(pt[0], pt[1], 2.0, fill=theme.cyan if theme.is_dark else "#0F172A", stroke="none")
    cv.circle(cx, sy, 2.5, fill=theme.gold if theme.is_dark else "#0F172A", stroke="none", glow=True)
    cv.text(cx + 6.0, sy - 9.0, "ℜf(z_0)", font_size=8.2, anchor="start", italic=True, rich=True)
    return cv.to_svg()


def fig_54(theme: Theme) -> str:
    n = 100
    s_dp = [0] * (n + 1)
    s_dp[0] = 1
    for i in range(1, n + 1):
        for m in range(i, 0, -1):
            s_dp[m] = m * s_dp[m] + s_dp[m - 1]
        s_dp[0] = 0
    max_s = max(s_dp)

    w, h = 384.0, 128.0
    cv = SvgCanvas(w, h, theme)
    x0, y0, pw, ph = 20.0, 14.0, 344.0, 88.0

    grid_col = theme.panel_stroke if theme.is_dark else "#CBD5E1"
    ax_col = theme.muted if theme.is_dark else "#1E293B"
    bar_col = theme.cyan if theme.is_dark else "#1E293B"
    peak_col = theme.gold if theme.is_dark else "#0F172A"

    for frac in (0.25, 0.5, 0.75, 1.0):
        gy = y0 + ph - frac * (ph - 4.0)
        cv.line(x0, gy, x0 + pw, gy, stroke=grid_col, stroke_width=0.6)

    m_min, m_max = 5, 100
    span_m = m_max - m_min + 1
    bw = pw / span_m
    for m in range(m_min, m_max + 1):
        ratio = s_dp[m] / max_s
        bh = ratio * (ph - 4.0)
        bx = x0 + (m - m_min) * bw
        if bh >= 0.35:
            col = peak_col if m in (28, 29) else bar_col
            cv.rect(bx + 0.4, y0 + ph - bh, max(1.2, bw - 0.8), bh, fill=col, stroke="none")

    cv.line(x0, y0 + ph, x0 + pw, y0 + ph, stroke=ax_col, stroke_width=0.95)
    for mv in range(10, 101, 10):
        tx = x0 + (mv - m_min + 0.5) * bw
        cv.line(tx, y0 + ph, tx, y0 + ph + 3.0, stroke=ax_col, stroke_width=0.85)
        cv.text(tx, y0 + ph + 10.5, str(mv), font_size=7.6, fill=theme.muted)

    cv.text(x0 + 0.66 * pw, y0 + 28.0, "greatest at m = 28, 29", font_size=8.2, italic=True, fill=theme.muted)
    return cv.to_svg()


BUILDERS: dict[str, Callable[[Theme], str]] = {
    "fig_37": fig_37,
    "fig_38": fig_38,
    "fig_39": fig_39,
    "fig_40": fig_40,
    "fig_41": fig_41,
    "fig_42": fig_42,
    "fig_43": fig_43,
    "fig_44": fig_44,
    "fig_45": fig_45,
    "fig_p371_paths": fig_p371_paths,
    "fig_p374_inline_1": fig_p374_inline_1,
    "fig_p374_inline_2": fig_p374_inline_2,
    "fig_p378_inline": fig_p378_inline,
    "fig_46": fig_46,
    "fig_47": fig_47,
    "fig_p390_inline": fig_p390_inline,
    "fig_p395_inline": fig_p395_inline,
    "fig_p403_inline": fig_p403_inline,
    "fig_p404_inline_1": fig_p404_inline_1,
    "fig_p404_inline_2": fig_p404_inline_2,
    "fig_p404_inline_3": fig_p404_inline_3,
    "fig_p404_inline_4": fig_p404_inline_4,
    "fig_48": fig_48,
    "fig_49": fig_49,
    "fig_50": fig_50,
    "fig_51": fig_51,
    "fig_p422_inline": fig_p422_inline,
    "fig_52": fig_52,
    "fig_53": fig_53,
    "fig_54": fig_54,
}

BUILDERS_P4 = BUILDERS

_ = rich_label


def render_part(out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for fig_id, fn in BUILDERS.items():
        m, c, p = emit_dual_figure(fig_id, fn, out_dir)
        paths.extend((m, c, p))
    return paths
