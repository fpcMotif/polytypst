"""High-elegance vector diagram generator producing publication-grade SVGs for John Roberts' The Modern Firm."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse
from matplotlib.axis import Axis
from matplotlib.spines import Spine
from matplotlib.text import Annotation, Text
from matplotlib.transforms import Bbox

# Configure matplotlib for publication styling
plt.rcParams["font.sans-serif"] = ["Songti SC", "PingFang SC", "Heiti SC", "Hiragino Sans GB", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"] = "none"  # Preserve text in SVG


INK = "#1a1a1a"
ZH_FONT = "Songti SC"
LATIN_FONT = "STIX Two Text"
# Traced pixel coordinates come from 150-dpi scans of the original book; this
# factor keeps each figure at its original size relative to the text block.
PX_PT = 0.33
CURVE_LW = 0.9
AXIS_LW = 0.7
GUIDE_LW = 0.5


def _canvas(w_px: float, h_px: float, px_pt: float = PX_PT):
    fig = plt.figure(figsize=(w_px * px_pt / 72, h_px * px_pt / 72))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w_px)
    ax.set_ylim(h_px, 0)
    ax.axis("off")
    return fig, ax


def _save(fig, out_path: Path) -> None:
    renderer = fig.canvas.get_renderer()
    ax = fig.axes[0]
    extents = [
        a.get_tightbbox(renderer)
        for a in ax.get_children()
        if a.get_visible() and a is not ax.patch and not isinstance(a, (Spine, Axis))
        and not (isinstance(a, Text) and not isinstance(a, Annotation) and not a.get_text())
    ]
    box = Bbox.union([b for b in extents if b is not None and (b.width > 0 or b.height > 0)])
    fig.savefig(out_path, format="svg", bbox_inches=box.transformed(fig.dpi_scale_trans.inverted()).padded(0.03))
    plt.close(fig)


def _zh(ax, x, y, s, size=8.0, **kw):
    kw.setdefault("ha", "center")
    kw.setdefault("va", "center")
    ax.text(x, y, s, fontfamily=ZH_FONT, fontsize=size, color=INK, **kw)


def _latin(ax, x, y, s, size=8.5, **kw):
    kw.setdefault("ha", "center")
    kw.setdefault("va", "center")
    ax.text(x, y, s, fontfamily=LATIN_FONT, fontsize=size, color=INK, **kw)


def _line(ax, xs, ys, lw=AXIS_LW, style="solid"):
    dashes = {"solid": None, "dashed": (4, 2.5), "dotted": (1, 1.8)}[style]
    (ln,) = ax.plot(xs, ys, color=INK, lw=lw, solid_capstyle="butt", clip_on=False)
    if dashes:
        ln.set_dashes(dashes)


def _arrow(ax, start, end, lw=0.7):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.22", lw=lw, color=INK, shrinkA=0, shrinkB=0),
        annotation_clip=False,
    )


def _smooth(points, n=24):
    """Catmull-Rom spline through the traced points, so curves pass exactly through peaks."""
    p = np.asarray(points, dtype=float)
    p = np.vstack([p[0], p, p[-1]])
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    segments = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        segments.append(
            0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t**2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t**3)
        )
    segments.append(p[-2][None])
    return np.vstack(segments)


def _relax(curve, sigma_px=16.0):
    """Gaussian-smooth along arc length; odd reflection at the ends keeps endpoints and end slopes fixed."""
    seg = np.hypot(*np.diff(curve, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    u = np.arange(0, s[-1], 1.0)
    c = np.column_stack([np.interp(u, s, curve[:, 0]), np.interp(u, s, curve[:, 1])])
    k = int(3 * sigma_px)
    if len(c) <= 2 * k + 1:
        return curve
    kernel = np.exp(-0.5 * (np.arange(-k, k + 1) / sigma_px) ** 2)
    kernel /= kernel.sum()
    padded = np.vstack([2 * c[0] - c[k:0:-1], c, 2 * c[-1] - c[-2:-k - 2:-1]])
    out = np.column_stack([np.convolve(padded[:, i], kernel, mode="valid") for i in range(2)])
    out[0], out[-1] = curve[0], curve[-1]
    return out


def _bezier(p0, p1, p2, p3, n=200):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, dtype=float) for p in (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3


def _curve(ax, points, style="solid", lw=CURVE_LW):
    c = _relax(_smooth(points))
    _line(ax, c[:, 0], c[:, 1], lw=lw, style=style)
    return c


def _y_at(curve, x):
    return float(np.interp(x, curve[:, 0], curve[:, 1]))


def _axes_l(ax, x0, y_top, y_base, x_right):
    _line(ax, [x0, x0, x_right], [y_top, y_base, y_base])


def generate_figure_1(out_path: Path) -> None:
    """图 1: 设计者、战略、活动、组织、环境与绩效 (original p.12)."""
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="20 8 405 272" width="218pt" height="146pt" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="tikz-stealth" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="7.5" markerHeight="6" orient="auto">
      <path d="M 0 0.5 L 9.5 4 L 0 7.5 L 2.6 4 Z" fill="#1a1a1a"/>
    </marker>
  </defs>
  <line x1="188" y1="42" x2="106" y2="104" stroke="#1a1a1a" stroke-width="0.95" marker-end="url(#tikz-stealth)"/>
  <line x1="272" y1="42" x2="354" y2="104" stroke="#1a1a1a" stroke-width="0.95" marker-end="url(#tikz-stealth)"/>
  <line x1="124" y1="126" x2="179" y2="126" stroke="#1a1a1a" stroke-width="0.95" marker-end="url(#tikz-stealth)"/>
  <line x1="281" y1="126" x2="316" y2="126" stroke="#1a1a1a" stroke-width="0.95" marker-end="url(#tikz-stealth)"/>

  <line x1="124" y1="145" x2="313" y2="229" stroke="#1a1a1a" stroke-width="6.2"/>
  <line x1="122" y1="144" x2="314" y2="229.5" stroke="#ffffff" stroke-width="4.2"/>
  <path d="M 306 218.5 L 316.5 230.5 L 300.5 231" fill="none" stroke="#1a1a1a" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>

  <line x1="363" y1="145" x2="363" y2="224" stroke="#1a1a1a" stroke-width="6.2"/>
  <line x1="363" y1="144" x2="363" y2="225" stroke="#ffffff" stroke-width="4.2"/>
  <path d="M 356 217 L 363 226.5 L 370 217" fill="none" stroke="#1a1a1a" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>

  <line x1="124" y1="250" x2="313" y2="250" stroke="#1a1a1a" stroke-width="6.2"/>
  <line x1="123" y1="250" x2="314" y2="250" stroke="#ffffff" stroke-width="4.2"/>
  <path d="M 306 243 L 315.5 250 L 306 257" fill="none" stroke="#1a1a1a" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>

  <rect x="188" y="18" width="84" height="36" fill="#ffffff" stroke="#1a1a1a" stroke-width="1.05"/>
  <text x="230" y="41" text-anchor="middle" font-family="Songti SC, STSong, Noto Serif CJK SC, serif" font-size="15.5" fill="#1a1a1a">设计者</text>

  <rect x="40" y="108" width="84" height="36" fill="#ffffff" stroke="#1a1a1a" stroke-width="1.05"/>
  <text x="82" y="131" text-anchor="middle" font-family="Songti SC, STSong, Noto Serif CJK SC, serif" font-size="15.5" fill="#1a1a1a">战略</text>

  <ellipse cx="230" cy="126" rx="45" ry="20" fill="#ffffff" stroke="#1a1a1a" stroke-width="1.05"/>
  <text x="230" y="131" text-anchor="middle" font-family="Songti SC, STSong, Noto Serif CJK SC, serif" font-size="15.5" fill="#1a1a1a">活动</text>

  <rect x="321" y="108" width="84" height="36" fill="#ffffff" stroke="#1a1a1a" stroke-width="1.05"/>
  <text x="363" y="131" text-anchor="middle" font-family="Songti SC, STSong, Noto Serif CJK SC, serif" font-size="15.5" fill="#1a1a1a">组织</text>

  <rect x="40" y="232" width="84" height="36" fill="#ffffff" stroke="#1a1a1a" stroke-width="1.05"/>
  <text x="82" y="255" text-anchor="middle" font-family="Songti SC, STSong, Noto Serif CJK SC, serif" font-size="15.5" fill="#1a1a1a">环境</text>

  <rect x="321" y="232" width="84" height="36" fill="#ffffff" stroke="#1a1a1a" stroke-width="1.05"/>
  <rect x="324" y="235" width="78" height="30" fill="none" stroke="#1a1a1a" stroke-width="0.65"/>
  <text x="363" y="255" text-anchor="middle" font-family="Songti SC, STSong, Noto Serif CJK SC, serif" font-size="15.5" fill="#1a1a1a">绩效</text>
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def generate_figure_2(out_path: Path) -> None:
    """图 2: 柔性 × 多样性 2×2 矩阵 (original p.24)."""
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="24 10 355 252" width="205pt" height="145pt" xmlns="http://www.w3.org/2000/svg">
  <rect x="112" y="20" width="252" height="178" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="1.5"/>
  <line x1="238" y1="20" x2="238" y2="198" stroke="#cbd5e1" stroke-width="1.4" stroke-dasharray="4 3"/>
  <line x1="112" y1="109" x2="364" y2="109" stroke="#cbd5e1" stroke-width="1.4" stroke-dasharray="4 3"/>

  <rect x="132" y="44" width="86" height="42" rx="6" fill="#ffffff" stroke="#334155" stroke-width="1.35"/>
  <text x="175" y="70" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="15" font-weight="500" fill="#0f172a">通用汽车</text>

  <rect x="258" y="44" width="86" height="42" rx="6" fill="#ffffff" stroke="#334155" stroke-width="1.35"/>
  <text x="301" y="70" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="15" font-weight="500" fill="#0f172a">丰田</text>

  <rect x="132" y="132" width="86" height="42" rx="6" fill="#ffffff" stroke="#334155" stroke-width="1.35"/>
  <text x="175" y="158" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="15" font-weight="500" fill="#0f172a">福特</text>

  <rect x="258" y="132" width="86" height="42" rx="6" fill="#f1f5f9" stroke="#64748b" stroke-width="1.35" stroke-dasharray="4 3"/>
  <text x="301" y="159" text-anchor="middle" font-family="STIX Two Text, Times New Roman, serif" font-size="18" font-weight="600" fill="#334155">?</text>

  <text x="44" y="102" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="15" font-weight="600" fill="#1e293b">柔</text>
  <text x="44" y="124" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="15" font-weight="600" fill="#1e293b">性</text>
  <text x="88" y="70" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="13.5" font-weight="500" fill="#475569">高</text>
  <text x="88" y="158" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="13.5" font-weight="500" fill="#475569">低</text>

  <text x="175" y="222" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="13.5" font-weight="500" fill="#475569">低</text>
  <text x="301" y="222" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="13.5" font-weight="500" fill="#475569">高</text>
  <text x="238" y="250" text-anchor="middle" font-family="Songti SC, PingFang SC, STSong, serif" font-size="15" font-weight="600" fill="#1e293b" letter-spacing="2">多样性</text>
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def generate_figure_3(out_path: Path) -> None:
    """图 3: 选择和绩效关系的经典模型 (original p.32)."""
    fig, ax = _canvas(480, 300)
    _axes_l(ax, 42, 18, 237, 442)
    c = _curve(ax, [(42, 147), (90, 97), (135, 52), (200, 22), (255, 52), (327, 105), (375, 157), (417, 202)])
    for x, label in ((200, "X"), (327, "Y")):
        _line(ax, [x, x], [_y_at(c, x), 237], lw=GUIDE_LW, style="dashed")
        _latin(ax, x, 252, label)
    _zh(ax, 262, 278, "选择")
    _zh(ax, 20, 140, "绩效", rotation=90)
    _save(fig, out_path)


def generate_figure_4(out_path: Path) -> None:
    """图 4: 选择和绩效的关系发生改变 (original p.33)."""
    fig, ax = _canvas(500, 330)
    _axes_l(ax, 57, 15, 210, 475)
    _curve(ax, [(65, 170), (90, 135), (140, 92), (205, 62), (260, 80), (312, 120), (360, 180)])
    new = _curve(ax, [(140, 160), (170, 110), (205, 62), (260, 30), (312, 22), (360, 30), (395, 48)], style="dashed")
    for x, label in ((205, "X"), (312, "X′")):
        _line(ax, [x, x], [_y_at(new, x), 210], lw=GUIDE_LW, style="dashed")
        _latin(ax, x, 226, label)
    _zh(ax, 260, 252, "选择")
    _zh(ax, 36, 112, "绩效", rotation=90)
    _save(fig, out_path)


def generate_figure_5(out_path: Path) -> None:
    """图 5: 非凹性的绩效关系 (original p.35)."""
    fig, ax = _canvas(530, 340)
    _axes_l(ax, 50, 18, 262, 505)
    c = _curve(ax, [
        (50, 118), (90, 75), (130, 35), (165, 25), (200, 35), (245, 85), (290, 130),
        (322, 140), (360, 122), (382, 100), (405, 90), (430, 110), (470, 152),
    ])
    for x, label in ((165, "Y"), (322, "Z"), (405, "X")):
        _line(ax, [x, x], [_y_at(c, x), 262], lw=GUIDE_LW, style="dashed")
        _latin(ax, x, 278, label)
    _zh(ax, 262, 306, "选择")
    _zh(ax, 28, 135, "绩效", rotation=90)
    _save(fig, out_path)


def _two_peak_field(x, y):
    def bump(cx, cy, sx, sy, theta_deg, height):
        th = np.deg2rad(theta_deg)
        u = (x - cx) * np.cos(th) + (y - cy) * np.sin(th)
        v = -(x - cx) * np.sin(th) + (y - cy) * np.cos(th)
        return height * np.exp(-(u**2 / (2 * sx**2) + v**2 / (2 * sy**2)))

    return bump(281, 118, 58, 40, 35, 1.0) + bump(163, 215, 34, 52, 15, 0.92)


def generate_figure_6(out_path: Path) -> None:
    """图 6: 非凹性允许存在多个不同的内在相互匹配的点 (original p.36)."""
    fig, ax = _canvas(460, 395)
    _axes_l(ax, 65, 50, 332, 435)

    xs, ys = np.meshgrid(np.linspace(75, 425, 400), np.linspace(18, 325, 360))
    z = _two_peak_field(xs, ys)
    ax.contour(xs, ys, z, levels=[0.13, 0.3, 0.52, 0.74], colors=INK, linewidths=CURVE_LW)
    for cx, cy in ((281, 118), (163, 215)):
        ax.add_patch(Ellipse((cx, cy), 10, 8, fill=False, ec=INK, lw=CURVE_LW))

    # Arrows point uphill and cross a contour line, as in the original.
    arrows = [  # (peak, screen angle in degrees, contour level)
        ((281, 118), -60, 0.3), ((281, 118), 30, 0.13), ((281, 118), 100, 0.3),
        ((163, 215), 15, 0.13), ((163, 215), 50, 0.3), ((163, 215), 140, 0.3), ((163, 215), -45, 0.74),
    ]
    for (cx, cy), angle, level in arrows:
        ray = np.deg2rad(angle)
        r = np.arange(0, 260, 0.5)
        vals = _two_peak_field(cx + r * np.cos(ray), cy + r * np.sin(ray))
        hit = r[np.argmax(vals < level)]
        px, py = cx + hit * np.cos(ray), cy + hit * np.sin(ray)
        gx = _two_peak_field(px + 0.5, py) - _two_peak_field(px - 0.5, py)
        gy = _two_peak_field(px, py + 0.5) - _two_peak_field(px, py - 0.5)
        d = np.array([gx, gy]) / np.hypot(gx, gy)
        _arrow(ax, (px - 14 * d[0], py - 14 * d[1]), (px + 9 * d[0], py + 9 * d[1]), lw=0.6)

    for (cx, cy), label in (((163, 215), "A"), ((281, 118), "B")):
        _line(ax, [52, cx], [cy, cy], lw=GUIDE_LW)
        _line(ax, [cx, cx], [cy, 345], lw=GUIDE_LW)
        _latin(ax, 38, cy, label)
        _latin(ax, cx, 362, label)
    _save(fig, out_path)


def generate_figure_7(out_path: Path) -> None:
    """图 7: 非凹性绩效关系的转变导致最佳绩效点的不连续改变 (original p.38)."""
    # Traced from a 220-dpi crop, hence the smaller pixel-to-point factor.
    fig, ax = _canvas(1150, 790, px_pt=0.225)
    t1, t2, t3 = (480, 445), (282, 565), (130, 658)

    _arrow(ax, t1, (482, 72))
    _arrow(ax, t1, (1052, 445))
    _line(ax, [t2[0], t2[0]], [t2[1], 100])
    _line(ax, [t2[0], 1030], [t2[1], t2[1]])
    _line(ax, [t3[0], t3[0]], [t3[1], 60])
    _line(ax, [t3[0], 1045], [t3[1], t3[1]])
    _arrow(ax, t1, (70, 712))

    lw = 1.2
    back = _curve(ax, [(482, 180), (520, 120), (610, 85), (690, 125), (760, 180), (830, 165), (900, 148), (980, 180), (1080, 222)], lw=lw)
    mid = _curve(ax, [(282, 300), (330, 250), (430, 210), (520, 260), (640, 305), (720, 265), (822, 210), (920, 245), (1015, 290)], lw=lw)
    front = _curve(ax, [(130, 430), (170, 385), (250, 352), (380, 400), (480, 445), (560, 438), (610, 410), (700, 320), (808, 267), (900, 300), (975, 380)], lw=lw)

    guides = [
        (back, 610, t1[1], "dashed", "Y₁", 6), (back, 900, t1[1], "dotted", "X₁", 6),
        (mid, 430, t2[1], "dashed", "Y₂", 6), (mid, 822, t2[1], "dashed", "X₂", 24),
        (front, 255, t3[1], "dotted", "Y₃", 6), (front, 808, t3[1], "dashed", "X₃", 6),
    ]
    for curve, x, base, style, label, dx in guides:
        _line(ax, [x, x], [_y_at(curve, x), base], lw=0.8, style=style)
        _latin(ax, x + dx, base + 30, label, size=8.5)

    _zh(ax, 525, 48, "绩效")
    _zh(ax, 1105, 445, "选择")
    _latin(ax, 505, 472, "T₁")
    _latin(ax, 244, 548, "T₂")
    _latin(ax, 44, 672, "T₃")
    _zh(ax, 48, 750, "时间")
    _save(fig, out_path)


def _arrow_to(ax, start, curve, frac, gap=3.0):
    """Arrow from a label to the point at `frac` along `curve`, stopping `gap` px short of the line."""
    tip = curve[int(frac * (len(curve) - 1))]
    d = tip - np.asarray(start, dtype=float)
    _arrow(ax, start, tip - gap * d / np.hypot(*d))


def generate_figure_8(out_path: Path) -> None:
    """图 8: 合作和主动行为 (original p.64)."""
    fig, ax = _canvas(450, 337)
    _axes_l(ax, 62, 12, 285, 410)
    frontier = _bezier((62, 65), (92, 215), (160, 272), (330, 285))
    _line(ax, frontier[:, 0], frontier[:, 1], lw=CURVE_LW)
    _arrow_to(ax, (125, 58), frontier, 0.05)
    _zh(ax, 155, 48, "市场")
    _arrow_to(ax, (180, 160), frontier, 0.28)
    _zh(ax, 212, 152, "边界")
    _arrow_to(ax, (318, 212), frontier, 0.9)
    _zh(ax, 330, 168, "理想的")
    _zh(ax, 330, 192, "等级机构")
    _zh(ax, 28, 150, "主动行为", rotation=90)
    _zh(ax, 210, 310, "合作行为")
    _save(fig, out_path)


def generate_figure_9(out_path: Path) -> None:
    """图 9: 长期关系拓宽了可实现的行为的组合 (original p.115)."""
    fig, ax = _canvas(470, 395)
    _axes_l(ax, 58, 30, 348, 455)
    outer = _bezier((58, 62), (170, 95), (290, 200), (312, 348))
    inner = _bezier((58, 62), (95, 150), (200, 290), (312, 348))
    for c in (outer, inner):
        _line(ax, c[:, 0], c[:, 1], lw=CURVE_LW)
    _arrow_to(ax, (162, 48), inner, 0.14)
    _zh(ax, 192, 28, "市场交易")
    _arrow_to(ax, (262, 156), outer, 0.6)
    _latin(ax, 276, 148, "R")
    _arrow_to(ax, (318, 232), inner, 0.78)
    _zh(ax, 352, 220, "内部供应")
    _zh(ax, 24, 195, "主动行为", rotation=90)
    _zh(ax, 265, 375, "合作行为")
    _save(fig, out_path)


def generate_serre_figure_1(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.8, 4.4), dpi=300)
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-0.22, 2.35)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.plot([-2.1, 2.1], [0, 0], color="#1e293b", lw=1.2)
    for tick in [-2, -1, 0, 1, 2]:
        ax.plot(tick, 0, "o", color="#0f172a", ms=3.2)
        ax.text(tick, -0.13, f"{tick}", ha="center", va="top", size=9.5, color="#0f172a")

    xs_d = np.linspace(-0.5, 0.5, 200)
    ys_d = np.sqrt(1.0 - xs_d**2)
    ax.fill_between(xs_d, ys_d, 2.25, facecolor="#f1f5f9", edgecolor="#334155", hatch="////", lw=0.0, zorder=1)

    y_s3 = np.sqrt(3.0) / 2.0
    for xv in [-1.5, -0.5, 0.5, 1.5]:
        ax.plot([xv, xv], [y_s3, 2.25], color="#0f172a", lw=1.2, zorder=3)
    ax.plot([-0.5, -0.5], [0.2887, y_s3], color="#334155", lw=0.95, zorder=3)
    ax.plot([0.5, 0.5], [0.2887, y_s3], color="#334155", lw=0.95, zorder=3)

    theta_mid = np.linspace(0, np.pi, 300)
    ax.plot(np.cos(theta_mid), np.sin(theta_mid), color="#0f172a", lw=1.2, zorder=3)

    theta_left = np.linspace(0, np.pi * 2.0 / 3.0, 200)
    ax.plot(-1.0 + np.cos(theta_left), np.sin(theta_left), color="#0f172a", lw=1.2, zorder=3)

    theta_right = np.linspace(np.pi / 3.0, np.pi, 200)
    ax.plot(1.0 + np.cos(theta_right), np.sin(theta_right), color="#0f172a", lw=1.2, zorder=3)

    for cx in [-2.0 / 3.0, -1.0 / 3.0, 1.0 / 3.0, 2.0 / 3.0]:
        th = np.linspace(0, np.pi, 150)
        x_arc = cx + (1.0 / 3.0) * np.cos(th)
        y_arc = (1.0 / 3.0) * np.sin(th)
        mask = (x_arc >= -1.0) & (x_arc <= 1.0) & ((x_arc**2 + y_arc**2) <= 1.001)
        ax.plot(x_arc[mask], y_arc[mask], color="#334155", lw=0.95, zorder=3)

    ax.plot(0.0, 1.0, "o", color="#0f172a", ms=3.5, zorder=4)
    ax.text(0.03, 1.06, "i", style="italic", size=9.5, ha="left", va="bottom", color="#0f172a", bbox=dict(fc="white", ec="none", pad=0.5))
    ax.plot(-0.5, y_s3, "o", color="#0f172a", ms=3.5, zorder=4)
    ax.text(-0.62, y_s3 + 0.08, "ρ", style="italic", size=9.5, ha="center", va="bottom", color="#0f172a")

    ax.text(-1.0, 1.48, "$T^{-1}$", ha="center", va="center", size=9.5, weight="bold", color="#0f172a")
    ax.text(0.0, 1.48, "1", ha="center", va="center", size=10, weight="bold", color="#0f172a", bbox=dict(fc="white", ec="none", pad=1.2))
    ax.text(1.0, 1.48, "T", ha="center", va="center", size=9.5, weight="bold", color="#0f172a")

    ax.text(-0.88, 0.72, "$T^{-1}S$", ha="center", va="center", size=8.5, color="#0f172a")
    ax.text(0.0, 0.72, "S", ha="center", va="center", size=9, weight="bold", color="#0f172a")
    ax.text(0.88, 0.72, "TS", ha="center", va="center", size=8.5, color="#0f172a")

    ax.text(-0.63, 0.36, "STS", ha="center", va="center", size=7.2, color="#1e293b")
    ax.text(-0.24, 0.36, "ST", ha="center", va="center", size=7.5, color="#1e293b")
    ax.text(0.24, 0.36, "$ST^{-1}$", ha="center", va="center", size=7.2, color="#1e293b")
    ax.text(0.65, 0.36, "$ST^{-1}S$", ha="center", va="center", size=6.8, color="#1e293b")

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_serre_figure_2(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(4.2, 4.8), dpi=300)
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-0.25, 2.55)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.plot([-1.15, 1.15], [0, 0], color="#1e293b", lw=1.1)
    th_semi = np.linspace(0, np.pi, 300)
    ax.plot(np.cos(th_semi), np.sin(th_semi), color="#475569", lw=1.0)

    y_s3 = np.sqrt(3.0) / 2.0
    ax.plot([-0.5, -0.5], [0, y_s3 - 0.12], "--", color="#475569", lw=0.95)
    ax.plot([0.5, 0.5], [0, y_s3 - 0.12], "--", color="#475569", lw=0.95)

    for xv, lbl in [(-1.0, "-1"), (-0.5, "-1/2"), (0.0, "0"), (0.5, "1/2"), (1.0, "1")]:
        ax.plot(xv, 0, "o", color="#0f172a", ms=2.8)
        ax.text(xv, -0.12, lbl, ha="center", va="top", size=8.5, color="#0f172a")

    y_top = 2.32
    r_eps = 0.11

    ax.plot([-0.5, 0.5], [y_top, y_top], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(-0.08, y_top), xytext=(0.1, y_top), arrowprops=dict(arrowstyle="->", lw=1.3, color="#0f172a"))

    ax.plot([-0.5, -0.5], [y_s3 + r_eps, y_top], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(-0.5, 1.55), xytext=(-0.5, 1.75), arrowprops=dict(arrowstyle="->", lw=1.3, color="#0f172a"))

    ax.plot([0.5, 0.5], [y_s3 + r_eps, y_top], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(0.5, 1.75), xytext=(0.5, 1.55), arrowprops=dict(arrowstyle="->", lw=1.3, color="#0f172a"))

    th_rho_l = np.linspace(np.pi / 2.0, -np.pi / 6.0, 60)
    ax.plot(-0.5 + r_eps * np.cos(th_rho_l), y_s3 + r_eps * np.sin(th_rho_l), color="#0f172a", lw=1.3)

    th_i = np.linspace(np.pi * 0.85, np.pi * 0.15, 80)
    ax.plot(0.0 + r_eps * np.cos(th_i), 1.0 + r_eps * np.sin(th_i), color="#0f172a", lw=1.3)
    ax.plot(0.0, 1.0, "o", color="#0f172a", ms=2.8)

    th_rho_r = np.linspace(np.pi * 7.0 / 6.0, np.pi / 2.0, 60)
    ax.plot(0.5 + r_eps * np.cos(th_rho_r), y_s3 + r_eps * np.sin(th_rho_r), color="#0f172a", lw=1.3)

    th_bc = np.linspace(np.pi * 0.61, np.pi * 0.535, 60)
    ax.plot(np.cos(th_bc), np.sin(th_bc), color="#0f172a", lw=1.4)
    th_cd = np.linspace(np.pi * 0.465, np.pi * 0.39, 60)
    ax.plot(np.cos(th_cd), np.sin(th_cd), color="#0f172a", lw=1.4)

    ax.text(-0.56, y_top, "A", ha="right", va="center", size=9.5, weight="bold", color="#0f172a")
    ax.text(0.56, y_top, "E", ha="left", va="center", size=9.5, weight="bold", color="#0f172a")
    ax.text(-0.56, y_s3 + r_eps + 0.04, "B", ha="right", va="bottom", size=8.5, weight="bold", color="#0f172a")
    ax.text(-0.37, y_s3 - 0.08, "B'", ha="center", va="top", size=8.5, weight="bold", color="#0f172a")
    ax.text(-0.14, 0.90, "C", ha="center", va="top", size=8.5, weight="bold", color="#0f172a")
    ax.text(0.14, 0.90, "C'", ha="center", va="top", size=8.5, weight="bold", color="#0f172a")
    ax.text(0.37, y_s3 - 0.08, "D", ha="center", va="top", size=8.5, weight="bold", color="#0f172a")
    ax.text(0.56, y_s3 + r_eps + 0.04, "D'", ha="left", va="bottom", size=8.5, weight="bold", color="#0f172a")

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_serre_vector_figures(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_serre_figure_1(out_dir / "serre_fig_1_domaine_fondamental.svg")
    generate_serre_figure_2(out_dir / "serre_fig_2_contour.svg")
    print("Generated both Serre publication-grade vector SVGs.")


def generate_all_vector_figures(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_figure_1(out_dir / "fig_1.svg")
    generate_figure_2(out_dir / "fig_2.svg")
    generate_figure_3(out_dir / "fig_3.svg")
    generate_figure_4(out_dir / "fig_4.svg")
    generate_figure_5(out_dir / "fig_5.svg")
    generate_figure_6(out_dir / "fig_6.svg")
    generate_figure_7(out_dir / "fig_7.svg")
    generate_figure_8(out_dir / "fig_8.svg")
    generate_figure_9(out_dir / "fig_9.svg")
    print("Generated all 9 publication-grade vector SVGs.")


if __name__ == "__main__":
    generate_all_vector_figures(Path("output/modern_firm/figures"))
    generate_serre_vector_figures(Path("output/serre_arithmetique/figures"))

