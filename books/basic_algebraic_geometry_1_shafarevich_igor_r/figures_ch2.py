import math
from collections.abc import Callable

from polytypst.vision.diagram_engine import (
    INK,
    arrow_line,
    axes_xy,
    smooth_curve,
    svg_document,
)

from .figures_common import (
    BLUE,
    RED,
    Point,
    filled_pt,
    mvar,
    open_pt,
    render_elliptic_components,
    seg,
    txt,
)

CHAPTER_FIG_TITLES: dict[str, str] = {
    "7": "Transversal curves on a surface",
    "8": "y^2 = x^3 - x over R",
    "9": "y^2 = x^3 - x over C",
    "10": "The blowup sigma: Pi -> P^2",
    "11": "The Newton polygon",
}


def fig_7() -> str:
    boundary: list[Point] = [
        (36.0, 128.0),
        (56.0, 58.0),
        (158.0, 22.0),
        (286.0, 34.0),
        (388.0, 68.0),
        (408.0, 140.0),
        (366.0, 208.0),
        (248.0, 236.0),
        (114.0, 222.0),
    ]
    d1_pts: list[Point] = [
        (124.0, 74.0),
        (156.0, 66.0),
        (214.0, 114.0),
        (276.0, 174.0),
        (316.0, 184.0),
    ]
    d2_pts: list[Point] = [
        (98.0, 188.0),
        (142.0, 178.0),
        (214.0, 114.0),
        (272.0, 72.0),
        (300.0, 78.0),
    ]
    regions = smooth_curve(boundary, cls="c-sub", closed=True, fill_cls="f-blue")
    curves = "\n".join(
        [
            smooth_curve(boundary, cls="c-main", closed=True),
            smooth_curve(d1_pts, cls="c-blue"),
            smooth_curve(d2_pts, cls="c-red"),
        ]
    )
    labels = "\n".join(
        [
            open_pt(214.0, 114.0, color=INK, r=4.4),
            mvar(188.0, 120.0, "x"),
            mvar(326.0, 190.0, "D", sub="1", color=BLUE),
            mvar(310.0, 82.0, "D", sub="2", color=RED),
            mvar(368.0, 144.0, "X"),
        ]
    )
    return svg_document(
        "0 0 436 256",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="7",
        title=CHAPTER_FIG_TITLES["7"],
        show_grid=False,
    )


def fig_8() -> str:
    ox, oy = 148.0, 196.0
    sx, sy = 104.0, 104.0
    axes, ax_lbl = axes_xy(
        ox,
        oy,
        16.0,
        360.0,
        18.0,
        374.0,
        x_label="x",
        y_label="y",
        origin_label="0",
        origin_dx=7.0,
        origin_dy=19.0,
    )
    reg, crv = render_elliptic_components(
        (-1.0, 0.0, 1.0),
        1.78,
        (ox, oy, sx, sy),
        oval_cls="c-blue",
        branch_cls="c-blue",
        oval_fill="f-blue",
    )
    labels = "\n".join(
        [
            ax_lbl,
            txt(ox - sx - 22.0, oy + 19.0, "\u22121", italic=False),
            txt(ox + sx - 13.0, oy + 19.0, "1", italic=False),
            filled_pt(ox - sx, oy, color=BLUE, r=3.2),
            filled_pt(ox, oy, color=BLUE, r=3.2),
            filled_pt(ox + sx, oy, color=BLUE, r=3.2),
        ]
    )
    return svg_document(
        "0 0 384 392",
        grid=axes,
        region=reg,
        curve=crv,
        label=labels,
        fig_id="8",
        title=CHAPTER_FIG_TITLES["8"],
    )


