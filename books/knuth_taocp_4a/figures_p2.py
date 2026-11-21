from __future__ import annotations

import cmath
import math
from collections.abc import Callable
from pathlib import Path

from .figures_common import SvgCanvas, Theme, emit_dual_figure, fmt

FIG15_A_SHAPE = (58, 57)
FIG15_A_RLE = [
    "26:4", "26:4", "26:5", "25:6", "25:6", "25:7", "24:8", "24:9", "24:9", "23:10",
    "23:11", "23:11", "22:3,27:7", "22:3,27:8", "22:3,28:7", "21:3,28:7", "21:3,28:8",
    "20:4,28:8", "20:3,29:7", "20:3,29:8", "19:4,29:8", "19:3,30:7", "19:3,30:8",
    "18:4,30:8", "18:3,31:7", "18:3,31:8", "17:3,31:8", "17:3,32:8", "17:3,32:8",
    "16:3,33:7", "16:3,33:8", "16:3,33:8", "15:3,34:7", "15:3,34:8", "15:3,34:8",
    "14:3,35:7", "14:3,35:8", "13:30", "13:30", "13:31", "12:4,36:8", "12:3,37:7",
    "12:3,37:8", "11:4,37:8", "11:3,38:7", "11:3,38:8", "10:3,38:8", "10:3,39:8",
    "10:3,39:8", "9:3,40:7", "9:3,40:8", "8:4,40:8", "7:6,40:8", "6:8,40:9",
    "3:13,38:13", "0:18,34:23", "0:18,34:23", "0:18,34:23",
]

FIG16_SHAPE = (84, 83)
FIG16_KANJI_RLE = [
    "19:1", "18:4", "17:8", "17:8", "17:10", "16:11", "16:6,41:2", "15:6,41:4,80:2",
    "15:6,41:5,79:4", "14:6,41:42", "14:5,41:42", "13:5,41:42", "13:5,41:6,60:5,78:5",
    "12:5,31:2,41:6,60:5,78:5", "4:2,12:4,30:4,41:6,60:5,78:5", "4:4,11:5,29:7,41:6,60:5,78:5",
    "4:6,11:4,29:8,41:6,60:5,78:5", "5:9,28:10,41:6,60:5,78:5", "6:7,27:11,41:6,60:5,78:5",
    "7:7,27:6,41:6,60:5,78:5", "8:7,26:7,41:6,60:5,78:5", "9:7,26:6,41:6,60:5,78:5",
    "10:7,24:7,41:6,60:5,78:5", "11:7,24:6,41:6,60:5,78:5", "11:7,23:6,41:6,60:5,78:5",
    "12:6,23:5,41:6,60:5,78:5", "12:6,22:5,41:6,60:5,78:5", "13:5,21:6,41:6,60:5,78:5",
    "14:3,21:5,41:6,60:5,78:5", "20:5,41:6,60:5,78:5", "20:4,41:6,60:5,78:5",
    "18:6,27:3,41:6,60:5,78:5", "18:5,27:3,41:6,60:5,78:5", "17:5,28:3,41:6,60:5,78:5",
    "17:4,28:4,41:6,60:5,78:5", "16:4,29:4,41:6,60:5,78:5", "15:5,29:5,41:6,60:5,78:5",
    "15:4,30:5,41:6,60:5,78:5", "14:4,30:5,41:6,60:5,78:5", "13:4,23:13,41:6,60:5,78:5",
    "3:33,41:42", "2:35,41:42", "2:27,31:6,41:42", "3:22,32:6,41:6,60:5,78:5",
    "3:21,32:7,41:6,60:5,78:5", "3:5,18:6,32:7,41:6,60:5,78:5", "4:4,18:6,32:7,41:6,60:5,78:5",
    "4:3,18:6,33:5,41:6,60:5,78:5", "18:6,33:5,41:6,60:5,78:5", "18:6,33:4,41:6,60:5,78:5",
    "18:6,34:3,41:6,60:5,78:5", "9:1,18:6,27:2,41:6,60:5,78:5", "8:5,18:6,27:3,41:6,60:5,78:5",
    "8:7,18:6,27:4,41:6,60:5,78:5", "8:8,18:6,28:3,41:6,60:5,78:5", "8:9,18:6,28:4,41:6,60:5,78:5",
    "8:8,18:6,29:4,41:6,60:5,78:5", "8:6,18:6,29:5,41:6,60:5,78:5", "7:6,18:6,30:4,41:6,60:5,78:5",
    "7:6,18:6,30:5,41:6,60:5,78:5", "7:6,18:6,30:5,41:6,60:5,78:5", "7:5,18:6,30:6,41:6,60:5,78:5",
    "7:5,18:6,31:5,41:6,60:5,78:5", "6:6,18:6,31:6,41:6,60:5,78:5", "6:5,18:6,31:6,41:6,60:5,78:5",
    "6:5,18:6,32:5,41:6,60:5,78:5", "6:5,18:6,32:6,41:6,60:5,78:5", "5:6,18:6,32:6,41:6,60:5,78:5",
    "5:5,18:6,32:6,41:6,60:5,78:5", "5:5,18:6,32:6,41:6,60:5,78:5", "5:4,18:6,32:6,41:6,60:5,78:5",
    "5:4,18:6,32:6,41:6,60:5,78:5", "4:5,18:6,33:4,41:6,60:5,78:5", "4:4,18:6,34:3,41:42",
    "3:5,18:6,41:42", "3:4,18:6,41:42", "2:4,18:6,41:6,78:5", "2:4,18:6,41:6,78:5",
    "2:4,18:6,41:6,78:5", "2:3,18:6,41:6,78:5", "1:4,18:6,41:5,78:4", "1:3,18:6,42:4",
    "0:3,18:6", "1:2,18:6",
]

FIG16_A_RLE = [
    "40:6", "40:7", "40:7", "39:8", "39:8", "38:10", "38:10", "38:10", "37:12", "37:13",
    "37:13", "36:14", "36:14", "36:15", "35:16", "35:16", "34:18", "34:18", "34:19",
    "34:5,40:13", "33:6,40:13", "33:5,41:12", "33:5,41:13", "32:6,42:12", "31:7,42:13",
    "31:6,42:13", "31:6,43:12", "31:5,43:13", "30:6,43:13", "30:5,44:12", "30:5,44:12",
    "29:6,45:12", "29:6,45:12", "28:7,45:13", "28:6,46:12", "28:6,46:12", "28:5,46:13",
    "27:6,46:13", "27:5,47:12", "26:6,47:13", "26:6,48:12", "26:6,48:13", "25:6,49:12",
    "25:6,49:12", "25:5,49:13", "25:5,49:13", "24:6,50:12", "24:5,50:12", "23:6,50:13",
    "23:6,51:12", "23:6,51:13", "22:6,52:12", "22:6,52:12", "22:5,52:13", "21:6,52:13",
    "21:44", "20:46", "20:46", "20:46", "19:48", "19:6,55:12", "19:5,55:13", "19:5,55:13",
    "18:6,56:12", "18:5,56:12", "17:6,56:13", "17:6,57:12", "17:6,57:12", "16:6,58:12",
    "16:6,58:13", "16:5,58:13", "15:6,58:13", "15:5,59:12", "15:5,59:13", "14:6,60:12",
    "14:6,60:12", "13:7,61:12", "13:7,61:12", "12:8,61:13", "11:10,61:13", "10:12,61:13",
    "6:19,58:19", "1:27,51:32", "0:29,51:32",
]

STENCILS_37 = [
    "00000111", "00001011", "00001111", "00010010", "00010011", "00010110", "00010111",
    "00011011", "00011111", "01010000", "01010010", "01010011", "01010100", "01010110",
    "01010111", "01110000", "01110010", "01110100", "01110110", "10010010", "10010011",
    "10010100", "10010110", "10010111", "10011011", "10011111", "11010000", "11010010",
    "11010011", "11010100", "11010110", "11010111", "11100000", "11110000", "11110010",
    "11110100", "11110110",
]

STENCILS_4 = ["01110011", "01110111", "11110011", "11110111"]

CHESHIRE_T0 = [
    ".......................1......",
    "....111...............11......",
    "....1.11.............1..1.....",
    "...1...11...1111111..1..1.....",
    "...1.1..1111.......111...1....",
    "...1.1..1............1.1.1....",
    "...1.1..1............1.1.1....",
    "...1.................1...1....",
    "...1..................1..1....",
    "....1...................1.1...",
    ".....1....................1...",
    ".....1..111.......111.....1...",
    ".....1.1...1.....1...1....1...",
    "11..1..111.1.....111.1.....1..",
    "..111..11111......111......1..",
    "....11.......1.1...........1..",
    "1111.........1.1..........1111",
    "...1111.....1..1......1111.1..",
    "...1.........11............1..",
    "....1...11...........111111111",
    ".....1...11111............1...",
    "......11...11111111111...1....",
    "........11..1111111....11.....",
    "..........1.........111.......",
    "...........1111111111.........",
]

USA_COORDS: dict[str, tuple[int, int]] = {
    "ND": (4, 0), "VT": (10, 0), "NH": (11, 0), "ME": (12, 0),
    "WA": (1, 1), "MT": (3, 1), "SD": (4, 1), "MN": (5, 1),
    "WI": (6, 1), "MI": (7, 1), "NY": (10, 1), "MA": (11, 1),
    "OR": (1, 2), "ID": (2, 2), "WY": (3, 2), "NE": (4, 2),
    "IA": (5, 2), "IL": (6, 2), "IN": (7, 2), "OH": (8, 2),
    "PA": (9, 2), "NJ": (10, 2), "CT": (11, 2), "RI": (12, 2),
    "CA": (0, 3), "NV": (1, 3), "UT": (2, 3), "CO": (3, 3),
    "KS": (4, 3), "MO": (5, 3), "KY": (7, 3), "WV": (8, 3),
    "MD": (9, 3), "DE": (10, 3),
    "AZ": (2, 4), "NM": (3, 4), "OK": (4, 4), "AR": (5, 4),
    "TN": (7, 4), "VA": (8, 4), "DC": (9, 4),
    "TX": (4, 5), "LA": (5, 5), "MS": (6, 5), "AL": (7, 5),
    "GA": (8, 5), "NC": (9, 5),
    "FL": (8, 6), "SC": (9, 6),
}

USA_EDGES: list[tuple[str, str]] = [
    ("ME", "NH"), ("NH", "VT"), ("NH", "MA"), ("VT", "MA"), ("VT", "NY"),
    ("MA", "RI"), ("MA", "CT"), ("MA", "NY"), ("RI", "CT"), ("CT", "NY"),
    ("NY", "NJ"), ("NY", "PA"), ("NJ", "DE"), ("NJ", "PA"),
    ("PA", "DE"), ("PA", "MD"), ("PA", "WV"), ("PA", "OH"),
    ("DE", "MD"), ("MD", "DC"), ("MD", "VA"), ("MD", "WV"),
    ("DC", "VA"), ("VA", "WV"), ("VA", "KY"), ("VA", "TN"), ("VA", "NC"),
    ("WV", "OH"), ("WV", "KY"), ("NC", "SC"), ("NC", "GA"), ("NC", "TN"),
    ("SC", "GA"), ("GA", "FL"), ("GA", "AL"), ("GA", "TN"), ("FL", "AL"),
    ("OH", "MI"), ("OH", "IN"), ("OH", "KY"), ("MI", "IN"), ("MI", "WI"),
    ("IN", "IL"), ("IN", "KY"), ("KY", "IL"), ("KY", "MO"), ("KY", "TN"),
    ("TN", "MO"), ("TN", "AR"), ("TN", "MS"), ("TN", "AL"), ("AL", "MS"),
    ("MS", "LA"), ("MS", "AR"), ("WI", "IL"), ("WI", "IA"), ("WI", "MN"),
    ("IL", "IA"), ("IL", "MO"), ("MN", "IA"), ("MN", "SD"), ("MN", "ND"),
    ("IA", "MO"), ("IA", "NE"), ("IA", "SD"),
    ("MO", "AR"), ("MO", "OK"), ("MO", "KS"), ("MO", "NE"),
    ("AR", "LA"), ("AR", "TX"), ("AR", "OK"), ("LA", "TX"),
    ("ND", "SD"), ("ND", "MT"), ("SD", "NE"), ("SD", "WY"), ("SD", "MT"),
    ("NE", "KS"), ("NE", "CO"), ("NE", "WY"), ("KS", "OK"), ("KS", "CO"),
    ("OK", "TX"), ("OK", "NM"), ("OK", "CO"), ("TX", "NM"),
    ("MT", "WY"), ("MT", "ID"), ("WY", "CO"), ("WY", "UT"), ("WY", "ID"),
    ("CO", "NM"), ("CO", "UT"), ("NM", "AZ"),
    ("ID", "UT"), ("ID", "NV"), ("ID", "OR"), ("ID", "WA"),
    ("UT", "AZ"), ("UT", "NV"), ("AZ", "NV"), ("AZ", "CA"),
    ("NV", "OR"), ("NV", "CA"), ("WA", "OR"), ("OR", "CA"),
]


def _decode_rle(shape: tuple[int, int], rows_rle: list[str]) -> list[list[int]]:
    nr, nc = shape
    mat = [[0] * nc for _ in range(nr)]
    for r, spec in enumerate(rows_rle):
        if not spec:
            continue
        for item in spec.split(","):
            s_str, ln_str = item.split(":")
            s, ln = int(s_str), int(ln_str)
            for c in range(s, min(nc, s + ln)):
                mat[r][c] = 1
    return mat


