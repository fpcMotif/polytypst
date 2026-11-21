from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

from .figures_common import SvgCanvas, Theme, emit_dual_figure, fmt, rich_label


def _pill(
    c: SvgCanvas,
    cx: float,
    cy: float,
    w: float,
    h: float,
    label: str,
    stroke: str | None = None,
    fill: str | None = None,
    font_size: float = 9.5,
    mono: bool = False,
    rich: bool = False,
    italic: bool = False,
) -> None:
    st = stroke or (c.theme.cyan if c.theme.is_dark else c.theme.fg)
    fl = fill or c.theme.node_fill
    c.rect(cx - w / 2, cy - h / 2, w, h, fill=fl, stroke=st, stroke_width=1.25, rx=h / 2)
    c.text(cx, cy, label, font_size=font_size, fill=c.theme.fg, mono=mono, rich=rich, italic=italic)


def _op_node(
    c: SvgCanvas,
    cx: float,
    cy: float,
    op: str,
    r: float = 7.4,
) -> None:
    if c.theme.is_dark:
        col_map = {
            "and": c.theme.cyan,
            "or": c.theme.mint,
            "xor": c.theme.gold,
            "gt": c.theme.coral,
            "lt": c.theme.violet,
            "": c.theme.cyan,
        }
        st = col_map.get(op, c.theme.cyan)
    else:
        st = c.theme.fg
    c.circle(cx, cy, r, fill=c.theme.node_fill, stroke=st, stroke_width=1.25)
    s = r * 0.52
    if op == "and":
        c.polyline([(cx - s * 0.85, cy + s * 0.72), (cx, cy - s * 0.82), (cx + s * 0.85, cy + s * 0.72)], stroke=c.theme.fg, stroke_width=1.15)
    elif op == "or":
        c.polyline([(cx - s * 0.85, cy - s * 0.72), (cx, cy + s * 0.82), (cx + s * 0.85, cy - s * 0.72)], stroke=c.theme.fg, stroke_width=1.15)
    elif op == "xor":
        p = r * 0.68
        c.line(cx - p, cy, cx + p, cy, stroke=c.theme.fg, stroke_width=1.1)
        c.line(cx, cy - p, cx, cy + p, stroke=c.theme.fg, stroke_width=1.1)
    elif op == "gt":
        c.polyline([(cx - s * 0.72, cy - s * 0.78), (cx + s * 0.78, cy), (cx - s * 0.72, cy + s * 0.78)], stroke=c.theme.fg, stroke_width=1.15)
    elif op == "lt":
        c.polyline([(cx + s * 0.72, cy - s * 0.78), (cx - s * 0.78, cy), (cx + s * 0.72, cy + s * 0.78)], stroke=c.theme.fg, stroke_width=1.15)


def fig_frontispiece(theme: Theme) -> str:
    w, h = 350.0, 430.0
    c = SvgCanvas(w, h, theme)
    cx = w / 2.0

    case_fill = "#131F35" if theme.is_dark else "#F1F5F9"
    case_dark = "#0D1626" if theme.is_dark else "#E2E8F0"
    wood_stroke = theme.gold if theme.is_dark else theme.fg
    pipe_outer = theme.cyan if theme.is_dark else theme.fg
    pipe_flat = theme.mint if theme.is_dark else "#334155"
    pipe_center = theme.gold if theme.is_dark else theme.fg
    accent_v = theme.violet if theme.is_dark else "#475569"
    mouth_col = theme.coral if theme.is_dark else theme.fg

    c.rect(42, 392, 266, 14, fill=case_dark, stroke=wood_stroke, stroke_width=1.5, rx=2)
    c.rect(54, 378, 242, 14, fill=case_fill, stroke=wood_stroke, stroke_width=1.3, rx=1.5)

    ped_x0, ped_w = cx - 68, 136.0
    c.rect(ped_x0, 380, ped_w, 11, fill=theme.bg, stroke=wood_stroke, stroke_width=1.0)
    for k in range(18):
        kx = ped_x0 + 4 + k * 7.3
        c.line(kx, 381, kx, 390, stroke=wood_stroke, stroke_width=0.9)
        if k % 7 not in (2, 6) and k < 17:
            c.rect(kx + 1.8, 381, 3.4, 5.2, fill=mouth_col if theme.is_dark else theme.fg)

    c.rect(68, 286, 214, 92, fill=case_fill, stroke=wood_stroke, stroke_width=1.5, rx=2)
    c.rect(78, 296, 32, 72, fill=case_dark, stroke=wood_stroke, stroke_width=1.1, rx=1.5)
    c.rect(240, 296, 32, 72, fill=case_dark, stroke=wood_stroke, stroke_width=1.1, rx=1.5)

    for side_x in (87.0, 99.0, 249.0, 261.0):
        for r in range(5):
            sy = 307 + r * 12.5
            c.circle(side_x, sy, 3.1, fill=theme.node_fill, stroke=pipe_outer, stroke_width=1.1)
            c.circle(side_x, sy, 1.0, fill=pipe_center)

    c.rect(118, 296, 114, 72, fill=case_dark, stroke=wood_stroke, stroke_width=1.2, rx=1.5)
    for my in (338.0, 351.0):
        c.rect(124, my, 102, 9.5, fill="#FFFFFF" if not theme.is_dark else "#E2E8F0", stroke=wood_stroke, stroke_width=1.0)
        for k in range(1, 21):
            kx = 124 + k * (102.0 / 21.0)
            c.line(kx, my, kx, my + 9.5, stroke="#334155", stroke_width=0.55)
        for k in range(20):
            if k % 7 not in (2, 6):
                kx = 124 + (k + 0.68) * (102.0 / 21.0)
                c.rect(kx, my, 2.7, 5.6, fill="#0F172A")

    c.rect(128, 302, 94, 28, fill=theme.node_fill, stroke=accent_v, stroke_width=1.1, rx=1.5)
    for sl in range(5):
        sy = 308.5 + sl * 3.8
        c.line(134, sy, 216, sy, stroke=theme.muted, stroke_width=0.75)
    bach_notes = [(150.0, 316.1, "♭"), (167.0, 318.0, ""), (184.0, 314.2, ""), (201.0, 316.1, "♮")]
    for nx, ny, acc in bach_notes:
        if acc:
            c.text(nx - 6.2, ny, acc, font_size=7.5, fill=pipe_center)
        c.ellipse(nx, ny, 2.7, 1.9, fill=pipe_center, stroke=pipe_center, stroke_width=0.8, rotate=-18)
        c.line(nx + 2.4, ny, nx + 2.4, ny - 9.5, stroke=pipe_center, stroke_width=1.0)

    c.path("M 68 286 L 34 256 L 316 256 L 282 286 Z", fill=case_dark, stroke=wood_stroke, stroke_width=1.5)
    c.path("M 68 286 Q 45 282 38 262", stroke=pipe_center, stroke_width=1.4)
    c.path("M 282 286 Q 305 282 312 262", stroke=pipe_center, stroke_width=1.4)
    c.rect(28, 246, 294, 11, fill=case_fill, stroke=wood_stroke, stroke_width=1.5, rx=1.5)

    def draw_pipe_bank(
        x0: float,
        x1: float,
        y_base: float,
        y_top_edge: float,
        y_top_mid: float,
        count: int,
        mouth_y_edge: float,
        mouth_y_mid: float,
        col: str,
        pipe_top_v: bool = True,
    ) -> None:
        pw_tot = x1 - x0
        gap = 1.4
        pw = (pw_tot - gap * (count - 1)) / count
        mid_i = (count - 1) / 2.0
        for i in range(count):
            t = abs(i - mid_i) / max(1.0, mid_i)
            px = x0 + i * (pw + gap)
            pcx = px + pw * 0.5
            ptop = y_top_mid + (y_top_edge - y_top_mid) * (t if pipe_top_v else (1.0 - t))
            pmouth = mouth_y_mid + (mouth_y_edge - mouth_y_mid) * t
            foot_h = y_base - pmouth
            body_fill = "#16243B" if theme.is_dark else "#FFFFFF"
            c.rect(px, ptop, pw, pmouth - ptop, fill=body_fill, stroke=col, stroke_width=1.15, rx=pw * 0.35)
            c.polyline(
                [(px, pmouth), (pcx, y_base), (px + pw, pmouth)],
                fill=case_dark if theme.is_dark else "#F8FAFC",
                stroke=col,
                stroke_width=1.1,
                closed=True,
            )
            c.polyline(
                [(px + pw * 0.16, pmouth - pw * 0.65), (pcx, pmouth), (px + pw * 0.84, pmouth - pw * 0.65)],
                fill=mouth_col if theme.is_dark else "#CBD5E1",
                stroke=col,
                stroke_width=0.9,
                closed=True,
            )
            c.line(px + pw * 0.12, pmouth, px + pw * 0.88, pmouth, stroke=mouth_col, stroke_width=1.2)
            if foot_h > 0:
                c.circle(pcx, y_base - 1.2, 0.9, fill=col, stroke="none")

    c.rect(32, 62, 62, 184, fill=case_dark, stroke=wood_stroke, stroke_width=1.4)
    c.rect(256, 62, 62, 184, fill=case_dark, stroke=wood_stroke, stroke_width=1.4)
    c.rect(94, 96, 48, 150, fill=case_fill, stroke=wood_stroke, stroke_width=1.3)
    c.rect(208, 96, 48, 150, fill=case_fill, stroke=wood_stroke, stroke_width=1.3)
    c.rect(142, 46, 66, 200, fill=case_dark, stroke=wood_stroke, stroke_width=1.5)

    draw_pipe_bank(36, 90, 245, 92, 70, 5, 224, 214, pipe_outer, True)
    draw_pipe_bank(260, 314, 245, 92, 70, 5, 224, 214, pipe_outer, True)

    c.line(94, 172, 142, 172, stroke=wood_stroke, stroke_width=1.4)
    c.line(208, 172, 256, 172, stroke=wood_stroke, stroke_width=1.4)
    draw_pipe_bank(97, 139, 171, 112, 124, 7, 159, 154, pipe_flat, False)
    draw_pipe_bank(211, 253, 171, 112, 124, 7, 159, 154, pipe_flat, False)
    draw_pipe_bank(97, 139, 245, 184, 196, 7, 232, 227, accent_v, False)
    draw_pipe_bank(211, 253, 245, 184, 196, 7, 232, 227, accent_v, False)

    draw_pipe_bank(146, 204, 245, 76, 54, 7, 222, 210, pipe_center, True)

    c.polyline([(26, 62), (63, 44), (100, 62)], fill=case_fill, stroke=wood_stroke, stroke_width=1.5, closed=True)
    c.polyline([(250, 62), (287, 44), (324, 62)], fill=case_fill, stroke=wood_stroke, stroke_width=1.5, closed=True)
    c.polyline([(136, 46), (175, 24), (214, 46)], fill=case_fill, stroke=pipe_center, stroke_width=1.6, closed=True)

    c.circle(63, 38, 4.0, fill=theme.node_fill, stroke=pipe_outer, stroke_width=1.3)
    c.circle(287, 38, 4.0, fill=theme.node_fill, stroke=pipe_outer, stroke_width=1.3)
    c.circle(175, 17, 5.0, fill=theme.node_fill, stroke=pipe_center, stroke_width=1.5, glow=True)
    c.line(175, 9, 175, 25, stroke=pipe_center, stroke_width=1.3)
    c.line(169, 17, 181, 17, stroke=pipe_center, stroke_width=1.3)

    for tx, tw in ((36.0, 54.0), (146.0, 58.0), (260.0, 54.0)):
        ty = 65.0 if tx != 146.0 else 49.0
        c.path(
            f"M {fmt(tx)} {fmt(ty)} Q {fmt(tx + tw * 0.25)} {fmt(ty + 9)} {fmt(tx + tw * 0.5)} {fmt(ty + 3)} "
            f"Q {fmt(tx + tw * 0.75)} {fmt(ty + 9)} {fmt(tx + tw)} {fmt(ty)}",
            stroke=pipe_center,
            stroke_width=1.1,
        )

    c.text(cx, 416, "J · S · B A C H", font_size=9.5, fill=theme.muted, sans=True, bold=True)
    return c.to_svg()


def _draw_suit_pip(c: SvgCanvas, cx: float, cy: float, suit: str, size: float, col: str, filled: bool = True) -> None:
    fl = col if filled else "none"
    sw = 0.9 if filled else 1.15
    if suit == "♦":
        s = size
        c.polyline([(cx, cy - s), (cx + s * 0.75, cy), (cx, cy + s), (cx - s * 0.75, cy)], fill=fl, stroke=col, stroke_width=sw, closed=True)
    elif suit == "♥":
        s = size * 0.95
        d = (
            f"M {fmt(cx)} {fmt(cy + s)} "
            f"C {fmt(cx - s * 1.15)} {fmt(cy + s * 0.2)} {fmt(cx - s * 1.05)} {fmt(cy - s * 0.85)} {fmt(cx - s * 0.45)} {fmt(cy - s * 0.85)} "
            f"C {fmt(cx - s * 0.15)} {fmt(cy - s * 0.85)} {fmt(cx)} {fmt(cy - s * 0.48)} {fmt(cx)} {fmt(cy - s * 0.35)} "
            f"C {fmt(cx)} {fmt(cy - s * 0.48)} {fmt(cx + s * 0.15)} {fmt(cy - s * 0.85)} {fmt(cx + s * 0.45)} {fmt(cy - s * 0.85)} "
            f"C {fmt(cx + s * 1.05)} {fmt(cy - s * 0.85)} {fmt(cx + s * 1.15)} {fmt(cy + s * 0.2)} {fmt(cx)} {fmt(cy + s)} Z"
        )
        c.path(d, stroke=col, stroke_width=sw, fill=fl)
    elif suit == "♠":
        s = size * 0.95
        d = (
            f"M {fmt(cx)} {fmt(cy - s)} "
            f"C {fmt(cx + s * 1.1)} {fmt(cy - s * 0.15)} {fmt(cx + s * 1.05)} {fmt(cy + s * 0.65)} {fmt(cx + s * 0.42)} {fmt(cy + s * 0.62)} "
            f"C {fmt(cx + s * 0.2)} {fmt(cy + s * 0.6)} {fmt(cx + s * 0.08)} {fmt(cy + s * 0.42)} {fmt(cx)} {fmt(cy + s * 0.3)} "
            f"C {fmt(cx - s * 0.08)} {fmt(cy + s * 0.42)} {fmt(cx - s * 0.2)} {fmt(cy + s * 0.6)} {fmt(cx - s * 0.42)} {fmt(cy + s * 0.62)} "
            f"C {fmt(cx - s * 1.05)} {fmt(cy + s * 0.65)} {fmt(cx - s * 1.1)} {fmt(cy - s * 0.15)} {fmt(cx)} {fmt(cy - s)} Z"
        )
        c.path(d, stroke=col, stroke_width=sw, fill=fl)
        c.polyline([(cx, cy + s * 0.32), (cx - s * 0.34, cy + s), (cx + s * 0.34, cy + s)], fill=fl, stroke=col, stroke_width=sw, closed=True)
    elif suit == "♣":
        r = size * 0.38
        c.circle(cx, cy - size * 0.42, r, fill=fl, stroke=col, stroke_width=sw)
        c.circle(cx - size * 0.42, cy + size * 0.08, r, fill=fl, stroke=col, stroke_width=sw)
        c.circle(cx + size * 0.42, cy + size * 0.08, r, fill=fl, stroke=col, stroke_width=sw)
        c.polyline([(cx, cy + size * 0.05), (cx - size * 0.32, cy + size * 0.92), (cx + size * 0.32, cy + size * 0.92)], fill=fl, stroke=col, stroke_width=sw, closed=True)


