from collections.abc import Callable

from polytypst.vision.diagram_engine import INK, arrow_line, svg_document

from .figures_common import (
    AMBER,
    BLUE,
    GREEN,
    RED,
    Point,
    cubic_secant_third,
    cubic_tangent_third,
    cubic_y,
    line_through,
    mvar,
    open_pt,
    panel_label,
    render_elliptic_components,
    seg,
    txt,
)

CHAPTER_FIG_TITLES: dict[str, str] = {
    "12": "Constructing functions on a plane cubic",
    "13": "The group law on a plane cubic",
    "14": "The inverse map gamma -> gamma_1",
    "15": "The map f(x, y) = xy",
}


def _map_pt(p: Point, frame: tuple[float, float, float, float]) -> Point:
    cx, cy, sx, sy = frame
    return (cx + sx * p[0], cy - sy * p[1])


def fig_12() -> str:
    roots = (-1.15, -0.06, 0.85)
    fa = (118.0, 150.0, 62.0, 52.0)
    fb = (412.0, 136.0, 62.0, 52.0)

    reg_a, crv_a = render_elliptic_components(roots, 1.88, fa)
    reg_b, crv_b = render_elliptic_components(roots, 1.88, fb)

    a0_m = (-1.13, -cubic_y(-1.13, roots))
    a_m = (-0.20, cubic_y(-0.20, roots))
    ba_m = cubic_secant_third(a0_m, a_m, roots)
    pa0, pa, pba = _map_pt(a0_m, fa), _map_pt(a_m, fa), _map_pt(ba_m, fa)
    l1_a_end = (pba[0] + 34.0, pba[1] + 92.0)

    b0_m = (-0.79, -cubic_y(-0.79, roots))
    bb_m, _ = cubic_tangent_third(b0_m, roots)
    pb0, pbb = _map_pt(b0_m, fb), _map_pt(bb_m, fb)
    l1_b_top = (pbb[0] + 12.0, pbb[1] - 110.0)

    regions = f"{reg_a}\n{reg_b}"
    curves = "\n".join(
        [
            crv_a,
            crv_b,
            line_through(pa0, pba, -0.14, 1.16, cls="c-red", stroke_width=1.85),
            line_through(pba, l1_a_end, -0.45, 1.05, cls="c-green", stroke_width=1.75),
            line_through(pb0, pbb, -0.26, 1.18, cls="c-red", stroke_width=1.85),
            line_through(pbb, l1_b_top, -0.28, 1.0, cls="c-green", stroke_width=1.75),
        ]
    )
    labels = "\n".join(
        [
            open_pt(pa0[0], pa0[1], color=RED, r=3.9),
            open_pt(pa[0], pa[1], color=RED, r=3.9),
            open_pt(pba[0], pba[1], color=GREEN, r=3.9),
            open_pt(pb0[0], pb0[1], color=RED, r=3.9),
            open_pt(pbb[0], pbb[1], color=GREEN, r=3.9),
            mvar(pa0[0] - 18.0, pa0[1] + 20.0, "\u03b1", sub="0", color=RED),
            mvar(pa[0] - 4.0, pa[1] - 10.0, "\u03b1", color=RED),
            mvar(
                0.5 * (pa[0] + pba[0]) - 10.0,
                0.5 * (pa[1] + pba[1]) - 8.0,
                "L",
                sub="0",
                color=RED,
            ),
            mvar(l1_a_end[0] - 4.0, l1_a_end[1] - 28.0, "L", sub="1", color=GREEN),
            mvar(pb0[0] - 8.0, pb0[1] + 20.0, "\u03b1", sub="0", color=RED),
            mvar(
                0.5 * (pb0[0] + pbb[0]) + 4.0,
                0.5 * (pb0[1] + pbb[1]) - 8.0,
                "L",
                sub="0",
                color=RED,
            ),
            mvar(l1_b_top[0] - 20.0, l1_b_top[1] + 14.0, "L", sub="1", color=GREEN),
            panel_label(136.0, 266.0, "a"),
            panel_label(428.0, 266.0, "b"),
        ]
    )
    return svg_document(
        "0 0 568 280",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="12",
        title=CHAPTER_FIG_TITLES["12"],
        show_grid=False,
    )