def _bitmap_runs_path(
    mat: list[list[int]],
    x0: float,
    y0: float,
    cw: float,
    ch: float,
) -> str:
    parts: list[str] = []
    nr = len(mat)
    nc = len(mat[0]) if nr else 0
    ch_s = fmt(ch)
    for r in range(nr):
        row = mat[r]
        c = 0
        ry = fmt(y0 + r * ch)
        while c < nc:
            if row[c]:
                s = c
                while c < nc and row[c]:
                    c += 1
                rx = fmt(x0 + s * cw)
                rw = fmt((c - s) * cw)
                parts.append(f"M{rx} {ry}h{rw}v{ch_s}h-{rw}z")
            else:
                c += 1
    return "".join(parts)


def _oval_node(
    cv: SvgCanvas,
    x: float,
    y: float,
    label: str,
    rx: float = 14.5,
    ry: float = 9.0,
    accent: str | None = None,
    fill: str | None = None,
    text_fill: str | None = None,
    font_size: float = 10.0,
    mono: bool = False,
    italic: bool = False,
    bold: bool = False,
) -> None:
    st = accent or (cv.theme.cyan if cv.theme.is_dark else cv.theme.fg)
    nf = fill or cv.theme.node_fill
    tf = text_fill or cv.theme.fg
    cv.ellipse(x, y, rx, ry, fill=nf, stroke=st, stroke_width=1.35)
    cv.text(x, y, label, font_size=font_size, fill=tf, mono=mono, italic=italic, bold=bold)


def _oval_edge_pt(
    cx: float,
    cy: float,
    tx: float,
    ty: float,
    rx: float,
    ry: float,
) -> tuple[float, float]:
    dx = tx - cx
    dy = ty - cy
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return cx, cy
    ang = math.atan2(dy / ry, dx / rx)
    return cx + rx * math.cos(ang), cy + ry * math.sin(ang)


def fig_p126_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(436, 52, theme)
    seg_bits = {
        "a": "1011011111100011",
        "b": "1111100111100100",
        "c": "1101111111110100",
        "d": "1011011011011110",
        "e": "1010001010111111",
        "f": "1000111111110011",
        "g": "0011111011111111",
    }
    w_seg = 12.0
    h_half = 12.0
    th = 2.4
    gap = 0.85

    def h_poly(cx: float, cy: float) -> list[tuple[float, float]]:
        x_l = cx - w_seg * 0.5 + gap
        x_r = cx + w_seg * 0.5 - gap
        ht = th * 0.5
        return [
            (x_l, cy),
            (x_l + ht, cy - ht),
            (x_r - ht, cy - ht),
            (x_r, cy),
            (x_r - ht, cy + ht),
            (x_l + ht, cy + ht),
        ]

    def v_poly(cx: float, y_top: float, y_bot: float) -> list[tuple[float, float]]:
        yt = y_top + gap
        yb = y_bot - gap
        ht = th * 0.5
        return [
            (cx, yt),
            (cx + ht, yt + ht),
            (cx + ht, yb - ht),
            (cx, yb),
            (cx - ht, yb - ht),
            (cx - ht, yt + ht),
        ]

    y_mid = 26.0
    for idx in range(16):
        bx = 26.0 + idx * 25.6
        polys = {
            "a": h_poly(bx, y_mid - h_half),
            "g": h_poly(bx, y_mid),
            "d": h_poly(bx, y_mid + h_half),
            "f": v_poly(bx - w_seg * 0.5, y_mid - h_half, y_mid),
            "b": v_poly(bx + w_seg * 0.5, y_mid - h_half, y_mid),
            "e": v_poly(bx - w_seg * 0.5, y_mid, y_mid + h_half),
            "c": v_poly(bx + w_seg * 0.5, y_mid, y_mid + h_half),
        }
        active_col = (theme.gold if idx >= 10 else theme.cyan) if theme.is_dark else theme.fg
        ghost_col = "#152033"
        for name in ("a", "b", "c", "d", "e", "f", "g"):
            on = seg_bits[name][idx] == "1"
            slanted = [(px - 0.11 * (py - y_mid), py) for px, py in polys[name]]
            if on:
                pstr = " ".join(f"{fmt(px)},{fmt(py)}" for px, py in slanted)
                glow = ' filter="url(#glow)"' if theme.is_dark else ""
                cv.add(f'<polygon points="{pstr}" fill="{active_col}"{glow}/>')
            elif theme.is_dark:
                pstr = " ".join(f"{fmt(px)},{fmt(py)}" for px, py in slanted)
                cv.add(f'<polygon points="{pstr}" fill="{ghost_col}"/>')
    return cv.to_svg()


def fig_p129_inline(theme: Theme) -> str:
    cv = SvgCanvas(412, 48, theme)
    states = [
        (set(), set()),
        ({2}, set()),
        ({2}, {9}),
        ({2, 3}, {9}),
        ({2, 3}, {1, 9}),
        ({2, 3, 5}, {1, 9}),
        ({2, 3, 5}, {1, 7, 9}),
        ({2, 3, 5, 8}, {1, 7, 9}),
    ]
    cell = 10.5
    grid_col = theme.muted if theme.is_dark else theme.fg
    x_col = theme.cyan if theme.is_dark else theme.fg
    o_col = theme.coral if theme.is_dark else theme.fg
    y0 = 8.2
    for bi, (xs, os) in enumerate(states):
        x0 = 16.0 + bi * 49.6
        for k in (1, 2):
            cv.line(x0 + k * cell, y0, x0 + k * cell, y0 + 3 * cell, stroke=grid_col, stroke_width=1.0)
            cv.line(x0, y0 + k * cell, x0 + 3 * cell, y0 + k * cell, stroke=grid_col, stroke_width=1.0)
        for pos in range(1, 10):
            r = (pos - 1) // 3
            c = (pos - 1) % 3
            cx = x0 + (c + 0.5) * cell
            cy = y0 + (r + 0.5) * cell
            if pos in xs:
                d = 2.9
                cv.line(cx - d, cy - d, cx + d, cy + d, stroke=x_col, stroke_width=1.35)
                cv.line(cx - d, cy + d, cx + d, cy - d, stroke=x_col, stroke_width=1.35)
            elif pos in os:
                cv.circle(cx, cy, 3.0, fill="none", stroke=o_col, stroke_width=1.3)
    return cv.to_svg()


def fig_11(theme: Theme) -> str:
    nr, nc = 200, 304
    cell = 1.0
    pad_x, pad_y = 16.0, 14.0
    cv = SvgCanvas(nc * cell + 2 * pad_x, nr * cell + 2 * pad_y, theme)
    mat: list[list[int]] = []
    for x in range(1, nr + 1):
        xr = (x - 350) >> 3
        row = [((((x ^ (~y)) & xr) ** 2) >> 12) & 1 for y in range(1, nc + 1)]
        mat.append(row)
    col = theme.cyan if theme.is_dark else theme.fg
    if theme.is_dark:
        cv.rect(pad_x - 1.5, pad_y - 1.5, nc * cell + 3.0, nr * cell + 3.0, fill="#0D1524", stroke=theme.panel_stroke, stroke_width=1.0)
    d = _bitmap_runs_path(mat, pad_x, pad_y, cell, cell)
    cv.add(f'<path d="{d}" fill="{col}" shape-rendering="crispEdges"/>')
    return cv.to_svg()


def fig_12(theme: Theme) -> str:
    cv = SvgCanvas(420, 262, theme)
    box_x, box_y, box_w, box_h = 66.0, 40.0, 288.0, 198.0
    dx3, dy3 = 16.0, -14.0
    edge_col = theme.panel_stroke if theme.is_dark else "#64748B"
    frame_col = theme.fg
    if theme.is_dark:
        cv.polyline(
            [(box_x, box_y), (box_x + dx3, box_y + dy3), (box_x + box_w + dx3, box_y + dy3), (box_x + box_w, box_y)],
            stroke=edge_col, stroke_width=1.1, fill="#111A2B", closed=True,
        )
        cv.polyline(
            [(box_x + box_w, box_y), (box_x + box_w + dx3, box_y + dy3), (box_x + box_w + dx3, box_y + box_h + dy3), (box_x + box_w, box_y + box_h)],
            stroke=edge_col, stroke_width=1.1, fill="#0E1625", closed=True,
        )
        cv.rect(box_x, box_y, box_w, box_h, fill="#0C1322", stroke=theme.cyan, stroke_width=1.4)
    else:
        cv.polyline(
            [(box_x, box_y), (box_x + dx3, box_y + dy3), (box_x + box_w + dx3, box_y + dy3), (box_x + box_w + dx3, box_y + box_h + dy3), (box_x + box_w, box_y + box_h)],
            stroke=frame_col, stroke_width=1.2, fill="none",
        )
        cv.line(box_x + box_w, box_y, box_x + box_w + dx3, box_y + dy3, stroke=frame_col, stroke_width=1.1)
        cv.line(box_x + dx3, box_y + dy3, box_x + dx3, box_y + box_h + dy3, stroke=edge_col, stroke_width=0.9, dashed="3,3")
        cv.line(box_x, box_y + box_h, box_x + dx3, box_y + box_h + dy3, stroke=edge_col, stroke_width=0.9, dashed="3,3")
        cv.line(box_x + dx3, box_y + box_h + dy3, box_x + box_w + dx3, box_y + box_h + dy3, stroke=edge_col, stroke_width=0.9, dashed="3,3")
        cv.rect(box_x, box_y, box_w, box_h, fill="none", stroke=frame_col, stroke_width=1.35)

    def draw_subbox(sx: float, sy: float, sw: float, sh: float, accent: str, label: str) -> None:
        sdx, sdy = 8.0, -7.0
        fill_top = "#182740" if theme.is_dark else "#F1F5F9"
        fill_side = "#142136" if theme.is_dark else "#E2E8F0"
        fill_front = "#111C30" if theme.is_dark else "#FFFFFF"
        st = accent if theme.is_dark else theme.fg
        cv.polyline([(sx, sy), (sx + sdx, sy + sdy), (sx + sw + sdx, sy + sdy), (sx + sw, sy)], stroke=st, stroke_width=1.15, fill=fill_top, closed=True)
        cv.polyline([(sx + sw, sy), (sx + sw + sdx, sy + sdy), (sx + sw + sdx, sy + sh + sdy), (sx + sw, sy + sh)], stroke=st, stroke_width=1.15, fill=fill_side, closed=True)
        cv.rect(sx, sy, sw, sh, fill=fill_front, stroke=st, stroke_width=1.3)
        cv.text(sx + sw * 0.5, sy + sh * 0.5, label, font_size=12.5, fill=st if theme.is_dark else theme.fg, italic=True)

    cb_l_x = 92.0
    cb_r_x = 304.0
    cb_w = 22.0
    cb_h = 28.0
    cb_ys = [54.0, 96.0, 138.0, 180.0]

    sub_x, sub_w = 164.0, 88.0
    sub_top_y, sub_bot_y, sub_h = 56.0, 140.0, 68.0
    top_ports = [sub_top_y + 12.0 + i * 14.5 for i in range(4)]
    bot_ports = [sub_bot_y + 12.0 + i * 14.5 for i in range(4)]

    wire_top = theme.cyan if theme.is_dark else theme.fg
    wire_bot = theme.mint if theme.is_dark else "#334155"
    io_col = theme.fg

    for i, cy in enumerate(cb_ys):
        y_hi = cy + 7.5
        y_lo = cy + 20.5
        cv.line(42.0, y_hi, cb_l_x, y_hi, stroke=io_col, stroke_width=1.3)
        cv.line(42.0, y_lo, cb_l_x, y_lo, stroke=io_col, stroke_width=1.3)
        cv.line(cb_r_x + cb_w, y_hi, 378.0, y_hi, stroke=io_col, stroke_width=1.3)
        cv.line(cb_r_x + cb_w, y_lo, 378.0, y_lo, stroke=io_col, stroke_width=1.3)
        cv.line(cb_l_x + cb_w, y_hi, sub_x, top_ports[i], stroke=wire_top, stroke_width=1.25)
        cv.line(cb_l_x + cb_w, y_lo, sub_x, bot_ports[i], stroke=wire_bot, stroke_width=1.25)
        cv.line(sub_x + sub_w, top_ports[i], cb_r_x + 4.0, y_hi, stroke=wire_top, stroke_width=1.25)
        cv.line(sub_x + sub_w, bot_ports[i], cb_r_x + 4.0, y_lo, stroke=wire_bot, stroke_width=1.25)

    for cy in cb_ys:
        draw_subbox(cb_l_x, cy, cb_w, cb_h, theme.gold, "")
        draw_subbox(cb_r_x, cy, cb_w, cb_h, theme.gold, "")

    draw_subbox(sub_x, sub_top_y, sub_w, sub_h, theme.cyan, "P(n)")
    draw_subbox(sub_x, sub_bot_y, sub_w, sub_h, theme.mint, "P(n)")

    cv.text(210.0, 225.0, "P(2n)", font_size=13.0, fill=theme.cyan if theme.is_dark else theme.fg, italic=True)

    cv.text(210.0, 14.0, "crossbar modules", font_size=11.0, fill=theme.gold if theme.is_dark else theme.fg)
    ptr_col = theme.gold if theme.is_dark else theme.muted
    cv.line(166.0, 17.0, cb_l_x + 14.0, 49.0, stroke=ptr_col, stroke_width=1.1, arrow_end=True)
    cv.line(254.0, 17.0, cb_r_x + 10.0, 49.0, stroke=ptr_col, stroke_width=1.1, arrow_end=True)

    by_top = cb_ys[0] + 5.0
    by_bot = cb_ys[-1] + 23.0
    by_mid = 0.5 * (by_top + by_bot)
    brace_l = (
        f"M 38 {fmt(by_top)} Q 32 {fmt(by_top)} 32 {fmt(by_top + 8)} "
        f"L 32 {fmt(by_mid - 7)} Q 32 {fmt(by_mid)} 26 {fmt(by_mid)} "
        f"Q 32 {fmt(by_mid)} 32 {fmt(by_mid + 7)} L 32 {fmt(by_bot - 8)} "
        f"Q 32 {fmt(by_bot)} 38 {fmt(by_bot)}"
    )
    brace_r = (
        f"M 382 {fmt(by_top)} Q 388 {fmt(by_top)} 388 {fmt(by_top + 8)} "
        f"L 388 {fmt(by_mid - 7)} Q 388 {fmt(by_mid)} 394 {fmt(by_mid)} "
        f"Q 388 {fmt(by_mid)} 388 {fmt(by_mid + 7)} L 388 {fmt(by_bot - 8)} "
        f"Q 388 {fmt(by_bot)} 382 {fmt(by_bot)}"
    )
    cv.path(brace_l, stroke=theme.muted if theme.is_dark else theme.fg, stroke_width=1.2)
    cv.path(brace_r, stroke=theme.muted if theme.is_dark else theme.fg, stroke_width=1.2)
    cv.text(15.0, by_mid, "2n inputs", font_size=11.0, fill=theme.fg, rotate=-90.0)
    cv.text(405.0, by_mid, "2n outputs", font_size=11.0, fill=theme.fg, rotate=90.0)
    return cv.to_svg()