def fig_1(theme: Theme) -> str:
    cw, ch = 54.0, 72.0
    gx, gy = 6.0, 6.0
    pad = 12.0
    w = 2 * pad + 4 * cw + 3 * gx
    h = 2 * pad + 4 * ch + 3 * gy
    c = SvgCanvas(w, h, theme)

    grid = [
        [("J", "♦"), ("A", "♥"), ("K", "♠"), ("Q", "♣")],
        [("Q", "♠"), ("K", "♣"), ("A", "♦"), ("J", "♥")],
        [("A", "♣"), ("J", "♠"), ("Q", "♥"), ("K", "♦")],
        [("K", "♥"), ("Q", "♦"), ("J", "♣"), ("A", "♠")],
    ]

    for r in range(4):
        for col_i in range(4):
            rank, suit = grid[r][col_i]
            x = pad + col_i * (cw + gx)
            y = pad + r * (ch + gy)
            is_red = suit in ("♥", "♦")
            if theme.is_dark:
                scol = theme.coral if is_red else theme.cyan
                card_bg = "#121C2E"
                card_st = theme.panel_stroke
                royal_acc = theme.gold
                pip_filled = True
            else:
                scol = "#475569" if is_red else "#0F172A"
                card_bg = "#FFFFFF"
                card_st = "#0F172A"
                royal_acc = "#334155"
                pip_filled = not is_red

            c.rect(x, y, cw, ch, fill=card_bg, stroke=card_st, stroke_width=1.25, rx=3.5)
            c.text(x + 6.5, y + 8.5, rank, font_size=8.8, fill=scol, bold=True, sans=True)
            _draw_suit_pip(c, x + 6.5, y + 17.5, suit, 3.2, scol, filled=pip_filled)

            c.text(x + cw - 6.5, y + ch - 8.5, rank, font_size=8.8, fill=scol, bold=True, sans=True, rotate=180)
            _draw_suit_pip(c, x + cw - 6.5, y + ch - 17.5, suit, 3.2, scol, filled=pip_filled)

            mcx, mcy = x + cw * 0.5, y + ch * 0.5
            if rank == "A":
                sz = 10.5 if suit == "♠" else 8.8
                _draw_suit_pip(c, mcx, mcy, suit, sz, scol, filled=pip_filled)
                if suit == "♠":
                    c.circle(mcx, mcy - 1.5, 3.2, fill=card_bg, stroke=royal_acc, stroke_width=0.9)
            else:
                fx, fy, fw, fh = x + 12.5, y + 10.0, cw - 25.0, ch - 20.0
                c.rect(fx, fy, fw, fh, fill=theme.node_alt if theme.is_dark else "#F8FAFC", stroke=scol, stroke_width=0.9, rx=1.2)
                c.line(fx, mcy, fx + fw, mcy, stroke=scol, stroke_width=0.75)
                for sign in (-1.0, 1.0):
                    hy = mcy + sign * (-14.5)
                    by_mid = mcy + sign * (-4.5)
                    c.polyline(
                        [(mcx - 9.5, mcy), (mcx - 6.5, by_mid - sign * 3.5), (mcx + 6.5, by_mid - sign * 3.5), (mcx + 9.5, mcy)],
                        fill=scol if theme.is_dark else "#CBD5E1",
                        stroke=royal_acc,
                        stroke_width=0.85,
                        closed=True,
                    )
                    c.line(mcx - 4.5, mcy, mcx + 4.5, by_mid - sign * 3.5, stroke=card_bg, stroke_width=0.8)
                    c.line(mcx + 4.5, mcy, mcx - 4.5, by_mid - sign * 3.5, stroke=card_bg, stroke_width=0.8)
                    c.circle(mcx, hy, 4.2, fill=card_bg, stroke=royal_acc, stroke_width=1.0)
                    cy_crown = hy + sign * (-4.5)
                    if rank == "K":
                        c.polyline(
                            [
                                (mcx - 5.2, hy + sign * (-2.2)),
                                (mcx - 5.6, cy_crown + sign * (-3.5)),
                                (mcx - 2.2, cy_crown + sign * (-1.0)),
                                (mcx, cy_crown + sign * (-4.2)),
                                (mcx + 2.2, cy_crown + sign * (-1.0)),
                                (mcx + 5.6, cy_crown + sign * (-3.5)),
                                (mcx + 5.2, hy + sign * (-2.2)),
                            ],
                            fill=royal_acc,
                            stroke=royal_acc,
                            stroke_width=0.75,
                            closed=True,
                        )
                        c.line(mcx + sign * 8.2, mcy, mcx + sign * 8.2, hy, stroke=royal_acc, stroke_width=1.1)
                    elif rank == "Q":
                        c.polyline(
                            [
                                (mcx - 4.8, hy + sign * (-2.2)),
                                (mcx - 3.2, cy_crown + sign * (-3.0)),
                                (mcx, cy_crown + sign * (-1.2)),
                                (mcx + 3.2, cy_crown + sign * (-3.0)),
                                (mcx + 4.8, hy + sign * (-2.2)),
                            ],
                            fill=royal_acc,
                            stroke=royal_acc,
                            stroke_width=0.75,
                            closed=True,
                        )
                        c.circle(mcx + sign * 7.8, hy + sign * 3.0, 2.0, fill=scol, stroke=royal_acc, stroke_width=0.75)
                    else:
                        c.polyline(
                            [
                                (mcx - 5.5, hy + sign * (-2.0)),
                                (mcx + 4.5, hy + sign * (-2.0)),
                                (mcx + 2.0, cy_crown + sign * (-3.0)),
                                (mcx - 4.2, cy_crown + sign * (-2.2)),
                            ],
                            fill=royal_acc,
                            stroke=royal_acc,
                            stroke_width=0.75,
                            closed=True,
                        )
                        c.line(mcx - sign * 8.2, mcy, mcx - sign * 8.2, cy_crown, stroke=royal_acc, stroke_width=1.0)
                    _draw_suit_pip(c, fx + (3.8 if sign < 0 else fw - 3.8), mcy + sign * (-15.5), suit, 2.1, scol, filled=pip_filled)

    return c.to_svg()


def _pent_pts(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    return [
        (cx + r * math.cos(-math.pi / 2 + k * 2 * math.pi / 5), cy + r * math.sin(-math.pi / 2 + k * 2 * math.pi / 5))
        for k in range(5)
    ]


def _draw_small_graph(
    c: SvgCanvas,
    pts: list[tuple[float, float]],
    edges: list[tuple[int, int]],
    vr: float = 2.6,
    edge_col: str | None = None,
    node_stroke: str | None = None,
    curved: dict[tuple[int, int], float] | None = None,
) -> None:
    ec = edge_col or (c.theme.muted if c.theme.is_dark else c.theme.fg)
    ns = node_stroke or (c.theme.cyan if c.theme.is_dark else c.theme.fg)
    curved_map = curved or {}
    for u, v in edges:
        cv = curved_map.get((u, v), curved_map.get((v, u), 0.0))
        c.graph_edge(pts[u][0], pts[u][1], pts[v][0], pts[v][1], r1=vr, r2=vr, curve=cv, stroke=ec, stroke_width=1.2)
    for px, py in pts:
        c.circle(px, py, vr, fill=c.theme.node_fill, stroke=ns, stroke_width=1.2)


def fig_2(theme: Theme) -> str:
    w, h = 432.0, 126.0
    c = SvgCanvas(w, h, theme)
    xs = [36.0, 96.0, 156.0, 224.0, 304.0, 386.0]
    cy = 64.0
    sub_labels = ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)"]
    names = [("P_5", True), ("C_5", True), ("K_5", True), ("3-cube", False), ("Petersen graph", False), ("Chvátal graph", False)]
    pal = [theme.cyan, theme.mint, theme.gold, theme.cyan, theme.coral, theme.violet] if theme.is_dark else [theme.fg] * 6

    for idx, (lbl, (nm, is_math)) in enumerate(zip(sub_labels, names)):
        c.text(xs[idx], 16, lbl, font_size=9.5, fill=theme.muted if theme.is_dark else theme.fg)
        c.text(xs[idx], 111, nm, font_size=9.5, fill=theme.fg, italic=is_math, rich=is_math)

    p_a = _pent_pts(xs[0], cy + 2, 18.0)
    _draw_small_graph(c, p_a, [(3, 4), (4, 0), (0, 1), (1, 2)], node_stroke=pal[0])

    p_b = _pent_pts(xs[1], cy + 2, 18.0)
    _draw_small_graph(c, p_b, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)], node_stroke=pal[1])

    p_c = _pent_pts(xs[2], cy + 2, 18.0)
    _draw_small_graph(c, p_c, [(i, j) for i in range(5) for j in range(i + 1, 5)], node_stroke=pal[2])

    s_out, s_in = 22.0, 9.5
    cx_d = xs[3]
    p_d = [
        (cx_d - s_out, cy - s_out), (cx_d + s_out, cy - s_out), (cx_d + s_out, cy + s_out), (cx_d - s_out, cy + s_out),
        (cx_d - s_in, cy - s_in), (cx_d + s_in, cy - s_in), (cx_d + s_in, cy + s_in), (cx_d - s_in, cy + s_in),
    ]
    e_d = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    _draw_small_graph(c, p_d, e_d, node_stroke=pal[3])

    p_e_out = _pent_pts(xs[4], cy + 2, 30.0)
    p_e_in = _pent_pts(xs[4], cy + 2, 13.5)
    p_e = p_e_out + p_e_in
    e_e = (
        [(i, (i + 1) % 5) for i in range(5)]
        + [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
        + [(i, 5 + i) for i in range(5)]
    )
    _draw_small_graph(c, p_e, e_e, node_stroke=pal[4])

    cx_f = xs[5]
    ro = 24.5
    ri_a, ri_b = 18.0, 8.2
    p_f = [
        (cx_f - ro, cy - ro), (cx_f + ro, cy - ro), (cx_f + ro, cy + ro), (cx_f - ro, cy + ro),
        (cx_f - ri_b, cy - ri_a), (cx_f + ri_b, cy - ri_a),
        (cx_f + ri_a, cy - ri_b), (cx_f + ri_a, cy + ri_b),
        (cx_f + ri_b, cy + ri_a), (cx_f - ri_b, cy + ri_a),
        (cx_f - ri_a, cy + ri_b), (cx_f - ri_a, cy - ri_b),
    ]
    e_f = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (0, 5), (1, 4), (1, 7), (2, 6), (2, 9), (3, 8), (3, 11), (0, 10),
        (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 4),
        (4, 8), (5, 9), (6, 10), (7, 11),
    ]
    cv_f = {(0, 1): -5.5, (1, 2): -5.5, (2, 3): -5.5, (3, 0): -5.5}
    _draw_small_graph(c, p_f, e_f, node_stroke=pal[5], curved=cv_f)
    return c.to_svg()


