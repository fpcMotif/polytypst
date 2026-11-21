from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

from .figures_common import SvgCanvas, Theme, emit_dual_figure, fmt

ForestNode = tuple["ForestNode", ...]
Forest = tuple[ForestNode, ...]
BinTree = tuple[ "BinTree", "BinTree" ] | None


def _lerp_hex(c1: str, c2: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02X}{g:02X}{b:02X}"


def _heat_color(theme: Theme, shade: float) -> str:
    s = max(0.0, min(1.0, shade))
    if not theme.is_dark:
        g = round(255.0 * (1.0 - s))
        return f"#{g:02X}{g:02X}{g:02X}"
    if s <= 0.30:
        return _lerp_hex("#101827", "#1B4965", s / 0.30)
    if s <= 0.72:
        return _lerp_hex("#1B4965", "#58C4DD", (s - 0.30) / 0.42)
    return _lerp_hex("#58C4DD", "#F4D03F", (s - 0.72) / 0.28)


def _catmull_rom_svg(pts: list[tuple[float, float]]) -> str:
    if not pts:
        return ""
    if len(pts) == 1:
        return f"M {fmt(pts[0][0])} {fmt(pts[0][1])}"
    if len(pts) == 2:
        return f"M {fmt(pts[0][0])} {fmt(pts[0][1])} L {fmt(pts[1][0])} {fmt(pts[1][1])}"
    segs = [f"M {fmt(pts[0][0])} {fmt(pts[0][1])}"]
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(n - 1, i + 2)]
        c1x = p1[0] + (p2[0] - p0[0]) / 6.0
        c1y = p1[1] + (p2[1] - p0[1]) / 6.0
        c2x = p2[0] - (p3[0] - p1[0]) / 6.0
        c2y = p2[1] - (p3[1] - p1[1]) / 6.0
        segs.append(f"C {fmt(c1x)} {fmt(c1y)} {fmt(c2x)} {fmt(c2y)} {fmt(p2[0])} {fmt(p2[1])}")
    return " ".join(segs)