def fig_9() -> str:
    cx, cy = 224.0, 148.0
    rx_out, ry_out = 194.0, 96.0
    rx_in, ry_in = 110.0, 52.0

    torus_even_odd = (
        f"M {cx - rx_out:.1f} {cy:.1f} "
        f"A {rx_out:.1f} {ry_out:.1f} 0 1 0 {cx + rx_out:.1f} {cy:.1f} "
        f"A {rx_out:.1f} {ry_out:.1f} 0 1 0 {cx - rx_out:.1f} {cy:.1f} Z "
        f"M {cx - rx_in:.1f} {cy:.1f} "
        f"A {rx_in:.1f} {ry_in:.1f} 0 1 1 {cx + rx_in:.1f} {cy:.1f} "
        f"A {rx_in:.1f} {ry_in:.1f} 0 1 1 {cx - rx_in:.1f} {cy:.1f} Z"
    )

    lx, rx_c, mr_x, mr_y = 72.0, 376.0, 42.0, 37.0
    left_front = (
        f"M {lx - mr_x:.1f} {cy:.1f} "
        f"A {mr_x:.1f} {mr_y:.1f} 0 0 1 {lx + mr_x:.1f} {cy:.1f}"
    )
    left_back = (
        f"M {lx - mr_x:.1f} {cy:.1f} "
        f"A {mr_x:.1f} {mr_y:.1f} 0 0 0 {lx + mr_x:.1f} {cy:.1f}"
    )
    right_front = (
        f"M {rx_c - mr_x:.1f} {cy:.1f} "
        f"A {mr_x:.1f} {mr_y:.1f} 0 0 1 {rx_c + mr_x:.1f} {cy:.1f}"
    )
    right_back = (
        f"M {rx_c - mr_x:.1f} {cy:.1f} "
        f"A {mr_x:.1f} {mr_y:.1f} 0 0 0 {rx_c + mr_x:.1f} {cy:.1f}"
    )

    regions = f'    <path d="{torus_even_odd}" class="f-blue" fill-rule="evenodd" />'
    curves = "\n".join(
        [
            f'    <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx_out:.1f}" ry="{ry_out:.1f}" class="c-main" />',
            f'    <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx_in:.1f}" ry="{ry_in:.1f}" class="c-main" />',
            f'    <path d="{left_back}" class="c-red-dash" />',
            f'    <path d="{right_back}" class="c-red-dash" />',
            f'    <path d="{left_front}" class="c-red" stroke-width="2.2" />',
            f'    <path d="{right_front}" class="c-red" stroke-width="2.2" />',
            seg((252.0, 34.0), (88.0, 114.0), cls="c-dash"),
            seg((366.0, 36.0), (382.0, 109.0), cls="c-dash"),
            seg((284.0, 224.0), (312.0, 254.0), cls="c-dash"),
        ]
    )
    labels = "\n".join(
        [
            txt(312.0, 27.0, "real locus", italic=False, color=RED, anchor="middle"),
            txt(348.0, 272.0, "the complex curve", italic=False, anchor="middle"),
        ]
    )
    return svg_document(
        "0 0 468 286",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="9",
        title=CHAPTER_FIG_TITLES["9"],
        show_grid=False,
    )


def fig_10() -> str:
    bx, by = 242.0, 386.0

    def _proj(x: float, y: float, z: float) -> Point:
        return (bx + 132.0 * x - 48.0 * y, by + 62.0 * y - z)

    plane_corners = [
        _proj(-1.26, 1.18, 0.0),
        _proj(1.20, 1.18, 0.0),
        _proj(1.28, -1.10, 0.0),
        _proj(-1.12, -1.10, 0.0),
    ]
    plane_d = "M " + " L ".join(f"{p[0]:.1f} {p[1]:.1f}" for p in plane_corners) + " Z"

    phis_deg = (0.0, 26.0, 68.0, 118.0, 158.0)
    z_top, z_bot = 312.0, 152.0

    def _hel(r: float, deg: float) -> Point:
        rad = math.radians(deg)
        z = z_top - (z_top - z_bot) * (deg / 180.0)
        return _proj(r * math.cos(rad), r * math.sin(rad), z)

    outer_edge: list[Point] = []
    inner_edge: list[Point] = []
    for k in range(55):
        dg = -20.0 + 216.0 * k / 54.0
        outer_edge.append(_hel(1.06, dg))
        inner_edge.append(_hel(-0.72, dg))

    sheet_pts = outer_edge + list(reversed(inner_edge))
    sheet_d = "M " + " L ".join(f"{p[0]:.1f} {p[1]:.1f}" for p in sheet_pts) + " Z"

    base_lines: list[str] = []
    lifted_lines: list[str] = []
    dot_els: list[str] = []
    lbl_els: list[str] = []

    lbl_offsets_top = (
        (9.0, 5.0, "start"),
        (9.0, 6.0, "start"),
        (9.0, 10.0, "start"),
        (2.0, 20.0, "middle"),
        (-9.0, 5.0, "end"),
    )
    lbl_offsets_bot = (
        (8.0, 5.0, "start"),
        (8.0, 6.0, "start"),
        (8.0, 5.0, "start"),
        (8.0, 5.0, "start"),
        (-8.0, 6.0, "end"),
    )

    for idx, dg in enumerate(phis_deg, start=1):
        rad = math.radians(dg)
        b_in = _proj(-0.76 * math.cos(rad), -0.76 * math.sin(rad), 0.0)
        b_out = _proj(0.88 * math.cos(rad), 0.88 * math.sin(rad), 0.0)
        base_lines.append(seg(b_in, b_out, cls="c-sub", stroke_width=1.4))
        dot_els.append(open_pt(b_out[0], b_out[1], color=BLUE, r=3.6))
        dx_b, dy_b, anc_b = lbl_offsets_bot[idx - 1]
        lbl_els.append(
            mvar(
                b_out[0] + dx_b,
                b_out[1] + dy_b,
                "L",
                sub=str(idx),
                color=BLUE,
                anchor=anc_b,
            )
        )

        h_in = _hel(-0.72, dg)
        h_out = _hel(1.06, dg)
        lifted_lines.append(seg(h_in, h_out, cls="c-amber", stroke_width=1.55))
        dot_els.append(open_pt(h_out[0], h_out[1], color=RED, r=3.8))
        dx_t, dy_t, anc_t = lbl_offsets_top[idx - 1]
        tx, ty = h_out[0] + dx_t, h_out[1] + dy_t
        lbl_els.append(
            f'    <text x="{tx:.1f}" y="{ty:.1f}" class="it" text-anchor="{anc_t}">'
            '\u03c3<tspan font-size="10.5px" dy="-5.5" font-style="normal">\u22121</tspan>'
            '<tspan dy="5.5" font-style="normal">(</tspan>L'
            f'<tspan font-size="10.5px" dy="3.5" font-style="normal">{idx}</tspan>'
            '<tspan dy="-3.5" font-style="normal">)</tspan></text>'
        )

    ax_top = _proj(0.0, 0.0, 366.0)
    ax_mid1 = _proj(0.0, 0.0, 232.0)
    ax_mid2 = _proj(0.0, 0.0, 154.0)
    ax_bot = _proj(0.0, 0.0, 118.0)

    regions = "\n".join(
        [
            f'    <path d="{plane_d}" class="f-blue" opacity="0.45" />',
            f'    <path d="{sheet_d}" class="f-amber" opacity="0.42" />',
            *base_lines,
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{plane_d}" class="c-main" />',
            seg(ax_mid1, ax_mid2, cls="c-red-dash"),
            seg(ax_top, ax_mid1, cls="c-red", stroke_width=1.9),
            seg(ax_mid2, ax_bot, cls="c-red", stroke_width=1.9),
            *lifted_lines,
            smooth_curve(outer_edge, cls="c-blue"),
            smooth_curve(inner_edge, cls="c-blue"),
            seg(outer_edge[0], inner_edge[0], cls="c-blue"),
            seg(outer_edge[-1], inner_edge[-1], cls="c-blue"),
            arrow_line(436.0, 166.0, 436.0, 224.0, cls="c-main", marker="arr"),
        ]
    )
    xi_p1_lbl = (
        f'    <text x="{ax_top[0] + 8.0:.1f}" y="{ax_top[1] + 12.0:.1f}" class="it" fill="{RED}">'
        '\u03be <tspan font-style="normal">\u00d7 </tspan>'
        '<tspan font-style="normal" font-weight="bold">P</tspan>'
        '<tspan font-size="10.5px" dy="-5.5" font-style="normal">1</tspan></text>'
    )
    labels = "\n".join(
        [
            filled_pt(bx, by, color=RED, r=3.6),
            mvar(bx - 4.0, by - 11.0, "\u03be", color=RED, anchor="middle"),
            mvar(408.0, 340.0, "P", sup="2", bold_base=True, color=BLUE),
            xi_p1_lbl,
            mvar(444.0, 198.0, "\u03c3"),
            *dot_els,
            *lbl_els,
        ]
    )
    return svg_document(
        "0 0 478 476",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="10",
        title=CHAPTER_FIG_TITLES["10"],
        show_grid=False,
    )