def fig_p028_inline(theme: Theme) -> str:
    w, h = 442.0, 74.0
    c = SvgCanvas(w, h, theme)
    cy = 37.0
    acc = theme.cyan if theme.is_dark else theme.fg

    x1 = 38.0
    p1 = [
        (x1 - 18, cy - 11), (x1 + 10, cy - 11), (x1 + 10, cy + 19), (x1 - 18, cy + 19),
        (x1 - 7, cy - 21), (x1 + 21, cy - 21), (x1 + 21, cy + 9), (x1 - 7, cy + 9),
    ]
    cube_e = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    _draw_small_graph(c, p1, cube_e, node_stroke=acc)

    x2 = 102.0
    p2 = [
        (x2 - 20, cy - 8), (x2 + 8, cy - 8), (x2 + 20, cy + 7), (x2 - 8, cy + 7),
        (x2 - 7, cy - 21), (x2 + 20, cy - 21), (x2 + 7, cy + 20), (x2 - 20, cy + 20),
    ]
    _draw_small_graph(c, p2, cube_e, node_stroke=theme.gold if theme.is_dark else acc)

    x3 = 176.0
    p3 = [
        (x3 - 28, cy - 20), (x3 + 28, cy - 20), (x3 + 28, cy + 20), (x3 - 28, cy + 20),
        (x3 - 9, cy), (x3 - 28, cy), (x3 + 9, cy), (x3 + 28, cy),
    ]
    e3 = [
        (0, 1), (2, 3), (0, 5), (5, 3), (1, 7), (7, 2),
        (0, 6), (1, 4), (3, 6), (2, 4), (5, 4), (6, 7),
    ]
    _draw_small_graph(c, p3, e3, node_stroke=theme.mint if theme.is_dark else acc)

    x4 = 248.0
    p4 = [
        (x4 - 6, cy - 24), (x4 + 13, cy - 24),
        (x4 - 20, cy - 9), (x4 + 26, cy - 9),
        (x4 - 21, cy + 10), (x4 + 26, cy + 11),
        (x4 - 7, cy + 24), (x4 + 13, cy + 24),
    ]
    e4 = [
        (0, 1), (0, 5), (0, 7),
        (1, 2), (1, 4),
        (2, 5), (2, 6),
        (3, 4), (3, 5), (3, 7),
        (4, 7), (6, 5),
    ]
    e4_cube = [
        (0, 1), (0, 4), (0, 7),
        (1, 2), (1, 6),
        (2, 5), (2, 7),
        (3, 4), (3, 5), (3, 6),
        (4, 5), (6, 7),
    ]
    _ = e4
    _draw_small_graph(c, p4, e4_cube, node_stroke=theme.coral if theme.is_dark else acc)

    x5 = 314.0
    a, b = 9.0, 22.0
    p5 = [
        (x5 - a, cy - b), (x5 + a, cy - b),
        (x5 + b, cy - a), (x5 + b, cy + a),
        (x5 + a, cy + b), (x5 - a, cy + b),
        (x5 - b, cy + a), (x5 - b, cy - a),
    ]
    e5 = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0),
        (0, 5), (1, 4), (7, 2), (6, 3),
    ]
    _draw_small_graph(c, p5, e5, node_stroke=theme.violet if theme.is_dark else acc)

    x6 = 376.0
    xs6 = [x6 - 27, x6 - 9, x6 + 9, x6 + 27]
    p6 = [(xx, cy - 10) for xx in xs6] + [(xx, cy + 10) for xx in xs6]
    e6 = [(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (0, 4), (1, 5), (2, 6), (3, 7), (0, 3), (4, 7)]
    cv6 = {(0, 3): -16.0, (4, 7): 16.0}
    _draw_small_graph(c, p6, e6, node_stroke=theme.cyan if theme.is_dark else acc, curved=cv6)

    c.text(422, cy, "(16)", font_size=10.0, fill=theme.muted if theme.is_dark else theme.fg)
    return c.to_svg()


def fig_p031_inline(theme: Theme) -> str:
    w, h = 380.0, 88.0
    c = SvgCanvas(w, h, theme)
    cy = 38.0

    x_s = 38.0
    p_star = [(x_s, cy)] + [
        (x_s + 20.0 * math.cos(-math.pi / 2 + k * 2 * math.pi / 5), cy + 20.0 * math.sin(-math.pi / 2 + k * 2 * math.pi / 5))
        for k in range(5)
    ]
    _draw_small_graph(c, p_star, [(0, i) for i in range(1, 6)], node_stroke=theme.cyan if theme.is_dark else theme.fg)
    c.text(68, cy + 2, ";", font_size=11.0, fill=theme.fg)
    c.text(x_s, 74, "K_{1,5}", font_size=10.5, italic=True, rich=True)

    p_b1 = [(100 + i * 16, cy - 11) for i in range(3)] + [(100 + i * 16, cy + 11) for i in range(3)]
    _draw_small_graph(c, p_b1, [(i, 3 + j) for i in range(3) for j in range(3)], node_stroke=theme.gold if theme.is_dark else theme.fg)
    c.text(149, cy, "≅", font_size=12.0, fill=theme.fg)
    hx = 182.0
    p_b2 = [(hx + 20.0 * math.cos(k * math.pi / 3), cy + 20.0 * math.sin(k * math.pi / 3)) for k in range(6)]
    e_b2 = [(k, (k + 1) % 6) for k in range(6)] + [(0, 3), (1, 4), (2, 5)]
    _draw_small_graph(c, p_b2, e_b2, node_stroke=theme.gold if theme.is_dark else theme.fg)
    c.text(213, cy + 2, ";", font_size=11.0, fill=theme.fg)
    c.text(149, 74, "K_{3,3}", font_size=10.5, italic=True, rich=True)

    kx = 252.0
    p_c1 = [(kx + 20.0 * math.cos(k * math.pi / 3), cy + 20.0 * math.sin(k * math.pi / 3)) for k in range(6)]
    e_c1 = [(i, j) for i in range(6) for j in range(i + 1, 6) if (i, j) not in ((0, 3), (1, 4), (2, 5))]
    _draw_small_graph(c, p_c1, e_c1, node_stroke=theme.mint if theme.is_dark else theme.fg)
    c.text(286, cy, "≅", font_size=12.0, fill=theme.fg)
    ox = 322.0
    ro, ri = 22.0, 9.5
    p_c2 = (
        [(ox + ro * math.cos(-math.pi / 2 + k * 2 * math.pi / 3), cy + 4 + ro * math.sin(-math.pi / 2 + k * 2 * math.pi / 3)) for k in range(3)]
        + [(ox + ri * math.cos(math.pi / 2 + k * 2 * math.pi / 3), cy + 4 + ri * math.sin(math.pi / 2 + k * 2 * math.pi / 3)) for k in range(3)]
    )
    e_c2 = [
        (0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3),
        (0, 4), (0, 5), (1, 3), (1, 5), (2, 3), (2, 4),
    ]
    _draw_small_graph(c, p_c2, e_c2, node_stroke=theme.mint if theme.is_dark else theme.fg)
    c.text(354, cy + 2, ".", font_size=11.0, fill=theme.fg)
    c.text(288, 74, "K_{2,2,2}", font_size=10.5, italic=True, rich=True)
    return c.to_svg()


def fig_p032_inline(theme: Theme) -> str:
    w, h = 380.0, 78.0
    c = SvgCanvas(w, h, theme)
    cy = 34.0
    vr = 2.5

    def draw_vec_label(x: float, y: float, letter: str) -> None:
        c.text(x, y, f"{letter}_5", font_size=10.5, italic=True, rich=True)
        c.line(x + 1.5, y - 4.8, x + 8.5, y - 4.8, stroke=theme.fg, stroke_width=0.85, arrow_end=True)

    xs1 = [24 + i * 20.0 for i in range(5)]
    col1 = theme.cyan if theme.is_dark else theme.fg
    for i in range(4):
        c.graph_edge(xs1[i], cy, xs1[i + 1], cy, r1=vr, r2=vr, stroke=col1, stroke_width=1.15, directed=True)
    arcs_k5 = [
        (0, 2, -11.0), (1, 3, 11.0), (2, 4, -11.0),
        (0, 3, 16.0), (1, 4, -16.0), (0, 4, -21.0),
    ]
    for u, v, cv in arcs_k5:
        c.graph_edge(xs1[u], cy, xs1[v], cy, r1=vr, r2=vr, curve=cv, stroke=col1, stroke_width=1.1, directed=True)
    for xx in xs1:
        c.circle(xx, cy, vr, fill=theme.node_fill, stroke=col1, stroke_width=1.2)
    c.text(118, cy + 1, ";", font_size=11.0)
    draw_vec_label(64, 63, "K")

    xs2 = [142 + i * 20.0 for i in range(5)]
    col2 = theme.gold if theme.is_dark else theme.fg
    for i in range(4):
        c.graph_edge(xs2[i], cy, xs2[i + 1], cy, r1=vr, r2=vr, stroke=col2, stroke_width=1.2, directed=True)
    for xx in xs2:
        c.circle(xx, cy, vr, fill=theme.node_fill, stroke=col2, stroke_width=1.2)
    c.text(236, cy + 1, ";", font_size=11.0)
    draw_vec_label(182, 63, "P")

    xs3 = [260 + i * 20.0 for i in range(5)]
    col3 = theme.mint if theme.is_dark else theme.fg
    for i in range(4):
        c.graph_edge(xs3[i], cy + 4, xs3[i + 1], cy + 4, r1=vr, r2=vr, stroke=col3, stroke_width=1.2, directed=True)
    d_ret = (
        f"M {fmt(xs3[4])} {fmt(cy + 4 - vr)} "
        f"C {fmt(xs3[4] + 10)} {fmt(cy - 15)} {fmt(xs3[0] - 10)} {fmt(cy - 15)} {fmt(xs3[0])} {fmt(cy + 4 - vr)}"
    )
    c.path(d_ret, stroke=col3, stroke_width=1.2, arrow_end=True)
    for xx in xs3:
        c.circle(xx, cy + 4, vr, fill=theme.node_fill, stroke=col3, stroke_width=1.2)
    c.text(356, cy + 4, ".", font_size=11.0)
    draw_vec_label(300, 63, "C")
    return c.to_svg()


def fig_3(theme: Theme) -> str:
    w, h = 440.0, 212.0
    c = SvgCanvas(w, h, theme)

    pos: dict[int, tuple[float, float]] = {
        1: (132.0, 24.0),
        10: (22.0, 74.0),
        9: (50.0, 74.0),
        8: (78.0, 74.0),
        14: (105.0, 74.0),
        0: (132.0, 74.0),
        15: (159.0, 74.0),
        6: (186.0, 74.0),
        4: (214.0, 74.0),
        11: (22.0, 114.0),
        7: (50.0, 114.0),
        3: (78.0, 114.0),
        16: (105.0, 114.0),
        2: (132.0, 114.0),
        13: (159.0, 114.0),
        12: (186.0, 114.0),
        5: (214.0, 114.0),
    }

    arcs = [
        (1, 0, 0.0),
        (0, 14, 0.0),
        (0, 8, -22.0),
        (8, 14, -6.5),
        (14, 8, -6.5),
        (8, 3, 0.0),
        (0, 16, 0.0),
        (16, 3, 0.0),
        (0, 13, 0.0),
        (13, 12, 0.0),
        (0, 15, 0.0),
        (0, 6, 22.0),
        (15, 6, -6.5),
        (6, 15, -6.5),
        (4, 5, -6.5),
        (5, 4, -6.5),
        (10, 11, -6.5),
        (11, 10, -6.5),
    ]
    ec = theme.cyan if theme.is_dark else theme.fg
    for u, v, cv in arcs:
        c.graph_edge(pos[u][0], pos[u][1], pos[v][0], pos[v][1], r1=9.2, r2=9.8, curve=cv, stroke=ec, stroke_width=1.15, directed=True)

    comp_col = {
        0: theme.gold, 1: theme.gold, 3: theme.cyan, 6: theme.cyan, 8: theme.cyan,
        12: theme.cyan, 13: theme.cyan, 14: theme.cyan, 15: theme.cyan, 16: theme.cyan,
        4: theme.mint, 5: theme.mint,
        10: theme.violet, 11: theme.violet,
        2: theme.coral, 7: theme.muted, 9: theme.muted,
    }
    for vid, (vx, vy) in pos.items():
        pw = 19.0 if vid >= 10 else 16.0
        st = comp_col[vid] if theme.is_dark else theme.fg
        _pill(c, vx, vy, pw, 14.0, str(vid), stroke=st, font_size=8.8)

    c.text(14, 144, "LEGEND", font_size=7.8, anchor="start", bold=True, sans=True, fill=theme.gold if theme.is_dark else theme.fg)
    c.text(14, 156, "0: Pierre Michel, the French conductor", font_size=7.1, anchor="start")
    c.text(14, 167, "1: Hercule Poirot, the Belgian detective", font_size=7.1, anchor="start")

    right_legend = [
        " 2: Samuel Edward Ratchett, the deceased American",
        " 3: Caroline Martha Hubbard, the American matron",
        " 4: Edward Henry Masterman, the British valet",
        " 5: Antonio Foscarelli, the Italian automobile salesman",
        " 6: Hector MacQueen, the American secretary",
        " 7: Harvey Harris, the Englishman who didn't show up",
        " 8: Hildegarde Schmidt, the German lady's maid",
        " 9: (vacancy)",
        "10: Greta Ohlsson, the Swedish nurse",
        "11: Mary Hermione Debenham, the English governess",
        "12: Helena Maria Andrenyi, the beautiful countess",
        "13: Rudolph Andrenyi, the Hungarian count/diplomat",
        "14: Natalia Dragomiroff, the Russian princess dowager",
        "15: Colonel Arbuthnot, the British officer from India",
        "16: Cyrus Bettman Hardman, the American detective",
    ]
    for i, line_txt in enumerate(right_legend):
        c.text(236, 17 + i * 12.2, line_txt.strip(), font_size=7.0, anchor="start")

    return c.to_svg()


_LISA_PORTRAIT = [
    "64454443435446545464557567766543344333",
    "64444433446644566666778688777766544334",
    "56654644455565466666850000000077655334",
    "65665664666655576782000000000000886555",
    "79877656777876778820146531000000097767",
    "97867987877778888506eefeb8300000008767",
    "9c89caa9999988785039eeeec7321000003448",
    "68769bd8dcc998bb0049cccec8742100000233",
    "32444664428ddce100565bc323321100000013",
    "335333321229c8810001025020002100000101",
    "433333212212233000bb8953abb85100000001",
    "1333222211111210006ccb54bca52000000134",
    "112222322221110000287a31b8521000000001",
    "113222222122111000036b2323311000000011",
    "01222222112111100003963244211000000001",
    "0002221121222330000009c532110000000002",
    "00002221112223300000000101000000000001",
    "00000212223333320000000100011100000001",
    "22222223223333330000000322112200000000",
    "32333111110011010000002233334420000000",
    "13221111111111000001457877887630000000",
    "2112121221111110000789aa99998630000000",
    "21113332211111000029aaaaa9998620000000",
    "1111101321110000249aaaaaaa998520001022",
    "111100001220000019aa889aaaaa8510100000",
    "1111111110000000002638aabba95000000000",
    "10110100000000011110000013300000000000",
    "00001111000000000001111000000000000000",
    "00000000000000000000100000000000000000",
    "02111210000000000000000000000000000000",
    "12222210000000000000000000000000000000",
    "00000000000000000000000000000000000000",
    "00000000000000000000000000000000000000",
    "00000000000000000000000000000000000000",
    "00000000000000000000000000000000000000",
    "00000000000000000000000000000000000000",
    "00000000000000000000000000000000000000",
    "00000000000100443200000000000000000000",
    "00000000000003444332220000000000000000",
    "00000000000002222333222320000000000000",
    "00000000000000001222222233000000000000",
    "00000000000001211111212100100000000000",
    "00000000000100331001220120001000000000",
    "00000000000021222100002101100000000000",
    "00000000000000120000000000000000000000",
    "00000000000000000000000000000000000000",
    "00000000000000000000000000000000000000",
    "00000000000000000000000000000000000000",
    "00000000000000000000000000000000000000",
]

_LISA_CLOSEUP = [
    "66789abbcdddddddddddddddddeeeeedddddcbbbbaa",
    "6689aabcdddddddddddddddddddeeeeeddddcbbbbaa",
    "56789abcddddddddddddddddddddeedddccdcbbaaaa",
    "56789abbccccdddddddddddddddddbbaaaabaaaa999",
    "56789aabbbabbbcdddddddddddcb9777778899a9999",
    "56789aaa99999abcdddddddddb98655566667788888",
    "56899998876678abcdddddddb966555555556666666",
    "568998766555668abdddddca9655555555555555555",
    "5667666555555568acdccda97554444444455555555",
    "55555555555555568bbbbba76554444445566655544",
    "45555556666655556abbbb965544444556777765544",
    "444455666655555559aaaa865544445555555555554",
    "444455554444455557aaaa755544445555543334444",
    "4444445554334455569aa9655444455556653433334",
    "5554556654444445569aa9654444555799754444444",
    "6655567865555555669aa9655445567aaa975555555",
    "6766678aa976556666aba96554455678a9997666555",
    "677666788765555667aba9655555566677776655555",
    "688776655555556777aba9655555566666655555555",
    "89aa98765555678999bcb9655555667876666555667",
    "8adddbba98888abbaabdb965555679aaa99aaaaabbc",
    "9bdddddddbaabbbbbbcdb86555568abbccddddddddd",
    "9abddddddddcdddcbccdb86555579abddddeeeeeedd",
]


def _lisa_palette(theme: Theme) -> list[str]:
    if theme.is_dark:
        return [
            "#070B14", "#0C1322", "#111C30", "#16253E",
            "#1C2F4E", "#233B5F", "#2B4872", "#345786",
            "#3E679B", "#4979B1", "#558CC8", "#65A1DB",
            "#7EB6E6", "#9ECAEF", "#C4E1F7", "#EAF6FF",
        ]
    out: list[str] = []
    for k in range(16):
        v = round(16 + k * (242 - 16) / 15.0)
        out.append(f"#{v:02X}{v:02X}{v:02X}")
    return out


def _draw_rookwise_grid(
    c: SvgCanvas,
    grid: list[str],
    x0: float,
    y0: float,
    cell: float,
    palette: list[str],
    draw_boundaries: bool,
    boundary_col: str,
) -> None:
    nr = len(grid)
    nc = len(grid[0])
    vals = [[int(ch, 16) for ch in row] for row in grid]
    for r in range(nr):
        c_idx = 0
        while c_idx < nc:
            lv = vals[r][c_idx]
            start = c_idx
            while c_idx < nc and vals[r][c_idx] == lv:
                c_idx += 1
            rx = x0 + start * cell
            ry = y0 + r * cell
            rw = (c_idx - start) * cell
            c.rect(rx, ry, rw + 0.25, cell + 0.25, fill=palette[lv])

    if draw_boundaries:
        segs: list[str] = []
        for r in range(nr + 1):
            c_idx = 0
            while c_idx < nc:
                has_edge = r == 0 or r == nr or vals[r - 1][c_idx] != vals[r][c_idx]
                if not has_edge:
                    c_idx += 1
                    continue
                start = c_idx
                while c_idx < nc and (r == 0 or r == nr or vals[r - 1][c_idx] != vals[r][c_idx]):
                    c_idx += 1
                segs.append(
                    f"M {fmt(x0 + start * cell)} {fmt(y0 + r * cell)} H {fmt(x0 + c_idx * cell)}"
                )
        for col_i in range(nc + 1):
            r = 0
            while r < nr:
                has_edge = col_i == 0 or col_i == nc or vals[r][col_i - 1] != vals[r][col_i]
                if not has_edge:
                    r += 1
                    continue
                start = r
                while r < nr and (col_i == 0 or col_i == nc or vals[r][col_i - 1] != vals[r][col_i]):
                    r += 1
                segs.append(
                    f"M {fmt(x0 + col_i * cell)} {fmt(y0 + start * cell)} V {fmt(y0 + r * cell)}"
                )
        c.path(" ".join(segs), stroke=boundary_col, stroke_width=0.68)


def fig_4(theme: Theme) -> str:
    w, h = 448.0, 200.0
    c = SvgCanvas(w, h, theme)
    pal = _lisa_palette(theme)

    px0, py0, pcell = 14.0, 12.0, 3.55
    pw = len(_LISA_PORTRAIT[0]) * pcell
    ph = len(_LISA_PORTRAIT) * pcell
    _draw_rookwise_grid(c, _LISA_PORTRAIT, px0, py0, pcell, pal, False, "none")
    c.rect(px0, py0, pw, ph, fill="none", stroke=theme.cyan if theme.is_dark else theme.fg, stroke_width=1.2)

    box_x = px0 + 18 * pcell
    box_y = py0 + 7 * pcell
    box_w = 10 * pcell
    box_h = 5.4 * pcell
    if theme.is_dark:
        c.rect(box_x, box_y, box_w, box_h, fill="none", stroke=theme.gold, stroke_width=1.1, dashed="2.5,2")

    cx0, cy0, ccell = 164.0, 38.0, 6.25
    cw = len(_LISA_CLOSEUP[0]) * ccell
    ch = len(_LISA_CLOSEUP) * ccell
    bcol = "#090D16" if theme.is_dark else "#0F172A"
    _draw_rookwise_grid(c, _LISA_CLOSEUP, cx0, cy0, ccell, pal, True, bcol)
    c.rect(cx0, cy0, cw, ch, fill="none", stroke=theme.gold if theme.is_dark else theme.fg, stroke_width=1.25)

    if theme.is_dark:
        c.line(box_x + box_w, box_y, cx0, cy0, stroke=theme.gold, stroke_width=0.85, dashed="3,2.5", opacity=0.75)
        c.line(box_x + box_w, box_y + box_h, cx0, cy0 + ch, stroke=theme.gold, stroke_width=0.85, dashed="3,2.5", opacity=0.75)

    return c.to_svg()


def fig_5(theme: Theme) -> str:
    w, h = 420.0, 170.0
    c = SvgCanvas(w, h, theme)
    vr = 2.5

    bx0, by0, bstep = 26.0, 20.0, 18.0
    b_pts: dict[tuple[int, int], tuple[float, float]] = {}
    for r in range(6):
        for col_i in range(9):
            b_pts[(r, col_i)] = (bx0 + col_i * bstep, by0 + r * bstep)
    ec_b = theme.muted if theme.is_dark else "#334155"
    ns_b = theme.cyan if theme.is_dark else theme.fg
    for (r1, c1), (x1, y1) in b_pts.items():
        for dr, dc in ((1, 2), (2, 1), (1, -2), (2, -1)):
            r2, c2 = r1 + dr, c1 + dc
            if (r2, c2) in b_pts:
                x2, y2 = b_pts[(r2, c2)]
                c.graph_edge(x1, y1, x2, y2, r1=vr, r2=vr, stroke=ec_b, stroke_width=0.95)
    for px, py in b_pts.values():
        c.circle(px, py, vr, fill=theme.node_fill, stroke=ns_b, stroke_width=1.15)

    bcx = bx0 + 4 * bstep
    c.text(bcx, 134, "board(6, 9, 0, 0, 5, 0, 0)", font_size=9.2, italic=True)
    c.text(bcx, 148, "(Knight moves on a 6 × 9 chessboard)", font_size=8.8, fill=theme.muted if theme.is_dark else theme.fg)

    sx_center, sy_top = 316.0, 20.0
    s_dx = 18.0
    s_dy = s_dx * math.sqrt(3.0) / 2.0
    s_pts: dict[tuple[int, int, int], tuple[float, float]] = {}
    for x1 in range(9):
        for x2 in range(8):
            x3 = 10 - x1 - x2
            if 0 <= x3 <= 6:
                row = 6 - x3
                px = sx_center + (x2 - x1) * 0.5 * s_dx - 9.0
                py = sy_top + row * s_dy
                s_pts[(x1, x2, x3)] = (px, py)

    ec_s = theme.muted if theme.is_dark else "#334155"
    ns_s = theme.gold if theme.is_dark else theme.fg
    for (a, b, d_v), (x1, y1) in s_pts.items():
        for da, db, dd in ((1, -1, 0), (1, 0, -1), (0, 1, -1)):
            nb = (a + da, b + db, d_v + dd)
            if nb in s_pts:
                x2, y2 = s_pts[nb]
                c.graph_edge(x1, y1, x2, y2, r1=vr, r2=vr, stroke=ec_s, stroke_width=1.05)
    for px, py in s_pts.values():
        c.circle(px, py, vr, fill=theme.node_fill, stroke=ns_s, stroke_width=1.15)

    c.text(312, 134, "simplex(10, 8, 7, 6, 0, 0, 0)", font_size=9.2, italic=True)
    c.text(312, 148, "(A truncated triangular grid)", font_size=8.8, fill=theme.muted if theme.is_dark else theme.fg)
    return c.to_svg()


def fig_p041_inline(theme: Theme) -> str:
    w, h = 408.0, 128.0
    c = SvgCanvas(w, h, theme)
    vr = 2.6
    cy = 64.0

    g_rel = [
        (0.0, -9.0), (0.0, 9.0), (16.0, 0.0),
        (34.0, -10.0), (34.0, 10.0), (52.0, 0.0),
    ]
    g_edges = [(0, 2), (1, 2), (2, 3), (2, 4), (3, 5), (4, 5)]
    gx0 = 20.0
    g_pts = [(gx0 + dx, cy + dy) for dx, dy in g_rel]
    _draw_small_graph(c, g_pts, g_edges, vr=vr, node_stroke=theme.cyan if theme.is_dark else theme.fg)

    c.rect(91, cy - 3.5, 7.0, 7.0, fill="none", stroke=theme.gold if theme.is_dark else theme.fg, stroke_width=1.2)

    h_rel = [(-10.0, -15.0), (10.0, -15.0), (0.0, 0.0), (0.0, 18.0)]
    h_edges = [(0, 1), (0, 2), (1, 2), (2, 3)]
    hx0 = 122.0
    h_pts = [(hx0 + dx, cy + dy) for dx, dy in h_rel]
    _draw_small_graph(c, h_pts, h_edges, vr=vr, node_stroke=theme.mint if theme.is_dark else theme.fg)

    c.text(154, cy, "=", font_size=12.0)

    px0, py0 = 188.0, 62.0
    g_prod = [
        (0.0, -24.0), (4.0, 22.0), (48.0, -2.0),
        (100.0, -26.0), (104.0, 20.0), (152.0, -4.0),
    ]
    h_prod = [(-9.0, -14.0), (9.0, -14.0), (0.0, 0.0), (0.0, 17.0)]

    prod_pts: dict[tuple[int, int], tuple[float, float]] = {}
    for ui, (ux, uy) in enumerate(g_prod):
        for vi, (vx, vy) in enumerate(h_prod):
            prod_pts[(ui, vi)] = (px0 + ux + vx, py0 + uy + vy)

    ec_g = theme.cyan if theme.is_dark else "#334155"
    ec_h = theme.mint if theme.is_dark else theme.fg
    for u1, u2 in g_edges:
        for vi in range(4):
            p1, p2 = prod_pts[(u1, vi)], prod_pts[(u2, vi)]
            c.graph_edge(p1[0], p1[1], p2[0], p2[1], r1=vr, r2=vr, stroke=ec_g, stroke_width=0.95)
    for ui in range(6):
        for v1, v2 in h_edges:
            p1, p2 = prod_pts[(ui, v1)], prod_pts[(ui, v2)]
            c.graph_edge(p1[0], p1[1], p2[0], p2[1], r1=vr, r2=vr, stroke=ec_h, stroke_width=1.15)
    for px, py in prod_pts.values():
        c.circle(px, py, vr, fill=theme.node_fill, stroke=theme.gold if theme.is_dark else theme.fg, stroke_width=1.1)

    c.text(392, cy + 4, ".", font_size=12.0)
    return c.to_svg()


def fig_p042_inline(theme: Theme) -> str:
    w, h = 384.0, 102.0
    c = SvgCanvas(w, h, theme)
    vr = 2.6
    sx, sy = 20.0, 18.0

    def draw_grid_base(x0: float, y0: float, col: str, wrap_h: bool, wrap_v: bool) -> None:
        pts = [[(x0 + ci * sx, y0 + ri * sy) for ci in range(4)] for ri in range(3)]
        wrap_col = theme.coral if theme.is_dark else theme.fg
        if wrap_h:
            for ri in range(3):
                lx, ly = pts[ri][0]
                rx, ry = pts[ri][3]
                d = (
                    f"M {fmt(lx - vr * 0.7)} {fmt(ly - vr * 0.7)} "
                    f"C {fmt(lx - 10)} {fmt(ly - 10)} {fmt(rx + 10)} {fmt(ry - 10)} {fmt(rx + vr * 0.7)} {fmt(ry - vr * 0.7)}"
                )
                c.path(d, stroke=wrap_col, stroke_width=1.05)
        if wrap_v:
            for ci in range(4):
                tx, ty = pts[0][ci]
                bx, by = pts[2][ci]
                d = (
                    f"M {fmt(tx + vr * 0.7)} {fmt(ty - vr * 0.7)} "
                    f"C {fmt(tx + 10)} {fmt(ty - 10)} {fmt(bx + 10)} {fmt(by + 10)} {fmt(bx + vr * 0.7)} {fmt(by + vr * 0.7)}"
                )
                c.path(d, stroke=theme.gold if theme.is_dark else theme.fg, stroke_width=1.05)
        for ri in range(3):
            for ci in range(3):
                p1, p2 = pts[ri][ci], pts[ri][ci + 1]
                c.graph_edge(p1[0], p1[1], p2[0], p2[1], r1=vr, r2=vr, stroke=col, stroke_width=1.2)
        for ri in range(2):
            for ci in range(4):
                p1, p2 = pts[ri][ci], pts[ri + 1][ci]
                c.graph_edge(p1[0], p1[1], p2[0], p2[1], r1=vr, r2=vr, stroke=col, stroke_width=1.2)
        for ri in range(3):
            for ci in range(4):
                px, py = pts[ri][ci]
                c.circle(px, py, vr, fill=theme.node_fill, stroke=col, stroke_width=1.2)

    xs = [28.0, 158.0, 290.0]
    y_top = 20.0
    draw_grid_base(xs[0], y_top, theme.cyan if theme.is_dark else theme.fg, False, False)
    draw_grid_base(xs[1], y_top, theme.mint if theme.is_dark else theme.fg, True, False)
    draw_grid_base(xs[2], y_top, theme.cyan if theme.is_dark else theme.fg, True, True)

    captions = [
        (xs[0] + 30, "P_3", "P_4", "(3 × 4 grid)"),
        (xs[1] + 30, "P_3", "C_4", "(3 × 4 cylinder)"),
        (xs[2] + 30, "C_3", "C_4", "(3 × 4 torus)"),
    ]
    for mcx, lhs, rhs, sub in captions:
        c.text(mcx - 13, 74, lhs, font_size=9.5, italic=True, rich=True)
        c.rect(mcx - 2.6, 71.2, 5.2, 5.2, fill="none", stroke=theme.fg, stroke_width=1.0)
        c.text(mcx + 13, 74, rhs, font_size=9.5, italic=True, rich=True)
        c.text(mcx, 89, sub, font_size=8.6, fill=theme.muted if theme.is_dark else theme.fg)

    return c.to_svg()


def fig_p047_inline(theme: Theme) -> str:
    w, h = 210.0, 186.0
    c = SvgCanvas(w, h, theme)
    cx, cy = w * 0.5, h * 0.5
    rad = 64.0
    vr = 2.8

    labels = [
        "[010]", "001", "[100]", "010", "[001]", "100", "[011]",
        "011", "[111]", "110", "[110]", "111", "[101]", "101",
    ]
    pts: list[tuple[float, float]] = []
    lpts: list[tuple[float, float]] = []
    for k in range(14):
        ang = -math.pi / 2.0 - math.pi / 14.0 + k * (2.0 * math.pi / 14.0)
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        lrad = rad + (16.5 if labels[k].startswith("[") else 14.0)
        lpts.append((cx + lrad * math.cos(ang), cy + lrad * math.sin(ang)))

    inc = {
        "001": {"[010]", "[100]", "[110]"},
        "010": {"[001]", "[100]", "[101]"},
        "011": {"[011]", "[100]", "[111]"},
        "100": {"[001]", "[010]", "[011]"},
        "101": {"[010]", "[101]", "[111]"},
        "110": {"[001]", "[110]", "[111]"},
        "111": {"[011]", "[101]", "[110]"},
    }
    idx_map = {lbl: i for i, lbl in enumerate(labels)}
    ec_ring = theme.cyan if theme.is_dark else theme.fg
    ec_chord = theme.gold if theme.is_dark else theme.fg
    for v_lbl, e_set in inc.items():
        u = idx_map[v_lbl]
        for e_lbl in e_set:
            v = idx_map[e_lbl]
            diff = min((u - v) % 14, (v - u) % 14)
            col = ec_ring if diff == 1 else ec_chord
            c.graph_edge(pts[u][0], pts[u][1], pts[v][0], pts[v][1], r1=vr, r2=vr, stroke=col, stroke_width=1.2)

    for k, (px, py) in enumerate(pts):
        is_edge = labels[k].startswith("[")
        st = (theme.coral if is_edge else theme.cyan) if theme.is_dark else theme.fg
        c.circle(px, py, vr, fill=theme.node_fill, stroke=st, stroke_width=1.25)
        lx, ly = lpts[k]
        tcol = (theme.gold if is_edge else theme.fg) if theme.is_dark else theme.fg
        c.text(lx, ly, labels[k], font_size=8.4, fill=tcol, mono=True)

    return c.to_svg()


_USA_POS: dict[str, tuple[int, int]] = {
    "ND": (4, 0), "VT": (10, 0), "NH": (11, 0), "ME": (12, 0),
    "WA": (1, 1), "MT": (3, 1), "SD": (4, 1), "MN": (5, 1), "WI": (6, 1), "MI": (7, 1), "NY": (10, 1), "MA": (11, 1),
    "OR": (1, 2), "ID": (2, 2), "WY": (3, 2), "NE": (4, 2), "IA": (5, 2), "IL": (6, 2), "IN": (7, 2), "OH": (8, 2), "PA": (9, 2), "NJ": (10, 2), "CT": (11, 2), "RI": (12, 2),
    "CA": (0, 3), "NV": (1, 3), "UT": (2, 3), "CO": (3, 3), "KS": (4, 3), "MO": (5, 3), "KY": (7, 3), "WV": (8, 3), "MD": (9, 3), "DE": (10, 3),
    "AZ": (2, 4), "NM": (3, 4), "OK": (4, 4), "AR": (5, 4), "TN": (7, 4), "VA": (8, 4), "DC": (9, 4),
    "TX": (4, 5), "LA": (5, 5), "MS": (6, 5), "AL": (7, 5), "GA": (8, 5), "NC": (9, 5),
    "FL": (8, 6), "SC": (9, 6),
}

_USA_EDGES: list[tuple[str, str]] = [
    ("WA", "OR"), ("WA", "ID"), ("OR", "CA"), ("OR", "NV"), ("OR", "ID"),
    ("CA", "NV"), ("CA", "AZ"), ("NV", "ID"), ("NV", "UT"), ("NV", "AZ"),
    ("ID", "MT"), ("ID", "WY"), ("ID", "UT"), ("MT", "ND"), ("MT", "SD"), ("MT", "WY"),
    ("WY", "SD"), ("WY", "NE"), ("WY", "CO"), ("WY", "UT"), ("UT", "CO"), ("UT", "AZ"),
    ("AZ", "NM"), ("ND", "SD"), ("ND", "MN"), ("SD", "MN"), ("SD", "IA"), ("SD", "NE"),
    ("NE", "IA"), ("NE", "MO"), ("NE", "KS"), ("NE", "CO"), ("CO", "KS"), ("CO", "OK"), ("CO", "NM"),
    ("NM", "OK"), ("NM", "TX"), ("MN", "WI"), ("MN", "IA"), ("IA", "WI"), ("IA", "IL"), ("IA", "MO"),
    ("MO", "IL"), ("MO", "KY"), ("MO", "TN"), ("MO", "AR"), ("MO", "OK"), ("MO", "KS"),
    ("KS", "OK"), ("OK", "AR"), ("OK", "TX"), ("TX", "AR"), ("TX", "LA"),
    ("AR", "TN"), ("AR", "MS"), ("AR", "LA"), ("LA", "MS"), ("WI", "MI"), ("WI", "IL"),
    ("IL", "IN"), ("IL", "KY"), ("MI", "IN"), ("MI", "OH"), ("IN", "OH"), ("IN", "KY"),
    ("OH", "PA"), ("OH", "WV"), ("OH", "KY"), ("KY", "WV"), ("KY", "VA"), ("KY", "TN"),
    ("TN", "VA"), ("TN", "NC"), ("TN", "GA"), ("TN", "AL"), ("TN", "MS"), ("MS", "AL"),
    ("AL", "GA"), ("AL", "FL"), ("GA", "NC"), ("GA", "SC"), ("GA", "FL"), ("NC", "VA"), ("NC", "SC"),
    ("VA", "WV"), ("VA", "MD"), ("VA", "DC"), ("WV", "PA"), ("WV", "MD"), ("MD", "PA"), ("MD", "DE"), ("MD", "DC"),
    ("PA", "NY"), ("PA", "NJ"), ("PA", "DE"), ("DE", "NJ"), ("NJ", "NY"),
    ("NY", "VT"), ("NY", "MA"), ("NY", "CT"), ("VT", "NH"), ("VT", "MA"),
    ("NH", "ME"), ("NH", "MA"), ("MA", "CT"), ("MA", "RI"), ("CT", "RI"),
]


def _draw_usa_pair(
    theme: Theme,
    ind_set: set[str],
    left_title_1: str,
    left_title_2: str,
    right_title_1: str,
    right_title_2: str,
) -> str:
    w, h = 412.0, 122.0
    c = SvgCanvas(w, h, theme)
    sx, sy = 13.5, 11.2
    vr = 2.4
    cover_set = set(_USA_POS) - ind_set

    for idx, (active, accent, t1, t2) in enumerate([
        (cover_set, theme.coral if theme.is_dark else theme.fg, left_title_1, left_title_2),
        (ind_set, theme.gold if theme.is_dark else theme.fg, right_title_1, right_title_2),
    ]):
        ox = 20.0 + idx * 208.0
        oy = 15.0
        ec = theme.muted if theme.is_dark else "#475569"
        for u, v in _USA_EDGES:
            x1, y1 = ox + _USA_POS[u][0] * sx, oy + _USA_POS[u][1] * sy
            x2, y2 = ox + _USA_POS[v][0] * sx, oy + _USA_POS[v][1] * sy
            c.graph_edge(x1, y1, x2, y2, r1=vr, r2=vr, stroke=ec, stroke_width=0.95)
        for st, (gx, gy) in _USA_POS.items():
            px, py = ox + gx * sx, oy + gy * sy
            if st in active:
                c.circle(px, py, vr + 0.2, fill=accent, stroke=accent, stroke_width=1.0, glow=theme.is_dark)
            else:
                st_col = theme.cyan if theme.is_dark else theme.fg
                c.circle(px, py, vr, fill=theme.bg, stroke=st_col, stroke_width=1.05)
        mcx = ox + 6 * sx
        c.text(mcx, 96, t1, font_size=8.8)
        c.text(mcx, 108, t2, font_size=8.8, fill=theme.muted if theme.is_dark else theme.fg)

    return c.to_svg()


def fig_p048_inline_1(theme: Theme) -> str:
    ind_11 = {"AR", "AZ", "CO", "DC", "GA", "ID", "IN", "MA", "ME", "MN", "PA"}
    return _draw_usa_pair(
        theme,
        ind_11,
        "Minimal vertex cover,",
        "with 38 vertices",
        "Maximal independent set,",
        "with 11 vertices",
    )


def fig_p048_inline_2(theme: Theme) -> str:
    ind_19 = {"CA", "CT", "DC", "DE", "FL", "IL", "KS", "LA", "ME", "MI", "MN", "MT", "NM", "SC", "TN", "UT", "VT", "WA", "WV"}
    return _draw_usa_pair(
        theme,
        ind_19,
        "Minimum vertex cover,",
        "with 30 vertices",
        "Maximum independent set,",
        "with 19 vertices",
    )


def _draw_polyomino_boundary(
    c: SvgCanvas,
    cells: set[tuple[int, int]],
    x0: float,
    y_bot: float,
    cw: float,
    ch: float,
    stroke: str,
    stroke_width: float,
    fill: str = "none",
) -> None:
    if fill != "none":
        for gx, gy in cells:
            c.rect(x0 + gx * cw, y_bot - (gy + 1) * ch, cw + 0.2, ch + 0.2, fill=fill)
    segs: list[str] = []
    for gx, gy in cells:
        px = x0 + gx * cw
        py_top = y_bot - (gy + 1) * ch
        py_b = y_bot - gy * ch
        if (gx, gy + 1) not in cells:
            segs.append(f"M {fmt(px)} {fmt(py_top)} H {fmt(px + cw)}")
        if (gx, gy - 1) not in cells:
            segs.append(f"M {fmt(px)} {fmt(py_b)} H {fmt(px + cw)}")
        if (gx - 1, gy) not in cells:
            segs.append(f"M {fmt(px)} {fmt(py_top)} V {fmt(py_b)}")
        if (gx + 1, gy) not in cells:
            segs.append(f"M {fmt(px + cw)} {fmt(py_top)} V {fmt(py_b)}")
    c.path(" ".join(segs), stroke=stroke, stroke_width=stroke_width)


def fig_p059_inline_1(theme: Theme) -> str:
    w, h = 420.0, 168.0
    c = SvgCanvas(w, h, theme)
    cw, ch = 13.8, 12.6

    lx0, ly_bot = 16.0, 148.0
    for ty in range(3):
        for tx in range(3):
            is_center = tx == 1 and ty == 1
            bx = lx0 + tx * 4 * cw
            by = ly_bot - (ty + 1) * 3 * ch
            if is_center and theme.is_dark:
                c.rect(bx, by, 4 * cw, 3 * ch, fill=theme.node_alt)
            for ry in range(3):
                for cx_i in range(4):
                    gx = tx * 4 + cx_i
                    gy = ty * 3 + ry
                    val = (3 * cx_i + 4 * ry) % 12
                    px = lx0 + (gx + 0.5) * cw
                    py = ly_bot - (gy + 0.5) * ch
                    col = (theme.gold if is_center else theme.muted) if theme.is_dark else (theme.fg if is_center else "#64748B")
                    c.text(px, py, str(val), font_size=7.6, fill=col, bold=is_center)
    for ty in range(3):
        for tx in range(3):
            if not (tx == 1 and ty == 1):
                c.rect(
                    lx0 + tx * 4 * cw,
                    ly_bot - (ty + 1) * 3 * ch,
                    4 * cw,
                    3 * ch,
                    fill="none",
                    stroke=theme.panel_stroke if theme.is_dark else "#64748B",
                    stroke_width=0.9,
                )
    c.rect(
        lx0 + 4 * cw,
        ly_bot - 6 * ch,
        4 * cw,
        3 * ch,
        fill="none",
        stroke=theme.gold if theme.is_dark else theme.fg,
        stroke_width=1.85,
    )

    rx0, ry_bot = 224.0, 152.0
    rcw, rch = 12.8, 12.2
    base_12 = {
        (1, 4), (1, 3),
        (0, 2), (1, 2), (2, 2), (3, 2),
        (-1, 1), (0, 1), (2, 1),
        (2, 0), (3, 0), (4, 0),
    }

    u_cells: dict[tuple[int, int], int] = {}
    for ty in range(3):
        for tx in range(3):
            if tx == 1 and ty == 1:
                continue
            ox, oy = tx * 4, ty * 3
            blk = {(ox + dx, oy + dy) for dx, dy in base_12}
            st_col = theme.panel_stroke if theme.is_dark else "#64748B"
            _draw_polyomino_boundary(c, blk, rx0, ry_bot, rcw, rch, st_col, 0.9)
            for gx, gy in blk:
                u_cells[(gx, gy)] = 1

    center_blk = {(4 + dx, 3 + dy) for dx, dy in base_12}
    st_bold = theme.cyan if theme.is_dark else theme.fg
    fl_bold = theme.node_alt if theme.is_dark else "none"
    _draw_polyomino_boundary(c, center_blk, rx0, ry_bot, rcw, rch, st_bold, 1.85, fill=fl_bold)
    for gx, gy in center_blk:
        u_cells[(gx, gy)] = 2

    for (gx, gy), status in sorted(u_cells.items()):
        val = (3 * gx + 4 * gy) % 12
        px = rx0 + (gx + 0.5) * rcw
        py = ry_bot - (gy + 0.5) * rch
        is_b = status == 2
        tcol = (theme.gold if is_b else theme.muted) if theme.is_dark else (theme.fg if is_b else "#64748B")
        c.text(px, py, str(val), font_size=7.3, fill=tcol, bold=is_b)

    return c.to_svg()


def fig_p059_inline_2(theme: Theme) -> str:
    w, h = 320.0, 178.0
    c = SvgCanvas(w, h, theme)
    cw, ch = 15.2, 14.2
    x0, y_bot = 82.0, 122.0

    base_13 = (
        {(cx_i, 0) for cx_i in range(4)}
        | {(cx_i, 1) for cx_i in range(5)}
        | {(cx_i, 2) for cx_i in range(1, 5)}
    )
    shifts = [
        (-5, -2), (0, -3),
        (-4, 1), (5, -1),
        (1, 3), (5, 2),
        (0, 0),
    ]
    offsets = [
        (-5, -2, False),
        (-1, -3, False),
        (-4, 1, False),
        (4, -1, False),
        (1, 3, False),
        (5, 2, False),
        (0, 0, True),
    ]
    _ = shifts

    for dx, dy, is_center in offsets:
        tile = {(gx + dx, gy + dy) for gx, gy in base_13}
        st = (theme.gold if is_center else theme.cyan) if theme.is_dark else (theme.fg if is_center else "#64748B")
        if not is_center and theme.is_dark:
            st = theme.panel_stroke
        fl = (theme.node_alt if theme.is_dark else "#F8FAFC") if is_center else "none"
        _draw_polyomino_boundary(c, tile, x0, y_bot, cw, ch, st, 1.95 if is_center else 0.95, fill=fl)
        for gx, gy in tile:
            val = (gx + 4 * gy) % 13
            px = x0 + (gx + 0.5) * cw
            py = y_bot - (gy + 0.5) * ch
            tcol = (theme.gold if is_center else theme.muted) if theme.is_dark else (theme.fg if is_center else "#64748B")
            c.text(px, py, str(val), font_size=8.2, fill=tcol, bold=is_center)

    c.text(x0 + 10.6 * cw, y_bot - 1.5 * ch, ".", font_size=12.0)
    return c.to_svg()


def fig_6(theme: Theme) -> str:
    w, h = 300.0, 244.0
    c = SvgCanvas(w, h, theme)
    c.elements.append('<g transform="translate(5,6)">')
    nr = 10.2

    pos: dict[str, tuple[float, float]] = {
        "w": (98.0, 26.0),
        "u": (156.0, 62.0),
        "~t": (98.0, 98.0),
        "~x": (156.0, 98.0),
        "~z": (196.0, 98.0),
        "y": (28.0, 134.0),
        "z": (74.0, 134.0),
        "x": (118.0, 134.0),
        "t": (162.0, 134.0),
        "~y": (254.0, 98.0),
        "~u": (118.0, 172.0),
        "~w": (162.0, 206.0),
    }
    disp: dict[str, str] = {
        "w": "w", "u": "u", "y": "y", "z": "z", "x": "x", "t": "t",
        "~t": "\\bar{t}", "~x": "\\bar{x}", "~z": "\\bar{z}",
        "~y": "\\bar{y}", "~u": "\\bar{u}", "~w": "\\bar{w}",
    }

    scc_col = theme.muted if theme.is_dark else "#64748B"
    for single in ("w", "y", "~y", "~w"):
        sx, sy = pos[single]
        c.circle(sx, sy, 18.5, fill="none", stroke=scc_col, stroke_width=0.95, dashed="2.2,2.2")

    d_scc1 = (
        "M 138 50 Q 158 38 176 54 L 212 86 Q 222 98 208 114 L 176 148 "
        "Q 160 158 146 142 Q 140 132 142 114 L 138 66 Q 136 54 138 50 Z"
    )
    c.path(d_scc1, stroke=theme.cyan if theme.is_dark else scc_col, stroke_width=0.95, dashed="2.2,2.2")

    d_scc2 = (
        "M 84 84 Q 102 74 114 90 Q 120 100 128 118 Q 138 136 136 174 "
        "Q 134 192 114 190 Q 98 188 88 170 L 60 144 Q 50 132 62 118 Z"
    )
    c.path(d_scc2, stroke=theme.gold if theme.is_dark else scc_col, stroke_width=0.95, dashed="2.2,2.2")

    ec = theme.fg if not theme.is_dark else theme.cyan
    straight_arcs = [
        ("w", "~t"), ("~t", "~x"), ("~x", "u"), ("~z", "~y"),
        ("y", "z"), ("x", "z"), ("x", "t"), ("~u", "x"), ("t", "~w"),
    ]
    for a, b in straight_arcs:
        c.graph_edge(pos[a][0], pos[a][1], pos[b][0], pos[b][1], r1=nr, r2=nr + 0.5, stroke=ec, stroke_width=1.2, directed=True)

    bi_pairs = [("u", "~z"), ("~t", "z"), ("z", "~u"), ("t", "~z")]
    for a, b in bi_pairs:
        ax, ay = pos[a]
        bx, by = pos[b]
        dx, dy = bx - ax, by - ay
        dist = math.hypot(dx, dy)
        ux, uy = dx / dist, dy / dist
        c.line(
            ax + ux * (nr + 1.0),
            ay + uy * (nr + 1.0),
            bx - ux * (nr + 1.0),
            by - uy * (nr + 1.0),
            stroke=theme.gold if theme.is_dark else ec,
            stroke_width=1.2,
            arrow_start=True,
            arrow_end=True,
        )

    c.polyline(
        [(pos["w"][0] + nr, pos["w"][1]), (pos["~y"][0], pos["w"][1]), (pos["~y"][0], pos["~y"][1] - nr - 0.8)],
        stroke=ec,
        stroke_width=1.15,
        arrow_end=True,
    )
    c.polyline(
        [(pos["y"][0], pos["y"][1] - nr), (pos["y"][0], pos["u"][1]), (pos["u"][0] - nr - 0.8, pos["u"][1])],
        stroke=ec,
        stroke_width=1.15,
        arrow_end=True,
    )
    c.polyline(
        [(pos["y"][0], pos["y"][1] + nr), (pos["y"][0], pos["~w"][1]), (pos["~w"][0] - nr - 0.8, pos["~w"][1])],
        stroke=ec,
        stroke_width=1.15,
        arrow_end=True,
    )
    c.polyline(
        [(pos["~u"][0] + nr, pos["~u"][1]), (pos["~y"][0], pos["~u"][1]), (pos["~y"][0], pos["~y"][1] + nr + 0.8)],
        stroke=ec,
        stroke_width=1.15,
        arrow_end=True,
    )

    c.graph_edge(pos["~t"][0], pos["~t"][1], pos["~z"][0], pos["~z"][1], r1=nr, r2=nr + 0.5, curve=-24.0, stroke=ec, stroke_width=1.15, directed=True)
    c.graph_edge(pos["x"][0], pos["x"][1], pos["~z"][0], pos["~z"][1], r1=nr, r2=nr + 0.5, curve=14.0, stroke=ec, stroke_width=1.15, directed=True)

    for k, (nx, ny) in pos.items():
        if k in ("t", "u", "~x", "~z"):
            st = theme.cyan
        elif k in ("x", "z", "~t", "~u"):
            st = theme.gold
        else:
            st = theme.mint
        c.circle(nx, ny, nr, fill=theme.node_fill, stroke=st if theme.is_dark else theme.fg, stroke_width=1.35)
        c.text(nx, ny + 0.5, disp[k], font_size=10.0, italic=True, rich=True)

    c.elements.append("</g>")
    return c.to_svg()


def fig_7(theme: Theme) -> str:
    w, h = 456.0, 198.0
    c = SvgCanvas(w, h, theme)

    ux, uy = 11.2, -7.2
    vx, vy = -11.2, -7.2
    wx, wy = 0.0, -13.2

    def proj(cx0: float, cy0: float, i: int, j: int, k: int) -> tuple[float, float]:
        return (cx0 + i * ux + j * vx + k * wx, cy0 + i * uy + j * vy + k * wy)

    front_faces = lambda i, j, k: (i == 0 or j == 0 or k == 3)

    specs = [
        (78.0, 152.0, (0, 3, 2, 3, 1, 3), {(0, 2, 1), (3, 3, 3)}, "(a) The interval [x .. y].", theme.cyan),
        (228.0, 152.0, (0, 2, 0, 2, 0, 1), {(0, 2, 1), (2, 0, 0)}, "(b) The interval [x .. z].", theme.mint),
        (378.0, 152.0, (2, 3, 0, 3, 0, 3), {(3, 3, 3), (2, 0, 0)}, "(c) The interval [y .. z].", theme.coral),
    ]

    boundary_lbls = [
        ((0, 0, 0), 5.0, 3.0, "start"),
        ((1, 0, 0), 5.0, 2.5, "start"),
        ((2, 0, 0), 6.0, 2.5, "start"),
        ((3, 0, 0), 5.0, 1.0, "start"),
        ((3, 0, 1), 5.0, 0.0, "start"),
        ((3, 0, 2), 5.0, 0.0, "start"),
        ((3, 0, 3), 5.0, -1.0, "start"),
        ((3, 1, 3), 5.0, -1.5, "start"),
        ((3, 2, 3), 5.0, -1.5, "start"),
        ((3, 3, 3), -4.5, -2.5, "end"),
        ((2, 3, 3), -4.5, -1.5, "end"),
        ((1, 3, 3), -4.5, -1.5, "end"),
        ((0, 3, 3), -5.0, -1.0, "end"),
        ((0, 3, 2), -5.0, 0.0, "end"),
        ((0, 3, 1), -5.0, 0.0, "end"),
        ((0, 3, 0), -5.0, 1.0, "end"),
        ((0, 2, 0), -5.0, 2.5, "end"),
        ((0, 1, 0), -5.0, 2.5, "end"),
    ]

    for cx0, cy0, (i0, i1, j0, j1, k0, k1), boxed, subcap, icol in specs:
        for pass_front in (False, True):
            for i in range(4):
                for j in range(4):
                    for k in range(4):
                        for di, dj, dk in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
                            ni, nj, nk = i + di, j + dj, k + dk
                            if ni < 4 and nj < 4 and nk < 4:
                                is_f = front_faces(i, j, k) and front_faces(ni, nj, nk)
                                if is_f != pass_front:
                                    continue
                                p1 = proj(cx0, cy0, i, j, k)
                                p2 = proj(cx0, cy0, ni, nj, nk)
                                col = (
                                    (theme.panel_stroke if not is_f else "#475569")
                                    if theme.is_dark
                                    else ("#CBD5E1" if not is_f else "#475569")
                                )
                                c.line(p1[0], p1[1], p2[0], p2[1], stroke=col, stroke_width=0.95 if is_f else 0.65)

        for pass_front in (False, True):
            for i in range(4):
                for j in range(4):
                    for k in range(4):
                        is_f = front_faces(i, j, k)
                        if is_f != pass_front:
                            continue
                        px, py = proj(cx0, cy0, i, j, k)
                        in_iv = i0 <= i <= i1 and j0 <= j <= j1 and k0 <= k <= k1
                        if (i, j, k) in boxed:
                            bcol = theme.gold if theme.is_dark else theme.fg
                            c.rect(px - 3.8, py - 3.8, 7.6, 7.6, fill=theme.bg, stroke=bcol, stroke_width=1.1)
                        if (i, j, k) == (2, 2, 1):
                            mcol = theme.gold if theme.is_dark else "#1E293B"
                            c.rect(px - 2.6, py - 2.6, 5.2, 5.2, fill=mcol, stroke=mcol, stroke_width=0.9)
                        elif in_iv:
                            fcol = icol if theme.is_dark else ("#0F172A" if is_f else "#64748B")
                            c.circle(px, py, 2.25 if is_f else 1.95, fill=fcol, stroke=fcol, stroke_width=0.7)
                            if theme.is_dark and not is_f:
                                c.circle(px, py, 1.95, fill=icol, stroke="none")
                        else:
                            st_c = ("#64748B" if is_f else "#334155") if theme.is_dark else ("#334155" if is_f else "#94A3B8")
                            c.circle(px, py, 2.1 if is_f else 1.75, fill=theme.bg, stroke=st_c, stroke_width=0.85)

        for (bi, bj, bk), dx, dy, anc in boundary_lbls:
            px, py = proj(cx0, cy0, bi, bj, bk)
            c.text(
                px + dx,
                py + dy,
                f"({bi},{bj},{bk})",
                font_size=5.6,
                anchor=anc,
                fill=theme.muted if theme.is_dark else theme.fg,
            )

        c.text(cx0, 182, subcap, font_size=8.6)

    return c.to_svg()


def fig_p081_inline(theme: Theme) -> str:
    w, h = 148.0, 132.0
    c = SvgCanvas(w, h, theme)
    vr = 2.7
    pts: dict[str, tuple[float, float]] = {
        "a": (52.0, 20.0),
        "b": (96.0, 20.0),
        "c": (74.0, 42.0),
        "d": (74.0, 68.0),
        "e": (52.0, 90.0),
        "h": (96.0, 90.0),
        "f": (30.0, 112.0),
        "g": (74.0, 112.0),
    }
    edges = [("a", "c"), ("b", "c"), ("c", "d"), ("d", "e"), ("d", "h"), ("e", "f"), ("e", "g")]
    ec = theme.cyan if theme.is_dark else theme.fg
    for u, v in edges:
        c.graph_edge(pts[u][0], pts[u][1], pts[v][0], pts[v][1], r1=vr, r2=vr, stroke=ec, stroke_width=1.35)
    lbl_off = {
        "a": (-9.0, 0.0),
        "b": (9.0, 0.0),
        "c": (-8.5, 1.5),
        "d": (-8.5, -1.5),
        "e": (-8.5, -1.0),
        "h": (9.0, 0.0),
        "f": (-9.0, 1.0),
        "g": (9.0, 1.0),
    }
    for k, (px, py) in pts.items():
        c.circle(px, py, vr, fill=theme.node_fill, stroke=theme.gold if theme.is_dark else theme.fg, stroke_width=1.35)
        ox, oy = lbl_off[k]
        c.text(px + ox, py + oy, k, font_size=11.0, italic=True)

    return c.to_svg()


def _draw_ci_cluster(
    c: SvgCanvas,
    x: float,
    y_i: float,
    y_j: float,
    inv_i: bool,
    inv_j: bool,
) -> None:
    theme = c.theme
    comp_col = theme.cyan if theme.is_dark else theme.fg
    inv_col = theme.coral if theme.is_dark else theme.fg
    r_dot = 2.0
    c.line(x, y_i, x, y_j, stroke=comp_col, stroke_width=1.2)
    c.circle(x, y_i, r_dot, fill=theme.bg, stroke=comp_col, stroke_width=1.15)
    c.circle(x, y_j, r_dot, fill=theme.bg, stroke=comp_col, stroke_width=1.15)
    if inv_i:
        for dx in (-6.5, 6.5):
            c.circle(x + dx, y_i, r_dot, fill=theme.node_alt if theme.is_dark else theme.bg, stroke=inv_col, stroke_width=1.15)
    if inv_j:
        for dx in (-6.5, 6.5):
            c.circle(x + dx, y_j, r_dot, fill=theme.node_alt if theme.is_dark else theme.bg, stroke=inv_col, stroke_width=1.15)


def fig_p088_eq73(theme: Theme) -> str:
    w, h = 408.0, 68.0
    c = SvgCanvas(w, h, theme)
    y1, y2 = 38.0, 52.0
    wire_col = theme.muted if theme.is_dark else theme.fg

    cases = [
        (52.0, "If ", "i", "j", False, False),
        (152.0, "If ", "i", "\\bar{j}", False, True),
        (252.0, "If ", "\\bar{i}", "j", True, False),
        (352.0, "If ", "\\bar{i}", "\\bar{j}", True, True),
    ]
    for cx, pref, lhs, rhs, ii, ij in cases:
        c.text(cx - 17, 17, pref, font_size=10.2)
        c.text(cx - 4, 17, lhs, font_size=10.2, italic=True, rich=True)
        c.text(cx + 8, 17, "→", font_size=10.2)
        c.text(cx + 20, 17, rhs, font_size=10.2, italic=True, rich=True)
        c.line(cx - 24, y1, cx + 24, y1, stroke=wire_col, stroke_width=1.1)
        c.line(cx - 24, y2, cx + 24, y2, stroke=wire_col, stroke_width=1.1)
        _draw_ci_cluster(c, cx, y1, y2, ii, ij)

    return c.to_svg()


def fig_p088_inline(theme: Theme) -> str:
    w, h = 396.0, 92.0
    c = SvgCanvas(w, h, theme)
    ys = [15.0 + i * 10.2 for i in range(7)]
    wire_col = theme.muted if theme.is_dark else theme.fg
    for y in ys:
        c.line(14, y, w - 14, y, stroke=wire_col, stroke_width=1.05)

    clusters = [
        (28.0, 1, 7, False, False),
        (50.0, 1, 4, False, True),
        (76.0, 1, 2, False, True),
        (98.0, 4, 7, False, False),
        (112.0, 1, 3, False, False),
        (128.0, 2, 7, False, False),
        (146.0, 1, 5, False, False),
        (168.0, 2, 4, False, True),
        (196.0, 1, 6, False, True),
        (218.0, 4, 5, False, False),
        (232.0, 2, 3, False, False),
        (250.0, 6, 7, False, False),
        (266.0, 4, 6, False, False),
        (282.0, 5, 7, False, False),
        (298.0, 2, 6, False, False),
        (314.0, 3, 7, False, False),
        (338.0, 3, 4, False, True),
        (366.0, 2, 5, False, True),
    ]
    for cx, li, lj, ii, ij in clusters:
        _draw_ci_cluster(c, cx, ys[li - 1], ys[lj - 1], ii, ij)

    return c.to_svg()


def fig_p102_inline_1(theme: Theme) -> str:
    w, h = 176.0, 128.0
    c = SvgCanvas(w, h, theme)
    dx, dy = 38.0, 29.0
    top_x, top_y = w * 0.5, 20.0
    pw, ph = 28.0, 15.0

    pts: dict[tuple[int, int, int], tuple[float, float]] = {}
    for r in range(4):
        for col_i in range(r + 1):
            coord = (3 - r, r - col_i, col_i)
            pts[coord] = (top_x + (col_i - r * 0.5) * dx, top_y + r * dy)

    ec = theme.muted if theme.is_dark else theme.fg
    for (x, y, z), (x1, y1) in pts.items():
        for d1, d2, d3 in ((-1, 1, 0), (-1, 0, 1), (0, -1, 1)):
            nb = (x + d1, y + d2, z + d3)
            if nb in pts:
                x2, y2 = pts[nb]
                c.line(x1, y1, x2, y2, stroke=ec, stroke_width=1.2)

    for (x, y, z), (px, py) in pts.items():
        lbl = f"{x}{y}{z}"
        if (x, y, z) == (1, 1, 1):
            st = theme.gold
        elif x == 0 or y == 0 or z == 0:
            st = theme.cyan
        else:
            st = theme.cyan
        _pill(c, px, py, pw, ph, lbl, stroke=st if theme.is_dark else theme.fg, font_size=8.8, mono=True)

    return c.to_svg()


_Y_STONE_ROWS = [
    "0",
    "01",
    "010",
    "0010",
    "00010",
    "011100",
    "0100000",
    "01011110",
    "010100010",
    "0101011010",
    "00101101010",
    "000100101010",
    "0110111010100",
    "01010000101000",
    "110011111001110",
    "0000000000000010",
]


def fig_p102_inline_2(theme: Theme) -> str:
    w, h = 186.0, 156.0
    c = SvgCanvas(w, h, theme)
    step_x = 9.8
    step_y = step_x * math.sqrt(3.0) / 2.0
    top_x, top_y = w * 0.5, 15.0
    sr = 3.45

    for r, row_bits in enumerate(_Y_STONE_ROWS):
        y = top_y + r * step_y
        x0 = top_x - r * 0.5 * step_x
        for col_i, bit in enumerate(row_bits):
            x = x0 + col_i * step_x
            if bit == "1":
                bcol = theme.gold if theme.is_dark else "#0F172A"
                c.circle(x, y, sr, fill=bcol, stroke=bcol, stroke_width=0.9)
            else:
                wcol = theme.cyan if theme.is_dark else "#0F172A"
                wfill = "#131F33" if theme.is_dark else "#FFFFFF"
                c.circle(x, y, sr, fill=wfill, stroke=wcol, stroke_width=0.95)

    return c.to_svg()


def fig_8(theme: Theme) -> str:
    w, h = 296.0, 312.0
    c = SvgCanvas(w, h, theme)

    ranks: dict[str, int] = {}
    for i in range(32):
        s = f"{i:05b}"
        pref = 0
        tot = 0
        for ch in s:
            pref += int(ch)
            tot += pref
        ranks[s] = tot

    x_slot: dict[str, float] = {
        "11111": 2.0,
        "11110": 1.4,
        "11101": 1.4,
        "11100": 0.8, "11011": 2.0,
        "11010": 1.4, "10111": 3.2,
        "11001": 1.4, "10110": 2.6, "01111": 5.2,
        "11000": 0.8, "10101": 2.6, "01110": 4.6,
        "10100": 2.0, "10011": 3.2, "01101": 4.6,
        "10010": 2.6, "01100": 4.0, "01011": 5.2,
        "10001": 2.6, "01010": 4.6, "00111": 6.4,
        "10000": 2.0, "01001": 4.6, "00110": 5.8,
        "01000": 4.0, "00101": 5.8,
        "00100": 5.2, "00011": 6.4,
        "00010": 5.8,
        "00001": 5.8,
        "00000": 5.2,
    }

    pts: dict[str, tuple[float, float]] = {}
    for s, rk in ranks.items():
        px = 18.0 + x_slot[s] * 38.0
        py = 18.0 + (15 - rk) * 18.4
        pts[s] = (px, py)

    def geq(a: str, b: str) -> bool:
        sa = sb = 0
        for ca, cb in zip(a, b):
            sa += int(ca)
            sb += int(cb)
            if sa < sb:
                return False
        return True

    verts = list(pts.keys())
    ec = theme.muted if theme.is_dark else "#334155"
    for a in verts:
        for b in verts:
            if ranks[a] - ranks[b] == 1 and geq(a, b):
                c.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], stroke=ec, stroke_width=1.05)

    hw_pal = [theme.coral, theme.violet, theme.cyan, theme.mint, theme.gold, theme.gold]
    for s, (px, py) in pts.items():
        hw = s.count("1")
        st = hw_pal[hw] if theme.is_dark else theme.fg
        _pill(c, px, py, 32.0, 12.6, s, stroke=st, font_size=7.6, mono=True)

    return c.to_svg()