def fig_13() -> str:
    roots = (-1.15, -0.10, 0.85)
    fa = (122.0, 152.0, 62.0, 56.0)
    fb = (412.0, 166.0, 62.0, 56.0)

    reg_a, crv_a = render_elliptic_components(roots, 1.72, fa)
    reg_b, crv_b = render_elliptic_components(roots, 1.72, fb)

    o_a = (-0.66, cubic_y(-0.66, roots))
    p_a, _ = cubic_tangent_third(o_a, roots)
    x_a = (-0.14, -cubic_y(-0.14, roots))
    xp_a = cubic_secant_third(p_a, x_a, roots)
    po_a, pp_a, px_a, pxp_a = (
        _map_pt(o_a, fa),
        _map_pt(p_a, fa),
        _map_pt(x_a, fa),
        _map_pt(xp_a, fa),
    )

    x_b = (-0.62, -cubic_y(-0.62, roots))
    y_b = (-0.13, -cubic_y(-0.13, roots))
    zp_b = cubic_secant_third(x_b, y_b, roots)
    o_b = (-0.54, cubic_y(-0.54, roots))
    z_b = cubic_secant_third(zp_b, o_b, roots)
    px_b, py_b, pzp_b, po_b, pz_b = (
        _map_pt(x_b, fb),
        _map_pt(y_b, fb),
        _map_pt(zp_b, fb),
        _map_pt(o_b, fb),
        _map_pt(z_b, fb),
    )

    regions = "\n".join(
        [
            reg_a,
            reg_b,
            line_through(po_a, pp_a, -0.34, 1.24, cls="c-amber", stroke_width=1.65),
            line_through(px_b, pzp_b, -0.26, 1.14, cls="c-amber", stroke_width=1.65),
        ]
    )
    curves = "\n".join(
        [
            crv_a,
            crv_b,
            line_through(pxp_a, pp_a, -0.28, 1.24, cls="c-red", stroke_width=1.85),
            line_through(pz_b, pzp_b, -0.24, 1.14, cls="c-red", stroke_width=1.85),
        ]
    )
    labels = "\n".join(
        [
            open_pt(po_a[0], po_a[1], color=AMBER, r=3.8),
            open_pt(pp_a[0], pp_a[1], color=AMBER, r=3.8),
            open_pt(px_a[0], px_a[1], color=RED, r=3.8),
            open_pt(pxp_a[0], pxp_a[1], color=RED, r=3.8),
            mvar(po_a[0] - 4.0, po_a[1] - 10.0, "o", color=AMBER),
            mvar(pp_a[0] + 6.0, pp_a[1] + 16.0, "p", color=AMBER),
            mvar(px_a[0] + 7.0, px_a[1] + 13.0, "x", color=RED),
            mvar(pxp_a[0] - 16.0, pxp_a[1] + 19.0, "x", prime="\u2032", color=RED),
            open_pt(px_b[0], px_b[1], color=AMBER, r=3.8),
            open_pt(py_b[0], py_b[1], color=AMBER, r=3.8),
            open_pt(pzp_b[0], pzp_b[1], color=AMBER, r=3.8),
            open_pt(po_b[0], po_b[1], color=RED, r=3.8),
            open_pt(pz_b[0], pz_b[1], color=RED, r=3.8),
            mvar(px_b[0] + 3.0, px_b[1] + 19.0, "x", color=AMBER),
            mvar(py_b[0] + 8.0, py_b[1] + 6.0, "y", color=AMBER),
            mvar(pzp_b[0] + 8.0, pzp_b[1] + 6.0, "z", prime="\u2032", color=AMBER),
            mvar(po_b[0] - 4.0, po_b[1] - 10.0, "o", color=RED),
            mvar(pz_b[0] - 16.0, pz_b[1] - 4.0, "z", color=RED),
            panel_label(134.0, 286.0, "a"),
            panel_label(426.0, 286.0, "b"),
        ]
    )
    return svg_document(
        "0 0 568 300",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="13",
        title=CHAPTER_FIG_TITLES["13"],
        show_grid=False,
    )