def _draw_binary_tree_pair(
    cv: SvgCanvas,
    nodes_spec: list[tuple[int, float, float, str, str, bool]],
    edges: list[tuple[int, int]],
    eq_x: float,
    right_shift: float,
) -> None:
    pos = {nid: (x, y, dec, bits, boxed) for nid, x, y, dec, bits, boxed in nodes_spec}
    edge_col = cv.theme.muted if cv.theme.is_dark else cv.theme.fg
    for u, v in edges:
        x1, y1, _, _, _ = pos[u]
        x2, y2, _, _, _ = pos[v]
        cv.graph_edge(x1, y1, x2, y2, r1=9.5, r2=9.5, stroke=edge_col, stroke_width=1.3)
        sx1, sy1 = _oval_edge_pt(x1 + right_shift, y1, x2 + right_shift, y2, 14.8, 8.5)
        sx2, sy2 = _oval_edge_pt(x2 + right_shift, y2, x1 + right_shift, y1, 14.8, 8.5)
        cv.line(sx1, sy1, sx2, sy2, stroke=edge_col, stroke_width=1.3)
    for _, x, y, dec, bits, boxed in nodes_spec:
        if boxed:
            cv.graph_node(x, y, dec, r=9.5, font_size=9.8, rich=False, stroke=cv.theme.cyan if cv.theme.is_dark else cv.theme.fg)
            _oval_node(cv, x + right_shift, y, bits, rx=14.8, ry=8.5, font_size=8.8, mono=True, accent=cv.theme.gold if cv.theme.is_dark else cv.theme.fg)
        else:
            col = cv.theme.muted if cv.theme.is_dark else cv.theme.fg
            cv.text(x, y, dec, font_size=9.8, fill=col)
            cv.text(x + right_shift, y, bits, font_size=8.8, fill=col, mono=True)
    cv.text(eq_x, 60.0, "=", font_size=15.0, fill=cv.theme.fg)


def fig_p178_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(486, 118, theme)
    ys = [18.0, 46.0, 74.0, 102.0]
    spec = [
        (1, 114.0, ys[0], "1", "0001", True),
        (2, 66.0, ys[1], "2", "0010", True),
        (3, 166.0, ys[1], "3", "0011", True),
        (4, 40.0, ys[2], "4", "0100", True),
        (5, 96.0, ys[2], "5", "0101", True),
        (6, 144.0, ys[2], "6", "0110", True),
        (7, 190.0, ys[2], "7", "0111", True),
        (8, 22.0, ys[3], "8", "1000", True),
        (9, 58.0, ys[3], "9", "1001", True),
        (10, 92.0, ys[3], "10", "1010", True),
    ]
    edges = [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (3, 7), (4, 8), (4, 9), (5, 10)]
    _draw_binary_tree_pair(cv, spec, edges, eq_x=226.0, right_shift=254.0)
    return cv.to_svg()


def fig_p178_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(496, 118, theme)
    ys = [18.0, 46.0, 74.0, 102.0]
    spec = [
        (8, 128.0, ys[0], "8", "1000", True),
        (4, 74.0, ys[1], "4", "0100", True),
        (12, 184.0, ys[1], "12", "1100", False),
        (2, 40.0, ys[2], "2", "0010", True),
        (6, 110.0, ys[2], "6", "0110", True),
        (10, 164.0, ys[2], "10", "1010", True),
        (1, 22.0, ys[3], "1", "0001", True),
        (3, 58.0, ys[3], "3", "0011", True),
        (5, 94.0, ys[3], "5", "0101", True),
        (7, 130.0, ys[3], "7", "0111", True),
        (9, 166.0, ys[3], "9", "1001", True),
    ]
    edges = [(8, 4), (8, 12), (4, 2), (4, 6), (12, 10), (2, 1), (2, 3), (6, 5), (6, 7), (10, 9)]
    _draw_binary_tree_pair(cv, spec, edges, eq_x=228.0, right_shift=262.0)
    return cv.to_svg()


def fig_p180_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(244, 132, theme)
    ys = [20.0, 52.0, 84.0, 114.0]
    nodes = {
        "A": (68.0, ys[0], "1", theme.cyan),
        "C": (36.0, ys[1], "2", theme.cyan),
        "D": (104.0, ys[1], "4", theme.cyan),
        "F": (36.0, ys[2], "3", theme.cyan),
        "G": (84.0, ys[2], "5", theme.cyan),
        "H": (128.0, ys[2], "7", theme.cyan),
        "J": (84.0, ys[3], "6", theme.cyan),
        "B": (188.0, ys[0], "8", theme.gold),
        "E": (188.0, ys[1], "9", theme.gold),
        "I": (188.0, ys[2], "10", theme.gold),
    }
    up_edges = [
        ("C", "A"), ("D", "A"), ("F", "C"), ("G", "D"), ("H", "D"), ("J", "G"),
        ("E", "B"), ("I", "E"),
    ]
    edge_col = theme.muted if theme.is_dark else theme.fg
    for child, parent in up_edges:
        x1, y1, _, _ = nodes[child]
        x2, y2, _, _ = nodes[parent]
        cv.graph_edge(x1, y1, x2, y2, r1=9.5, r2=10.5, stroke=edge_col, stroke_width=1.3, directed=True)
    for name, (x, y, rank, acc) in nodes.items():
        st = acc if theme.is_dark else theme.fg
        cv.graph_node(x, y, name, r=9.5, font_size=10.5, italic=True, rich=False, stroke=st)
        cv.text(x + 13.5, y + 1.0, rank, font_size=9.0, fill=theme.muted if theme.is_dark else theme.fg, anchor="start")
    return cv.to_svg()


def fig_p180_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(460, 130, theme)
    ys = [20.0, 52.0, 82.0, 112.0]
    nodes = {
        "1000": (222.0, ys[0], True, "B → Λ"),
        "0100": (126.0, ys[1], True, "D → A → Λ"),
        "1100": (326.0, ys[1], False, ""),
        "0010": (62.0, ys[2], True, "C → A"),
        "0110": (192.0, ys[2], True, "J → G → D"),
        "1010": (306.0, ys[2], True, "I → E → B"),
        "0001": (30.0, ys[3], True, ""),
        "0011": (94.0, ys[3], True, "F → C"),
        "0101": (162.0, ys[3], True, ""),
        "0111": (226.0, ys[3], True, "H → D"),
        "1001": (292.0, ys[3], True, ""),
    }
    edges = [
        ("1000", "0100"), ("1000", "1100"),
        ("0100", "0010"), ("0100", "0110"), ("1100", "1010"),
        ("0010", "0001"), ("0010", "0011"), ("0110", "0101"), ("0110", "0111"), ("1010", "1001"),
    ]
    edge_col = theme.muted if theme.is_dark else theme.fg
    for u, v in edges:
        x1, y1, _, _ = nodes[u]
        x2, y2, _, _ = nodes[v]
        p1 = _oval_edge_pt(x1, y1, x2, y2, 17.5, 9.0)
        p2 = _oval_edge_pt(x2, y2, x1, y1, 17.5, 9.0)
        cv.line(p1[0], p1[1], p2[0], p2[1], stroke=edge_col, stroke_width=1.3)
    for bits, (x, y, boxed, chain) in nodes.items():
        if boxed:
            _oval_node(cv, x, y, bits, rx=17.5, ry=9.0, font_size=9.5, mono=True, accent=theme.cyan if theme.is_dark else theme.fg)
        else:
            cv.text(x, y, bits, font_size=9.5, fill=theme.muted if theme.is_dark else theme.fg, mono=True)
        if chain:
            cv.text(x + 21.5, y, chain, font_size=9.8, fill=theme.gold if theme.is_dark else theme.fg, anchor="start", italic=True)
    return cv.to_svg()


def _poincare_geodesic_through(z1: complex, z2: complex) -> tuple[complex, complex]:
    cross = z1.real * z2.imag - z1.imag * z2.real
    if abs(cross) < 1e-7:
        u = (z2 - z1) / abs(z2 - z1)
        return -u, u
    w1 = 1.0 + abs(z1) ** 2
    w2 = 1.0 + abs(z2) ** 2
    det = 2.0 * cross
    cx = (w1 * z2.imag - w2 * z1.imag) / det
    cy = (z1.real * w2 - z2.real * w1) / det
    center = complex(cx, cy)
    r = math.sqrt(max(0.0, abs(center) ** 2 - 1.0))
    d_ang = cmath.phase(center)
    alpha = math.atan2(r, 1.0)
    return cmath.rect(1.0, d_ang - alpha), cmath.rect(1.0, d_ang + alpha)


def _poincare_arc_svg(
    z1: complex,
    z2: complex,
    cx0: float,
    cy0: float,
    rad: float,
) -> str:
    p1x, p1y = cx0 + rad * z1.real, cy0 + rad * z1.imag
    p2x, p2y = cx0 + rad * z2.real, cy0 + rad * z2.imag
    cross = z1.real * z2.imag - z1.imag * z2.real
    if abs(cross) < 1e-5:
        return f"M {fmt(p1x)} {fmt(p1y)} L {fmt(p2x)} {fmt(p2y)}"
    w1 = 1.0 + abs(z1) ** 2
    w2 = 1.0 + abs(z2) ** 2
    det = 2.0 * cross
    cc = complex((w1 * z2.imag - w2 * z1.imag) / det, (z1.real * w2 - z2.real * w1) / det)
    rc = math.sqrt(max(1e-9, abs(cc) ** 2 - 1.0)) * rad
    a1 = cmath.phase(z1 - cc)
    a2 = cmath.phase(z2 - cc)
    da = (a2 - a1 + math.pi) % (2.0 * math.pi) - math.pi
    sweep = 1 if da > 0 else 0
    return f"M {fmt(p1x)} {fmt(p1y)} A {fmt(rc)} {fmt(rc)} 0 0 {sweep} {fmt(p2x)} {fmt(p2y)}"


def fig_13(theme: Theme) -> str:
    cv = SvgCanvas(424, 212, theme)
    rad = 82.0
    phi = 0.5 * (1.0 + math.sqrt(5.0))
    r_a = math.tanh(0.5 * math.acosh(phi / math.sqrt(2.0)))
    r_b = math.tanh(0.5 * math.acosh((1.0 / math.sqrt(2.0)) / math.sin(math.pi / 5.0)))
    r_c = 0.44
    u_pp = cmath.rect(1.0, -math.pi / 4.0)
    u_rr = cmath.rect(1.0, math.pi / 4.0)
    z_o = 0.0 + 0.0j
    z_p = -u_pp
    z_pp = u_pp
    z_r = -u_rr
    z_rp = u_rr
    z_a = r_a * z_p
    z_b = r_b * z_rp
    z_c = r_c * z_pp
    e1, e2 = _poincare_geodesic_through(z_a, z_b)
    if abs(e1 - z_p) < abs(e2 - z_p):
        z_q, z_qp = e1, e2
    else:
        z_q, z_qp = e2, e1
    s1, s2 = _poincare_geodesic_through(z_c, z_qp * 0.9999)
    z_s = s1 if abs(s1 - z_qp) > abs(s2 - z_qp) else s2
    t1, t2 = _poincare_geodesic_through(z_q * 0.9999, z_c)
    z_t = t1 if abs(t1 - z_q) > abs(t2 - z_q) else t2

    def mobius(z: complex, z0: complex) -> complex:
        return (z + z0) / (1.0 + z0.conjugate() * z)

    z0_shift = -0.24 + 0.16j
    views = [
        (106.0, 106.0, lambda z: mobius(z, z0_shift)),
        (318.0, 106.0, lambda z: z),
    ]
    for dcx, dcy, tf in views:
        fill_disk = "#0E1729" if theme.is_dark else "#FFFFFF"
        rim_col = theme.fg
        cv.circle(dcx, dcy, rad, fill=fill_disk, stroke=rim_col, stroke_width=1.4)
        lines = [
            (tf(z_p), tf(z_pp), theme.cyan),
            (tf(z_r), tf(z_rp), theme.cyan),
            (tf(z_q), tf(z_qp), theme.gold),
            (tf(z_s), tf(z_qp), theme.mint),
            (tf(z_q), tf(z_t), theme.coral),
        ]
        for u1, u2, acc in lines:
            col = acc if theme.is_dark else theme.fg
            cv.path(_poincare_arc_svg(u1, u2, dcx, dcy, rad), stroke=col, stroke_width=1.35)
        ideal_pts = [
            ("P", tf(z_p)), ("P'", tf(z_pp)), ("R", tf(z_r)), ("R'", tf(z_rp)),
            ("Q", tf(z_q)), ("Q'", tf(z_qp)), ("S", tf(z_s)), ("T", tf(z_t)),
        ]
        for lbl, zp in ideal_pts:
            ang = cmath.phase(zp)
            lx = dcx + (rad + 11.5) * math.cos(ang)
            ly = dcy + (rad + 11.5) * math.sin(ang)
            cv.text(lx, ly, lbl, font_size=10.5, fill=theme.fg, italic=True)
        interior = [
            ("O", tf(z_o), (-8.5, -7.5)),
            ("A", tf(z_a), (-9.5, -5.0)),
            ("B", tf(z_b), (8.5, -6.5)),
            ("C", tf(z_c), (8.5, 7.5)),
        ]
        for lbl, zp, (ox, oy) in interior:
            px = dcx + rad * zp.real
            py = dcy + rad * zp.imag
            dot_col = theme.gold if theme.is_dark else theme.fg
            cv.circle(px, py, 2.2, fill=dot_col, stroke="none")
            cv.text(px + ox, py + oy, lbl, font_size=10.0, fill=theme.fg, italic=True)
    return cv.to_svg()