def _draw_and_gate(c: SvgCanvas, x: float, y_mid: float, gw: float, gh: float, stroke: str, fill: str) -> None:
    r = gh * 0.5
    body_w = gw - r
    d = (
        f"M {fmt(x)} {fmt(y_mid - r)} H {fmt(x + body_w)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + body_w)} {fmt(y_mid + r)} "
        f"H {fmt(x)} Z"
    )
    c.path(d, stroke=stroke, stroke_width=1.25, fill=fill)


def _draw_or_gate(c: SvgCanvas, x: float, y_mid: float, gw: float, gh: float, stroke: str, fill: str, is_xor: bool = False) -> None:
    r = gh * 0.5
    d = (
        f"M {fmt(x)} {fmt(y_mid - r)} "
        f"Q {fmt(x + gw * 0.55)} {fmt(y_mid - r)} {fmt(x + gw)} {fmt(y_mid)} "
        f"Q {fmt(x + gw * 0.55)} {fmt(y_mid + r)} {fmt(x)} {fmt(y_mid + r)} "
        f"Q {fmt(x + gw * 0.24)} {fmt(y_mid)} {fmt(x)} {fmt(y_mid - r)} Z"
    )
    c.path(d, stroke=stroke, stroke_width=1.25, fill=fill)
    if is_xor:
        dx = -3.8
        d2 = f"M {fmt(x + dx)} {fmt(y_mid - r)} Q {fmt(x + dx + gw * 0.24)} {fmt(y_mid)} {fmt(x + dx)} {fmt(y_mid + r)}"
        c.path(d2, stroke=stroke, stroke_width=1.2)