def fig_14() -> str:
    roots = (-1.15, -0.06, 0.85)
    frame = (166.0, 168.0, 82.0, 68.0)
    reg, crv = render_elliptic_components(roots, 1.82, frame)

    g_m = (-1.13, -cubic_y(-1.13, roots))
    g1_m = (-0.22, cubic_y(-0.22, roots))
    o_m = cubic_secant_third(g_m, g1_m, roots)
    pg, pg1, po = _map_pt(g_m, frame), _map_pt(g1_m, frame), _map_pt(o_m, frame)

    curves = "\n".join(
        [
            crv,
            line_through(pg, po, -0.14, 1.14, cls="c-red", stroke_width=2.0),
        ]
    )
    labels = "\n".join(
        [
            open_pt(pg[0], pg[1], color=RED, r=4.2),
            open_pt(pg1[0], pg1[1], color=RED, r=4.2),
            open_pt(po[0], po[1], color=BLUE, r=4.2),
            mvar(pg[0] - 18.0, pg[1] - 8.0, "\u03b3", color=RED),
            mvar(pg1[0] - 6.0, pg1[1] - 12.0, "\u03b3", sub="1", color=RED),
            mvar(po[0] - 18.0, po[1] - 8.0, "o", color=BLUE),
        ]
    )
    return svg_document(
        "0 0 388 308",
        region=reg,
        curve=curves,
        label=labels,
        fig_id="14",
        title=CHAPTER_FIG_TITLES["14"],
        show_grid=False,
    )


def fig_15() -> str:
    cx, cy = 224.0, 96.0
    left_d = (
        f"M 24.0 22.0 L 198.0 22.0 "
        f"C 198.0 64.0, 210.0 92.0, {cx:.1f} {cy:.1f} "
        f"C 210.0 100.0, 198.0 128.0, 198.0 170.0 "
        f"L 24.0 170.0 Z"
    )
    right_d = (
        f"M 424.0 22.0 L 250.0 22.0 "
        f"C 250.0 64.0, 238.0 92.0, {cx:.1f} {cy:.1f} "
        f"C 238.0 100.0, 250.0 128.0, 250.0 170.0 "
        f"L 424.0 170.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{left_d}" class="f-blue" opacity="0.52" />',
            f'    <path d="{right_d}" class="f-blue" opacity="0.52" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{left_d}" class="c-blue" />',
            f'    <path d="{right_d}" class="c-blue" />',
            arrow_line(332.0, 172.0, 332.0, 220.0, cls="c-main", marker="arr"),
            seg((20.0, 228.0), (428.0, 228.0), cls="c-red", stroke_width=2.0),
        ]
    )
    origin_lbl = (
        f'    <text x="{cx + 28.0:.1f}" y="{cy + 5.0:.1f}" class="lbl" fill="{RED}">'
        '(<tspan class="it">u</tspan> = 0, <tspan class="it">v</tspan> = 0)</text>'
    )
    u_zero_top = txt(
        cx + 4.0,
        52.0,
        '<tspan class="it">u</tspan> = 0',
        italic=False,
        color=INK,
        anchor="middle",
        size=13.0,
        rotate=-90.0,
    )
    u_zero_bot = txt(
        cx + 4.0,
        142.0,
        '<tspan class="it">u</tspan> = 0',
        italic=False,
        color=INK,
        anchor="middle",
        size=13.0,
        rotate=-90.0,
    )
    labels = "\n".join(
        [
            open_pt(cx, cy, color=RED, r=4.5),
            mvar(
                104.0,
                102.0,
                "\u0393",
                overbar=True,
                color=BLUE,
                size=18.0,
                anchor="middle",
            ),
            origin_lbl,
            u_zero_top,
            u_zero_bot,
            mvar(344.0, 202.0, "q"),
        ]
    )
    return svg_document(
        "0 0 448 250",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="15",
        title=CHAPTER_FIG_TITLES["15"],
        show_grid=False,
    )


CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "12": fig_12,
    "13": fig_13,
    "14": fig_14,
    "15": fig_15,
}