def _invert_circle(z: complex, center: complex, r_sq: float) -> complex:
    diff = z - center
    denom = abs(diff) ** 2
    if denom < 1e-12:
        return z
    return center + (r_sq / denom) * diff


def _pentagrid_mirrors() -> tuple[list[tuple[complex, float]], list[complex]]:
    r_m = math.tanh(0.5 * math.acosh(math.sqrt(1.0 + 1.0 / math.sqrt(5.0))))
    d_c = 0.5 * (1.0 / r_m + r_m)
    r_c_sq = d_c * d_c - 1.0
    mirrors: list[tuple[complex, float]] = []
    for k in range(5):
        ang = math.pi * 0.5 + k * 2.0 * math.pi / 5.0
        mirrors.append((cmath.rect(d_c, ang), r_c_sq))
    r_v = math.tanh(0.5 * math.acosh(1.0 / math.tan(math.pi / 5.0)))
    verts = [cmath.rect(r_v, -math.pi * 0.5 + k * 2.0 * math.pi / 5.0) for k in range(5)]
    return mirrors, verts


def fig_14(theme: Theme) -> str:
    cv = SvgCanvas(268, 268, theme)
    dcx, dcy, rad = 134.0, 134.0, 118.0
    cv.circle(dcx, dcy, rad, fill="#0B1322" if theme.is_dark else "#FFFFFF", stroke="none")
    mirrors, base_verts = _pentagrid_mirrors()
    base_mids = [
        cmath.rect(
            math.tanh(0.5 * math.acosh(math.sqrt(1.0 + 1.0 / math.sqrt(5.0)))),
            math.pi * 0.5 + k * 2.0 * math.pi / 5.0,
        )
        for k in range(5)
    ]

    seen_centers: list[complex] = [0.0 + 0.0j]
    tiles: list[tuple[complex, list[complex], list[complex]]] = [(0.0 + 0.0j, base_verts, base_mids)]
    queue: list[tuple[complex, list[complex], list[complex], int]] = [(0.0 + 0.0j, base_verts, base_mids, 0)]

    while queue:
        zc, vs, ms, depth = queue.pop(0)
        if depth >= 4:
            continue
        for mc, mr2 in mirrors:
            nzc = _invert_circle(zc, mc, mr2)
            if abs(nzc) > 0.975:
                continue
            if any(abs(nzc - prev) < 1e-3 for prev in seen_centers):
                continue
            seen_centers.append(nzc)
            nvs = [_invert_circle(v, mc, mr2) for v in vs]
            nms = [_invert_circle(m, mc, mr2) for m in ms]
            tiles.append((nzc, nvs, nms))
            queue.append((nzc, nvs, nms, depth + 1))

    sym_col = "#1D2D47" if theme.is_dark else "#CBD5E1"
    for zc, vs, ms in tiles:
        if abs(zc) > 0.93:
            continue
        for p in vs + ms:
            cv.path(_poincare_arc_svg(zc, p, dcx, dcy, rad), stroke=sym_col, stroke_width=0.45)

    edge_seen: set[tuple[int, int, int, int]] = set()
    edge_col = theme.cyan if theme.is_dark else theme.fg
    for _, vs, _ in tiles:
        for i in range(5):
            a, b = vs[i], vs[(i + 1) % 5]
            k1 = (round(a.real * 2000), round(a.imag * 2000))
            k2 = (round(b.real * 2000), round(b.imag * 2000))
            ek = (*min(k1, k2), *max(k1, k2))
            if ek in edge_seen:
                continue
            edge_seen.add(ek)
            cv.path(_poincare_arc_svg(a, b, dcx, dcy, rad), stroke=edge_col, stroke_width=1.05)

    cv.circle(dcx, dcy, rad, fill="none", stroke=theme.gold if theme.is_dark else theme.fg, stroke_width=1.5)
    return cv.to_svg()


def fig_p184_inline(theme: Theme) -> str:
    cv = SvgCanvas(356, 356, theme)
    dcx, dcy = 178.0, 178.0
    scale = 196.0
    mirrors, v0 = _pentagrid_mirrors()
    r_m = math.tanh(0.5 * math.acosh(math.sqrt(1.0 + 1.0 / math.sqrt(5.0))))
    m0 = [
        cmath.rect(r_m, -0.3 * math.pi),
        cmath.rect(r_m, 0.1 * math.pi),
        cmath.rect(r_m, 0.5 * math.pi),
        cmath.rect(r_m, 0.9 * math.pi),
        cmath.rect(r_m, -0.7 * math.pi),
    ]
    mirror_by_edge = {
        "n": mirrors[3],
        "e": mirrors[4],
        "s": mirrors[0],
        "w": mirrors[1],
        "o": mirrors[2],
    }

    def reflect_tile(
        zc: complex,
        vs: list[complex],
        ms: list[complex],
        seq: list[tuple[complex, float]],
    ) -> tuple[complex, list[complex], list[complex]]:
        c_cur, v_cur, m_cur = zc, list(vs), list(ms)
        for mc, mr2 in seq:
            c_cur = _invert_circle(c_cur, mc, mr2)
            v_cur = [_invert_circle(p, mc, mr2) for p in v_cur]
            m_cur = [_invert_circle(p, mc, mr2) for p in m_cur]
        return c_cur, v_cur, m_cur

    mn = mirror_by_edge["n"]
    me = mirror_by_edge["e"]
    ms_m = mirror_by_edge["s"]
    mw = mirror_by_edge["w"]
    mo = mirror_by_edge["o"]

    cell_defs: list[tuple[str, list[tuple[complex, float]], list[str], int, str]] = [
        ("1000", [], ["n", "e", "s", "w", "o"], 0, "s"),
        ("10", [mn], ["n", "e", "s", "w", "o"], 2, "s"),
        ("100001", [me], ["n", "o", "e", "s", "w"], 0, "n"),
        ("100000", [ms_m], ["n", "e", "s", "w", "o"], 0, "n"),
        ("100010", [mw], ["n", "e", "s", "w", "o"], 0, "n"),
        ("101001", [mo], ["n", "o", "e", "s", "w"], 1, "o"),
        ("1010", [mo, mn], ["n", "e", "s", "w", "o"], 0, "n"),
        ("1001", [mn, me], ["n", "o", "e", "s", "w"], 0, "n"),
        ("10000001", [ms_m, me], ["n", "o", "e", "s", "w"], 0, "n"),
        ("10001001", [mw, ms_m], ["n", "o", "e", "s", "w"], 1, "o"),
        ("10100101", [mo, mw], ["n", "o", "e", "s", "w"], 0, "n"),
    ]

    built: dict[str, tuple[complex, list[complex], list[complex]]] = {}
    for code, seq, _, _, _ in cell_defs:
        built[code] = reflect_tile(0.0 + 0.0j, v0, m0, seq)

    parent_for_anchor = {
        "1000": None,
        "10": ("1000", 0),
        "100001": ("1000", 1),
        "100000": ("1000", 2),
        "100010": ("1000", 3),
        "101001": ("1000", 4),
        "1010": ("10", None),
        "1001": ("10", None),
        "10000001": ("100000", None),
        "10001001": ("100000", None),
        "10100101": ("101001", None),
    }

    sym_col = "#1D2D47" if theme.is_dark else "#E2E8F0"
    for code, _, _, _, _ in cell_defs:
        zc, vs, ms_pts = built[code]
        for p in vs + ms_pts:
            cv.path(_poincare_arc_svg(zc, p, dcx, dcy, scale), stroke=sym_col, stroke_width=0.65)

    edge_drawn: set[tuple[int, int, int, int]] = set()
    for code, _, _, _, _ in cell_defs:
        _, vs, _ = built[code]
        is_center = code == "1000"
        col = (theme.gold if is_center else theme.cyan) if theme.is_dark else theme.fg
        for i in range(5):
            a, b = vs[i], vs[(i + 1) % 5]
            k1 = (round(a.real * 2000), round(a.imag * 2000))
            k2 = (round(b.real * 2000), round(b.imag * 2000))
            ek = (*min(k1, k2), *max(k1, k2))
            if ek in edge_drawn and not is_center:
                continue
            edge_drawn.add(ek)
            cv.path(_poincare_arc_svg(a, b, dcx, dcy, scale), stroke=col, stroke_width=1.4 if is_center else 1.1)

    for code, _, cw_lbls, _, anchor_lbl in cell_defs:
        zc, _, ms_pts = built[code]
        angs = [cmath.phase(mp - zc) for mp in ms_pts]
        order = sorted(range(5), key=lambda idx: angs[idx])
        anc = parent_for_anchor[code]
        if anc is None:
            s_idx = max(range(5), key=lambda idx: ms_pts[idx].imag)
            start_pos = order.index(s_idx) - cw_lbls.index("s")
        else:
            p_code, _ = anc
            p_zc, _, _ = built[p_code]
            shared_i = min(range(5), key=lambda idx: abs(ms_pts[idx] - p_zc))
            start_pos = order.index(shared_i) - cw_lbls.index(anchor_lbl)
        for k_pos, m_idx in enumerate(order):
            lbl = cw_lbls[(k_pos - start_pos) % 5]
            mp = ms_pts[m_idx]
            lp = zc + 0.74 * (mp - zc)
            lx = dcx + scale * lp.real
            ly = dcy + scale * lp.imag
            lcol = theme.muted if theme.is_dark else "#334155"
            cv.text(lx, ly, lbl, font_size=8.2, fill=lcol, italic=True)
        cx_p = dcx + scale * zc.real
        cy_p = dcy + scale * zc.imag
        fs = 11.5 if code == "1000" else (8.0 if len(code) >= 8 else 9.2)
        tcol = (theme.gold if code == "1000" else theme.fg) if theme.is_dark else theme.fg
        cv.text(cx_p, cy_p, code, font_size=fs, fill=tcol, bold=(code == "1000"))

    return cv.to_svg()


def fig_15(theme: Theme) -> str:
    mat_a = _decode_rle(FIG15_A_SHAPE, FIG15_A_RLE)
    nr, nc = FIG15_A_SHAPE
    mat_b = [[0] * nc for _ in range(nr)]
    for r in range(nr):
        for c in range(nc):
            if mat_a[r][c]:
                interior = (
                    r > 0 and r + 1 < nr and c > 0 and c + 1 < nc
                    and mat_a[r - 1][c] == 1 and mat_a[r + 1][c] == 1
                    and mat_a[r][c - 1] == 1 and mat_a[r][c + 1] == 1
                )
                mat_b[r][c] = 0 if interior else 1
    cell = 2.15
    gw = nc * cell
    gh = nr * cell
    cv = SvgCanvas(316, 168, theme)
    col_a = theme.cyan if theme.is_dark else theme.fg
    col_b = theme.gold if theme.is_dark else theme.fg
    d_a = _bitmap_runs_path(mat_a, 22.0, 14.0, cell, cell)
    d_b = _bitmap_runs_path(mat_b, 172.0, 14.0, cell, cell)
    cv.add(f'<path d="{d_a}" fill="{col_a}" shape-rendering="crispEdges"/>')
    cv.add(f'<path d="{d_b}" fill="{col_b}" shape-rendering="crispEdges"/>')
    cv.text(22.0 + gw * 0.5, 14.0 + gh + 15.0, "(a)", font_size=11.0, fill=theme.fg)
    cv.text(172.0 + gw * 0.5, 14.0 + gh + 15.0, "(b)", font_size=11.0, fill=theme.fg)
    return cv.to_svg()