def fig_p111_inline_1(theme: Theme) -> str:
    w, h = 408.0, 78.0
    c = SvgCanvas(w, h, theme)
    wc = theme.fg if not theme.is_dark else theme.muted
    gf = theme.node_fill
    c_and = theme.cyan if theme.is_dark else theme.fg
    c_or = theme.mint if theme.is_dark else theme.fg
    c_xor = theme.gold if theme.is_dark else theme.fg

    y2, y1, y3 = 20.0, 39.0, 58.0
    c.text(16, y2, "2", font_size=9.5)
    c.text(16, y1, "1", font_size=9.5)
    c.text(16, y3, "3", font_size=9.5)

    c.line(24, y2, 68, y2, stroke=wc, stroke_width=1.15)
    c.line(24, y1, 46, y1, stroke=wc, stroke_width=1.15)
    c.circle(46, y1, 1.8, fill=wc, stroke="none")
    c.polyline([(46, y1), (46, 30), (68, 30)], stroke=wc, stroke_width=1.15)
    c.polyline([(46, y1), (46, 48), (63.5, 48)], stroke=wc, stroke_width=1.15)
    c.line(24, y3, 68, y3, stroke=wc, stroke_width=1.15)

    _draw_and_gate(c, 68, 25, 22, 18, c_and, gf)
    _draw_and_gate(c, 68, 53, 22, 18, c_and, gf)
    c.circle(65.5, 48, 2.3, fill=theme.bg, stroke=theme.coral if theme.is_dark else theme.fg, stroke_width=1.15)

    c.polyline([(90, 25), (104, 25), (104, 34), (118, 34)], stroke=wc, stroke_width=1.15)
    c.polyline([(90, 53), (104, 53), (104, 44), (118, 44)], stroke=wc, stroke_width=1.15)
    _draw_or_gate(c, 115, 39, 25, 20, c_or, gf, is_xor=False)
    c.line(140, 39, 158, 39, stroke=wc, stroke_width=1.15)

    c.text(186, 40, "and", font_size=10.2)

    rx = 216.0
    ry1, ry2, ry3 = 20.0, 36.0, 58.0
    c.text(rx, ry1, "1", font_size=9.5)
    c.text(rx, ry2, "2", font_size=9.5)
    c.text(rx, ry3, "3", font_size=9.5)

    c.polyline([(rx + 8, ry1), (298, ry1), (298, 27), (312, 27)], stroke=wc, stroke_width=1.15)
    c.polyline([(rx + 8, ry2), (252, ry2)], stroke=wc, stroke_width=1.15)
    c.line(rx + 8, ry3, 236, ry3, stroke=wc, stroke_width=1.15)
    c.circle(236, ry3, 1.8, fill=wc, stroke="none")
    c.polyline([(236, ry3), (236, 46), (252, 46)], stroke=wc, stroke_width=1.15)
    _draw_or_gate(c, 250, 41, 25, 20, c_xor, gf, is_xor=True)

    c.polyline([(275, 41), (298, 41), (298, 37), (312, 37)], stroke=wc, stroke_width=1.15)
    _draw_and_gate(c, 312, 32, 22, 18, c_and, gf)

    c.polyline([(334, 32), (346, 32), (346, 36), (360, 36)], stroke=wc, stroke_width=1.15)
    c.polyline([(236, ry3), (346, ry3), (346, 46), (360, 46)], stroke=wc, stroke_width=1.15)
    _draw_or_gate(c, 358, 41, 25, 20, c_xor, gf, is_xor=True)
    c.line(383, 41, 396, 41, stroke=wc, stroke_width=1.15)
    c.text(401, 44, ".", font_size=11.0)

    return c.to_svg()