def _tokenize_math(raw: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch in ("_", "^") and i + 1 < n:
            kind = "sub" if ch == "_" else "sup"
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
            tokens.append((seg, kind))
        elif ch.isalpha() or ch in ("α", "μ", "ω", "ξ"):
            tokens.append((ch, "it"))
            i += 1
        else:
            j = i + 1
            while j < n and raw[j] not in ("_", "^") and not raw[j].isalpha() and raw[j] not in ("α", "μ", "ω", "ξ"):
                j += 1
            tokens.append((raw[i:j], "rm"))
            i = j
    return tokens


def _text_clean(
    cv: SvgCanvas,
    x: float,
    y: float,
    raw: str,
    font_size: float = 9.5,
    fill: str | None = None,
    anchor: str = "middle",
    italic: bool = True,
) -> None:
    _ = italic
    col = fill or cv.theme.fg
    toks = _tokenize_math(raw)
    widths: list[float] = []
    for seg, kind in toks:
        if kind in ("sub", "sup"):
            widths.append(len(seg) * font_size * 0.42)
        elif kind == "it":
            w_factor = 0.62 if seg.isupper() else 0.52
            widths.append(len(seg) * font_size * w_factor)
        else:
            widths.append(len(seg) * font_size * 0.48)
    total_w = sum(widths)
    if anchor == "middle":
        cur_x = x - 0.5 * total_w
    elif anchor == "end":
        cur_x = x - total_w
    else:
        cur_x = x
    for (seg, kind), w in zip(toks, widths):
        if kind == "sub":
            cv.text(cur_x + 0.5 * w, y + font_size * 0.25, seg, font_size=font_size * 0.72, fill=col)
        elif kind == "sup":
            is_alpha = seg.isalpha() or seg in ("ξ",)
            cv.text(cur_x + 0.5 * w, y - font_size * 0.34, seg, font_size=font_size * 0.74, fill=col, italic=is_alpha)
        elif kind == "it":
            cv.text(cur_x + 0.5 * w, y, seg, font_size=font_size, fill=col, italic=True)
        else:
            cv.text(cur_x + 0.5 * w, y, seg, font_size=font_size, fill=col)
        cur_x += w


def _pill(
    cv: SvgCanvas,
    cx: float,
    cy: float,
    w: float,
    h: float,
    label: str = "",
    stroke: str | None = None,
    fill: str | None = None,
    font_size: float = 9.5,
    mono: bool = False,
    italic: bool = False,
    rich: bool = False,
    text_fill: str | None = None,
) -> None:
    st = stroke or (cv.theme.cyan if cv.theme.is_dark else cv.theme.fg)
    fl = fill or cv.theme.node_fill
    cv.rect(cx - w * 0.5, cy - h * 0.5, w, h, fill=fl, stroke=st, stroke_width=1.35, rx=h * 0.5)
    if label:
        if rich:
            _text_clean(cv, cx, cy, label, font_size=font_size, fill=text_fill or cv.theme.fg, italic=italic)
        else:
            cv.text(
                cx,
                cy,
                label,
                font_size=font_size,
                fill=text_fill or cv.theme.fg,
                mono=mono,
                italic=italic,
                rich=False,
            )


def _solve_xi(n: float) -> float:
    x = 2.36
    for _ in range(30):
        ex = math.exp(x)
        x -= (x * ex - n) / (ex * (x + 1.0))
    return x


def fig_55(theme: Theme) -> str:
    cv = SvgCanvas(224, 206, theme)
    n = 25
    fact_n = math.factorial(n)
    part_weights: list[tuple[tuple[int, ...], int]] = []

    def gen_parts(rem: int, max_part: int, cur: list[int]) -> None:
        if rem == 0:
            denom = 1
            i = 0
            m = len(cur)
            while i < m:
                j = i + 1
                while j < m and cur[j] == cur[i]:
                    j += 1
                cnt = j - i
                k = cur[i]
                denom *= math.factorial(cnt) * (math.factorial(k) ** cnt)
                i = j
            part_weights.append((tuple(cur), fact_n // denom))
            return
        for v in range(min(rem, max_part), 0, -1):
            cur.append(v)
            gen_parts(rem - v, v, cur)
            cur.pop()

    gen_parts(n, n, [])
    bell_n = sum(w for _, w in part_weights)

    x0, y0 = 46.0, 32.0
    cell = 6.2
    for r in range(n):
        for c in range(n):
            if (r + 1) * (c + 1) > n:
                continue
            cov = sum(w for p, w in part_weights if len(p) > r and p[r] > c)
            prob = cov / bell_n
            fl = _heat_color(theme, prob)
            if theme.is_dark:
                st = "#263449"
            else:
                st = "#475569" if prob > 0.65 else "#CBD5E1"
            cv.rect(x0 + c * cell, y0 + r * cell, cell, cell, fill=fl, stroke=st, stroke_width=0.55)

    axis_col = theme.fg
    cv.line(x0, y0, x0 + n * cell, y0, stroke=axis_col, stroke_width=1.45)
    cv.line(x0, y0, x0, y0 + n * cell, stroke=axis_col, stroke_width=1.45)
    cv.text(x0 - 6.0, y0 - 6.0, "0", font_size=9.5, fill=theme.muted if theme.is_dark else theme.fg)

    xi = _solve_xi(float(n))
    exi = math.e * xi
    exp_xi_m1 = math.exp(xi) - 1.0

    for val, lbl in [(xi, "ξ"), (exi, "eξ")]:
        tx = x0 + val * cell
        cv.line(tx, y0 - 3.5, tx, y0, stroke=axis_col, stroke_width=1.1)
        cv.text(tx, y0 - 10.5, lbl, font_size=9.5, italic=True, fill=theme.gold if theme.is_dark else theme.fg)

    for val, lbl, is_rich in [(xi, "ξ", False), (exp_xi_m1, "e^ξ − 1", True)]:
        ty = y0 + val * cell
        cv.line(x0 - 3.5, ty, x0, ty, stroke=axis_col, stroke_width=1.1)
        tcol = theme.gold if theme.is_dark else theme.fg
        if is_rich:
            _text_clean(cv, x0 - 6.5, ty, lbl, font_size=9.2, fill=tcol, anchor="end", italic=True)
        else:
            cv.text(x0 - 6.5, ty, lbl, font_size=9.2, anchor="end", italic=True, fill=tcol)

    curve_pts: list[tuple[float, float]] = []
    steps = 64
    for s_idx in range(steps + 1):
        xv = 14.5 * s_idx / steps
        fy = sum((xi ** (xv + j)) / math.gamma(xv + j + 1.0) for j in range(1, 45))
        curve_pts.append((x0 + xv * cell, y0 + fy * cell))
    cpath = _catmull_rom_svg(curve_pts)
    if theme.is_dark:
        cv.path(cpath, stroke=theme.coral, stroke_width=1.7, glow=True)
    else:
        cv.path(cpath, stroke="#FFFFFF", stroke_width=2.3, opacity=0.72)
        cv.path(cpath, stroke="#0F172A", stroke_width=1.15)
    return cv.to_svg()


def fig_p446_inline(theme: Theme) -> str:
    cv = SvgCanvas(468, 78, theme)
    Spec = tuple[int | None, list["Spec"]]

    def L(lbl: int) -> Spec:
        return (lbl, [])

    def I(*ch: Spec) -> Spec:
        return (None, list(ch))

    trees: list[Spec] = [
        I(I(I(I(L(1))))),
        I(I(I(L(1), L(2)))),
        I(I(L(1), I(L(2)))),
        I(I(I(L(1)), L(2))),
        I(I(L(1), L(2), L(3))),
        I(I(L(1)), I(L(2))),
        I(L(1), I(I(L(2)))),
        I(I(I(L(1))), L(2)),
        I(L(1), I(L(2), L(3))),
        I(I(L(1), L(3)), L(2)),
        I(I(L(1), L(2)), L(3)),
        I(L(1), L(2), I(L(3))),
        I(L(1), I(L(2)), L(3)),
        I(I(L(1)), L(2), L(3)),
        I(L(1), L(2), L(3), L(4)),
    ]

    leaf_gap = 7.4
    dy = 12.2
    y_top = 12.0

    def leaf_count(sp: Spec) -> int:
        return 1 if not sp[1] else sum(leaf_count(c) for c in sp[1])

    widths = [max(1, leaf_count(t) - 1) * leaf_gap for t in trees]
    total_tree_w = sum(widths)
    gap = (468.0 - 28.0 - total_tree_w) / (len(trees) - 1)
    cur_x = 14.0

    edge_col = "#64748B" if theme.is_dark else theme.fg
    int_col = theme.cyan if theme.is_dark else theme.fg
    leaf_col = theme.gold if theme.is_dark else theme.fg

    for t, w in zip(trees, widths):
        leaf_idx = 0
        x_base = cur_x

        def draw_node(sp: Spec, depth: int, xb: float = x_base) -> float:
            nonlocal leaf_idx
            lbl, ch = sp
            ny = y_top + depth * dy
            if not ch:
                nx = xb + leaf_idx * leaf_gap
                leaf_idx += 1
                cv.circle(nx, ny, 2.1, fill=leaf_col, stroke="none")
                cv.text(nx, ny + 8.8, str(lbl), font_size=8.2, fill=leaf_col if theme.is_dark else theme.fg)
                return nx
            cxs = [draw_node(c, depth + 1, xb) for c in ch]
            nx = 0.5 * (cxs[0] + cxs[-1])
            for cx_child in cxs:
                cv.line(nx, ny, cx_child, ny + dy, stroke=edge_col, stroke_width=1.15)
            cv.circle(nx, ny, 2.1, fill=int_col, stroke="none")
            return nx

        draw_node(t, 0)
        cur_x += w + gap

    return cv.to_svg()


def _rgs_to_blocks(rgs: str) -> tuple[frozenset[int], ...]:
    groups: dict[str, set[int]] = {}
    for idx, ch in enumerate(rgs):
        groups.setdefault(ch, set()).add(idx)
    return tuple(frozenset(g) for g in groups.values())


def _refines(fine: tuple[frozenset[int], ...], coarse: tuple[frozenset[int], ...]) -> bool:
    return all(any(bf <= bc for bc in coarse) for bf in fine)


def fig_p447_inline(theme: Theme) -> str:
    cv = SvgCanvas(460, 146, theme)
    levels = [
        ["0123"],
        ["0012", "0102", "0112", "0120", "0121", "0122"],
        ["0001", "0010", "0011", "0100", "0101", "0110", "0111"],
        ["0000"],
    ]
    ys = [20.0, 55.0, 91.0, 126.0]
    pos: dict[str, tuple[float, float]] = {}
    for r_idx, row in enumerate(levels):
        m = len(row)
        if m == 1:
            pos[row[0]] = (230.0, ys[r_idx])
        else:
            span = 360.0 if m == 6 else 396.0
            x_start = 230.0 - span * 0.5
            step = span / (m - 1)
            for i, s in enumerate(row):
                pos[s] = (x_start + i * step, ys[r_idx])

    blocks = {s: _rgs_to_blocks(s) for row in levels for s in row}
    edge_col = "#4B6282" if theme.is_dark else "#475569"
    for r_idx in range(3):
        for s_hi in levels[r_idx]:
            x1, y1 = pos[s_hi]
            for s_lo in levels[r_idx + 1]:
                if _refines(blocks[s_hi], blocks[s_lo]):
                    x2, y2 = pos[s_lo]
                    cv.line(x1, y1 + 7.5, x2, y2 - 7.5, stroke=edge_col, stroke_width=1.05)

    row_accents = [theme.gold, theme.cyan, theme.mint, theme.violet]
    for r_idx, row in enumerate(levels):
        acc = row_accents[r_idx] if theme.is_dark else theme.fg
        for s in row:
            px, py = pos[s]
            _pill(cv, px, py, 34.0, 15.0, s, stroke=acc, font_size=9.2, mono=True)
    return cv.to_svg()


def fig_56(theme: Theme) -> str:
    cv = SvgCanvas(280, 122, theme)
    cell = 10.6

    def draw_board(x0: float, y0: float, row_lens: list[int], rooks: list[tuple[int, int]]) -> None:
        rook_set = set(rooks)
        grid_stroke = "#334766" if theme.is_dark else "#94A3B8"
        cell_fill = theme.cell_light if theme.is_dark else "#FFFFFF"
        for r, rlen in enumerate(row_lens):
            for c in range(rlen):
                cx = x0 + (c + 0.5) * cell
                cy = y0 + (r + 0.5) * cell
                cv.rect(x0 + c * cell, y0 + r * cell, cell, cell, fill=cell_fill, stroke=grid_stroke, stroke_width=0.8)
                if (r, c) in rook_set:
                    rcol = theme.gold if theme.is_dark else theme.fg
                    cv.circle(cx, cy, 2.7, fill=rcol, stroke="none", glow=theme.is_dark)
                else:
                    cancelled = any((rc == c and rr > r) or (rr == r and rc > c) for rr, rc in rooks)
                    if cancelled:
                        hcol = theme.cyan if theme.is_dark else theme.fg
                        cv.circle(cx, cy, 2.45, fill=cell_fill, stroke=hcol, stroke_width=1.05)

    draw_board(
        18.0,
        13.0,
        [3, 1, 4, 1, 5, 9, 2, 6, 5],
        [(2, 1), (3, 0), (5, 3), (7, 4)],
    )
    draw_board(
        166.0,
        13.0,
        [9] * 9,
        [(0, 6), (1, 2), (2, 5), (3, 3), (4, 7), (5, 1), (6, 8), (7, 0), (8, 4)],
    )
    return cv.to_svg()


def fig_p454_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(460, 44, theme)
    groups = [
        [(1, 2), (1, 3), (4, 1), (1, 5), (1, 6)],
        [(2, 3), (4, 2), (2, 5), (4, 3), (4, 5)],
        [(2, 6), (5, 3), (3, 6), (6, 4), (6, 5)],
    ]
    cell = 11.4
    plus_gap = 12.6
    eq_gap = 18.0
    group_w = 5 * cell + 4 * plus_gap
    total_w = 3 * group_w + 2 * eq_gap
    x = 0.5 * (460.0 - total_w)
    y = 10.6
    op_col = theme.muted if theme.is_dark else theme.fg
    for gi, grp in enumerate(groups):
        for di, (pa, pb) in enumerate(grp):
            cv.domino(x, y, pa, pb, vertical=True, cell=cell, inverted=True)
            x += cell
            if di < 4:
                cv.text(x + 0.5 * plus_gap, y + cell, "+", font_size=10.5, fill=op_col)
                x += plus_gap
        if gi < 2:
            cv.text(x + 0.5 * eq_gap, y + cell, "=", font_size=11.5, fill=theme.gold if theme.is_dark else theme.fg)
            x += eq_gap
    return cv.to_svg()


def fig_p454_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(320, 68, theme)
    s = "(())((())((()(()))())(()(())))"
    hex_digits = "123456789abcdef"
    x0 = 15.5
    dx = 9.95
    l_cnt = 0
    r_cnt = 0
    stack: list[tuple[int, int]] = []
    pairs: list[tuple[int, int, int]] = []

    for i, ch in enumerate(s):
        xi = x0 + i * dx
        cv.text(xi, 24.0, ch, font_size=11.5, mono=True, fill=theme.fg)
        if ch == "(":
            cv.text(
                xi,
                11.5,
                hex_digits[l_cnt],
                font_size=8.2,
                mono=True,
                fill=theme.cyan if theme.is_dark else theme.fg,
            )
            l_cnt += 1
            stack.append((i, 0))
        else:
            cv.text(
                xi,
                36.0,
                hex_digits[r_cnt],
                font_size=8.2,
                mono=True,
                fill=theme.gold if theme.is_dark else theme.fg,
            )
            r_cnt += 1
            open_i, max_inner = stack.pop()
            h = max_inner + 1
            pairs.append((open_i, i, h))
            if stack:
                pi, pm = stack[-1]
                stack[-1] = (pi, max(pm, h))

    palette = [theme.cyan, theme.mint, theme.gold, theme.coral, theme.violet]
    y_top = 42.5
    for i0, i1, h in pairs:
        xa = x0 + i0 * dx
        xb = x0 + i1 * dx
        yb = y_top + h * 4.1
        bcol = palette[(h - 1) % len(palette)] if theme.is_dark else theme.fg
        cv.polyline([(xa, y_top), (xa, yb), (xb, yb), (xb, y_top)], stroke=bcol, stroke_width=1.05, linejoin="miter")
    return cv.to_svg()


def _eq2_forest_geometry() -> tuple[dict[str, tuple[float, float]], list[tuple[str, str]], dict[str, list[str]]]:
    pos = {
        "12": (36.0, 22.0),
        "21": (36.0, 48.0),
        "3f": (172.0, 22.0),
        "44": (86.0, 48.0),
        "53": (86.0, 74.0),
        "6a": (154.0, 48.0),
        "78": (140.0, 74.0),
        "85": (120.0, 100.0),
        "97": (158.0, 100.0),
        "a6": (158.0, 126.0),
        "b9": (184.0, 74.0),
        "ce": (238.0, 48.0),
        "db": (218.0, 74.0),
        "ed": (256.0, 74.0),
        "fc": (256.0, 100.0),
    }
    children: dict[str, list[str]] = {
        "12": ["21"],
        "21": [],
        "3f": ["44", "6a", "ce"],
        "44": ["53"],
        "53": [],
        "6a": ["78", "b9"],
        "78": ["85", "97"],
        "85": [],
        "97": ["a6"],
        "a6": [],
        "b9": [],
        "ce": ["db", "ed"],
        "db": [],
        "ed": ["fc"],
        "fc": [],
    }
    edges = [(u, v) for u, ch in children.items() for v in ch]
    return pos, edges, children


def fig_p455_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(286, 146, theme)
    pos, edges, _ = _eq2_forest_geometry()
    r = 8.8
    t1_nodes = {"12", "21"}
    for u, v in edges:
        col = (theme.mint if u in t1_nodes else theme.cyan) if theme.is_dark else theme.fg
        cv.graph_edge(*pos[u], *pos[v], r1=r, r2=r, stroke=col, stroke_width=1.35)
    for name, (nx, ny) in pos.items():
        st = (theme.mint if name in t1_nodes else theme.cyan) if theme.is_dark else theme.fg
        cv.circle(nx, ny, r, fill=theme.node_fill, stroke=st, stroke_width=1.4)
        cv.text(nx, ny, name, font_size=8.6, mono=True, fill=theme.fg)
    return cv.to_svg()


def _worm_contour_path(
    pos: dict[str, tuple[float, float]],
    children: dict[str, list[str]],
    roots: list[str],
    rad: float,
    corridor_w: float,
    x_start: float,
    x_end: float,
) -> str:
    d_trim = math.sqrt(rad * rad - corridor_w * corridor_w)
    delta_ang = math.asin(corridor_w / rad)

    def arc_ccw(cx: float, cy: float, a_from: float, a_to: float) -> str:
        diff = (a_from - a_to) % (2.0 * math.pi)
        if diff < 1e-4:
            diff = 2.0 * math.pi
        ex = cx + rad * math.cos(a_to)
        ey = cy + rad * math.sin(a_to)
        large = 1 if diff > math.pi else 0
        return f"A {fmt(rad)} {fmt(rad)} 0 {large} 0 {fmt(ex)} {fmt(ey)}"

    def walk_subtree(u: str, in_ang: float, out_ang: float) -> list[str]:
        ux, uy = pos[u]
        ch = children[u]
        if not ch:
            return [arc_ccw(ux, uy, in_ang, out_ang)]
        cmds: list[str] = []
        cur_ang = in_ang
        for v in ch:
            vx, vy = pos[v]
            ang_uv = math.atan2(vy - uy, vx - ux)
            ang_vu = math.atan2(uy - vy, ux - vx)
            u_dep = ang_uv + delta_ang
            v_arr = ang_vu - delta_ang
            v_dep = ang_vu + delta_ang
            u_ret = ang_uv - delta_ang
            cmds.append(arc_ccw(ux, uy, cur_ang, u_dep))
            vx_arr = vx + rad * math.cos(v_arr)
            vy_arr = vy + rad * math.sin(v_arr)
            cmds.append(f"L {fmt(vx_arr)} {fmt(vy_arr)}")
            cmds.extend(walk_subtree(v, v_arr, v_dep))
            ux_ret = ux + rad * math.cos(u_ret)
            uy_ret = uy + rad * math.sin(u_ret)
            cmds.append(f"L {fmt(ux_ret)} {fmt(uy_ret)}")
            cur_ang = u_ret
        cmds.append(arc_ccw(ux, uy, cur_ang, out_ang))
        return cmds

    y_line = pos[roots[0]][1] - corridor_w
    parts = [f"M {fmt(x_start)} {fmt(y_line)}"]
    for r_node in roots:
        rx = pos[r_node][0]
        in_x = rx - d_trim
        parts.append(f"L {fmt(in_x)} {fmt(y_line)}")
        in_ang = math.atan2(-corridor_w, -d_trim)
        out_ang = math.atan2(-corridor_w, d_trim)
        parts.extend(walk_subtree(r_node, in_ang, out_ang))
    parts.append(f"L {fmt(x_end)} {fmt(y_line)}")
    return " ".join(parts)


def fig_p455_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(316, 148, theme)
    base_pos, edges, children = _eq2_forest_geometry()
    pos = {k: (x + 4.0, y + 2.0) for k, (x, y) in base_pos.items()}
    r_node = 7.2
    edge_col = theme.cyan if theme.is_dark else theme.fg
    for u, v in edges:
        cv.graph_edge(*pos[u], *pos[v], r1=r_node, r2=r_node, stroke=edge_col, stroke_width=1.25)
    for nx, ny in pos.values():
        cv.circle(nx, ny, r_node, fill=theme.node_fill, stroke=edge_col, stroke_width=1.35)

    rad = 10.2
    corridor_w = 2.65
    cpath = _worm_contour_path(pos, children, ["12", "3f"], rad, corridor_w, 12.0, 276.0)
    wcol = theme.gold if theme.is_dark else theme.fg
    cv.path(cpath, stroke=wcol, stroke_width=1.2, dashed="1.6,2.4")

    wy = pos["3f"][1] - corridor_w
    wx = 278.0
    worm_d = (
        f"M {fmt(wx)} {fmt(wy)} "
        f"C {fmt(wx + 4.0)} {fmt(wy - 0.3)} {fmt(wx + 7.2)} {fmt(wy + 2.8)} {fmt(wx + 10.6)} {fmt(wy + 2.8)} "
        f"C {fmt(wx + 14.5)} {fmt(wy + 2.8)} {fmt(wx + 17.5)} {fmt(wy - 1.2)} {fmt(wx + 21.5)} {fmt(wy - 1.2)} "
        f"C {fmt(wx + 22.8)} {fmt(wy - 1.2)} {fmt(wx + 23.2)} {fmt(wy - 3.4)} {fmt(wx + 21.2)} {fmt(wy - 3.4)} "
        f"C {fmt(wx + 17.2)} {fmt(wy - 3.4)} {fmt(wx + 14.2)} {fmt(wy + 0.6)} {fmt(wx + 10.6)} {fmt(wy + 0.6)} "
        f"C {fmt(wx + 7.6)} {fmt(wy + 0.6)} {fmt(wx + 4.4)} {fmt(wy - 2.1)} {fmt(wx + 0.8)} {fmt(wy - 1.8)}"
    )
    worm_fill = "#2B2612" if theme.is_dark else "#FFFFFF"
    cv.path(worm_d, stroke=wcol, stroke_width=1.1, fill=worm_fill)
    cv.circle(wx + 20.8, wy - 2.3, 0.75, fill=wcol, stroke="none")
    return cv.to_svg()


def fig_p455_inline_3(theme: Theme) -> str:
    cv = SvgCanvas(328, 174, theme)
    links: dict[str, tuple[str | None, str | None]] = {
        "12": ("21", "3f"),
        "21": (None, None),
        "3f": ("44", None),
        "44": ("53", "6a"),
        "53": (None, None),
        "6a": ("78", "ce"),
        "78": ("85", "b9"),
        "85": (None, "97"),
        "97": ("a6", None),
        "a6": (None, None),
        "b9": (None, None),
        "ce": ("db", None),
        "db": (None, "ed"),
        "ed": ("fc", None),
        "fc": (None, None),
    }
    slot = 0
    int_pos: dict[str, tuple[float, float]] = {}
    ext_list: list[tuple[str, bool, float, float]] = []
    x0, dx = 16.0, 9.85
    y0, dy = 18.0, 17.5

    def place(u: str | None, parent: str | None, is_left: bool, depth: int) -> None:
        nonlocal slot
        if u is None:
            sx = x0 + slot * dx
            sy = y0 + depth * dy
            slot += 1
            if parent is not None:
                ext_list.append((parent, is_left, sx, sy))
            return
        lc, rc = links[u]
        place(lc, u, True, depth + 1)
        ux = x0 + slot * dx
        uy = y0 + depth * dy
        slot += 1
        int_pos[u] = (ux, uy)
        place(rc, u, False, depth + 1)

    place("12", None, True, 0)

    r = 8.0
    sq = 5.2
    icol = theme.cyan if theme.is_dark else theme.fg
    ecol = theme.gold if theme.is_dark else theme.fg
    edge_col = "#64748B" if theme.is_dark else theme.fg

    for u, (lc, rc) in links.items():
        ux, uy = int_pos[u]
        for child in (lc, rc):
            if child is not None:
                cx_p, cy_p = int_pos[child]
                cv.graph_edge(ux, uy, cx_p, cy_p, r1=r, r2=r, stroke=edge_col, stroke_width=1.25)

    for parent, _, sx, sy in ext_list:
        px, py = int_pos[parent]
        cv.graph_edge(px, py, sx, sy, r1=r, r2=sq * 0.6, stroke=edge_col, stroke_width=1.05)
        cv.rect(
            sx - sq * 0.5,
            sy - sq * 0.5,
            sq,
            sq,
            fill=theme.sink_true_fill if theme.is_dark else "#FFFFFF",
            stroke=ecol,
            stroke_width=1.15,
        )

    for u, (ux, uy) in int_pos.items():
        cv.circle(ux, uy, r, fill=theme.node_fill, stroke=icol, stroke_width=1.35)
        cv.text(ux, uy, u, font_size=7.8, mono=True, fill=theme.fg)
    return cv.to_svg()


def _parens_to_forest_and_bt(s: str) -> tuple[Forest, BinTree]:
    idx = 0
    n = len(s)

    def parse_seq() -> tuple[Forest, BinTree]:
        nonlocal idx
        if idx >= n or s[idx] == ")":
            return (), None
        idx += 1
        inside_f, left_bt = parse_seq()
        idx += 1
        rest_f, right_bt = parse_seq()
        return (inside_f,) + rest_f, (left_bt, right_bt)

    return parse_seq()


def _links_to_bt_and_forest(root: int, l_arr: dict[int, int], r_arr: dict[int, int]) -> tuple[BinTree, Forest]:
    def build_bt(u: int) -> BinTree:
        if u == 0:
            return None
        return (build_bt(l_arr[u]), build_bt(r_arr[u]))

    def build_f(u: int) -> Forest:
        if u == 0:
            return ()
        return (build_f(l_arr[u]),) + build_f(r_arr[u])

    return build_bt(root), build_f(root)


def _mirror_forest(f: Forest) -> Forest:
    return tuple(_mirror_forest(c) for c in reversed(f))


def _mirror_bt(bt: BinTree) -> BinTree:
    if bt is None:
        return None
    return (_mirror_bt(bt[1]), _mirror_bt(bt[0]))


def _bt_to_forest(bt: BinTree) -> Forest:
    if bt is None:
        return ()
    return (_bt_to_forest(bt[0]),) + _bt_to_forest(bt[1])


def _forest_preorder_e_s(f: Forest) -> tuple[str, str]:
    e_list: list[str] = []
    s_list: list[str] = []

    def visit(node: ForestNode) -> int:
        idx = len(e_list)
        e_list.append(str(len(node)))
        s_list.append("0")
        desc = 0
        for ch in node:
            desc += 1 + visit(ch)
        s_list[idx] = str(desc)
        return desc

    for root in f:
        visit(root)
    return "".join(e_list), "".join(s_list)


def _draw_mini_forest(cv: SvgCanvas, cx: float, cy: float, f: Forest, accent: str | None = None) -> None:
    dx = 5.8
    dy = 4.9
    pts: list[tuple[float, float]] = []
    edges: list[tuple[float, float, float, float]] = []
    leaf_cursor = 0.0

    def layout_tree(node: ForestNode, depth: int) -> tuple[float, float]:
        nonlocal leaf_cursor
        ny = depth * dy
        if not node:
            nx = leaf_cursor * dx
            leaf_cursor += 1.0
            pts.append((nx, ny))
            return nx, ny
        child_coords = [layout_tree(ch, depth + 1) for ch in node]
        nx = 0.5 * (child_coords[0][0] + child_coords[-1][0])
        pts.append((nx, ny))
        for chx, chy in child_coords:
            edges.append((nx, ny, chx, chy))
        return nx, ny

    for i, r_node in enumerate(f):
        if i > 0:
            leaf_cursor += 0.25
        layout_tree(r_node, 0)

    if not pts:
        return
    min_x = min(p[0] for p in pts)
    max_x = max(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    max_y = max(p[1] for p in pts)
    ox = cx - 0.5 * (min_x + max_x)
    oy = cy - 0.5 * (min_y + max_y)
    col = accent or (cv.theme.cyan if cv.theme.is_dark else cv.theme.fg)
    edge_col = "#64748B" if cv.theme.is_dark else cv.theme.fg
    for x1, y1, x2, y2 in edges:
        cv.line(x1 + ox, y1 + oy, x2 + ox, y2 + oy, stroke=edge_col, stroke_width=0.95)
    for px, py in pts:
        cv.circle(px + ox, py + oy, 1.45, fill=col, stroke="none")


def _draw_mini_bt(cv: SvgCanvas, cx: float, cy: float, bt: BinTree, accent: str | None = None) -> None:
    dx = 3.35
    dy = 3.85
    slot = 0
    int_pts: list[tuple[float, float]] = []
    ext_pts: list[tuple[float, float]] = []
    edges: list[tuple[float, float, float, float]] = []

    def walk(node: BinTree, depth: int) -> tuple[float, float]:
        nonlocal slot
        if node is None:
            nx = slot * dx
            ny = depth * dy
            slot += 1
            ext_pts.append((nx, ny))
            return nx, ny
        lx, ly = walk(node[0], depth + 1)
        nx = slot * dx
        ny = depth * dy
        slot += 1
        int_pts.append((nx, ny))
        rx, ry = walk(node[1], depth + 1)
        edges.append((nx, ny, lx, ly))
        edges.append((nx, ny, rx, ry))
        return nx, ny

    walk(bt, 0)
    all_pts = int_pts + ext_pts
    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)
    ox = cx - 0.5 * (min_x + max_x)
    oy = cy - 0.5 * (min_y + max_y)
    icol = accent or (cv.theme.cyan if cv.theme.is_dark else cv.theme.fg)
    ecol = cv.theme.gold if cv.theme.is_dark else cv.theme.fg
    edge_col = "#64748B" if cv.theme.is_dark else cv.theme.fg
    for x1, y1, x2, y2 in edges:
        cv.line(x1 + ox, y1 + oy, x2 + ox, y2 + oy, stroke=edge_col, stroke_width=0.85)
    sq = 2.1
    sfill = cv.theme.sink_true_fill if cv.theme.is_dark else "#FFFFFF"
    for ex, ey in ext_pts:
        cv.rect(ex + ox - sq * 0.5, ey + oy - sq * 0.5, sq, sq, fill=sfill, stroke=ecol, stroke_width=0.75)
    for ix, iy in int_pts:
        cv.circle(ix + ox, iy + oy, 1.4, fill=icol, stroke="none")


def _draw_mini_matching(cv: SvgCanvas, cx: float, cy: float, s: str) -> None:
    rad = 8.4
    ring_col = "#334766" if cv.theme.is_dark else "#CBD5E1"
    cv.circle(cx, cy, rad, fill="none", stroke=ring_col, stroke_width=0.75)
    pts = []
    for k in range(8):
        ang = 0.5 * math.pi - k * (0.25 * math.pi)
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    stack: list[int] = []
    chord_col = cv.theme.gold if cv.theme.is_dark else cv.theme.fg
    for i, ch in enumerate(s):
        if ch == "(":
            stack.append(i)
        else:
            j = stack.pop()
            cv.line(pts[j][0], pts[j][1], pts[i][0], pts[i][1], stroke=chord_col, stroke_width=1.0)
    dot_col = cv.theme.cyan if cv.theme.is_dark else cv.theme.fg
    for px, py in pts:
        cv.circle(px, py, 1.25, fill=dot_col, stroke="none")


def _alg_p_strings(n: int = 4) -> list[str]:
    a = ["("] + ["()"[k % 2] for k in range(2 * n)]
    a[0] = ")"
    out: list[str] = []
    m = 2 * n - 1
    while True:
        out.append("".join(a[1 : 2 * n + 1]))
        a[m] = ")"
        if a[m - 1] == ")":
            a[m - 1] = "("
            m -= 1
        else:
            j = m - 1
            k = 2 * n - 1
            while a[j] == "(":
                a[j] = ")"
                a[k] = "("
                j -= 1
                k -= 2
            if j == 0:
                break
            a[j] = "("
            m = 2 * n - 1
    return out


def fig_p456_table1(theme: Theme) -> str:
    rows = _alg_p_strings(4)
    row_h = 23.0
    y_head = 19.0
    y_rule1 = 30.0
    h_total = y_rule1 + len(rows) * row_h + 12.0
    cv = SvgCanvas(460, h_total, theme)

    cols = [42.0, 108.0, 172.0, 232.0, 280.0, 328.0, 376.0, 426.0]
    headers = [
        ("a_1a_2…a_8", True),
        ("forest", False),
        ("binary tree", False),
        ("d_1d_2d_3d_4", True),
        ("z_1z_2z_3z_4", True),
        ("p_1p_2p_3p_4", True),
        ("c_1c_2c_3c_4", True),
        ("matching", False),
    ]
    rule_col = "#334766" if theme.is_dark else "#0F172A"
    cv.line(10.0, 7.0, 450.0, 7.0, stroke=rule_col, stroke_width=1.15)
    for x, (lbl, is_math) in zip(cols, headers):
        if is_math:
            _text_clean(cv, x, y_head, lbl, font_size=9.0, fill=theme.fg, italic=True)
        else:
            cv.text(x, y_head, lbl, font_size=9.0, fill=theme.fg)
    cv.line(10.0, y_rule1, 450.0, y_rule1, stroke=rule_col, stroke_width=0.85)

    for r_idx, s in enumerate(rows):
        ry = y_rule1 + (r_idx + 0.5) * row_h
        if theme.is_dark and r_idx % 2 == 1:
            cv.rect(10.0, ry - 0.5 * row_h, 440.0, row_h, fill="#111A2B", stroke="none")
        f, bt = _parens_to_forest_and_bt(s)
        z_vals = [i + 1 for i, ch in enumerate(s) if ch == "("]
        d_vals = [
            z_vals[k + 1] - z_vals[k] - 1 if k < 3 else 8 - z_vals[3]
            for k in range(4)
        ]
        c_vals = [2 * (k + 1) - 1 - z_vals[k] for k in range(4)]
        stack: list[int] = []
        p_vals: list[int] = []
        l_num = 0
        for ch in s:
            if ch == "(":
                l_num += 1
                stack.append(l_num)
            else:
                p_vals.append(stack.pop())

        cv.text(cols[0], ry, s, font_size=8.8, mono=True, fill=theme.fg)
        _draw_mini_forest(cv, cols[1], ry, f, accent=theme.mint if theme.is_dark else None)
        _draw_mini_bt(cv, cols[2], ry, bt, accent=theme.cyan if theme.is_dark else None)
        cv.text(cols[3], ry, "".join(map(str, d_vals)), font_size=9.0, mono=True, fill=theme.fg)
        cv.text(cols[4], ry, "".join(map(str, z_vals)), font_size=9.0, mono=True, fill=theme.fg)
        cv.text(cols[5], ry, "".join(map(str, p_vals)), font_size=9.0, mono=True, fill=theme.fg)
        cv.text(cols[6], ry, "".join(map(str, c_vals)), font_size=9.0, mono=True, fill=theme.fg)
        _draw_mini_matching(cv, cols[7], ry, s)

    cv.line(10.0, y_rule1 + len(rows) * row_h, 450.0, y_rule1 + len(rows) * row_h, stroke=rule_col, stroke_width=1.15)
    return cv.to_svg()


def _alg_b_trees(n: int = 4) -> list[tuple[dict[int, int], dict[int, int]]]:
    l_arr = {k: (k + 1 if k < n else 0) for k in range(1, n + 1)}
    l_arr[n + 1] = 1
    r_arr = {k: 0 for k in range(1, n + 1)}
    out: list[tuple[dict[int, int], dict[int, int]]] = []
    while True:
        out.append(({k: l_arr[k] for k in range(1, n + 1)}, {k: r_arr[k] for k in range(1, n + 1)}))
        j = 1
        while l_arr[j] == 0:
            r_arr[j] = 0
            l_arr[j] = j + 1
            j += 1
        if j > n:
            break
        y = l_arr[j]
        k = 0
        while r_arr[y] > 0:
            k = y
            y = r_arr[y]
        if k > 0:
            r_arr[k] = 0
        else:
            l_arr[j] = 0
        r_arr[y] = r_arr[j]
        r_arr[j] = y
    return out


def _forest_to_bt(f: Forest) -> BinTree:
    if not f:
        return None
    return (_forest_to_bt(f[0]), _forest_to_bt(f[1:]))


def fig_p459_table2(theme: Theme) -> str:
    b_rows = _alg_b_trees(4)
    p_rows = _alg_p_strings(4)
    row_h = 22.5
    y_head = 19.0
    y_rule1 = 30.0
    h_total = y_rule1 + len(b_rows) * row_h + 12.0
    cv = SvgCanvas(460, h_total, theme)

    cols = [34.0, 82.0, 140.0, 200.0, 254.0, 302.0, 360.0, 420.0]
    headers = [
        ("l_1l_2l_3l_4", True),
        ("r_1r_2r_3r_4", True),
        ("binary tree", False),
        ("forest", False),
        ("e_1e_2e_3e_4", True),
        ("s_1s_2s_3s_4", True),
        ("colex forest", False),
        ("lsib/rchild", False),
    ]
    rule_col = "#334766" if theme.is_dark else "#0F172A"
    cv.line(10.0, 7.0, 450.0, 7.0, stroke=rule_col, stroke_width=1.15)
    for x, (lbl, is_math) in zip(cols, headers):
        if is_math:
            _text_clean(cv, x, y_head, lbl, font_size=9.0, fill=theme.fg, italic=True)
        else:
            cv.text(x, y_head, lbl, font_size=9.0, fill=theme.fg)
    cv.line(10.0, y_rule1, 450.0, y_rule1, stroke=rule_col, stroke_width=0.85)

    for r_idx, ((l_arr, r_arr), p_str) in enumerate(zip(b_rows, p_rows)):
        ry = y_rule1 + (r_idx + 0.5) * row_h
        if theme.is_dark and r_idx % 2 == 1:
            cv.rect(10.0, ry - 0.5 * row_h, 440.0, row_h, fill="#111A2B", stroke="none")
        bt, f = _links_to_bt_and_forest(1, l_arr, r_arr)
        e_str, s_str = _forest_preorder_e_s(f)
        p_f, _ = _parens_to_forest_and_bt(p_str)
        colex_f = _mirror_forest(p_f)
        lsib_bt = _forest_to_bt(colex_f)

        l_str = "".join(str(l_arr[i]) for i in range(1, 5))
        r_str = "".join(str(r_arr[i]) for i in range(1, 5))
        cv.text(cols[0], ry, l_str, font_size=9.0, mono=True, fill=theme.fg)
        cv.text(cols[1], ry, r_str, font_size=9.0, mono=True, fill=theme.fg)
        _draw_mini_bt(cv, cols[2], ry, bt, accent=theme.cyan if theme.is_dark else None)
        _draw_mini_forest(cv, cols[3], ry, f, accent=theme.mint if theme.is_dark else None)
        cv.text(cols[4], ry, e_str, font_size=9.0, mono=True, fill=theme.fg)
        cv.text(cols[5], ry, s_str, font_size=9.0, mono=True, fill=theme.fg)
        _draw_mini_forest(cv, cols[6], ry, colex_f, accent=theme.violet if theme.is_dark else None)
        _draw_mini_bt(cv, cols[7], ry, lsib_bt, accent=theme.coral if theme.is_dark else None)

    cv.line(10.0, y_rule1 + len(b_rows) * row_h, 450.0, y_rule1 + len(b_rows) * row_h, stroke=rule_col, stroke_width=1.15)
    return cv.to_svg()


def fig_p461_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(296, 98, theme)
    col_a = theme.cyan if theme.is_dark else theme.fg
    col_b = theme.gold if theme.is_dark else theme.fg
    col_sub = theme.mint if theme.is_dark else theme.fg
    edge_col = "#64748B" if theme.is_dark else theme.fg
    r = 9.0

    cv.text(22.0, 48.0, "from", font_size=11.0, fill=theme.muted if theme.is_dark else theme.fg)

    ax1, ay1 = 80.0, 30.0
    bx1, by1 = 104.0, 54.0
    cv.line(ax1, 10.0, ax1, ay1 - r, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(ax1, ay1, 56.0, 54.0, r1=r, r2=7.0, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(ax1, ay1, bx1, by1, r1=r, r2=r, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(bx1, by1, 82.0, 80.0, r1=r, r2=7.0, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(bx1, by1, 126.0, 80.0, r1=r, r2=7.0, stroke=edge_col, stroke_width=1.3)
    cv.graph_node(ax1, ay1, "A", r=r, stroke=col_a, font_size=9.5, italic=True)
    cv.graph_node(bx1, by1, "B", r=r, stroke=col_b, font_size=9.5, italic=True)
    _pill(cv, 56.0, 56.0, 21.0, 12.5, "α", stroke=col_sub, font_size=9.5, italic=True)
    _pill(cv, 82.0, 82.0, 21.0, 12.5, "μ", stroke=col_sub, font_size=9.5, italic=True)
    _pill(cv, 126.0, 82.0, 21.0, 12.5, "ω", stroke=col_sub, font_size=9.5, italic=True)

    cv.text(158.0, 48.0, "to", font_size=11.0, fill=theme.muted if theme.is_dark else theme.fg)

    bx2, by2 = 236.0, 30.0
    ax2, ay2 = 212.0, 54.0
    cv.line(bx2, 10.0, bx2, by2 - r, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(bx2, by2, ax2, ay2, r1=r, r2=r, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(bx2, by2, 260.0, 54.0, r1=r, r2=7.0, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(ax2, ay2, 190.0, 80.0, r1=r, r2=7.0, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(ax2, ay2, 234.0, 80.0, r1=r, r2=7.0, stroke=edge_col, stroke_width=1.3)
    cv.graph_node(bx2, by2, "B", r=r, stroke=col_b, font_size=9.5, italic=True)
    cv.graph_node(ax2, ay2, "A", r=r, stroke=col_a, font_size=9.5, italic=True)
    _pill(cv, 190.0, 82.0, 21.0, 12.5, "α", stroke=col_sub, font_size=9.5, italic=True)
    _pill(cv, 234.0, 82.0, 21.0, 12.5, "μ", stroke=col_sub, font_size=9.5, italic=True)
    _pill(cv, 260.0, 56.0, 21.0, 12.5, "ω", stroke=col_sub, font_size=9.5, italic=True)
    return cv.to_svg()


def fig_p461_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(348, 102, theme)
    col_a = theme.cyan if theme.is_dark else theme.fg
    col_b = theme.gold if theme.is_dark else theme.fg
    col_sub = theme.mint if theme.is_dark else theme.fg
    edge_col = "#64748B" if theme.is_dark else theme.fg
    r = 8.6

    cv.text(20.0, 46.0, "from", font_size=11.0, fill=theme.muted if theme.is_dark else theme.fg)

    px1, py1 = 98.0, 12.0
    xs1 = [54.0, 84.0, 114.0, 144.0]
    y_row1 = 36.0
    cv.path(f"M {fmt(px1 - 14.0)} {fmt(py1)} Q {fmt(xs1[0] + 6.0)} {fmt(py1 + 6.0)} {fmt(xs1[0])} {fmt(y_row1 - 6.5)}", stroke=edge_col, stroke_width=1.2)
    cv.line(px1 - 5.0, py1, xs1[1], y_row1 - r, stroke=edge_col, stroke_width=1.2)
    cv.line(px1 + 5.0, py1, xs1[2], y_row1 - r, stroke=edge_col, stroke_width=1.2)
    cv.path(f"M {fmt(px1 + 14.0)} {fmt(py1)} Q {fmt(xs1[3] - 6.0)} {fmt(py1 + 6.0)} {fmt(xs1[3])} {fmt(y_row1 - 6.5)}", stroke=edge_col, stroke_width=1.2)
    cv.line(xs1[1], y_row1 + r, xs1[1], 56.0, stroke=edge_col, stroke_width=1.2)
    cv.line(xs1[2], y_row1 + r, xs1[2], 56.0, stroke=edge_col, stroke_width=1.2)

    _pill(cv, xs1[0], y_row1, 22.0, 12.5, "⋯", stroke=col_sub, font_size=9.5)
    cv.graph_node(xs1[1], y_row1, "A", r=r, stroke=col_a, font_size=9.2, italic=True)
    cv.graph_node(xs1[2], y_row1, "B", r=r, stroke=col_b, font_size=9.2, italic=True)
    _pill(cv, xs1[3], y_row1, 22.0, 12.5, "ω", stroke=col_sub, font_size=9.5, italic=True)
    _pill(cv, xs1[1], 62.5, 22.0, 12.5, "α", stroke=col_sub, font_size=9.5, italic=True)
    _pill(cv, xs1[2], 62.5, 22.0, 12.5, "μ", stroke=col_sub, font_size=9.5, italic=True)

    cv.text(178.0, 46.0, "to", font_size=11.0, fill=theme.muted if theme.is_dark else theme.fg)

    px2, py2 = 264.0, 12.0
    xs2 = [218.0, 264.0, 310.0]
    cv.path(f"M {fmt(px2 - 13.0)} {fmt(py2)} Q {fmt(xs2[0] + 6.0)} {fmt(py2 + 6.0)} {fmt(xs2[0])} {fmt(y_row1 - 6.5)}", stroke=edge_col, stroke_width=1.2)
    cv.line(px2, py2, xs2[1], y_row1 - r, stroke=edge_col, stroke_width=1.2)
    cv.path(f"M {fmt(px2 + 13.0)} {fmt(py2)} Q {fmt(xs2[2] - 6.0)} {fmt(py2 + 6.0)} {fmt(xs2[2])} {fmt(y_row1 - 6.5)}", stroke=edge_col, stroke_width=1.2)
    ax2, ay2 = 247.0, 62.5
    mx2, my2 = 282.0, 62.5
    cv.graph_edge(xs2[1], y_row1, ax2, ay2, r1=r, r2=r, stroke=edge_col, stroke_width=1.2)
    cv.graph_edge(xs2[1], y_row1, mx2, my2, r1=r, r2=6.5, stroke=edge_col, stroke_width=1.2)
    cv.line(ax2, ay2 + r, ax2, 82.0, stroke=edge_col, stroke_width=1.2)

    _pill(cv, xs2[0], y_row1, 22.0, 12.5, "⋯", stroke=col_sub, font_size=9.5)
    cv.graph_node(xs2[1], y_row1, "B", r=r, stroke=col_b, font_size=9.2, italic=True)
    _pill(cv, xs2[2], y_row1, 22.0, 12.5, "ω", stroke=col_sub, font_size=9.5, italic=True)
    cv.graph_node(ax2, ay2, "A", r=r, stroke=col_a, font_size=9.2, italic=True)
    _pill(cv, mx2, my2, 22.0, 12.5, "μ", stroke=col_sub, font_size=9.5, italic=True)
    _pill(cv, ax2, 88.5, 22.0, 12.5, "α", stroke=col_sub, font_size=9.5, italic=True)
    return cv.to_svg()


def fig_p461_inline_3(theme: Theme) -> str:
    cv = SvgCanvas(280, 62, theme)
    col_a = theme.cyan if theme.is_dark else theme.fg
    col_b = theme.gold if theme.is_dark else theme.fg
    hi_col = theme.coral if theme.is_dark else theme.fg
    r = 8.8
    cv.line(54.0, 9.0, 54.0, 24.0 - r, stroke=hi_col, stroke_width=1.5, arrow_end=True)
    cv.graph_node(54.0, 24.0, "A", r=r, stroke=col_a, font_size=9.2, italic=True)
    cv.graph_edge(54.0, 24.0, 82.0, 44.0, r1=r, r2=r, stroke=hi_col, stroke_width=1.5, directed=True)
    cv.graph_node(82.0, 44.0, "B", r=r, stroke=col_b, font_size=9.2, italic=True)
    cv.line(82.0 - 6.2, 44.0 + 6.2, 69.0, 55.0, stroke=hi_col, stroke_width=1.5, arrow_end=True)

    cv.line(110.0, 32.0, 138.0, 32.0, stroke=theme.muted if theme.is_dark else theme.fg, stroke_width=1.3, arrow_start=True, arrow_end=True)

    cv.line(184.0, 9.0, 184.0, 24.0 - r, stroke=hi_col, stroke_width=1.5, arrow_end=True)
    cv.graph_node(184.0, 24.0, "B", r=r, stroke=col_b, font_size=9.2, italic=True)
    cv.graph_edge(184.0, 24.0, 156.0, 44.0, r1=r, r2=r, stroke=hi_col, stroke_width=1.5, directed=True)
    cv.graph_node(156.0, 44.0, "A", r=r, stroke=col_a, font_size=9.2, italic=True)
    cv.line(156.0 + 6.2, 44.0 + 6.2, 169.0, 55.0, stroke=hi_col, stroke_width=1.5, arrow_end=True)

    cv.text(236.0, 32.0, "(αμ)ω = α(μω)", font_size=9.5, italic=True, fill=theme.fg)
    return cv.to_svg()


def fig_p461_inline_4(theme: Theme) -> str:
    cv = SvgCanvas(456, 118, theme)
    col_a = theme.cyan if theme.is_dark else theme.fg
    col_n = theme.gold if theme.is_dark else theme.fg
    col_sub = theme.mint if theme.is_dark else theme.fg
    edge_col = "#64748B" if theme.is_dark else theme.fg
    r = 8.4

    def draw_apair(ax: float, ay: float, idx: int) -> None:
        cv.line(ax, ay + r, ax, ay + 25.0 - 6.0, stroke=edge_col, stroke_width=1.15)
        cv.circle(ax, ay, r, fill=theme.node_fill, stroke=col_a, stroke_width=1.45)
        _text_clean(cv, ax, ay, f"A_{idx}", font_size=8.2, fill=theme.fg, italic=True)
        _pill(cv, ax, ay + 25.0, 20.5, 11.8, f"α_{idx}", stroke=col_sub, font_size=8.2, italic=True, rich=True)

    def top_fan(px: float, py: float, targets: list[tuple[float, float]]) -> None:
        m = len(targets)
        for i, (tx, ty) in enumerate(targets):
            off = (i - 0.5 * (m - 1)) * 6.5
            if i == 0 or i == m - 1:
                mx = 0.5 * (px + off + tx)
                cv.path(f"M {fmt(px + off)} {fmt(py)} Q {fmt(mx)} {fmt(py + 5.0)} {fmt(tx)} {fmt(ty - r)}", stroke=edge_col, stroke_width=1.15)
            else:
                cv.line(px + off, py, tx, ty - r, stroke=edge_col, stroke_width=1.15)

    y_top = 34.0
    xs1 = [22.0, 48.0, 74.0, 100.0]
    top_fan(61.0, 11.0, [(x, y_top) for x in xs1])
    for i in range(3):
        draw_apair(xs1[i], y_top, i + 1)
    cv.graph_node(xs1[3], y_top, "n", r=r, stroke=col_n, font_size=8.8, italic=True)
    cv.text(114.0, 56.0, ",", font_size=12.0, fill=theme.fg)

    xs2 = [132.0, 158.0, 184.0]
    top_fan(158.0, 11.0, [(x, y_top) for x in xs2])
    draw_apair(xs2[0], y_top, 1)
    draw_apair(xs2[1], y_top, 2)
    cv.graph_node(xs2[2], y_top, "n", r=r, stroke=col_n, font_size=8.8, italic=True)
    cv.line(xs2[2], y_top + r, xs2[2], 62.0 - r, stroke=edge_col, stroke_width=1.15)
    draw_apair(xs2[2], 62.0, 3)
    cv.text(200.0, 56.0, ",", font_size=12.0, fill=theme.fg)

    xs3 = [220.0, 260.0]
    top_fan(240.0, 11.0, [(x, y_top) for x in xs3])
    draw_apair(xs3[0], y_top, 1)
    cv.graph_node(xs3[1], y_top, "n", r=r, stroke=col_n, font_size=8.8, italic=True)
    cv.graph_edge(xs3[1], y_top, 246.0, 62.0, r1=r, r2=r, stroke=edge_col, stroke_width=1.15)
    cv.graph_edge(xs3[1], y_top, 274.0, 62.0, r1=r, r2=r, stroke=edge_col, stroke_width=1.15)
    draw_apair(246.0, 62.0, 2)
    draw_apair(274.0, 62.0, 3)
    cv.text(294.0, 56.0, ",", font_size=12.0, fill=theme.fg)

    nx4 = 374.0
    cv.line(nx4, 11.0, nx4, y_top - r, stroke=edge_col, stroke_width=1.15)
    cv.graph_node(nx4, y_top, "n", r=r, stroke=col_n, font_size=8.8, italic=True)
    for cx_c, idx in [(346.0, 1), (374.0, 2), (402.0, 3)]:
        cv.graph_edge(nx4, y_top, cx_c, 62.0, r1=r, r2=r, stroke=edge_col, stroke_width=1.15)
        draw_apair(cx_c, 62.0, idx)
    return cv.to_svg()


def _alg_l_trees(n: int = 4) -> list[tuple[dict[int, int], dict[int, int], dict[int, int]]]:
    l_arr = {j: 0 for j in range(n + 1)}
    l_arr[0] = 1
    r_arr = {j: (j + 1 if j < n else 0) for j in range(1, n + 1)}
    k_arr = {j: j - 1 for j in range(1, n + 1)}
    o_arr = {j: -1 for j in range(1, n + 1)}
    o_arr[0] = 1
    out: list[tuple[dict[int, int], dict[int, int], dict[int, int]]] = []
    while True:
        out.append((dict(l_arr), dict(r_arr), dict(k_arr)))
        j = n
        p = 0
        while True:
            if o_arr[j] > 0:
                m = l_arr[j]
                if m != 0:
                    action = "R"
                    break
            else:
                m = k_arr[j]
                if m != 0:
                    action = "L"
                    break
                p = j
            o_arr[j] = -o_arr[j]
            j -= 1
            if j == 0:
                return out
        if action == "L":
            r_arr[m] = l_arr[j]
            l_arr[j] = m
            x = k_arr[m]
            k_arr[j] = x
            if x == 0:
                l_arr[p] = j
            else:
                r_arr[x] = j
        else:
            l_arr[j] = r_arr[m]
            r_arr[m] = j
            k_arr[j] = m
            x = k_arr[m]
            if x == 0:
                l_arr[p] = m
            else:
                r_arr[x] = m


def fig_p463_table3(theme: Theme) -> str:
    l_rows = _alg_l_trees(4)
    row_h = 22.5
    y_head = 19.0
    y_rule1 = 30.0
    h_total = y_rule1 + len(l_rows) * row_h + 12.0
    cv = SvgCanvas(468, h_total, theme)

    cols = [34.0, 82.0, 126.0, 178.0, 232.0, 282.0, 334.0, 384.0, 434.0]
    headers = [
        ("l_0l_1l_2l_3l_4", True),
        ("r_1r_2r_3r_4", True),
        ("k_1k_2k_3k_4", True),
        ("binary tree", False),
        ("forest", False),
        ("q_1q_2q_3q_4", True),
        ("coforest", False),
        ("u_1u_2u_3u_4", True),
        ("dual", False),
    ]
    rule_col = "#334766" if theme.is_dark else "#0F172A"
    cv.line(8.0, 7.0, 460.0, 7.0, stroke=rule_col, stroke_width=1.15)
    for x, (lbl, is_math) in zip(cols, headers):
        if is_math:
            _text_clean(cv, x, y_head, lbl, font_size=8.7, fill=theme.fg, italic=True)
        else:
            cv.text(x, y_head, lbl, font_size=8.7, fill=theme.fg)
    cv.line(8.0, y_rule1, 460.0, y_rule1, stroke=rule_col, stroke_width=0.85)

    for r_idx, (l_arr, r_arr, k_arr) in enumerate(l_rows):
        ry = y_rule1 + (r_idx + 0.5) * row_h
        if theme.is_dark and r_idx % 2 == 1:
            cv.rect(8.0, ry - 0.5 * row_h, 452.0, row_h, fill="#111A2B", stroke="none")
        root = l_arr[0]
        l_sub = {i: l_arr[i] for i in range(1, 5)}
        bt, f = _links_to_bt_and_forest(root, l_sub, r_arr)
        q_order: list[int] = []

        def pre(
            u: int,
            acc: list[int] = q_order,
            lm: dict[int, int] = l_sub,
            rm: dict[int, int] = r_arr,
        ) -> None:
            if u == 0:
                return
            acc.append(u)
            pre(lm[u], acc, lm, rm)
            pre(rm[u], acc, lm, rm)

        pre(root)
        cof = _mirror_forest(f)
        _, u_str = _forest_preorder_e_s(cof)
        dual_f = _bt_to_forest(_mirror_bt(bt))

        cv.text(cols[0], ry, "".join(str(l_arr[i]) for i in range(5)), font_size=8.8, mono=True, fill=theme.fg)
        cv.text(cols[1], ry, "".join(str(r_arr[i]) for i in range(1, 5)), font_size=8.8, mono=True, fill=theme.fg)
        cv.text(cols[2], ry, "".join(str(k_arr[i]) for i in range(1, 5)), font_size=8.8, mono=True, fill=theme.fg)
        _draw_mini_bt(cv, cols[3], ry, bt, accent=theme.cyan if theme.is_dark else None)
        _draw_mini_forest(cv, cols[4], ry, f, accent=theme.mint if theme.is_dark else None)
        cv.text(cols[5], ry, "".join(map(str, q_order)), font_size=8.8, mono=True, fill=theme.fg)
        _draw_mini_forest(cv, cols[6], ry, cof, accent=theme.violet if theme.is_dark else None)
        cv.text(cols[7], ry, u_str, font_size=8.8, mono=True, fill=theme.fg)
        _draw_mini_forest(cv, cols[8], ry, dual_f, accent=theme.gold if theme.is_dark else None)

    cv.line(8.0, y_rule1 + len(l_rows) * row_h, 460.0, y_rule1 + len(l_rows) * row_h, stroke=rule_col, stroke_width=1.15)
    return cv.to_svg()


def fig_p465_inline(theme: Theme) -> str:
    cv = SvgCanvas(376, 108, theme)
    RT = tuple[str, list["RT"]]
    tree: RT = (
        "34",
        [
            ("23", [("12", [("01", []), ("02", [])]), ("13", [("01", []), ("02", []), ("03", [])])]),
            (
                "24",
                [
                    ("12", [("01", []), ("02", [])]),
                    ("13", [("01", []), ("02", []), ("03", [])]),
                    ("14", [("01", []), ("02", []), ("03", []), ("04", [])]),
                ],
            ),
        ],
    )
    leaf_idx = 0
    x0, dx = 18.0, 26.2
    ys = [16.0, 42.0, 68.0, 94.0]
    accents = [theme.gold, theme.coral, theme.cyan, theme.mint]
    edge_col = "#4B6282" if theme.is_dark else "#475569"

    def draw_rt(node: RT, depth: int) -> float:
        nonlocal leaf_idx
        lbl, ch = node
        ny = ys[depth]
        if not ch:
            nx = x0 + leaf_idx * dx
            leaf_idx += 1
        else:
            cxs = [draw_rt(c, depth + 1) for c in ch]
            nx = 0.5 * (cxs[0] + cxs[-1])
            for cx_c in cxs:
                cv.line(nx, ny + 6.5, cx_c, ys[depth + 1] - 6.5, stroke=edge_col, stroke_width=1.1)
        st = accents[depth] if theme.is_dark else theme.fg
        _pill(cv, nx, ny, 21.0, 13.0, lbl, stroke=st, font_size=8.6, mono=True)
        return nx

    draw_rt(tree, 0)
    return cv.to_svg()


def fig_p466_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(240, 168, theme)
    x0, dx = 30.0, 44.0
    y0, dy = 18.0, 29.0
    pw, ph = 23.0, 13.5
    edge_col = theme.cyan if theme.is_dark else theme.fg
    cont_col = theme.muted if theme.is_dark else theme.fg

    for q in range(5):
        for p in range(q + 1):
            cx = x0 + p * dx
            cy = y0 + q * dy
            if p <= q - 1:
                cv.line(cx, cy - ph * 0.5, cx, cy - dy + ph * 0.5 + 1.0, stroke=edge_col, stroke_width=1.2, arrow_end=True)
            if p >= 1:
                cv.line(cx - pw * 0.5, cy, cx - dx + pw * 0.5 + 1.0, cy, stroke=edge_col, stroke_width=1.2, arrow_end=True)
            if q == 4:
                cv.line(cx, cy + 20.0, cx, cy + ph * 0.5 + 1.0, stroke=cont_col, stroke_width=1.1, arrow_end=True)

    for q in range(5):
        for p in range(q + 1):
            cx = x0 + p * dx
            cy = y0 + q * dy
            st = (theme.gold if (p == 0 and q == 0) else (theme.violet if p == q else theme.cyan)) if theme.is_dark else theme.fg
            _pill(cv, cx, cy, pw, ph, f"{p}{q}", stroke=st, font_size=8.8, mono=True)
    return cv.to_svg()


def fig_p466_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(280, 74, theme)
    up_col = theme.mint if theme.is_dark else theme.fg
    left_col = theme.coral if theme.is_dark else theme.fg
    _pill(cv, 240.0, 48.0, 26.0, 14.0, "nn", stroke=theme.violet if theme.is_dark else theme.fg, font_size=9.2, italic=True)
    cv.line(225.0, 48.0, 182.0, 48.0, stroke=theme.muted if theme.is_dark else theme.fg, stroke_width=1.2, dashed="2.5,2.5", arrow_end=True)
    _pill(cv, 165.0, 48.0, 26.0, 14.0, "pq", stroke=theme.gold if theme.is_dark else theme.fg, font_size=9.2, italic=True)

    cv.line(165.0, 40.0, 165.0, 25.0, stroke=up_col, stroke_width=1.3, arrow_end=True)
    _pill(cv, 165.0, 15.5, 34.0, 13.0, "p,q−1", stroke=up_col, font_size=8.0, italic=True)
    cv.text(212.0, 15.5, "emit ')'", font_size=8.5, fill=up_col)

    cv.line(150.0, 48.0, 108.0, 48.0, stroke=left_col, stroke_width=1.3, arrow_end=True)
    _pill(cv, 87.0, 48.0, 34.0, 13.0, "p−1,q", stroke=left_col, font_size=8.0, italic=True)
    cv.text(38.0, 48.0, "emit '('", font_size=8.5, fill=left_col)
    return cv.to_svg()


def _ballot_table(n: int) -> list[list[int]]:
    c = [[0] * (n + 1) for _ in range(n + 1)]
    for q in range(n + 1):
        c[0][q] = 1
        for p in range(1, q + 1):
            c[p][q] = c[p - 1][q] + (c[p][q - 1] if p <= q - 1 else 0)
    return c


def fig_57(theme: Theme) -> str:
    n = 50
    c_tab = _ballot_table(n)
    cat_n = c_tab[n][n]

    step = 3.55
    x0 = 14.0
    y0 = 12.0
    max_d = 21
    cv = SvgCanvas(x0 * 2 + 100 * step, y0 + (max_d + 2) * step + 10.0, theme)

    top_fill = _heat_color(theme, 1.0)
    for k in range(n):
        xa = x0 + 2 * k * step
        xb = x0 + (2 * k + 2) * step
        xm = x0 + (2 * k + 1) * step
        ym = y0 + step
        cv.polyline([(xa, y0), (xb, y0), (xm, ym)], stroke=top_fill, stroke_width=0.25, fill=top_fill, closed=True)

    prob_ge: dict[tuple[int, int], float] = {}
    exp_w: list[tuple[float, float]] = []
    for m in range(1, 2 * n):
        weights: dict[int, int] = {}
        for w in range(m % 2, min(m, 2 * n - m) + 1, 2):
            i = (m + w) // 2
            j = (m - w) // 2
            if 0 <= j <= i <= n and (n - i) <= (n - j):
                weights[w] = c_tab[j][i] * c_tab[n - i][n - j]
        running = 0
        mean_w = 0.0
        for w in sorted(weights.keys(), reverse=True):
            running += weights[w]
            prob_ge[(m, w)] = running / cat_n
            mean_w += w * (weights[w] / cat_n)
        exp_w.append((x0 + m * step, y0 + mean_w * step))

    for d in range(1, max_d + 1):
        for m in range(1, 2 * n):
            if (m - d) % 2 == 0:
                continue
            pr = prob_ge.get((m, d + 1), 0.0)
            if pr < 0.0005:
                continue
            col = _heat_color(theme, pr)
            cx = x0 + m * step
            cy = y0 + d * step
            cv.polyline(
                [(cx - step, cy), (cx, cy - step), (cx + step, cy), (cx, cy + step)],
                stroke=col,
                stroke_width=0.22,
                fill=col,
                closed=True,
            )

    cpath = _catmull_rom_svg(exp_w)
    if theme.is_dark:
        cv.path(cpath, stroke=theme.coral, stroke_width=1.55, glow=True)
    else:
        cv.path(cpath, stroke="#FFFFFF", stroke_width=2.0, opacity=0.68)
        cv.path(cpath, stroke="#0F172A", stroke_width=1.0)
    return cv.to_svg()


def _catalan_list(n_max: int) -> list[int]:
    c = [0] * (n_max + 1)
    c[0] = 1
    for k in range(1, n_max + 1):
        c[k] = c[k - 1] * (4 * k - 2) // (k + 1)
    return c


def _compute_f_table(n: int, max_l: int) -> list[list[int]]:
    cat = _catalan_list(n)
    f = [[0] * (n + 1) for _ in range(max_l + 1)]
    for s in range(1, n + 1):
        f[0][s] = cat[s - 1]
    for lv in range(1, max_l + 1):
        for s in range(lv + 1, n + 1):
            tot = 0
            for j in range(1, s - lv + 1):
                tot += cat[j - 1] * f[lv - 1][s - j]
            f[lv][s] = tot
    return f


def fig_58(theme: Theme) -> str:
    n = 50
    max_l = 35
    cat = _catalan_list(n)
    cat_n = cat[n]
    cat_nm1 = cat[n - 1]

    pitch = 6.95
    rad = 2.98
    x0 = 14.0
    y0 = 14.0
    cv = SvgCanvas(x0 * 2 + (n - 1) * pitch, y0 * 2 + max_l * pitch, theme)

    mean_pts: list[tuple[float, float]] = []
    full_f = _compute_f_table(n, n - 1)
    for m in range(1, n + 1):
        cx = x0 + (m - 1) * pitch
        mean_l = 0.0
        for lv in range(n):
            t_lm = sum(
                math.comb(lv, j) * full_f[j][m] * full_f[lv - j][n + 1 - m]
                for j in range(max(0, lv - (n - m)), min(lv, m - 1) + 1)
            )
            mean_l += lv * (t_lm / cat_n)
            if lv <= max_l:
                shade = min(1.0, t_lm / cat_nm1)
                if shade >= 0.0015:
                    cy = y0 + lv * pitch
                    cv.circle(cx, cy, rad, fill=_heat_color(theme, shade), stroke="none")
        mean_pts.append((cx, y0 + mean_l * pitch))

    cpath = _catmull_rom_svg(mean_pts)
    if theme.is_dark:
        cv.path(cpath, stroke=theme.coral, stroke_width=1.6, glow=True)
    else:
        cv.path(cpath, stroke="#FFFFFF", stroke_width=2.0, opacity=0.65)
        cv.path(cpath, stroke="#0F172A", stroke_width=1.05)
    return cv.to_svg()


def fig_59(theme: Theme) -> str:
    n = 50
    max_l = 37
    cat = _catalan_list(n)
    cat_n = cat[n]
    cat_nm1 = cat[n - 1]
    full_f = _compute_f_table(n + 1, n)

    pitch = 6.85
    sq = 5.95
    x0 = 14.0
    y0 = 14.0
    cv = SvgCanvas(x0 * 2 + n * pitch, y0 * 2 + (max_l - 1) * pitch, theme)

    mean_pts: list[tuple[float, float]] = []
    for m in range(n + 1):
        cx = x0 + m * pitch
        mean_l = 0.0
        for lv in range(1, n + 1):
            if m in (0, n):
                t_ext = full_f[lv - 1][n]
            else:
                t_ext = sum(
                    math.comb(lv, j) * full_f[j - 1][m] * full_f[lv - j - 1][n - m]
                    for j in range(max(1, lv - (n - m)), min(lv - 1, m) + 1)
                )
            mean_l += lv * (t_ext / cat_n)
            if lv <= max_l:
                shade = min(1.0, t_ext / cat_nm1)
                if shade >= 0.0015:
                    cy = y0 + (lv - 1) * pitch
                    cv.rect(cx - sq * 0.5, cy - sq * 0.5, sq, sq, fill=_heat_color(theme, shade), stroke="none")
        mean_pts.append((cx, y0 + (mean_l - 1.0) * pitch))

    cpath = _catmull_rom_svg(mean_pts)
    if theme.is_dark:
        cv.path(cpath, stroke=theme.coral, stroke_width=1.6, glow=True)
    else:
        cv.path(cpath, stroke="#FFFFFF", stroke_width=2.0, opacity=0.65)
        cv.path(cpath, stroke="#0F172A", stroke_width=1.05)
    return cv.to_svg()


def fig_p470_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(280, 62, theme)
    icol = theme.cyan if theme.is_dark else theme.fg
    scol = theme.gold if theme.is_dark else theme.fg
    edge_col = "#64748B" if theme.is_dark else theme.fg
    r = 6.2
    sq = 13.5

    rx1, ry1 = 78.0, 17.0
    cv.graph_edge(rx1, ry1, 56.0, 44.0, r1=r, r2=8.0, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(rx1, ry1, 100.0, 44.0, r1=r, r2=8.0, stroke=edge_col, stroke_width=1.3)
    cv.circle(rx1, ry1, r, fill=theme.node_fill, stroke=icol, stroke_width=1.4)
    cv.rect(56.0 - sq * 0.5, 44.0 - sq * 0.5, sq, sq, fill=theme.sink_true_fill if theme.is_dark else "#FFFFFF", stroke=scol, stroke_width=1.35)
    cv.text(56.0, 44.0, "n", font_size=9.2, italic=True, fill=scol if theme.is_dark else theme.fg)
    cv.text(100.0, 44.0, "x", font_size=11.0, italic=True, fill=theme.fg)

    cv.text(140.0, 31.0, "or", font_size=11.0, fill=theme.muted if theme.is_dark else theme.fg)

    rx2, ry2 = 202.0, 17.0
    cv.graph_edge(rx2, ry2, 180.0, 44.0, r1=r, r2=8.0, stroke=edge_col, stroke_width=1.3)
    cv.graph_edge(rx2, ry2, 224.0, 44.0, r1=r, r2=8.0, stroke=edge_col, stroke_width=1.3)
    cv.circle(rx2, ry2, r, fill=theme.node_fill, stroke=icol, stroke_width=1.4)
    cv.text(180.0, 44.0, "x", font_size=11.0, italic=True, fill=theme.fg)
    cv.rect(224.0 - sq * 0.5, 44.0 - sq * 0.5, sq, sq, fill=theme.sink_true_fill if theme.is_dark else "#FFFFFF", stroke=scol, stroke_width=1.35)
    cv.text(224.0, 44.0, "n", font_size=9.2, italic=True, fill=scol if theme.is_dark else theme.fg)
    return cv.to_svg()


def fig_p470_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(468, 92, theme)
    DTree = int | tuple["DTree", "DTree"]
    trees: list[DTree] = [
        0,
        (1, 0),
        (1, (2, 0)),
        ((1, (2, 0)), 3),
        ((4, (1, (2, 0))), 3),
        ((4, (1, (2, 0))), (3, 5)),
        ((4, ((6, 1), (2, 0))), (3, 5)),
    ]

    def count_slots(t: DTree) -> int:
        return 1 if isinstance(t, int) else count_slots(t[0]) + 1 + count_slots(t[1])

    slot_dx = 5.4
    dy = 14.5
    widths = [max(10.0, (count_slots(t) - 1) * slot_dx) for t in trees]
    gap = (468.0 - 28.0 - sum(widths)) / (len(trees) - 1)
    cur_x = 14.0

    icol = theme.cyan if theme.is_dark else theme.fg
    scol = theme.gold if theme.is_dark else theme.fg
    edge_col = "#64748B" if theme.is_dark else theme.fg
    r = 3.6
    sq = 9.8

    for ti, (t, w) in enumerate(zip(trees, widths)):
        slot = 0

        def max_d(node: DTree) -> int:
            return 0 if isinstance(node, int) else 1 + max(max_d(node[0]), max_d(node[1]))

        md = max_d(t)
        y_base = 44.0 - 0.5 * md * dy

        def draw_dt(
            node: DTree,
            depth: int,
            xb: float = cur_x,
            yb: float = y_base,
            tw: float = w,
            max_dep: int = md,
        ) -> tuple[float, float, bool]:
            nonlocal slot
            if isinstance(node, int):
                nx = xb + slot * slot_dx if max_dep > 0 else xb + 0.5 * tw
                ny = yb + depth * dy
                slot += 1
                cv.rect(
                    nx - sq * 0.5,
                    ny - sq * 0.5,
                    sq,
                    sq,
                    fill=theme.sink_true_fill if theme.is_dark else "#FFFFFF",
                    stroke=scol,
                    stroke_width=1.05,
                )
                cv.text(nx, ny, str(node), font_size=7.2, mono=True, fill=scol if theme.is_dark else theme.fg)
                return nx, ny, True
            lx, ly, l_leaf = draw_dt(node[0], depth + 1, xb, yb, tw, max_dep)
            nx = xb + slot * slot_dx
            ny = yb + depth * dy
            slot += 1
            rx, ry, r_leaf = draw_dt(node[1], depth + 1, xb, yb, tw, max_dep)
            cv.graph_edge(nx, ny, lx, ly, r1=r, r2=sq * 0.56 if l_leaf else r, stroke=edge_col, stroke_width=1.05)
            cv.graph_edge(nx, ny, rx, ry, r1=r, r2=sq * 0.56 if r_leaf else r, stroke=edge_col, stroke_width=1.05)
            cv.circle(nx, ny, r, fill=theme.node_fill, stroke=icol, stroke_width=1.15)
            return nx, ny, False

        draw_dt(t, 0)
        cur_x += w
        if ti < len(trees) - 1:
            cv.text(cur_x + 0.5 * gap, 50.0, ",", font_size=11.0, fill=theme.muted if theme.is_dark else theme.fg)
            cur_x += gap
    return cv.to_svg()


def _christmas_tree_rows(order: int = 8) -> list[list[str]]:
    rows: list[list[str]] = [["0", "1"]]
    for _ in range(2, order + 1):
        nxt: list[list[str]] = []
        for r in rows:
            if len(r) > 1:
                nxt.append([x + "0" for x in r[1:]])
            nxt.append([r[0] + "0"] + [x + "1" for x in r])
        rows = nxt
    return rows


def fig_p472_table4(theme: Theme) -> str:
    rows = _christmas_tree_rows(8)
    row_h = 7.6
    y_top = 12.0
    h_total = y_top + len(rows) * row_h + 10.0
    cv = SvgCanvas(448, h_total, theme)

    x0 = 28.0
    col_dx = 49.0
    palette = [
        theme.violet,
        theme.coral,
        theme.gold,
        theme.mint,
        theme.cyan,
        theme.mint,
        theme.gold,
        theme.coral,
        theme.violet,
    ]
    rule_col = "#334766" if theme.is_dark else "#0F172A"
    cv.line(10.0, 5.0, 438.0, 5.0, stroke=rule_col, stroke_width=1.0)
    for r_idx, row in enumerate(rows):
        ry = y_top + (r_idx + 0.5) * row_h
        for bits in row:
            wt = bits.count("1")
            cx = x0 + wt * col_dx
            col = palette[wt] if theme.is_dark else theme.fg
            cv.text(cx, ry, bits, font_size=6.4, mono=True, fill=col)
    cv.line(10.0, y_top + len(rows) * row_h + 3.0, 438.0, y_top + len(rows) * row_h + 3.0, stroke=rule_col, stroke_width=1.0)
    return cv.to_svg()


def fig_p477_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(280, 82, theme)
    cv.text(56.0, 41.0, "G =", font_size=11.5, italic=True, fill=theme.fg)
    p1 = (104.0, 41.0)
    p2 = (150.0, 16.0)
    p3 = (150.0, 66.0)
    p4 = (196.0, 41.0)
    r = 8.8
    ecol = theme.cyan if theme.is_dark else theme.fg
    pcol = theme.gold if theme.is_dark else theme.fg
    lcol = theme.muted if theme.is_dark else theme.fg

    cv.graph_edge(*p1, *p2, r1=r, r2=r, stroke=pcol, stroke_width=1.55)
    cv.graph_edge(*p1, *p3, r1=r, r2=r, stroke=ecol, stroke_width=1.35)
    cv.graph_edge(*p2, *p3, r1=r, r2=r, stroke=ecol, stroke_width=1.35)
    cv.graph_edge(*p2, *p4, r1=r, r2=r, stroke=ecol, stroke_width=1.35)
    cv.graph_edge(*p3, *p4, r1=r, r2=r, stroke=ecol, stroke_width=1.35)

    cv.text(122.0, 22.0, "p", font_size=9.5, italic=True, fill=pcol)
    cv.text(122.0, 60.0, "q", font_size=9.5, italic=True, fill=lcol)
    cv.text(157.0, 41.0, "r", font_size=9.5, italic=True, fill=lcol)
    cv.text(178.0, 22.0, "s", font_size=9.5, italic=True, fill=lcol)
    cv.text(178.0, 60.0, "t", font_size=9.5, italic=True, fill=lcol)

    for lbl, pt in [("1", p1), ("2", p2), ("3", p3), ("4", p4)]:
        st = (pcol if lbl in ("1", "2") else ecol) if theme.is_dark else theme.fg
        cv.graph_node(*pt, lbl, r=r, stroke=st, font_size=9.2)
    return cv.to_svg()


def fig_p477_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(280, 82, theme)
    cv.text(64.0, 41.0, "G / p =", font_size=11.5, italic=True, fill=theme.fg)
    p12 = (138.0, 17.0)
    p3 = (138.0, 65.0)
    p4 = (192.0, 41.0)
    r = 8.8
    ecol = theme.cyan if theme.is_dark else theme.fg
    pcol = theme.gold if theme.is_dark else theme.fg
    lcol = theme.muted if theme.is_dark else theme.fg

    cv.graph_edge(p12[0] - 4.0, p12[1], p3[0] - 3.0, p3[1], r1=8.0, r2=r, curve=13.0, stroke=ecol, stroke_width=1.35)
    cv.graph_edge(p12[0] + 4.0, p12[1], p3[0] + 3.0, p3[1], r1=8.0, r2=r, curve=-13.0, stroke=ecol, stroke_width=1.35)
    cv.graph_edge(p12[0] + 6.0, p12[1], p4[0], p4[1], r1=9.0, r2=r, stroke=ecol, stroke_width=1.35)
    cv.graph_edge(*p3, *p4, r1=r, r2=r, stroke=ecol, stroke_width=1.35)

    cv.text(119.0, 42.0, "q", font_size=9.5, italic=True, fill=lcol)
    cv.text(156.0, 42.0, "r", font_size=9.5, italic=True, fill=lcol)
    cv.text(171.0, 22.0, "s", font_size=9.5, italic=True, fill=lcol)
    cv.text(171.0, 60.0, "t", font_size=9.5, italic=True, fill=lcol)

    _pill(cv, p12[0], p12[1], 27.0, 15.5, "1,2", stroke=pcol, font_size=8.8)
    cv.graph_node(*p3, "3", r=r, stroke=ecol, font_size=9.2)
    cv.graph_node(*p4, "4", r=r, stroke=ecol, font_size=9.2)
    return cv.to_svg()


def fig_p477_inline_3(theme: Theme) -> str:
    cv = SvgCanvas(280, 82, theme)
    cv.text(56.0, 41.0, "G \\ p =", font_size=11.5, italic=True, fill=theme.fg)
    p1 = (108.0, 41.0)
    p2 = (154.0, 16.0)
    p3 = (154.0, 66.0)
    p4 = (200.0, 41.0)
    r = 8.8
    ecol = theme.cyan if theme.is_dark else theme.fg
    lcol = theme.muted if theme.is_dark else theme.fg

    cv.graph_edge(*p1, *p3, r1=r, r2=r, stroke=ecol, stroke_width=1.35)
    cv.graph_edge(*p2, *p3, r1=r, r2=r, stroke=ecol, stroke_width=1.35)
    cv.graph_edge(*p2, *p4, r1=r, r2=r, stroke=ecol, stroke_width=1.35)
    cv.graph_edge(*p3, *p4, r1=r, r2=r, stroke=ecol, stroke_width=1.35)

    cv.text(126.0, 60.0, "q", font_size=9.5, italic=True, fill=lcol)
    cv.text(161.0, 41.0, "r", font_size=9.5, italic=True, fill=lcol)
    cv.text(182.0, 22.0, "s", font_size=9.5, italic=True, fill=lcol)
    cv.text(182.0, 60.0, "t", font_size=9.5, italic=True, fill=lcol)

    for lbl, pt in [("1", p1), ("2", p2), ("3", p3), ("4", p4)]:
        cv.graph_node(*pt, lbl, r=r, stroke=ecol, font_size=9.2)
    return cv.to_svg()


def fig_p480_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(280, 108, theme)
    pos = {
        "A": (140.0, 16.0),
        "a": (78.0, 44.0),
        "B": (140.0, 44.0),
        "D": (204.0, 44.0),
        "b": (106.0, 72.0),
        "C": (140.0, 72.0),
        "e": (174.0, 72.0),
        "f": (190.0, 72.0),
        "g": (222.0, 72.0),
        "c": (124.0, 96.0),
        "d": (156.0, 96.0),
    }
    edges = [
        ("A", "a"),
        ("A", "B"),
        ("A", "D"),
        ("B", "b"),
        ("B", "C"),
        ("B", "e"),
        ("C", "c"),
        ("C", "d"),
        ("D", "f"),
        ("D", "g"),
    ]
    r = 8.4
    edge_col = "#64748B" if theme.is_dark else theme.fg
    for u, v in edges:
        cv.graph_edge(*pos[u], *pos[v], r1=r, r2=r, stroke=edge_col, stroke_width=1.25)
    for name, (nx, ny) in pos.items():
        is_super = name.isupper()
        st = (theme.gold if is_super else theme.cyan) if theme.is_dark else theme.fg
        cv.graph_node(nx, ny, name, r=r, stroke=st, font_size=9.2, italic=True)
    return cv.to_svg()


def fig_p480_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(448, 86, theme)
    r = 2.6
    ecol = theme.cyan if theme.is_dark else theme.fg
    scol = theme.gold if theme.is_dark else theme.fg
    lcol = theme.fg

    def vdot(x: float, y: float, term: bool = False) -> None:
        st = scol if (term and theme.is_dark) else ecol
        cv.circle(x, y, r, fill=theme.node_fill, stroke=st, stroke_width=1.25)

    cv.text(20.0, 43.0, "A =", font_size=11.0, italic=True, fill=lcol)
    sa, ua, va, ta = (38.0, 43.0), (66.0, 43.0), (96.0, 43.0), (124.0, 43.0)
    wa = (81.0, 68.0)
    cv.path(f"M {fmt(sa[0])} {fmt(sa[1])} Q 81 6 {fmt(ta[0])} {fmt(ta[1])}", stroke=ecol, stroke_width=1.25)
    cv.line(*sa, *ua, stroke=ecol, stroke_width=1.25)
    cv.path(f"M {fmt(ua[0])} {fmt(ua[1])} Q 81 30 {fmt(va[0])} {fmt(va[1])}", stroke=ecol, stroke_width=1.25)
    cv.path(f"M {fmt(ua[0])} {fmt(ua[1])} Q 81 56 {fmt(va[0])} {fmt(va[1])}", stroke=ecol, stroke_width=1.25)
    cv.line(*va, *ta, stroke=ecol, stroke_width=1.25)
    cv.path(f"M {fmt(sa[0])} {fmt(sa[1])} Q 54 65 {fmt(wa[0])} {fmt(wa[1])}", stroke=ecol, stroke_width=1.25)
    cv.path(f"M {fmt(wa[0])} {fmt(wa[1])} Q 108 65 {fmt(ta[0])} {fmt(ta[1])}", stroke=ecol, stroke_width=1.25)
    cv.text(81.0, 14.0, "a", font_size=8.8, italic=True, fill=lcol)
    cv.text(52.0, 36.0, "b", font_size=8.8, italic=True, fill=lcol)
    cv.text(81.0, 30.0, "c", font_size=8.8, italic=True, fill=lcol)
    cv.text(81.0, 56.0, "d", font_size=8.8, italic=True, fill=lcol)
    cv.text(110.0, 36.0, "e", font_size=8.8, italic=True, fill=lcol)
    cv.text(55.0, 66.0, "f", font_size=8.8, italic=True, fill=lcol)
    cv.text(107.0, 66.0, "g", font_size=8.8, italic=True, fill=lcol)
    vdot(*sa, True)
    vdot(*ua)
    vdot(*va)
    vdot(*ta, True)
    vdot(*wa)
    cv.text(135.0, 48.0, ",", font_size=11.0, fill=lcol)

    cv.text(158.0, 43.0, "B =", font_size=11.0, italic=True, fill=lcol)
    sb, ub, vb, tb = (176.0, 43.0), (202.0, 43.0), (232.0, 43.0), (258.0, 43.0)
    cv.line(*sb, *ub, stroke=ecol, stroke_width=1.25)
    cv.path(f"M {fmt(ub[0])} {fmt(ub[1])} Q 217 29 {fmt(vb[0])} {fmt(vb[1])}", stroke=ecol, stroke_width=1.25)
    cv.path(f"M {fmt(ub[0])} {fmt(ub[1])} Q 217 57 {fmt(vb[0])} {fmt(vb[1])}", stroke=ecol, stroke_width=1.25)
    cv.line(*vb, *tb, stroke=ecol, stroke_width=1.25)
    cv.text(189.0, 35.0, "b", font_size=8.8, italic=True, fill=lcol)
    cv.text(217.0, 28.0, "c", font_size=8.8, italic=True, fill=lcol)
    cv.text(217.0, 58.0, "d", font_size=8.8, italic=True, fill=lcol)
    cv.text(245.0, 35.0, "e", font_size=8.8, italic=True, fill=lcol)
    vdot(*sb, True)
    vdot(*ub)
    vdot(*vb)
    vdot(*tb, True)
    cv.text(269.0, 48.0, ",", font_size=11.0, fill=lcol)

    cv.text(292.0, 43.0, "C =", font_size=11.0, italic=True, fill=lcol)
    sc, tc = (310.0, 43.0), (344.0, 43.0)
    cv.path(f"M {fmt(sc[0])} {fmt(sc[1])} Q 327 29 {fmt(tc[0])} {fmt(tc[1])}", stroke=ecol, stroke_width=1.25)
    cv.path(f"M {fmt(sc[0])} {fmt(sc[1])} Q 327 57 {fmt(tc[0])} {fmt(tc[1])}", stroke=ecol, stroke_width=1.25)
    cv.text(327.0, 28.0, "c", font_size=8.8, italic=True, fill=lcol)
    cv.text(327.0, 58.0, "d", font_size=8.8, italic=True, fill=lcol)
    vdot(*sc, True)
    vdot(*tc, True)
    cv.text(354.0, 48.0, ",", font_size=11.0, fill=lcol)

    cv.text(377.0, 43.0, "D =", font_size=11.0, italic=True, fill=lcol)
    sd, md_pt, td = (395.0, 43.0), (416.0, 43.0), (437.0, 43.0)
    cv.line(*sd, *md_pt, stroke=ecol, stroke_width=1.25)
    cv.line(*md_pt, *td, stroke=ecol, stroke_width=1.25)
    cv.text(405.5, 35.0, "f", font_size=8.8, italic=True, fill=lcol)
    cv.text(426.5, 35.0, "g", font_size=8.8, italic=True, fill=lcol)
    vdot(*sd, True)
    vdot(*md_pt)
    vdot(*td, True)
    return cv.to_svg()


BUILDERS: dict[str, Callable[[Theme], str]] = {
    "fig_55": fig_55,
    "fig_p446_inline": fig_p446_inline,
    "fig_p447_inline": fig_p447_inline,
    "fig_56": fig_56,
    "fig_p454_inline_1": fig_p454_inline_1,
    "fig_p454_inline_2": fig_p454_inline_2,
    "fig_p455_inline_1": fig_p455_inline_1,
    "fig_p455_inline_2": fig_p455_inline_2,
    "fig_p455_inline_3": fig_p455_inline_3,
    "fig_p456_table1": fig_p456_table1,
    "fig_p459_table2": fig_p459_table2,
    "fig_p461_inline_1": fig_p461_inline_1,
    "fig_p461_inline_2": fig_p461_inline_2,
    "fig_p461_inline_3": fig_p461_inline_3,
    "fig_p461_inline_4": fig_p461_inline_4,
    "fig_p463_table3": fig_p463_table3,
    "fig_p465_inline": fig_p465_inline,
    "fig_p466_inline_1": fig_p466_inline_1,
    "fig_p466_inline_2": fig_p466_inline_2,
    "fig_57": fig_57,
    "fig_58": fig_58,
    "fig_59": fig_59,
    "fig_p470_inline_1": fig_p470_inline_1,
    "fig_p470_inline_2": fig_p470_inline_2,
    "fig_p472_table4": fig_p472_table4,
    "fig_p477_inline_1": fig_p477_inline_1,
    "fig_p477_inline_2": fig_p477_inline_2,
    "fig_p477_inline_3": fig_p477_inline_3,
    "fig_p480_inline_1": fig_p480_inline_1,
    "fig_p480_inline_2": fig_p480_inline_2,
}

BUILDERS_P5: dict[str, Callable[[Theme], str]] = BUILDERS


def render_part(out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for fig_id, fn in BUILDERS.items():
        m, c, p = emit_dual_figure(fig_id, fn, out_dir)
        paths.extend((m, c, p))
    return paths