def _thin_guo_hall(mat: list[list[int]]) -> list[list[int]]:
    nr = len(mat)
    nc = len(mat[0])
    s_set = {tuple(int(ch) for ch in bits) for bits in STENCILS_37}
    cur = [row[:] for row in mat]
    unchanged = 0
    step = 1
    while unchanged < 2 and step < 120:
        nxt = [row[:] for row in cur]
        changed = False
        odd = (step % 2) == 1
        for r in range(nr):
            row_r = cur[r]
            for c in range(nc):
                if not row_r[c]:
                    continue
                nw = cur[r - 1][c - 1] if (r > 0 and c > 0) else 0
                n = cur[r - 1][c] if r > 0 else 0
                ne = cur[r - 1][c + 1] if (r > 0 and c + 1 < nc) else 0
                w = cur[r][c - 1] if c > 0 else 0
                e = cur[r][c + 1] if c + 1 < nc else 0
                sw = cur[r + 1][c - 1] if (r + 1 < nr and c > 0) else 0
                s = cur[r + 1][c] if r + 1 < nr else 0
                se = cur[r + 1][c + 1] if (r + 1 < nr and c + 1 < nc) else 0
                tup = (nw, n, ne, w, e, sw, s, se) if odd else (se, s, sw, e, w, ne, n, nw)
                if tup in s_set:
                    nxt[r][c] = 0
                    changed = True
        cur = nxt
        unchanged = 0 if changed else (unchanged + 1)
        step += 1
    return cur


def fig_16(theme: Theme) -> str:
    body_k = _decode_rle(FIG16_SHAPE, FIG16_KANJI_RLE)
    body_a = _decode_rle(FIG16_SHAPE, FIG16_A_RLE)
    skel_k = _thin_guo_hall(body_k)
    skel_a = _thin_guo_hall(body_a)
    cell = 1.9
    cv = SvgCanvas(366, 186, theme)
    body_col = "#22344E" if theme.is_dark else "#CBD5E1"
    skel_k_col = theme.gold if theme.is_dark else theme.fg
    skel_a_col = theme.cyan if theme.is_dark else theme.fg
    cv.add(f'<path d="{_bitmap_runs_path(body_k, 18.0, 13.0, cell, cell)}" fill="{body_col}" shape-rendering="crispEdges"/>')
    cv.add(f'<path d="{_bitmap_runs_path(skel_k, 18.0, 13.0, cell, cell)}" fill="{skel_k_col}" shape-rendering="crispEdges"/>')
    cv.add(f'<path d="{_bitmap_runs_path(body_a, 192.0, 13.0, cell, cell)}" fill="{body_col}" shape-rendering="crispEdges"/>')
    cv.add(f'<path d="{_bitmap_runs_path(skel_a, 192.0, 13.0, cell, cell)}" fill="{skel_a_col}" shape-rendering="crispEdges"/>')
    return cv.to_svg()


def fig_p187_block2x2(theme: Theme) -> str:
    cv = SvgCanvas(60, 48, theme)
    cell = 7.5
    x0, y0 = 15.0, 9.0
    bg_cell = theme.cell_light if theme.is_dark else "#FFFFFF"
    fg_cell = theme.cyan if theme.is_dark else theme.fg
    grid_col = theme.muted if theme.is_dark else "#64748B"
    cv.rect(x0, y0, 4 * cell, 4 * cell, fill=bg_cell, stroke=grid_col, stroke_width=0.9)
    cv.rect(x0 + cell, y0 + cell, 2 * cell, 2 * cell, fill=fg_cell, stroke="none")
    for k in range(1, 4):
        cv.line(x0 + k * cell, y0, x0 + k * cell, y0 + 4 * cell, stroke=grid_col, stroke_width=0.75)
        cv.line(x0, y0 + k * cell, x0 + 4 * cell, y0 + k * cell, stroke=grid_col, stroke_width=0.75)
    cv.rect(x0, y0, 4 * cell, 4 * cell, fill="none", stroke=grid_col, stroke_width=0.9)
    return cv.to_svg()


def _draw_stencil_row(stencils: list[str], cell: float, pitch: float, pad_x: float, pad_y: float, theme: Theme) -> str:
    w = 2.0 * pad_x + (len(stencils) - 1) * pitch + 3.0 * cell
    h = 2.0 * pad_y + 3.0 * cell
    cv = SvgCanvas(w, h, theme)
    fg_col = theme.cyan if theme.is_dark else theme.fg
    ctr_col = theme.gold if theme.is_dark else theme.fg
    grid_col = "#334868" if theme.is_dark else "#94A3B8"
    bg_col = "#101A2C" if theme.is_dark else "#FFFFFF"
    coords = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
    fill_parts: list[str] = []
    ctr_parts: list[str] = []
    grid_parts: list[str] = []
    s3 = fmt(3.0 * cell)
    cs = fmt(cell)
    for idx, bits in enumerate(stencils):
        bx = pad_x + idx * pitch
        by = pad_y
        grid_parts.append(f"M{fmt(bx)} {fmt(by)}h{s3}v{s3}h-{s3}z")
        for k in (1, 2):
            grid_parts.append(f"M{fmt(bx + k * cell)} {fmt(by)}v{s3}")
            grid_parts.append(f"M{fmt(bx)} {fmt(by + k * cell)}h{s3}")
        ctr_parts.append(f"M{fmt(bx + cell)} {fmt(by + cell)}h{cs}v{cs}h-{cs}z")
        for bit_ch, (r, c) in zip(bits, coords):
            if bit_ch == "1":
                fill_parts.append(f"M{fmt(bx + c * cell)} {fmt(by + r * cell)}h{cs}v{cs}h-{cs}z")
    cv.add(f'<path d="{"".join(x for x in grid_parts if x.endswith("z"))}" fill="{bg_col}"/>')
    cv.add(f'<path d="{"".join(fill_parts)}" fill="{fg_col}" shape-rendering="crispEdges"/>')
    cv.add(f'<path d="{"".join(ctr_parts)}" fill="{ctr_col}" shape-rendering="crispEdges"/>')
    cv.add(f'<path d="{"".join(grid_parts)}" fill="none" stroke="{grid_col}" stroke-width="0.45"/>')
    return cv.to_svg()


def fig_p187_stencils37(theme: Theme) -> str:
    return _draw_stencil_row(STENCILS_37, cell=3.0, pitch=12.0, pad_x=12.0, pad_y=10.5, theme=theme)


def fig_p187_stencils4(theme: Theme) -> str:
    return _draw_stencil_row(STENCILS_4, cell=4.2, pitch=17.5, pad_x=14.0, pad_y=10.5, theme=theme)


def _step_levialdi(mat: list[list[int]]) -> list[list[int]]:
    nr = len(mat)
    nc = len(mat[0])
    out = [[0] * nc for _ in range(nr)]
    for r in range(nr):
        for c in range(nc):
            cur = mat[r][c]
            w = mat[r][c - 1] if c > 0 else 0
            s = mat[r + 1][c] if r + 1 < nr else 0
            sw = mat[r + 1][c - 1] if (r + 1 < nr and c > 0) else 0
            out[r][c] = (cur & (w | sw | s)) | (w & s)
    return out


def fig_17(theme: Theme) -> str:
    m0 = [[1 if ch == "1" else 0 for ch in row] for row in CHESHIRE_T0]
    m1 = _step_levialdi(m0)
    m2 = _step_levialdi(m1)
    m3 = _step_levialdi(m2)
    cell = 3.9
    bw = 30.0 * cell
    bh = 25.0 * cell
    cv = SvgCanvas(414, 138, theme)
    panels = [(16.0, m0, "(a)", theme.cyan), (148.0, m1, "(b)", theme.gold), (280.0, m3, "(c)", theme.mint)]
    border_col = theme.panel_stroke if theme.is_dark else "#94A3B8"
    bg_box = "#0E1626" if theme.is_dark else "#FFFFFF"
    for px, mat, lbl, acc in panels:
        py = 13.0
        cv.rect(px, py, bw, bh, fill=bg_box, stroke=border_col, stroke_width=1.0)
        col = acc if theme.is_dark else theme.fg
        cv.add(f'<path d="{_bitmap_runs_path(mat, px, py, cell, cell)}" fill="{col}" shape-rendering="crispEdges"/>')
        cv.rect(px, py, bw, bh, fill="none", stroke=border_col, stroke_width=1.0)
        cv.text(px + bw * 0.5, py + bh + 14.5, lbl, font_size=11.0, fill=theme.fg)
    return cv.to_svg()


def fig_p192_inline(theme: Theme) -> str:
    cv = SvgCanvas(246, 232, theme)
    cw, ch = 40.0, 30.0
    gx0, gy0 = 24.0, 20.0

    def sx(xv: float) -> float:
        return gx0 + (xv - 17.0) * cw

    def sy(yv: float) -> float:
        return gy0 + (5.0 - yv) * ch

    grid_col = "#24364F" if theme.is_dark else "#CBD5E1"
    for xv in range(18, 21):
        cv.line(sx(xv), sy(5.3), sx(xv), sy(-1.3), stroke=grid_col, stroke_width=0.9)
    for yv in range(5):
        cv.line(sx(16.7), sy(yv), sx(21.3), sy(yv), stroke=grid_col, stroke_width=0.9)

    arc_pts: list[tuple[float, float]] = []
    for k in range(81):
        yv = -1.25 + k * (6.55 / 80.0)
        val = 1.0 - (yv / 10.0) ** 2
        if val > 0:
            xv = 20.0 * math.sqrt(val)
            if 16.6 <= xv <= 21.3:
                arc_pts.append((sx(xv), sy(yv)))
    cv.polyline(arc_pts, stroke=theme.gold if theme.is_dark else "#64748B", stroke_width=1.25)

    stair = [
        (sx(20), sy(-1.3)), (sx(20), sy(2)), (sx(19), sy(2)),
        (sx(19), sy(4)), (sx(18), sy(4)), (sx(18), sy(5)), (sx(17), sy(5)), (sx(17), sy(5.35)),
    ]
    cv.polyline(stair, stroke=theme.cyan if theme.is_dark else theme.fg, stroke_width=2.1)

    examined = {(20, 1), (20, 2), (20, 3), (19, 3), (19, 4), (19, 5), (18, 5)}
    for yi, y_cell in enumerate([5, 4, 3, 2, 1, 0]):
        for xi, x_cell in enumerate([18, 19, 20, 21]):
            if (x_cell, y_cell) == (18, 5):
                pass
            q = 4 * x_cell * x_cell + 16 * y_cell * y_cell - 4 * x_cell - 16 * y_cell - 1595
            cx = gx0 + (xi + 0.5) * cw
            cy = gy0 + (yi + 0.5) * ch
            txt = f"−{abs(q)}" if q < 0 else str(q)
            if theme.is_dark:
                col = theme.gold if (x_cell, y_cell) in examined else (theme.cyan if q < 0 else theme.muted)
            else:
                col = theme.fg
            cv.text(cx, cy, txt, font_size=9.5, fill=col)

    dot_x, dot_y = sx(20), sy(0)
    cv.circle(dot_x, dot_y, 2.8, fill=theme.coral if theme.is_dark else theme.fg, stroke="none")
    cv.text(sx(21.22), sy(0), "(21, 0)", font_size=9.2, fill=theme.fg, anchor="start")
    cv.circle(sx(21), sy(0), 2.3, fill=theme.fg, stroke="none")
    return cv.to_svg()


def fig_18(theme: Theme) -> str:
    cv = SvgCanvas(224, 224, theme)
    dcx, dcy, rad = 112.0, 112.0, 98.0
    light_fill = "#101B2E" if theme.is_dark else "#FFFFFF"
    dark_fill = theme.cyan if theme.is_dark else "#0F172A"
    cv.circle(dcx, dcy, rad, fill=light_fill, stroke="none")

    r0 = math.sqrt(0.5 * (1.0 + math.sqrt(2.0)) * (4.0 - math.sqrt(2.0) - math.sqrt(6.0)))
    v_base = [cmath.rect(r0, -math.pi * 0.5 + k * 2.0 * math.pi / 3.0) for k in range(3)]

    mirrors: list[tuple[complex, float]] = []
    for i in range(3):
        z1, z2 = v_base[i], v_base[(i + 1) % 3]
        cross = z1.real * z2.imag - z1.imag * z2.real
        w1 = 1.0 + abs(z1) ** 2
        w2 = 1.0 + abs(z2) ** 2
        det = 2.0 * cross
        cc = complex((w1 * z2.imag - w2 * z1.imag) / det, (z1.real * w2 - z2.real * w1) / det)
        mirrors.append((cc, abs(cc) ** 2 - 1.0))

    seen: dict[tuple[int, int], None] = {(0, 0): None}
    triangles: list[tuple[list[complex], int]] = [(v_base, 0)]
    queue: list[tuple[complex, list[complex], int, int]] = [(0.0 + 0.0j, v_base, 0, 0)]

    while queue:
        zc, vs, parity, depth = queue.pop(0)
        if depth >= 9:
            continue
        for mc, mr2 in mirrors:
            nzc = _invert_circle(zc, mc, mr2)
            if abs(nzc) > 0.985:
                continue
            key = (round(nzc.real * 1500), round(nzc.imag * 1500))
            if key in seen:
                continue
            seen[key] = None
            nvs = [_invert_circle(v, mc, mr2) for v in vs]
            span = max(abs(nvs[0] - nvs[1]), abs(nvs[1] - nvs[2]), abs(nvs[2] - nvs[0]))
            if span < 0.014:
                continue
            triangles.append((nvs, 1 - parity))
            queue.append((nzc, nvs, 1 - parity, depth + 1))

    dark_paths: list[str] = []
    edge_paths: list[str] = []
    for vs, parity in triangles:
        segs: list[str] = []
        for i in range(3):
            a, b = vs[i], vs[(i + 1) % 3]
            seg = _poincare_arc_svg(a, b, dcx, dcy, rad)
            if i == 0:
                segs.append(seg)
            else:
                idx_a = seg.find("A ")
                if idx_a != -1:
                    segs.append(seg[idx_a:])
                else:
                    idx_l = seg.find("L ")
                    segs.append(seg[idx_l:])
        poly_d = " ".join(segs) + " Z"
        if parity == 1:
            dark_paths.append(poly_d)
        elif theme.is_dark:
            edge_paths.append(poly_d)

    if theme.is_dark and edge_paths:
        cv.add(f'<path d="{" ".join(edge_paths)}" fill="none" stroke="#1E3354" stroke-width="0.35"/>')
    cv.add(f'<path d="{" ".join(dark_paths)}" fill="{dark_fill}" stroke="{dark_fill}" stroke-width="0.22"/>')
    cv.circle(dcx, dcy, rad, fill="none", stroke=theme.gold if theme.is_dark else theme.fg, stroke_width=1.45)
    return cv.to_svg()