def fig_p111_inline_2(theme: Theme) -> str:
    w, h = 232.0, 96.0
    c = SvgCanvas(w, h, theme)
    r = 7.8
    ec = theme.muted if theme.is_dark else theme.fg

    lx = 58.0
    c.graph_edge(lx, 20, lx - 22, 46, r1=r, r2=r, stroke=ec, stroke_width=1.2)
    c.graph_edge(lx, 20, lx + 22, 46, r1=r, r2=r, stroke=ec, stroke_width=1.2)
    c.graph_edge(lx - 22, 46, lx - 34, 72, r1=r, r2=5.5, stroke=ec, stroke_width=1.2)
    c.graph_edge(lx - 22, 46, lx - 10, 72, r1=r, r2=5.5, stroke=ec, stroke_width=1.2)
    c.graph_edge(lx + 22, 46, lx + 10, 72, r1=r, r2=5.5, stroke=ec, stroke_width=1.2)
    c.graph_edge(lx + 22, 46, lx + 34, 72, r1=r, r2=5.5, stroke=ec, stroke_width=1.2)

    _op_node(c, lx, 20, "or", r=r)
    _op_node(c, lx - 22, 46, "and", r=r)
    _op_node(c, lx + 22, 46, "lt", r=r)
    for tx, lbl in ((lx - 34, "1"), (lx - 10, "2"), (lx + 10, "1"), (lx + 34, "3")):
        c.text(tx, 75, lbl, font_size=10.5)

    c.text(122, 48, "and", font_size=10.5)

    rx = 172.0
    c.graph_edge(rx, 16, rx - 13, 39, r1=r, r2=5.5, stroke=ec, stroke_width=1.2)
    c.graph_edge(rx, 16, rx + 13, 39, r1=r, r2=r, stroke=ec, stroke_width=1.2)
    c.graph_edge(rx + 13, 39, rx, 62, r1=r, r2=5.5, stroke=ec, stroke_width=1.2)
    c.graph_edge(rx + 13, 39, rx + 26, 62, r1=r, r2=r, stroke=ec, stroke_width=1.2)
    c.graph_edge(rx + 26, 62, rx + 14, 84, r1=r, r2=5.5, stroke=ec, stroke_width=1.2)
    c.graph_edge(rx + 26, 62, rx + 38, 84, r1=r, r2=5.5, stroke=ec, stroke_width=1.2)

    _op_node(c, rx, 16, "xor", r=r)
    _op_node(c, rx + 13, 39, "and", r=r)
    _op_node(c, rx + 26, 62, "xor", r=r)
    c.text(rx - 13, 42, "3", font_size=10.5)
    c.text(rx, 65, "1", font_size=10.5)
    c.text(rx + 14, 86, "2", font_size=10.5)
    c.text(rx + 38, 86, "3", font_size=10.5)

    return c.to_svg()


def _draw_chain_diagram(
    c: SvgCanvas,
    ox: float,
    oy: float,
    title: str | None,
    ops: list[tuple[float, float, str]],
    leaves: list[tuple[float, float, str]],
    wires: list[tuple[int, str, int, float]],
    r: float = 6.2,
) -> None:
    ec = c.theme.muted if c.theme.is_dark else c.theme.fg
    if title is not None:
        rx, ry, _ = ops[0]
        c.text(ox + rx - r - 6.0, oy + ry, f"{title} =", font_size=8.8, anchor="end", italic=True, rich=True)
    for src_i, dst_kind, dst_i, cv in wires:
        x1, y1, _ = ops[src_i]
        if dst_kind == "op":
            x2, y2, _ = ops[dst_i]
            c.graph_edge(ox + x1, oy + y1, ox + x2, oy + y2, r1=r, r2=r, curve=cv, stroke=ec, stroke_width=1.05)
        else:
            x2, y2, _ = leaves[dst_i]
            c.graph_edge(ox + x1, oy + y1, ox + x2, oy + y2, r1=r, r2=4.8, curve=cv, stroke=ec, stroke_width=1.05)
    for gx, gy, op in ops:
        _op_node(c, ox + gx, oy + gy, op, r=r)
    for lx, ly, lbl in leaves:
        c.text(ox + lx, oy + ly + 1.0, lbl, font_size=8.2)


def _balanced_7(root_op: str, l_op: str, r_op: str, ll: str, lr: str, rl: str, rr: str) -> tuple[
    list[tuple[float, float, str]],
    list[tuple[float, float, str]],
    list[tuple[int, str, int, float]],
]:
    ops = [
        (0.0, 0.0, root_op),
        (-22.0, 16.0, l_op), (22.0, 16.0, r_op),
        (-33.0, 32.0, ll), (-11.0, 32.0, lr), (11.0, 32.0, rl), (33.0, 32.0, rr),
    ]
    leaves = [
        (-40.0, 48.0, "1"), (-26.0, 48.0, "2"), (-18.0, 48.0, "3"), (-4.0, 48.0, "4"),
        (4.0, 48.0, "1"), (18.0, 48.0, "2"), (26.0, 48.0, "3"), (40.0, 48.0, "4"),
    ]
    wires: list[tuple[int, str, int, float]] = [
        (0, "op", 1, 0.0), (0, "op", 2, 0.0),
        (1, "op", 3, 0.0), (1, "op", 4, 0.0),
        (2, "op", 5, 0.0), (2, "op", 6, 0.0),
        (3, "lf", 0, 0.0), (3, "lf", 1, 0.0),
        (4, "lf", 2, 0.0), (4, "lf", 3, 0.0),
        (5, "lf", 4, 0.0), (5, "lf", 5, 0.0),
        (6, "lf", 6, 0.0), (6, "lf", 7, 0.0),
    ]
    return ops, leaves, wires


def _balanced_3(root_op: str, l_op: str, r_op: str) -> tuple[
    list[tuple[float, float, str]],
    list[tuple[float, float, str]],
    list[tuple[int, str, int, float]],
]:
    ops = [(0.0, 0.0, root_op), (-15.0, 16.0, l_op), (15.0, 16.0, r_op)]
    leaves = [(-22.0, 32.0, "1"), (-8.0, 32.0, "2"), (8.0, 32.0, "3"), (22.0, 32.0, "4")]
    wires: list[tuple[int, str, int, float]] = [
        (0, "op", 1, 0.0), (0, "op", 2, 0.0),
        (1, "lf", 0, 0.0), (1, "lf", 1, 0.0),
        (2, "lf", 2, 0.0), (2, "lf", 3, 0.0),
    ]
    return ops, leaves, wires


def fig_9(theme: Theme) -> str:
    w, h = 448.0, 316.0
    c = SvgCanvas(w, h, theme)

    y_r1, y_r2, y_r3, y_r4 = 18.0, 88.0, 168.0, 242.0

    o, lf, wr = _balanced_3("and", "and", "and")
    _draw_chain_diagram(c, 82.0, y_r1, "S_4", o, lf, wr)
    o, lf, wr = _balanced_7("xor", "and", "and", "and", "or", "or", "and")
    _draw_chain_diagram(c, 218.0, y_r1, "S_3", o, lf, wr)
    o, lf, wr = _balanced_7("and", "or", "and", "and", "and", "or", "or")
    _draw_chain_diagram(c, 368.0, y_r1, "S_{3,4}", o, lf, wr)

    s2_ops = [
        (0.0, 0.0, "gt"), (-14.0, 16.0, "or"), (14.0, 16.0, "xor"),
        (-26.0, 32.0, "xor"), (0.0, 32.0, "xor"), (26.0, 32.0, "xor"),
    ]
    s2_lf = [(-33.0, 48.0, "1"), (-19.0, 48.0, "3"), (-7.0, 48.0, "1"), (7.0, 48.0, "2"), (19.0, 48.0, "3"), (33.0, 48.0, "4")]
    s2_wr: list[tuple[int, str, int, float]] = [
        (0, "op", 1, 0.0), (0, "op", 2, 0.0),
        (1, "op", 3, 0.0), (1, "op", 4, 0.0),
        (2, "op", 4, 0.0), (2, "op", 5, 0.0),
        (3, "lf", 0, 0.0), (3, "lf", 1, 0.0),
        (4, "lf", 2, 0.0), (4, "lf", 3, 0.0),
        (5, "lf", 4, 0.0), (5, "lf", 5, 0.0),
    ]
    _draw_chain_diagram(c, 64.0, y_r2, "S_2", s2_ops, s2_lf, s2_wr)

    s24_ops = [
        (0.0, 0.0, "gt"), (-16.0, 16.0, "or"), (16.0, 16.0, "xor"),
        (-25.0, 32.0, "or"), (5.0, 32.0, "xor"), (27.0, 32.0, "xor"),
    ]
    s24_lf = [(-32.0, 48.0, "1"), (-18.0, 48.0, "2"), (-7.0, 32.0, "3"), (-2.0, 48.0, "1"), (12.0, 48.0, "2"), (20.0, 48.0, "3"), (34.0, 48.0, "4")]
    s24_wr: list[tuple[int, str, int, float]] = [
        (0, "op", 1, 0.0), (0, "op", 2, 0.0),
        (1, "op", 3, 0.0), (1, "lf", 2, 0.0),
        (2, "op", 4, 0.0), (2, "op", 5, 0.0),
        (3, "lf", 0, 0.0), (3, "lf", 1, 0.0),
        (4, "lf", 3, 0.0), (4, "lf", 4, 0.0),
        (5, "lf", 5, 0.0), (5, "lf", 6, 0.0),
    ]
    _draw_chain_diagram(c, 164.0, y_r2, "S_{2,4}", s24_ops, s24_lf, s24_wr)

    def chain_s23_like(mid_op: str, r_op: str) -> tuple[
        list[tuple[float, float, str]],
        list[tuple[float, float, str]],
        list[tuple[int, str, int, float]],
    ]:
        ops_l = [
            (0.0, 0.0, "xor"), (-18.0, 15.0, mid_op), (18.0, 15.0, r_op),
            (-30.0, 30.0, "xor"), (-6.0, 30.0, "xor"), (-39.0, 45.0, "xor"),
        ]
        lf_l = [
            (-46.0, 60.0, "1"), (-32.0, 60.0, "2"), (-21.0, 45.0, "3"),
            (-13.0, 45.0, "3"), (1.0, 45.0, "4"), (11.0, 30.0, "1"), (25.0, 30.0, "2"),
        ]
        wr_l: list[tuple[int, str, int, float]] = [
            (0, "op", 1, 0.0), (0, "op", 2, 0.0),
            (1, "op", 3, 0.0), (1, "op", 4, 0.0),
            (3, "op", 5, 0.0), (3, "lf", 2, 0.0),
            (5, "lf", 0, 0.0), (5, "lf", 1, 0.0),
            (4, "lf", 3, 0.0), (4, "lf", 4, 0.0),
            (2, "lf", 5, 0.0), (2, "lf", 6, 0.0),
        ]
        return ops_l, lf_l, wr_l

    o, lf, wr = chain_s23_like("gt", "or")
    _draw_chain_diagram(c, 274.0, y_r2, "S_{2,3}", o, lf, wr)
    o, lf, wr = _balanced_7("or", "or", "and", "and", "and", "or", "or")
    _draw_chain_diagram(c, 384.0, y_r2, "S_{2,3,4}", o, lf, wr)

    o, lf, wr = _balanced_7("xor", "or", "or", "or", "and", "and", "or")
    _draw_chain_diagram(c, 74.0, y_r3, "S_1", o, lf, wr)
    o, lf, wr = _balanced_7("xor", "and", "or", "or", "or", "xor", "xor")
    _draw_chain_diagram(c, 192.0, y_r3, "S_{1,4}", o, lf, wr)
    o, lf, wr = _balanced_3("xor", "xor", "xor")
    _draw_chain_diagram(c, 294.0, y_r3, "S_{1,3}", o, lf, wr)

    s134_ops = [
        (0.0, 0.0, "or"), (-16.0, 16.0, "and"), (16.0, 16.0, "xor"),
        (-25.0, 32.0, "and"), (5.0, 32.0, "xor"), (27.0, 32.0, "xor"),
    ]
    _draw_chain_diagram(c, 388.0, y_r3, "S_{1,3,4}", s134_ops, s24_lf, s24_wr)

    o, lf, wr = chain_s23_like("or", "and")
    _draw_chain_diagram(c, 76.0, y_r4, "S_{1,2}", o, lf, wr)
    o, lf, wr = _balanced_7("xor", "or", "or", "and", "and", "xor", "xor")
    _draw_chain_diagram(c, 186.0, y_r4, "S_{1,2,4}", o, lf, wr)

    s123_ops = [
        (0.0, 0.0, "or"), (-16.0, 16.0, "or"), (16.0, 16.0, "xor"),
        (-27.0, 32.0, "xor"), (-5.0, 32.0, "xor"),
    ]
    s123_lf = [
        (-34.0, 48.0, "1"), (-20.0, 48.0, "2"), (-12.0, 48.0, "3"), (2.0, 48.0, "4"),
        (9.0, 32.0, "1"), (23.0, 32.0, "3"),
    ]
    s123_wr: list[tuple[int, str, int, float]] = [
        (0, "op", 1, 0.0), (0, "op", 2, 0.0),
        (1, "op", 3, 0.0), (1, "op", 4, 0.0),
        (3, "lf", 0, 0.0), (3, "lf", 1, 0.0),
        (4, "lf", 2, 0.0), (4, "lf", 3, 0.0),
        (2, "lf", 4, 0.0), (2, "lf", 5, 0.0),
    ]
    _draw_chain_diagram(c, 302.0, y_r4, "S_{1,2,3}", s123_ops, s123_lf, s123_wr)

    o, lf, wr = _balanced_3("or", "or", "or")
    _draw_chain_diagram(c, 404.0, y_r4, "S_{1,2,3,4}", o, lf, wr)

    return c.to_svg()