def _cross_mark(x: float, y: float, r: float = 6.2, cls: str = "c-main") -> str:
    return (
        f'    <line x1="{x - r:.1f}" y1="{y - r:.1f}" x2="{x + r:.1f}" y2="{y + r:.1f}" class="{cls}" stroke-width="2.0" />\n'
        f'    <line x1="{x - r:.1f}" y1="{y + r:.1f}" x2="{x + r:.1f}" y2="{y - r:.1f}" class="{cls}" stroke-width="2.0" />'
    )


def fig_11() -> str:
    ox, oy = 46.0, 256.0
    dx, dy = 26.0, 42.0

    def _pt(i: float, j: float) -> Point:
        return (ox + i * dx, oy - j * dy)

    axes, _ = axes_xy(
        ox,
        oy,
        18.0,
        342.0,
        18.0,
        282.0,
        x_label="",
        y_label="",
        origin_label="",
    )
    hull_pts = [_pt(2.35, 5.30), _pt(5.0, 0.0), _pt(11.6, 0.0), _pt(11.6, 5.30)]
    hull_d = "M " + " L ".join(f"{p[0]:.1f} {p[1]:.1f}" for p in hull_pts) + " Z"
    regions = f'    <path d="{hull_d}" class="f-amber" opacity="0.38" />'

    lattice_pts = (
        (3.0, 4.0, True),
        (4.0, 2.0, True),
        (6.0, 4.0, False),
        (9.0, 4.0, False),
        (7.0, 2.0, False),
        (10.0, 2.0, False),
        (8.0, 1.0, False),
    )
    curves = seg(_pt(2.35, 5.30), _pt(5.0, 0.0), cls="c-blue", stroke_width=2.3)
    labels = "\n".join(
        _cross_mark(*_pt(i, j), cls="c-red" if on_edge else "c-green")
        for i, j, on_edge in lattice_pts
    )
    return svg_document(
        "0 0 362 296",
        grid=axes,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="11",
        title=CHAPTER_FIG_TITLES["11"],
    )


CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "7": fig_7,
    "8": fig_8,
    "9": fig_9,
    "10": fig_10,
    "11": fig_11,
}