def fig_19(theme: Theme) -> str:
    pts: list[tuple[float, float]] = [
        (220.0, 23.0), (199.0, 88.0), (194.0, 152.0), (163.0, 105.0),
        (134.0, 116.0), (105.0, 127.0), (159.0, 168.5), (221.0, 216.2),
        (221.0, 268.0), (221.0, 286.0), (209.0, 305.0), (197.0, 324.0),
        (176.1, 331.5), (161.0, 337.0), (133.0, 337.0), (117.0, 337.0),
        (101.0, 333.0), (85.0, 329.0), (68.0, 329.0), (51.0, 329.0),
        (23.0, 339.0), (42.0, 283.0), (46.0, 211.0), (95.0, 258.0),
        (120.0, 243.0), (139.0, 231.6), (86.0, 189.0), (28.0, 142.3),
        (28.0, 92.0), (28.0, 68.0), (42.0, 53.0), (60.0, 33.7),
        (79.0, 29.0), (103.0, 23.1), (124.0, 23.1), (136.0, 23.1),
        (154.0, 26.8), (172.0, 30.5), (186.0, 30.5), (196.0, 30.5),
    ]
    ox, oy = 18.0, 10.0
    spts = [(x + ox, y + oy) for x, y in pts]
    cv = SvgCanvas(276, 372, theme)

    ctrl_col = "#3B5275" if theme.is_dark else "#94A3B8"
    poly_pts = spts + [spts[0]]
    cv.polyline(poly_pts, stroke=ctrl_col, stroke_width=0.85, dashed="2.2,2.2")

    q_parts = [f"M {fmt(spts[0][0])} {fmt(spts[0][1])}"]
    for j in range(20):
        cx, cy = spts[2 * j + 1]
        ex, ey = spts[(2 * j + 2) % 40]
        q_parts.append(f"Q {fmt(cx)} {fmt(cy)} {fmt(ex)} {fmt(ey)}")
    q_parts.append("Z")
    curve_col = theme.cyan if theme.is_dark else theme.fg
    fill_s = "rgba(88,196,221,0.06)" if theme.is_dark else "none"
    cv.path(" ".join(q_parts), stroke=curve_col, stroke_width=1.75, fill=fill_s, glow=theme.is_dark)

    offsets: dict[int, tuple[float, float]] = {
        0: (8.5, 0.0), 1: (-9.0, -1.0), 2: (8.5, 1.0), 3: (0.0, -9.0),
        4: (5.5, 9.0), 5: (-8.5, 0.0), 6: (7.5, -7.0), 7: (9.0, 0.0),
        8: (9.0, 0.0), 9: (9.0, 1.0), 10: (11.5, 1.0), 11: (11.5, 1.0),
        12: (9.5, 7.5), 13: (0.0, 10.0), 14: (0.0, -9.5), 15: (0.0, 10.0),
        16: (2.0, -9.5), 17: (0.0, -9.5), 18: (0.0, 10.0), 19: (-1.0, -9.5),
        20: (-11.0, 1.0), 21: (11.5, 1.0), 22: (-11.5, -1.0), 23: (0.0, 10.0),
        24: (9.5, 7.5), 25: (11.5, 0.0), 26: (-9.5, 7.5), 27: (-11.5, 0.0),
        28: (11.5, 0.0), 29: (-11.5, 0.0), 30: (10.5, 6.0), 31: (-9.5, -6.0),
        32: (8.0, 8.5), 33: (0.0, -9.5), 34: (0.0, 9.5), 35: (0.0, -9.5),
        36: (2.0, -9.5), 37: (0.0, 9.5), 38: (0.0, -9.5), 39: (2.5, 9.5),
    }
    for idx, (px, py) in enumerate(spts):
        is_ctrl = (idx % 2) == 1
        dcol = (theme.gold if is_ctrl else theme.cyan) if theme.is_dark else theme.fg
        cv.circle(px, py, 2.2, fill=dcol, stroke="none")
        dx, dy = offsets[idx]
        tcol = (theme.gold if is_ctrl else theme.fg) if theme.is_dark else theme.fg
        cv.text(px + dx, py + dy, str(idx), font_size=8.2, fill=tcol)
    return cv.to_svg()


def fig_p199_inline(theme: Theme) -> str:
    n = 256
    cell = 0.8
    pad = 14.0
    cv = SvgCanvas(n * cell + 2 * pad, n * cell + 2 * pad, theme)
    mat = [[((x * x * y) >> 11) & 1 for y in range(1, n + 1)] for x in range(1, n + 1)]
    if theme.is_dark:
        cv.rect(pad - 1.0, pad - 1.0, n * cell + 2.0, n * cell + 2.0, fill="#0D1524", stroke=theme.panel_stroke, stroke_width=0.9)
    col = theme.cyan if theme.is_dark else theme.fg
    cv.add(f'<path d="{_bitmap_runs_path(mat, pad, pad, cell, cell)}" fill="{col}" shape-rendering="crispEdges"/>')
    return cv.to_svg()


def fig_p211_inline(theme: Theme) -> str:
    cv = SvgCanvas(344, 48, theme)
    mat_x = [
        [0, 0, 1, 1, 1, 0, 1, 0],
        [0, 1, 1, 0, 1, 0, 0, 1],
        [1, 1, 1, 1, 1, 0, 0, 0],
    ]
    mat_xd = [
        [0, 0, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 0, 0, 1],
        [1, 1, 1, 1, 1, 0, 0, 0],
    ]
    mat_xdl = [
        [0, 0, 1, 1, 1],
        [0, 1, 1, 1, 1],
        [0, 1, 1, 1, 1],
    ]
    cell = 7.2
    ym = 24.0

    def draw_mat(mx: float, mat: list[list[int]], acc: str) -> float:
        nr = len(mat)
        nc = len(mat[0])
        my = ym - 0.5 * nr * cell
        bg = "#101A2C" if theme.is_dark else "#FFFFFF"
        gr = "#334868" if theme.is_dark else "#94A3B8"
        fg = acc if theme.is_dark else theme.fg
        cv.rect(mx, my, nc * cell, nr * cell, fill=bg, stroke=gr, stroke_width=0.75)
        cv.add(f'<path d="{_bitmap_runs_path(mat, mx, my, cell, cell)}" fill="{fg}" shape-rendering="crispEdges"/>')
        for r in range(1, nr):
            cv.line(mx, my + r * cell, mx + nc * cell, my + r * cell, stroke=gr, stroke_width=0.55)
        for c in range(1, nc):
            cv.line(mx + c * cell, my, mx + c * cell, my + nr * cell, stroke=gr, stroke_width=0.55)
        cv.rect(mx, my, nc * cell, nr * cell, fill="none", stroke=gr, stroke_width=0.8)
        return mx + nc * cell

    cv.text(23.0, ym, "X =", font_size=11.0, fill=theme.fg, italic=True)
    end1 = draw_mat(39.0, mat_x, theme.cyan)
    cv.text(end1 + 7.0, ym + 1.0, ";", font_size=12.0, fill=theme.fg)
    cv.text(end1 + 21.0, ym, "X", font_size=11.0, fill=theme.fg, italic=True)
    cv.text(end1 + 28.5, ym - 4.2, "D", font_size=7.8, fill=theme.fg, italic=True)
    cv.text(end1 + 38.0, ym, "=", font_size=11.0, fill=theme.fg)
    end2 = draw_mat(end1 + 48.0, mat_xd, theme.gold)
    cv.text(end2 + 7.0, ym + 1.0, ";", font_size=12.0, fill=theme.fg)
    cv.text(end2 + 21.0, ym, "X", font_size=11.0, fill=theme.fg, italic=True)
    cv.text(end2 + 31.0, ym - 4.2, "DL", font_size=7.8, fill=theme.fg, italic=True)
    cv.text(end2 + 44.0, ym, "=", font_size=11.0, fill=theme.fg)
    end3 = draw_mat(end2 + 54.0, mat_xdl, theme.mint)
    cv.text(end3 + 6.0, ym + 2.0, ".", font_size=12.5, fill=theme.fg)
    return cv.to_svg()


def fig_20(theme: Theme) -> str:
    a = [
        [0, 1, 1, 1, 0],
        [1, 0, 1, 0, 1],
        [1, 1, 0, 1, 1],
        [1, 0, 1, 0, 1],
        [0, 1, 1, 1, 0],
    ]
    for _ in range(6):
        m = len(a)
        m2 = 2 * m - 1
        b = [[0] * m2 for _ in range(m2)]
        for i in range(m):
            ai = a[i]
            b2i = b[2 * i]
            for j in range(m):
                b2i[2 * j] = ai[j]
                if j + 1 < m:
                    b2i[2 * j + 1] = ai[j] ^ ai[j + 1]
            if i + 1 < m:
                ai1 = a[i + 1]
                b2i1 = b[2 * i + 1]
                for j in range(m):
                    b2i1[2 * j] = ai[j] ^ ai1[j]
        a = b
    n = len(a)
    cell = 0.6
    pad = 13.0
    cv = SvgCanvas(n * cell + 2 * pad, n * cell + 2 * pad, theme)
    if theme.is_dark:
        cv.rect(pad - 1.0, pad - 1.0, n * cell + 2.0, n * cell + 2.0, fill="#0D1524", stroke=theme.panel_stroke, stroke_width=0.9)
    col = theme.gold if theme.is_dark else theme.fg
    cv.add(f'<path d="{_bitmap_runs_path(a, pad, pad, cell, cell)}" fill="{col}" shape-rendering="crispEdges"/>')
    return cv.to_svg()


def fig_21(theme: Theme) -> str:
    cv = SvgCanvas(164, 166, theme)
    r = 11.5
    p1 = (82.0, 24.0)
    p2l = (46.0, 66.0)
    p2r = (118.0, 66.0)
    p3 = (82.0, 106.0)
    s_f = (54.0, 144.0)
    s_t = (110.0, 144.0)
    cv.bdd_edge(*p1, *p2l, is_hi=False, r1=r, r2=r)
    cv.bdd_edge(*p1, *p2r, is_hi=True, r1=r, r2=r)
    cv.bdd_edge(*p2l, *s_f, is_hi=False, r1=r, r2=9.5, curve=6.0)
    cv.bdd_edge(*p2l, *p3, is_hi=True, r1=r, r2=r)
    cv.bdd_edge(*p2r, *p3, is_hi=False, r1=r, r2=r)
    cv.bdd_edge(*p2r, *s_t, is_hi=True, r1=r, r2=9.5, curve=-6.0)
    cv.bdd_edge(*p3, *s_f, is_hi=False, r1=r, r2=9.5)
    cv.bdd_edge(*p3, *s_t, is_hi=True, r1=r, r2=9.5)
    cv.bdd_node(*p1, "1", r=r, accent=theme.cyan if theme.is_dark else None)
    cv.bdd_node(*p2l, "2", r=r, accent=theme.gold if theme.is_dark else None)
    cv.bdd_node(*p2r, "2", r=r, accent=theme.gold if theme.is_dark else None)
    cv.bdd_node(*p3, "3", r=r, accent=theme.violet if theme.is_dark else None)
    cv.bdd_sink(*s_f, "⊥", size=16.5, is_true=False)
    cv.bdd_sink(*s_t, "⊤", size=16.5, is_true=True)
    return cv.to_svg()