def fig_p117_inline(theme: Theme) -> str:
    w, h = 452.0, 226.0
    c = SvgCanvas(w, h, theme)
    r = 3.9

    def cat_r(l1: str, l2: str, l3: str, l4: str, target_idx: int) -> tuple[
        list[tuple[float, float, str]],
        list[tuple[float, float, str]],
        list[tuple[int, str, int, float]],
    ]:
        ops = [
            (0.0, 0.0, ""), (-8.0, 10.0, ""), (-4.0, 20.0, ""),
            (0.0, 30.0, ""), (4.0, 40.0, ""), (8.0, 50.0, ""),
        ]
        lf = [
            (-15.0, 20.0, l1), (-11.0, 30.0, l2), (-7.0, 40.0, l3),
            (-3.0, 50.0, l4), (2.0, 61.0, "1"), (14.0, 61.0, "2"),
        ]
        cv_map = {5: 16.0, 4: 14.0, 3: 12.0}
        wr: list[tuple[int, str, int, float]] = [
            (0, "op", 1, 0.0), (0, "op", target_idx, cv_map[target_idx]),
            (1, "lf", 0, 0.0), (1, "op", 2, 0.0),
            (2, "lf", 1, 0.0), (2, "op", 3, 0.0),
            (3, "lf", 2, 0.0), (3, "op", 4, 0.0),
            (4, "lf", 3, 0.0), (4, "op", 5, 0.0),
            (5, "lf", 4, 0.0), (5, "lf", 5, 0.0),
        ]
        return ops, lf, wr

    row1_specs = [
        (
            [(0, 0, ""), (-12, 11, ""), (9, 11, ""), (2, 22, ""), (-3, 33, ""), (18, 22, "")],
            [(-19, 23, "4"), (8, 33, "3"), (-9, 45, "1"), (3, 45, "2"), (12, 34, "1"), (24, 34, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 4, 0), (2, "op", 3, 0), (2, "op", 5, 0), (3, "op", 4, 0), (3, "lf", 1, 0), (4, "lf", 2, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (-9, 11, ""), (9, 11, ""), (-1, 22, ""), (17, 22, ""), (11, 33, "")],
            [(-16, 23, "3"), (-7, 34, "1"), (5, 34, "2"), (23, 34, "4"), (5, 45, "1"), (17, 45, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 3, 0), (2, "op", 3, 0), (2, "op", 4, 0), (3, "lf", 1, 0), (3, "lf", 2, 0), (4, "op", 5, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (7, 11, ""), (-2, 22, ""), (16, 22, ""), (-9, 33, ""), (10, 33, "")],
            [(3, 33, "3"), (22, 34, "4"), (-15, 45, "1"), (-3, 45, "2"), (4, 45, "1"), (16, 45, "2")],
            [(0, "op", 4, -12), (0, "op", 1, 0), (1, "op", 2, 0), (1, "op", 3, 0), (2, "op", 4, 0), (2, "lf", 0, 0), (3, "op", 5, 0), (3, "lf", 1, 0), (4, "lf", 2, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (-10, 11, ""), (10, 11, ""), (-1, 22, ""), (5, 33, ""), (19, 22, "")],
            [(-17, 23, "4"), (-8, 34, "3"), (-1, 45, "1"), (11, 45, "2"), (13, 34, "1"), (25, 34, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 3, 0), (2, "op", 3, 0), (2, "op", 5, 0), (3, "lf", 1, 0), (3, "op", 4, 0), (4, "lf", 2, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (7, 11, ""), (-1, 22, ""), (-7, 33, ""), (-13, 44, ""), (16, 22, "")],
            [(5, 34, "4"), (-1, 45, "3"), (-19, 56, "1"), (-7, 56, "2"), (10, 34, "1"), (22, 34, "2")],
            [(0, "op", 3, -13), (0, "op", 1, 0), (1, "op", 2, 0), (1, "op", 5, 0), (2, "op", 3, 0), (2, "lf", 0, 0), (3, "op", 4, 0), (3, "lf", 1, 0), (4, "lf", 2, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (7, 11, ""), (-1, 22, ""), (-7, 33, ""), (-13, 44, ""), (16, 22, "")],
            [(5, 34, "4"), (-1, 45, "3"), (-19, 56, "1"), (-7, 56, "2"), (10, 34, "1"), (22, 34, "2")],
            [(0, "op", 4, -15), (0, "op", 1, 0), (1, "op", 2, 0), (1, "op", 5, 0), (2, "op", 3, 0), (2, "lf", 0, 0), (3, "op", 4, 0), (3, "lf", 1, 0), (4, "lf", 2, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (8, 11, ""), (1, 22, ""), (-7, 33, ""), (-13, 44, ""), (11, 33, "")],
            [(15, 23, "4"), (-1, 45, "3"), (-19, 56, "1"), (-7, 56, "2"), (5, 45, "1"), (17, 45, "2")],
            [(0, "op", 4, -15), (0, "op", 1, 0), (1, "op", 2, 0), (1, "lf", 0, 0), (2, "op", 3, 0), (2, "op", 5, 0), (3, "op", 4, 0), (3, "lf", 1, 0), (4, "lf", 2, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (8, 11, ""), (0, 22, ""), (-10, 33, ""), (10, 33, ""), (4, 44, "")],
            [(15, 23, "4"), (-16, 45, "1"), (-4, 45, "2"), (16, 45, "3"), (-2, 56, "1"), (10, 56, "2")],
            [(0, "op", 3, -12), (0, "op", 1, 0), (1, "op", 2, 0), (1, "lf", 0, 0), (2, "op", 3, 0), (2, "op", 4, 0), (3, "lf", 1, 0), (3, "lf", 2, 0), (4, "op", 5, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
    ]

    row2_specs = [
        (
            [(0, 0, ""), (8, 11, ""), (1, 22, ""), (-7, 33, ""), (-13, 44, ""), (11, 33, "")],
            [(15, 23, "4"), (-1, 45, "3"), (-19, 56, "1"), (-7, 56, "2"), (5, 45, "1"), (17, 45, "2")],
            [(0, "op", 3, -12), (0, "op", 1, 0), (1, "op", 2, 0), (1, "lf", 0, 0), (2, "op", 3, 0), (2, "op", 5, 0), (3, "op", 4, 0), (3, "lf", 1, 0), (4, "lf", 2, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (-10, 11, ""), (10, 11, ""), (-4, 22, ""), (2, 33, ""), (-4, 44, "")],
            [(-16, 23, "4"), (16, 23, "2"), (-10, 34, "1"), (8, 45, "3"), (-10, 56, "1"), (2, 56, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 3, 0), (2, "op", 4, 0), (2, "lf", 1, 0), (3, "lf", 2, 0), (3, "op", 4, 0), (4, "op", 5, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (-10, 11, ""), (10, 11, ""), (-5, 22, ""), (0, 33, ""), (5, 44, "")],
            [(-16, 23, "2"), (16, 23, "4"), (-11, 34, "1"), (-6, 45, "3"), (-1, 56, "1"), (11, 56, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 3, 0), (2, "op", 5, 0), (2, "lf", 1, 0), (3, "lf", 2, 0), (3, "op", 4, 0), (4, "lf", 3, 0), (4, "op", 5, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (-10, 11, ""), (10, 11, ""), (-5, 22, ""), (1, 33, ""), (6, 44, "")],
            [(-16, 23, "2"), (16, 23, "4"), (-11, 34, "1"), (-5, 45, "3"), (0, 56, "1"), (12, 56, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 3, 0), (2, "op", 4, 0), (2, "lf", 1, 0), (3, "lf", 2, 0), (3, "op", 4, 0), (4, "lf", 3, 0), (4, "op", 5, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        (
            [(0, 0, ""), (-9, 11, ""), (9, 11, ""), (0, 22, ""), (5, 33, ""), (10, 44, "")],
            [(-15, 23, "2"), (15, 23, "4"), (-6, 34, "1"), (-1, 45, "3"), (4, 56, "1"), (16, 56, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 3, 0), (2, "op", 3, 0), (2, "lf", 1, 0), (3, "lf", 2, 0), (3, "op", 4, 0), (4, "lf", 3, 0), (4, "op", 5, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        cat_r("4", "2", "1", "3", 5),
        cat_r("4", "2", "1", "3", 4),
        cat_r("4", "2", "1", "3", 3),
        (
            [(0, 0, ""), (-10, 11, ""), (10, 11, ""), (-5, 22, ""), (5, 22, ""), (0, 33, "")],
            [(-16, 23, "1"), (16, 23, "2"), (-11, 34, "3"), (11, 34, "4"), (-6, 45, "1"), (6, 45, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 3, 0), (2, "op", 4, 0), (2, "lf", 1, 0), (3, "lf", 2, 0), (3, "op", 5, 0), (4, "op", 5, 0), (4, "lf", 3, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
    ]

    row3_specs = [
        (
            [(0, 0, ""), (-9, 11, ""), (9, 11, ""), (4, 22, ""), (-2, 33, ""), (4, 44, "")],
            [(-15, 23, "1"), (15, 23, "2"), (10, 34, "4"), (-8, 45, "3"), (-2, 56, "1"), (10, 56, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 4, 0), (2, "op", 3, 0), (2, "lf", 1, 0), (3, "op", 4, 0), (3, "lf", 2, 0), (4, "lf", 3, 0), (4, "op", 5, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        cat_r("2", "4", "1", "3", 5),
        cat_r("2", "4", "1", "3", 4),
        cat_r("2", "4", "1", "3", 3),
        (
            [(0, 0, ""), (-8, 11, ""), (8, 11, ""), (0, 22, ""), (5, 33, ""), (10, 44, "")],
            [(-14, 23, "1"), (14, 23, "2"), (-6, 34, "4"), (-1, 45, "3"), (4, 56, "1"), (16, 56, "2")],
            [(0, "op", 1, 0), (0, "op", 2, 0), (1, "lf", 0, 0), (1, "op", 3, 0), (2, "op", 3, 0), (2, "lf", 1, 0), (3, "lf", 2, 0), (3, "op", 4, 0), (4, "lf", 3, 0), (4, "op", 5, 0), (5, "lf", 4, 0), (5, "lf", 5, 0)],
        ),
        cat_r("2", "1", "4", "3", 5),
        cat_r("2", "1", "4", "3", 4),
        cat_r("2", "1", "4", "3", 3),
    ]

    for idx, (o, lf, wr) in enumerate(row1_specs):
        _draw_chain_diagram(c, 32.0 + idx * 55.0, 12.0, None, o, lf, wr, r=r)
    for idx, (o, lf, wr) in enumerate(row2_specs):
        _draw_chain_diagram(c, 30.0 + idx * 49.0, 82.0, None, o, lf, wr, r=r)
    for idx, (o, lf, wr) in enumerate(row3_specs):
        _draw_chain_diagram(c, 34.0 + idx * 55.0, 154.0, None, o, lf, wr, r=r)

    return c.to_svg()


def fig_10(theme: Theme) -> str:
    w, h = 468.0, 482.0
    c = SvgCanvas(w, h, theme)
    r = 5.6

    y1, y2, y3, y4, y5 = 22.0, 108.0, 206.0, 312.0, 398.0

    s4_ops = [
        (0, 0, "xor"), (-15, 13, "and"), (22, 13, "and"),
        (-6, 26, "or"), (38, 26, "and"),
        (-20, 39, "and"), (24, 39, "or"), (52, 39, "and"),
        (10, 52, "and"), (42, 52, "or"),
    ]
    s4_lf = [
        (-27, 26, "1"), (4, 39, "1"), (-28, 52, "2"), (33, 52, "2"), (62, 52, "5"),
        (3, 66, "3"), (17, 66, "4"), (35, 66, "3"), (49, 66, "4"),
    ]
    s4_wr: list[tuple[int, str, int, float]] = [
        (0, "op", 1, 0), (0, "op", 2, 0),
        (1, "lf", 0, 0), (1, "op", 5, 0),
        (2, "op", 3, 0), (2, "op", 4, 0),
        (3, "op", 5, 0), (3, "lf", 1, 0),
        (4, "op", 6, 0), (4, "op", 7, 0),
        (5, "lf", 2, 0), (5, "op", 8, 0),
        (6, "op", 8, 0), (6, "lf", 3, 0),
        (7, "op", 9, 0), (7, "lf", 4, 0),
        (8, "lf", 5, 0), (8, "lf", 6, 0),
        (9, "lf", 7, 0), (9, "lf", 8, 0),
    ]
    _draw_chain_diagram(c, 78.0, y1, "S_4", s4_ops, s4_lf, s4_wr, r=r)

    s45_ops = [
        (0, 0, "xor"), (20, 13, "and"),
        (-2, 26, "xor"), (40, 26, "xor"),
        (8, 39, "and"), (50, 39, "and"),
        (-2, 52, "and"), (18, 52, "or"), (40, 52, "or"), (60, 52, "and"),
    ]
    s45_lf = [
        (-18, 13, "1"), (-11, 39, "1"), (31, 39, "1"),
        (-8, 66, "2"), (4, 66, "3"), (12, 66, "4"), (24, 66, "5"),
        (34, 66, "2"), (46, 66, "3"), (54, 66, "4"), (66, 66, "5"),
    ]
    s45_wr: list[tuple[int, str, int, float]] = [
        (0, "lf", 0, 0), (0, "op", 1, 0),
        (1, "op", 2, 0), (1, "op", 3, 0),
        (2, "lf", 1, 0), (2, "op", 4, 0),
        (3, "lf", 2, 0), (3, "op", 5, 0),
        (4, "op", 6, 0), (4, "op", 7, 0),
        (5, "op", 8, 0), (5, "op", 9, 0),
        (6, "lf", 3, 0), (6, "lf", 4, 0),
        (7, "lf", 5, 0), (7, "lf", 6, 0),
        (8, "lf", 7, 0), (8, "lf", 8, 0),
        (9, "lf", 9, 0), (9, "lf", 10, 0),
    ]
    _draw_chain_diagram(c, 212.0, y1, "S_{4,5}", s45_ops, s45_lf, s45_wr, r=r)

    s3_ops = [
        (0, 0, "and"), (15, 12, "xor"),
        (-28, 25, "xor"), (-2, 25, "gt"), (32, 25, "or"),
        (-42, 38, "xor"), (-15, 38, "xor"), (8, 38, "xor"), (-23, 51, "xor"),
    ]
    s3_lf = [
        (-48, 52, "4"), (-36, 52, "5"), (-6, 51, "3"),
        (2, 52, "3"), (14, 52, "4"), (26, 39, "1"), (38, 39, "2"),
        (-29, 64, "1"), (-17, 64, "2"),
    ]
    s3_wr: list[tuple[int, str, int, float]] = [
        (0, "op", 2, 0), (0, "op", 1, 0),
        (1, "op", 3, 0), (1, "op", 4, 0),
        (2, "op", 5, 0), (2, "op", 6, 0),
        (3, "op", 6, 0), (3, "op", 7, 0),
        (4, "lf", 5, 0), (4, "lf", 6, 0),
        (5, "lf", 0, 0), (5, "lf", 1, 0),
        (6, "op", 8, 0), (6, "lf", 2, 0),
        (7, "lf", 3, 0), (7, "lf", 4, 0),
        (8, "lf", 7, 0), (8, "lf", 8, 0),
    ]
    _draw_chain_diagram(c, 376.0, y1, "S_3", s3_ops, s3_lf, s3_wr, r=r)

    _draw_chain_diagram(
        c,
        104.0,
        y2,
        "S_{3,5}",
        [
            (0, 0, "and"), (-25, 11, "or"), (26, 11, "xor"),
            (-41, 23, "and"), (-10, 23, "and"), (20, 23, "xor"),
            (-23, 35, "or"), (-1, 35, "or"), (14, 35, "xor"), (7, 47, "xor"),
        ],
        [
            (-47, 36, "1"), (-35, 36, "2"), (-29, 48, "3"), (-17, 48, "4"),
            (-9, 48, "5"), (34, 24, "5"), (28, 36, "4"), (22, 48, "3"),
            (1, 60, "1"), (13, 60, "2"),
        ],
        [
            (0, "op", 1, 0), (0, "op", 2, 0),
            (1, "op", 3, 0), (1, "op", 4, 0),
            (2, "op", 5, 0), (2, "lf", 5, 0),
            (3, "lf", 0, 0), (3, "lf", 1, 0),
            (4, "op", 6, 0), (4, "op", 7, 0),
            (5, "op", 8, 0), (5, "lf", 6, 0),
            (6, "lf", 2, 0), (6, "lf", 3, 0),
            (7, "lf", 4, 0), (7, "op", 9, 0),
            (8, "op", 9, 0), (8, "lf", 7, 0),
            (9, "lf", 8, 0), (9, "lf", 9, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        228.0,
        y2,
        "S_{3,4}",
        [
            (0, 0, "and"), (-18, 12, "or"), (18, 12, "xor"),
            (-33, 24, "or"), (2, 24, "and"), (33, 24, "or"),
            (-7, 36, "xor"), (11, 36, "xor"), (-1, 48, "xor"), (19, 48, "and"),
        ],
        [
            (-39, 37, "3"), (-27, 37, "4"), (27, 37, "1"), (39, 37, "2"),
            (-15, 49, "5"), (-7, 61, "1"), (5, 61, "2"), (13, 61, "3"), (25, 61, "4"),
        ],
        [
            (0, "op", 1, 0), (0, "op", 2, 0),
            (1, "op", 3, 0), (1, "op", 6, 0),
            (2, "op", 4, 0), (2, "op", 5, 0),
            (3, "lf", 0, 0), (3, "lf", 1, 0),
            (4, "op", 6, 0), (4, "op", 7, 0),
            (5, "lf", 2, 0), (5, "lf", 3, 0),
            (6, "lf", 4, 0), (6, "op", 8, 0),
            (7, "op", 8, 0), (7, "op", 9, 0),
            (8, "lf", 5, 0), (8, "lf", 6, 0),
            (9, "lf", 7, 0), (9, "lf", 8, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        366.0,
        y2,
        "S_{3,4,5}",
        [
            (0, 0, "xor"), (-22, 12, "and"),
            (-42, 24, "or"), (0, 24, "or"),
            (-32, 36, "xor"), (-10, 36, "xor"), (12, 36, "xor"),
            (0, 54, "xor"), (-10, 66, "xor"),
        ],
        [
            (-38, 49, "2"), (-16, 49, "4"), (6, 49, "5"), (10, 66, "3"),
            (-16, 79, "1"), (-4, 79, "2"),
        ],
        [
            (0, "op", 1, 0), (0, "op", 7, 36.0),
            (1, "op", 2, 0), (1, "op", 3, 0),
            (2, "op", 8, -22.0), (2, "op", 4, 0),
            (3, "op", 5, 0), (3, "op", 6, 0),
            (4, "lf", 0, 0), (4, "op", 7, -6.0),
            (5, "lf", 1, 0), (5, "op", 7, 0),
            (6, "lf", 2, 0), (6, "op", 7, 6.0),
            (7, "op", 8, 0), (7, "lf", 3, 0),
            (8, "lf", 4, 0), (8, "lf", 5, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        86.0,
        y3,
        "S_{2,5}",
        [
            (0, 0, "xor"), (14, 12, "gt"),
            (-8, 24, "or"), (30, 24, "xor"),
            (-24, 36, "xor"), (8, 36, "xor"),
            (-36, 48, "or"), (-12, 48, "or"), (3, 48, "xor"), (-2, 60, "and"),
        ],
        [
            (24, 37, "4"), (36, 37, "5"), (14, 49, "4"),
            (-42, 61, "1"), (-30, 61, "2"), (-19, 61, "3"), (9, 61, "3"),
            (-8, 73, "1"), (4, 73, "2"),
        ],
        [
            (0, "op", 4, -15.0), (0, "op", 1, 0),
            (1, "op", 2, 0), (1, "op", 3, 0),
            (2, "op", 4, 0), (2, "op", 5, 0),
            (3, "lf", 0, 0), (3, "lf", 1, 0),
            (4, "op", 6, 0), (4, "op", 7, 0),
            (5, "op", 8, 0), (5, "lf", 2, 0),
            (6, "lf", 3, 0), (6, "lf", 4, 0),
            (7, "lf", 5, 0), (7, "op", 9, 0),
            (8, "op", 9, 0), (8, "lf", 6, 0),
            (9, "lf", 7, 0), (9, "lf", 8, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        196.0,
        y3,
        "S_{2,4}",
        [
            (0, 0, "xor"), (-22, 13, "xor"), (24, 13, "gt"),
            (-32, 26, "xor"), (-12, 26, "xor"), (14, 26, "or"),
            (4, 39, "or"), (24, 39, "or"),
        ],
        [
            (-38, 39, "1"), (-26, 39, "2"), (-18, 39, "3"), (-6, 39, "4"),
            (33, 26, "5"), (-2, 52, "1"), (10, 52, "2"), (18, 52, "3"), (30, 52, "4"),
        ],
        [
            (0, "op", 1, 0), (0, "op", 2, 0),
            (1, "op", 3, 0), (1, "op", 4, 0),
            (2, "op", 5, 0), (2, "lf", 4, 0),
            (3, "lf", 0, 0), (3, "lf", 1, 0),
            (4, "lf", 2, 0), (4, "lf", 3, 0),
            (5, "op", 6, 0), (5, "op", 7, 0),
            (6, "lf", 5, 0), (6, "lf", 6, 0),
            (7, "lf", 7, 0), (7, "lf", 8, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        294.0,
        y3,
        "S_{2,4,5}",
        [
            (0, 0, "xor"), (12, 13, "gt"),
            (-4, 26, "or"), (26, 26, "xor"),
            (-20, 39, "or"), (14, 39, "xor"), (36, 39, "xor"),
            (-30, 52, "xor"), (-10, 52, "xor"),
        ],
        [
            (-11, 13, "1"), (8, 52, "2"), (20, 52, "3"), (30, 52, "4"), (42, 52, "5"),
            (-36, 65, "1"), (-24, 65, "2"), (-16, 65, "3"), (-4, 65, "4"),
        ],
        [
            (0, "lf", 0, 0), (0, "op", 1, 0),
            (1, "op", 2, 0), (1, "op", 3, 0),
            (2, "op", 4, 0), (2, "op", 5, 0),
            (3, "op", 5, 0), (3, "op", 6, 0),
            (4, "op", 7, 0), (4, "op", 8, 0),
            (5, "lf", 1, 0), (5, "lf", 2, 0),
            (6, "lf", 3, 0), (6, "lf", 4, 0),
            (7, "lf", 5, 0), (7, "lf", 6, 0),
            (8, "lf", 7, 0), (8, "lf", 8, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        396.0,
        y3,
        "S_{2,3,5}",
        [
            (0, 0, "xor"), (-16, 12, "gt"),
            (-30, 24, "xor"), (-2, 24, "xor"),
            (-22, 36, "xor"), (-14, 48, "gt"), (-6, 60, "gt"),
            (2, 72, "or"), (-8, 84, "xor"), (12, 84, "xor"),
        ],
        [
            (-8, 37, "2"), (4, 37, "3"),
            (-29, 49, "2"), (-21, 61, "4"), (-13, 73, "2"),
            (-14, 97, "1"), (-2, 97, "5"), (6, 97, "4"), (18, 97, "5"),
        ],
        [
            (0, "op", 1, 0), (0, "op", 7, 28.0),
            (1, "op", 2, 0), (1, "op", 3, 0),
            (2, "op", 8, -22.0), (2, "op", 4, 0),
            (3, "lf", 0, 0), (3, "lf", 1, 0),
            (4, "lf", 2, 0), (4, "op", 5, 0),
            (5, "lf", 3, 0), (5, "op", 6, 0),
            (6, "lf", 4, 0), (6, "op", 7, 0),
            (7, "op", 8, 0), (7, "op", 9, 0),
            (8, "lf", 5, 0), (8, "lf", 6, 0),
            (9, "lf", 7, 0), (9, "lf", 8, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        88.0,
        y4,
        "S_{2,3}",
        [
            (0, 0, "xor"), (-20, 13, "or"), (20, 13, "gt"),
            (-32, 26, "xor"), (3, 26, "xor"), (35, 26, "xor"),
            (-8, 39, "xor"), (14, 39, "xor"),
        ],
        [
            (-38, 39, "2"), (-26, 39, "3"), (29, 39, "4"), (41, 39, "5"),
            (-14, 52, "1"), (-2, 52, "2"), (8, 52, "3"), (20, 52, "4"),
        ],
        [
            (0, "op", 1, 0), (0, "op", 2, 0),
            (1, "op", 3, 0), (1, "op", 6, 0),
            (2, "op", 4, 0), (2, "op", 5, 0),
            (3, "lf", 0, 0), (3, "lf", 1, 0),
            (4, "op", 6, 0), (4, "op", 7, 0),
            (5, "lf", 2, 0), (5, "lf", 3, 0),
            (6, "lf", 4, 0), (6, "lf", 5, 0),
            (7, "lf", 6, 0), (7, "lf", 7, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        208.0,
        y4,
        "S_{2,3,4}",
        [
            (0, 0, "xor"), (18, 13, "and"),
            (-4, 26, "or"), (40, 26, "or"),
            (-14, 39, "xor"), (6, 39, "and"), (30, 39, "and"), (50, 39, "xor"),
            (-8, 52, "or"), (44, 52, "or"),
        ],
        [
            (-14, 13, "1"), (-22, 52, "1"), (0, 52, "4"), (12, 52, "5"),
            (24, 52, "2"), (36, 52, "3"), (58, 52, "1"),
            (-14, 65, "2"), (-2, 65, "3"), (38, 65, "4"), (50, 65, "5"),
        ],
        [
            (0, "lf", 0, 0), (0, "op", 1, 0),
            (1, "op", 2, 0), (1, "op", 3, 0),
            (2, "op", 4, 0), (2, "op", 5, 0),
            (3, "op", 6, 0), (3, "op", 7, 0),
            (4, "lf", 1, 0), (4, "op", 8, 0),
            (5, "lf", 2, 0), (5, "lf", 3, 0),
            (6, "lf", 4, 0), (6, "lf", 5, 0),
            (7, "op", 9, 0), (7, "lf", 6, 0),
            (8, "lf", 7, 0), (8, "lf", 8, 0),
            (9, "lf", 9, 0), (9, "lf", 10, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        344.0,
        y4,
        "S_{1,5}",
        [
            (0, 0, "and"), (-22, 13, "xor"), (22, 13, "xor"),
            (-12, 26, "xor"), (32, 26, "or"),
            (-22, 39, "or"), (-2, 39, "or"), (22, 39, "xor"), (42, 39, "xor"),
        ],
        [
            (-31, 26, "1"), (13, 26, "1"),
            (-28, 52, "2"), (-16, 52, "3"), (-8, 52, "4"), (4, 52, "5"),
            (16, 52, "2"), (28, 52, "3"), (36, 52, "4"), (48, 52, "5"),
        ],
        [
            (0, "op", 1, 0), (0, "op", 2, 0),
            (1, "lf", 0, 0), (1, "op", 3, 0),
            (2, "lf", 1, 0), (2, "op", 4, 0),
            (3, "op", 5, 0), (3, "op", 6, 0),
            (4, "op", 7, 0), (4, "op", 8, 0),
            (5, "lf", 2, 0), (5, "lf", 3, 0),
            (6, "lf", 4, 0), (6, "lf", 5, 0),
            (7, "lf", 6, 0), (7, "lf", 7, 0),
            (8, "lf", 8, 0), (8, "lf", 9, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        88.0,
        y5,
        "S_{1,4}",
        [
            (0, 0, "xor"), (16, 13, "and"),
            (-4, 26, "or"), (34, 26, "or"),
            (-22, 39, "xor"), (12, 39, "xor"), (46, 39, "xor"),
            (2, 52, "xor"), (22, 52, "xor"),
        ],
        [
            (-28, 52, "1"), (-16, 52, "5"), (40, 52, "2"), (52, 52, "3"),
            (-4, 65, "1"), (8, 65, "2"), (16, 65, "3"), (28, 65, "4"),
        ],
        [
            (0, "op", 4, -14.0), (0, "op", 1, 0),
            (1, "op", 2, 0), (1, "op", 3, 0),
            (2, "op", 4, 0), (2, "op", 5, 0),
            (3, "op", 8, -8.0), (3, "op", 6, 0),
            (4, "lf", 0, 0), (4, "lf", 1, 0),
            (5, "op", 7, 0), (5, "op", 8, 0),
            (6, "lf", 2, 0), (6, "lf", 3, 0),
            (7, "lf", 4, 0), (7, "lf", 5, 0),
            (8, "lf", 6, 0), (8, "lf", 7, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        244.0,
        y5,
        "S_{1,3,4}",
        [
            (0, 0, "xor"), (-26, 12, "gt"), (30, 12, "xor"),
            (-44, 24, "and"), (-10, 24, "lt"), (22, 24, "or"),
            (-54, 36, "or"), (-34, 36, "or"), (-2, 36, "xor"),
            (-2, 48, "xor"), (22, 48, "xor"),
        ],
        [
            (40, 24, "1"), (-19, 36, "1"),
            (-60, 49, "2"), (-48, 49, "3"), (-40, 49, "4"), (-28, 49, "5"),
            (-8, 61, "2"), (4, 61, "3"), (16, 61, "4"), (28, 61, "5"),
        ],
        [
            (0, "op", 1, 0), (0, "op", 2, 0),
            (1, "op", 3, 0), (1, "op", 4, 0),
            (2, "op", 5, 0), (2, "lf", 0, 0),
            (3, "op", 6, 0), (3, "op", 7, 0),
            (4, "lf", 1, 0), (4, "op", 8, 0),
            (5, "op", 9, 0), (5, "op", 10, 0),
            (6, "lf", 2, 0), (6, "lf", 3, 0),
            (7, "lf", 4, 0), (7, "lf", 5, 0),
            (8, "op", 9, 0), (8, "op", 10, 0),
            (9, "lf", 6, 0), (9, "lf", 7, 0),
            (10, "lf", 8, 0), (10, "lf", 9, 0),
        ],
        r=r,
    )

    _draw_chain_diagram(
        c,
        382.0,
        y5,
        "S_{1,2,5}",
        [
            (0, 0, "xor"), (-24, 13, "and"), (26, 13, "xor"),
            (-36, 26, "xor"), (-12, 26, "xor"), (16, 26, "or"), (38, 26, "or"),
            (-28, 39, "xor"), (-4, 39, "xor"),
        ],
        [
            (-44, 39, "1"), (-20, 39, "1"),
            (10, 39, "2"), (22, 39, "3"), (32, 39, "4"), (44, 39, "5"),
            (-34, 52, "2"), (-22, 52, "3"), (-10, 52, "4"), (2, 52, "5"),
        ],
        [
            (0, "op", 1, 0), (0, "op", 2, 0),
            (1, "op", 3, 0), (1, "op", 4, 0),
            (2, "op", 5, 0), (2, "op", 6, 0),
            (3, "lf", 0, 0), (3, "op", 7, 0),
            (4, "lf", 1, 0), (4, "op", 8, 0),
            (5, "lf", 2, 0), (5, "lf", 3, 0),
            (6, "lf", 4, 0), (6, "lf", 5, 0),
            (7, "lf", 6, 0), (7, "lf", 7, 0),
            (8, "lf", 8, 0), (8, "lf", 9, 0),
        ],
        r=r,
    )

    return c.to_svg()


def fig_p126_inline_1(theme: Theme) -> str:
    w, h = 112.0, 126.0
    c = SvgCanvas(w, h, theme)
    cx, cy = w * 0.5, h * 0.5
    slant = 0.13

    def sh(x: float, y: float) -> tuple[float, float]:
        return (cx + x - (y - 0.0) * slant, cy + y)

    seg_fill = "#192942" if theme.is_dark else "#E2E8F0"
    seg_stroke = theme.cyan if theme.is_dark else theme.fg
    lbl_col = theme.gold if theme.is_dark else theme.fg

    def h_seg(yc: float, lbl: str) -> None:
        hw, ht = 21.5, 6.2
        pts = [
            sh(-hw + ht, yc - ht), sh(hw - ht, yc - ht), sh(hw, yc),
            sh(hw - ht, yc + ht), sh(-hw + ht, yc + ht), sh(-hw, yc),
        ]
        c.polyline(pts, fill=seg_fill, stroke=seg_stroke, stroke_width=1.15, closed=True)
        lx, ly = sh(0.0, yc)
        c.text(lx, ly, lbl, font_size=10.5, fill=lbl_col, italic=True)

    def v_seg(xc: float, y_top: float, y_bot: float, lbl: str) -> None:
        ht = 6.2
        ym = 0.5 * (y_top + y_bot)
        pts = [
            sh(xc, y_top), sh(xc + ht, y_top + ht), sh(xc + ht, y_bot - ht),
            sh(xc, y_bot), sh(xc - ht, y_bot - ht), sh(xc - ht, y_top + ht),
        ]
        c.polyline(pts, fill=seg_fill, stroke=seg_stroke, stroke_width=1.15, closed=True)
        lx, ly = sh(xc, ym)
        c.text(lx, ly, lbl, font_size=10.5, fill=lbl_col, italic=True)

    v_seg(-22.5, -45.5, -1.0, "f")
    v_seg(22.5, -45.5, -1.0, "b")
    v_seg(-22.5, 1.0, 45.5, "e")
    v_seg(22.5, 1.0, 45.5, "c")
    h_seg(-46.5, "a")
    h_seg(0.0, "g")
    h_seg(46.5, "d")

    return c.to_svg()


BUILDERS_P1: dict[str, Callable[[Theme], str]] = {
    "fig_frontispiece": fig_frontispiece,
    "fig_1": fig_1,
    "fig_2": fig_2,
    "fig_p028_inline": fig_p028_inline,
    "fig_p031_inline": fig_p031_inline,
    "fig_p032_inline": fig_p032_inline,
    "fig_3": fig_3,
    "fig_4": fig_4,
    "fig_5": fig_5,
    "fig_p041_inline": fig_p041_inline,
    "fig_p042_inline": fig_p042_inline,
    "fig_p047_inline": fig_p047_inline,
    "fig_p048_inline_1": fig_p048_inline_1,
    "fig_p048_inline_2": fig_p048_inline_2,
    "fig_p059_inline_1": fig_p059_inline_1,
    "fig_p059_inline_2": fig_p059_inline_2,
    "fig_6": fig_6,
    "fig_7": fig_7,
    "fig_p081_inline": fig_p081_inline,
    "fig_p088_eq73": fig_p088_eq73,
    "fig_p088_inline": fig_p088_inline,
    "fig_p102_inline_1": fig_p102_inline_1,
    "fig_p102_inline_2": fig_p102_inline_2,
    "fig_8": fig_8,
    "fig_p111_inline_1": fig_p111_inline_1,
    "fig_p111_inline_2": fig_p111_inline_2,
    "fig_9": fig_9,
    "fig_p117_inline": fig_p117_inline,
    "fig_10": fig_10,
    "fig_p126_inline_1": fig_p126_inline_1,
}

BUILDERS: dict[str, Callable[[Theme], str]] = BUILDERS_P1


def render_part(out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for fig_id, fn in BUILDERS_P1.items():
        m, c, p = emit_dual_figure(fig_id, fn, out_dir)
        paths.extend((m, c, p))
    return paths


__all__ = ["BUILDERS", "BUILDERS_P1", "render_part", "rich_label"]