def _draw_c6_bdds(cv: SvgCanvas, left_x: float, right_x: float, show_counts: bool, show_cycle_and_captions: bool) -> None:
    ys = [18.0, 41.0, 66.0, 91.0, 116.0, 141.0, 166.0]
    r = 8.5
    sk = 13.0
    sr = 7.2

    ind_nodes: dict[str, tuple[float, float, str, str]] = {
        "n15": (left_x + 76.0, ys[0], "1", "18"),
        "n9": (left_x + 38.0, ys[1], "2", "13"),
        "n14": (left_x + 114.0, ys[1], "2", "5"),
        "n7": (left_x + 24.0, ys[2], "3", "8"),
        "n8": (left_x + 52.0, ys[2], "3", "5"),
        "n13": (left_x + 100.0, ys[2], "3", "5"),
        "n5": (left_x + 12.0, ys[3], "4", "5"),
        "n6": (left_x + 38.0, ys[3], "4", "3"),
        "n11": (left_x + 90.0, ys[3], "4", "3"),
        "n12": (left_x + 116.0, ys[3], "4", "2"),
        "n3": (left_x + 12.0, ys[4], "5", "3"),
        "n4": (left_x + 38.0, ys[4], "5", "2"),
        "n10": (left_x + 116.0, ys[4], "5", "1"),
        "n2": (left_x + 86.0, ys[5], "6", "1"),
    }
    ind_sinks: dict[str, tuple[float, float, str, str]] = {
        "sf_r2": (left_x + 130.0, ys[2], "⊥", "0"),
        "sf_r3": (left_x + 64.0, ys[3], "⊥", "0"),
        "sf_r4a": (left_x + 64.0, ys[4], "⊥", "0"),
        "sf_r4b": (left_x + 142.0, ys[4], "⊥", "0"),
        "sf_r5a": (left_x + 62.0, ys[5], "⊥", "0"),
        "sf_r5b": (left_x + 142.0, ys[5], "⊥", "0"),
        "st": (left_x + 62.0, ys[6], "⊤", "1"),
        "sf_bot": (left_x + 88.0, ys[6], "⊥", "0"),
    }
    ind_edges: list[tuple[str, str, bool, float]] = [
        ("n15", "n9", False, 0.0), ("n15", "n14", True, 0.0),
        ("n9", "n7", False, 0.0), ("n9", "n8", True, 0.0),
        ("n14", "n13", False, 0.0), ("n14", "sf_r2", True, 0.0),
        ("n7", "n5", False, 0.0), ("n7", "n6", True, 0.0),
        ("n8", "n5", False, 0.0), ("n8", "sf_r3", True, 0.0),
        ("n13", "n11", False, 0.0), ("n13", "n12", True, 0.0),
        ("n5", "n3", False, 0.0), ("n5", "n4", True, 0.0),
        ("n6", "n3", False, 0.0), ("n6", "sf_r4a", True, 0.0),
        ("n11", "n2", False, 0.0), ("n11", "n10", True, 0.0),
        ("n12", "n2", False, 6.0), ("n12", "sf_r4b", True, 0.0),
        ("n3", "st", False, 14.0), ("n3", "n2", True, -6.0),
        ("n4", "st", False, 6.0), ("n4", "sf_r5a", True, 0.0),
        ("n10", "n2", False, 0.0), ("n10", "sf_r5b", True, 0.0),
        ("n2", "st", False, 0.0), ("n2", "sf_bot", True, 0.0),
    ]

    ker_nodes: dict[str, tuple[float, float, str, str]] = {
        "k16": (right_x + 76.0, ys[0], "1", "5"),
        "k10": (right_x + 38.0, ys[1], "2", "3"),
        "k15": (right_x + 114.0, ys[1], "2", "2"),
        "k5": (right_x + 24.0, ys[2], "3", "1"),
        "k9": (right_x + 52.0, ys[2], "3", "2"),
        "k14": (right_x + 100.0, ys[2], "3", "2"),
        "k4": (right_x + 12.0, ys[3], "4", "2"),
        "k8": (right_x + 38.0, ys[3], "4", "1"),
        "k12": (right_x + 90.0, ys[3], "4", "1"),
        "k13": (right_x + 116.0, ys[3], "4", "1"),
        "k3": (right_x + 12.0, ys[4], "5", "1"),
        "k7": (right_x + 38.0, ys[4], "5", "1"),
        "k11": (right_x + 116.0, ys[4], "5", "1"),
        "k2": (right_x + 38.0, ys[5], "6", "1"),
        "k6": (right_x + 86.0, ys[5], "6", "1"),
    }
    ker_sinks: dict[str, tuple[float, float, str, str]] = {
        "kf_r2": (right_x + 130.0, ys[2], "⊥", "0"),
        "kf_r3": (right_x + 64.0, ys[3], "⊥", "0"),
        "kf_r4a": (right_x + 64.0, ys[4], "⊥", "0"),
        "kf_r4b": (right_x + 142.0, ys[4], "⊥", "0"),
        "kf_r5a": (right_x + 62.0, ys[5], "⊥", "0"),
        "kf_r5b": (right_x + 142.0, ys[5], "⊥", "0"),
        "kf_botL": (right_x + 38.0, ys[6], "⊥", "0"),
        "kt": (right_x + 62.0, ys[6], "⊤", "1"),
        "kf_botR": (right_x + 86.0, ys[6], "⊥", "0"),
    }
    ker_edges: list[tuple[str, str, bool, float]] = [
        ("k16", "k10", False, 0.0), ("k16", "k15", True, 0.0),
        ("k10", "k5", False, 0.0), ("k10", "k9", True, 0.0),
        ("k15", "k14", False, 0.0), ("k15", "kf_r2", True, 0.0),
        ("k5", "kf_r3", False, 0.0), ("k5", "k4", True, 0.0),
        ("k9", "k8", False, 0.0), ("k9", "kf_r3", True, 0.0),
        ("k14", "k12", False, 0.0), ("k14", "k13", True, 0.0),
        ("k4", "k3", False, 0.0), ("k4", "kf_r4a", True, -4.0),
        ("k8", "k7", False, 0.0), ("k8", "k3", True, 0.0),
        ("k12", "kf_r4a", False, 0.0), ("k12", "k11", True, 0.0),
        ("k13", "k7", False, -10.0), ("k13", "kf_r4b", True, 0.0),
        ("k3", "k2", False, 0.0), ("k3", "kf_botL", True, 12.0),
        ("k7", "kf_r5a", False, 0.0), ("k7", "k6", True, -4.0),
        ("k11", "k6", False, 0.0), ("k11", "kf_r5b", True, 0.0),
        ("k2", "kf_botL", False, 0.0), ("k2", "kt", True, 0.0),
        ("k6", "kt", False, 0.0), ("k6", "kf_botR", True, 0.0),
    ]

    lvl_cols = [cv.theme.cyan, cv.theme.gold, cv.theme.mint, cv.theme.violet, cv.theme.cyan, cv.theme.gold]

    for nodes, sinks, edges in [(ind_nodes, ind_sinks, ind_edges), (ker_nodes, ker_sinks, ker_edges)]:
        all_pts = {k: (v[0], v[1], True) for k, v in nodes.items()}
        all_pts.update({k: (v[0], v[1], False) for k, v in sinks.items()})
        for u, v, is_hi, crv in edges:
            x1, y1, ub = all_pts[u]
            x2, y2, vb = all_pts[v]
            cv.bdd_edge(x1, y1, x2, y2, is_hi=is_hi, r1=(r if ub else sr), r2=(r if vb else sr), curve=crv)
        for (nx, ny, lbl, cnt) in nodes.values():
            acc = lvl_cols[(int(lbl) - 1) % 6] if cv.theme.is_dark else None
            cv.bdd_node(nx, ny, lbl, r=r, accent=acc, font_size=9.2)
            if show_counts:
                cv.text(nx + r + 3.0, ny, cnt, font_size=8.2, fill=cv.theme.gold if cv.theme.is_dark else cv.theme.fg, anchor="start")
        for (sx, sy, lbl, cnt) in sinks.values():
            cv.bdd_sink(sx, sy, lbl, size=sk, is_true=(lbl == "⊤"))
            if show_counts:
                cv.text(sx + sk * 0.5 + 2.8, sy, cnt, font_size=8.0, fill=cv.theme.muted if cv.theme.is_dark else cv.theme.fg, anchor="start")

    if show_cycle_and_captions:
        cx_h, cy_h, rh = 234.0, 92.0, 26.0
        hpts = [
            (cx_h + rh * math.cos(-math.pi * 0.5 + k * math.pi / 3.0), cy_h + rh * math.sin(-math.pi * 0.5 + k * math.pi / 3.0))
            for k in range(6)
        ]
        for i in range(6):
            cv.graph_edge(*hpts[i], *hpts[(i + 1) % 6], r1=8.0, r2=8.0, stroke=cv.theme.muted if cv.theme.is_dark else cv.theme.fg, stroke_width=1.3)
        for i, (hx, hy) in enumerate(hpts, start=1):
            cv.graph_node(hx, hy, str(i), r=8.0, font_size=9.0, rich=False, stroke=cv.theme.gold if cv.theme.is_dark else cv.theme.fg)
        cv.text(cx_h - 6.0, cy_h + 46.0, "The cycle ", font_size=10.0, fill=cv.theme.fg)
        cv.text(cx_h + 21.0, cy_h + 46.0, "C", font_size=10.0, fill=cv.theme.fg, italic=True)
        cv.text(cx_h + 27.5, cy_h + 49.0, "6", font_size=7.4, fill=cv.theme.fg)
        cv.text(left_x + 76.0, 188.0, "Independent sets", font_size=10.2, fill=cv.theme.fg)
        cv.text(right_x + 76.0, 188.0, "Kernels", font_size=10.2, fill=cv.theme.fg)


def fig_p222_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(468, 202, theme)
    _draw_c6_bdds(cv, left_x=14.0, right_x=298.0, show_counts=False, show_cycle_and_captions=True)
    return cv.to_svg()


def fig_p222_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(456, 184, theme)
    _draw_c6_bdds(cv, left_x=14.0, right_x=262.0, show_counts=True, show_cycle_and_captions=False)
    return cv.to_svg()


def fig_p224_inline_1(theme: Theme) -> str:
    cv = SvgCanvas(316, 212, theme)
    ys = [20.0, 46.0, 72.0, 98.0, 124.0, 150.0, 176.0]
    rx, ry = 13.5, 8.2
    sk = 13.0
    nodes: dict[str, tuple[float, float, str]] = {
        "me": (146.0, ys[0], "ME"),
        "nh0": (114.0, ys[1], "NH"),
        "nh1": (178.0, ys[1], "NH"),
        "vt0": (82.0, ys[2], "VT"),
        "vt1": (210.0, ys[2], "VT"),
        "ma0": (110.0, ys[3], "MA"),
        "ma2": (166.0, ys[3], "MA"),
        "ma1": (246.0, ys[3], "MA"),
        "ri0": (54.0, ys[4], "RI"),
        "ri3": (166.0, ys[4], "RI"),
        "ri2": (222.0, ys[4], "RI"),
        "ri1": (278.0, ys[4], "RI"),
        "ct0": (54.0, ys[5], "CT"),
        "ct1": (110.0, ys[5], "CT"),
        "ct3": (166.0, ys[5], "CT"),
        "ct2": (278.0, ys[5], "CT"),
        "ny0": (28.0, ys[6], "NY"),
        "ny1": (138.0, ys[6], "NY"),
        "ny2": (248.0, ys[6], "NY"),
    }
    sinks: dict[str, tuple[float, float]] = {
        "sf_vt": (146.0, ys[2]),
        "sf_ma": (54.0, ys[3]),
        "sf_ri": (110.0, ys[4]),
        "sf_ct": (222.0, ys[5]),
        "sf_ny1": (82.0, ys[6]),
        "sf_ny2": (192.0, ys[6]),
        "sf_ny3": (296.0, ys[6]),
    }
    edges: list[tuple[str, str, bool]] = [
        ("me", "nh0", False), ("me", "nh1", True),
        ("nh0", "sf_vt", False), ("nh0", "vt0", True),
        ("nh1", "vt1", False), ("nh1", "sf_vt", True),
        ("vt0", "ma0", False), ("vt0", "sf_ma", True),
        ("vt1", "ma1", False), ("vt1", "ma2", True),
        ("ma0", "ri0", False), ("ma0", "sf_ri", True),
        ("ma2", "ri3", False), ("ma2", "sf_ri", True),
        ("ma1", "ri1", False), ("ma1", "ri2", True),
        ("ri0", "ct0", False), ("ri0", "ct1", True),
        ("ri3", "ct0", False), ("ri3", "ct3", True),
        ("ri2", "ct3", False), ("ri2", "sf_ct", True),
        ("ri1", "sf_ct", False), ("ri1", "ct2", True),
        ("ct0", "sf_ny1", False), ("ct0", "ny0", True),
        ("ct1", "ny1", False), ("ct1", "sf_ny1", True),
        ("ct3", "ny0", False), ("ct3", "sf_ny2", True),
        ("ct2", "ny2", False), ("ct2", "sf_ny3", True),
    ]

    for u, v, is_hi in edges:
        x1, y1, _ = nodes[u]
        if v in nodes:
            x2, y2, _ = nodes[v]
            p1 = _oval_edge_pt(x1, y1, x2, y2, rx, ry)
            p2 = _oval_edge_pt(x2, y2, x1, y1, rx, ry)
        else:
            x2, y2 = sinks[v]
            p1 = _oval_edge_pt(x1, y1, x2, y2, rx, ry)
            p2 = _oval_edge_pt(x2, y2, x1, y1, 7.2, 7.2)
        col = theme.hi_stroke if is_hi else theme.lo_stroke
        cv.line(p1[0], p1[1], p2[0], p2[1], stroke=col, stroke_width=1.35, dashed=(False if is_hi else "3.2,2.4"))

    cut_y = 198.0
    rays = [
        ("ny0", 28.0, False), ("ny0", 66.0, True),
        ("ny1", 112.0, True), ("ny1", 174.0, False),
        ("ny2", 206.0, True), ("ny2", 268.0, False),
    ]
    for u, tx, is_hi in rays:
        x1, y1, _ = nodes[u]
        p1 = _oval_edge_pt(x1, y1, tx, cut_y, rx, ry)
        col = theme.hi_stroke if is_hi else theme.lo_stroke
        cv.line(p1[0], p1[1], tx, cut_y, stroke=col, stroke_width=1.35, dashed=(False if is_hi else "3.2,2.4"))

    cv.line(12.0, cut_y, 304.0, cut_y, stroke=theme.muted if theme.is_dark else "#64748B", stroke_width=1.2, dashed="1.8,3.2")

    row_acc = [theme.cyan, theme.gold, theme.mint, theme.violet, theme.cyan, theme.gold, theme.mint]
    row_map = {"ME": 0, "NH": 1, "VT": 2, "MA": 3, "RI": 4, "CT": 5, "NY": 6}
    for (nx, ny, lbl) in nodes.values():
        acc = row_acc[row_map[lbl]] if theme.is_dark else theme.fg
        _oval_node(cv, nx, ny, lbl, rx=rx, ry=ry, font_size=8.6, accent=acc, bold=False)
    for (sx, sy) in sinks.values():
        cv.bdd_sink(sx, sy, "⊥", size=sk, is_true=False)
    return cv.to_svg()


def fig_p224_inline_2(theme: Theme) -> str:
    cv = SvgCanvas(486, 188, theme)
    min_set = {"CA", "ID", "ND", "CO", "IA", "LA", "OH", "GA", "DC", "DE", "MA", "ME"}
    max_set = {"WA", "NV", "WY", "ND", "KS", "TX", "WI", "IN", "TN", "FL", "SC", "WV", "DC", "NJ", "VT", "RI", "ME"}

    dx_grid = 17.6
    dy_grid = 20.2
    rx, ry = 7.4, 5.2
    panels = [
        (14.0, min_set, "Minimum weight = 155", theme.cyan),
        (254.0, max_set, "Maximum weight = 492", theme.gold),
    ]
    edge_col = "#2E4365" if theme.is_dark else "#94A3B8"
    for ox, chosen, caption, hi_acc in panels:
        oy = 16.0
        for u, v in USA_EDGES:
            cu, ru = USA_COORDS[u]
            cv_c, rv = USA_COORDS[v]
            x1, y1 = ox + cu * dx_grid, oy + ru * dy_grid
            x2, y2 = ox + cv_c * dx_grid, oy + rv * dy_grid
            active_e = (u in chosen) or (v in chosen)
            ecol = ("#3E5984" if active_e else edge_col) if theme.is_dark else edge_col
            cv.line(x1, y1, x2, y2, stroke=ecol, stroke_width=0.85)
        for st, (col_i, row_i) in USA_COORDS.items():
            nx = ox + col_i * dx_grid
            ny = oy + row_i * dy_grid
            sel = st in chosen
            if sel:
                nf = hi_acc if theme.is_dark else "#0F172A"
                nb = hi_acc if theme.is_dark else "#0F172A"
                tf = "#090D16" if theme.is_dark else "#FFFFFF"
            else:
                nf = "#111B2E" if theme.is_dark else "#FFFFFF"
                nb = "#475E82" if theme.is_dark else "#475569"
                tf = theme.fg
            _oval_node(cv, nx, ny, st, rx=rx, ry=ry, accent=nb, fill=nf, text_fill=tf, font_size=6.3, bold=sel)
        cv.text(ox + 6.0 * dx_grid, oy + 6.0 * dy_grid + 25.0, caption, font_size=10.2, fill=theme.fg)
    return cv.to_svg()


def fig_22(theme: Theme) -> str:
    cv = SvgCanvas(432, 336, theme)
    gx0, gy0, gstep = 42.0, 128.0, 34.0
    g_nums = [[1, 2, 4], [3, 5, 7], [6, 8, 9]]
    g_pos: dict[int, tuple[float, float]] = {}
    for r_i in range(3):
        for c_i in range(3):
            g_pos[g_nums[r_i][c_i]] = (gx0 + c_i * gstep, gy0 + r_i * gstep)
    p3_edges = [(1, 2), (1, 3), (2, 4), (4, 7), (2, 5), (3, 5), (3, 6), (5, 7), (5, 8), (6, 8), (7, 9), (8, 9)]
    for u, v in p3_edges:
        cv.graph_edge(*g_pos[u], *g_pos[v], r1=10.0, r2=10.0, stroke=theme.cyan if theme.is_dark else theme.fg, stroke_width=1.45)
    for num, (px, py) in g_pos.items():
        cv.graph_node(px, py, str(num), r=10.0, font_size=10.0, rich=False, stroke=theme.gold if theme.is_dark else theme.fg)

    bx0 = 158.0
    ys = [18.0 + k * 24.0 for k in range(13)]
    rx, ry = 9.8, 7.2
    sk = 12.0
    sr = 6.8

    nodes: dict[int, tuple[float, float, str]] = {
        36: (bx0 + 82.0, ys[0], "12"),
        25: (bx0 + 60.0, ys[1], "13"),
        35: (bx0 + 106.0, ys[1], "13"),
        24: (bx0 + 74.0, ys[2], "24"),
        34: (bx0 + 132.0, ys[2], "24"),
        18: (bx0 + 52.0, ys[3], "47"),
        23: (bx0 + 86.0, ys[3], "47"),
        27: (bx0 + 120.0, ys[3], "47"),
        33: (bx0 + 156.0, ys[3], "47"),
        17: (bx0 + 58.0, ys[4], "25"),
        22: (bx0 + 92.0, ys[4], "25"),
        26: (bx0 + 126.0, ys[4], "25"),
        32: (bx0 + 190.0, ys[4], "25"),
        16: (bx0 + 80.0, ys[5], "35"),
        21: (bx0 + 142.0, ys[5], "35"),
        31: (bx0 + 190.0, ys[5], "35"),
        10: (bx0 + 62.0, ys[6], "36"),
        15: (bx0 + 102.0, ys[6], "36"),
        19: (bx0 + 142.0, ys[6], "36"),
        20: (bx0 + 182.0, ys[6], "36"),
        30: (bx0 + 222.0, ys[6], "36"),
        9: (bx0 + 92.0, ys[7], "57"),
        14: (bx0 + 132.0, ys[7], "57"),
        29: (bx0 + 172.0, ys[7], "57"),
        5: (bx0 + 58.0, ys[8], "58"),
        8: (bx0 + 98.0, ys[8], "58"),
        11: (bx0 + 138.0, ys[8], "58"),
        13: (bx0 + 178.0, ys[8], "58"),
        28: (bx0 + 218.0, ys[8], "58"),
        4: (bx0 + 98.0, ys[9], "68"),
        7: (bx0 + 148.0, ys[9], "68"),
        12: (bx0 + 198.0, ys[9], "68"),
        3: (bx0 + 132.0, ys[10], "79"),
        6: (bx0 + 174.0, ys[10], "79"),
        2: (bx0 + 154.0, ys[11], "89"),
    }

    sinks: dict[str, tuple[float, float, str]] = {
        "sf2": (bx0 + 42.0, ys[2], "⊥"),
        "sf4a": (bx0 + 28.0, ys[4], "⊥"),
        "sf4b": (bx0 + 158.0, ys[4], "⊥"),
        "sf5": (bx0 + 46.0, ys[5], "⊥"),
        "sf7a": (bx0 + 52.0, ys[7], "⊥"),
        "sf9": (bx0 + 58.0, ys[9], "⊥"),
        "sf10a": (bx0 + 98.0, ys[10], "⊥"),
        "sf10b": (bx0 + 212.0, ys[10], "⊥"),
        "sf11": (bx0 + 120.0, ys[11], "⊥"),
        "sf12": (bx0 + 138.0, ys[12], "⊥"),
        "st12": (bx0 + 174.0, ys[12], "⊤"),
    }

    transitions: list[tuple[int, int | str, int | str]] = [
        (36, 25, 35),
        (25, "sf2", 24), (35, 24, 34),
        (24, 18, 23), (34, 27, 33),
        (18, "sf4a", 17), (23, 17, 22), (27, "sf4b", 26), (33, 26, 32),
        (17, "sf5", 16), (22, 16, 21), (26, 16, 15), (32, 31, 20),
        (16, 10, 15), (21, 19, 20), (31, 30, 20),
        (10, "sf7a", 9), (15, 9, 14), (19, "sf7a", 8), (20, 8, 13), (30, 9, 29),
        (9, 5, 8), (14, 11, 13), (29, 28, 13),
        (5, "sf9", 4), (8, 4, 7), (11, 4, 3), (13, 12, 6), (28, "sf10b", 12),
        (4, "sf10a", 3), (7, "sf10a", 6), (12, 3, 6),
        (3, "sf11", 2), (6, 2, "st12"),
        (2, "sf12", "st12"),
    ]

    for nid, lo_t, hi_t in transitions:
        x1, y1, _ = nodes[nid]
        for target, is_hi in [(lo_t, False), (hi_t, True)]:
            if isinstance(target, int):
                x2, y2, _ = nodes[target]
                p1 = _oval_edge_pt(x1, y1, x2, y2, rx, ry)
                p2 = _oval_edge_pt(x2, y2, x1, y1, rx, ry)
            else:
                x2, y2, _ = sinks[target]
                p1 = _oval_edge_pt(x1, y1, x2, y2, rx, ry)
                p2 = _oval_edge_pt(x2, y2, x1, y1, sr, sr)
            col = theme.hi_stroke if is_hi else theme.lo_stroke
            cv.line(p1[0], p1[1], p2[0], p2[1], stroke=col, stroke_width=1.2, dashed=(False if is_hi else "2.8,2.2"))

    palette = [theme.cyan, theme.gold, theme.mint, theme.violet]
    lvl_order = ["12", "13", "24", "47", "25", "35", "36", "57", "58", "68", "79", "89"]
    for (nx, ny, lbl) in nodes.values():
        acc = palette[lvl_order.index(lbl) % 4] if theme.is_dark else theme.fg
        _oval_node(cv, nx, ny, lbl, rx=rx, ry=ry, font_size=8.0, accent=acc)
    for (sx, sy, lbl) in sinks.values():
        cv.bdd_sink(sx, sy, lbl, size=sk, is_true=(lbl == "⊤"))
    return cv.to_svg()


def fig_p227_inline(theme: Theme) -> str:
    cv = SvgCanvas(256, 186, theme)
    cx = 128.0
    dx = 36.0
    dy = 25.0
    y0 = 22.0
    r = 9.5
    sk = 13.0

    pos: dict[tuple[int, int], tuple[float, float]] = {}
    for row in range(1, 6):
        ry = y0 + (row - 1) * dy
        x_start = cx - 0.5 * (row - 1) * dx
        for k in range(row):
            pos[(row, k)] = (x_start + k * dx, ry)

    sink_y = y0 + 5.0 * dy
    sink_x0 = cx - 2.5 * dx
    sinks = [(sink_x0 + k * dx, sink_y) for k in range(6)]

    for row in range(1, 5):
        for k in range(row):
            x1, y1 = pos[(row, k)]
            cv.bdd_edge(x1, y1, *pos[(row + 1, k)], is_hi=False, r1=r, r2=r)
            cv.bdd_edge(x1, y1, *pos[(row + 1, k + 1)], is_hi=True, r1=r, r2=r)
    for k in range(5):
        x1, y1 = pos[(5, k)]
        cv.bdd_edge(x1, y1, sinks[k][0], sinks[k][1], is_hi=False, r1=r, r2=7.2)
        cv.bdd_edge(x1, y1, sinks[k + 1][0], sinks[k + 1][1], is_hi=True, r1=r, r2=7.2)

    palette = [theme.cyan, theme.gold, theme.mint, theme.violet, theme.cyan]
    for row in range(1, 6):
        acc = palette[row - 1] if theme.is_dark else None
        for k in range(row):
            cv.bdd_node(*pos[(row, k)], str(row), r=r, accent=acc, font_size=9.8)

    for k, (sx, sy) in enumerate(sinks):
        fill = "#142034" if theme.is_dark else "#FFFFFF"
        st = theme.gold if theme.is_dark else theme.fg
        cv.rect(sx - sk * 0.5, sy - sk * 0.5, sk, sk, fill=fill, stroke=st, stroke_width=1.4, rx=1.8)
        cv.text(sx, sy + 14.5, f"ν={k}", font_size=8.6, fill=theme.muted if theme.is_dark else theme.fg, italic=True)

    return cv.to_svg()


BUILDERS: dict[str, Callable[[Theme], str]] = {
    "fig_p126_inline_2": fig_p126_inline_2,
    "fig_p129_inline": fig_p129_inline,
    "fig_11": fig_11,
    "fig_12": fig_12,
    "fig_p178_inline_1": fig_p178_inline_1,
    "fig_p178_inline_2": fig_p178_inline_2,
    "fig_p180_inline_1": fig_p180_inline_1,
    "fig_p180_inline_2": fig_p180_inline_2,
    "fig_13": fig_13,
    "fig_14": fig_14,
    "fig_p184_inline": fig_p184_inline,
    "fig_15": fig_15,
    "fig_16": fig_16,
    "fig_p187_block2x2": fig_p187_block2x2,
    "fig_p187_stencils37": fig_p187_stencils37,
    "fig_p187_stencils4": fig_p187_stencils4,
    "fig_17": fig_17,
    "fig_p192_inline": fig_p192_inline,
    "fig_18": fig_18,
    "fig_19": fig_19,
    "fig_p199_inline": fig_p199_inline,
    "fig_p211_inline": fig_p211_inline,
    "fig_20": fig_20,
    "fig_21": fig_21,
    "fig_p222_inline_1": fig_p222_inline_1,
    "fig_p222_inline_2": fig_p222_inline_2,
    "fig_p224_inline_1": fig_p224_inline_1,
    "fig_p224_inline_2": fig_p224_inline_2,
    "fig_22": fig_22,
    "fig_p227_inline": fig_p227_inline,
}

BUILDERS_P2: dict[str, Callable[[Theme], str]] = BUILDERS


def render_part(out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for fig_id, fn in BUILDERS.items():
        m, c, p = emit_dual_figure(fig_id, fn, out_dir)
        paths.extend((m, c, p))
    return paths
