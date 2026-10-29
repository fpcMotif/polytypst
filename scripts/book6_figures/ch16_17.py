from __future__ import annotations

from collections.abc import Callable

from scripts.book2_figures.engine import (
    Annotation,
    BarSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    VSpan,
    render_figure_svg,
)


def _fig_16_4(mode: ThemeMode = "mono") -> str:
    ticks = [(0.0, "0.5"), (1.0, "0.75"), (2.0, "中位"), (3.0, "1"), (4.0, "1.5"), (5.0, "2")]
    xs = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    left = [
        ("加拿大", 5, [89.6, 68.7, 63.8, 58.4, 39.1, 30.6]),
        ("法国", 2, [78.9, 64.9, 63.9, 63.2, 58.4, 55.1]),
        ("德国", 4, [53.7, 56.5, 57.3, 58.2, 59.2, 43.7]),
        ("意大利", 3, [82.4, 78.6, 78.6, 78.6, 78.4, 80.1]),
        ("OECD平均", 0, [84.9, 74.7, 72.4, 70.2, 65.3, 60.8]),
    ]
    right = [
        ("日本", 5, [53.0, 43.5, 41.3, 39.0, 33.9, 30.5]),
        ("瑞典", 2, [82.2, 69.7, 66.8, 64.0, 72.5, 73.6]),
        ("英国", 4, [66.1, 48.7, 45.0, 41.4, 29.1, 22.6]),
        ("美国", 3, [67.7, 57.9, 55.2, 52.6, 47.5, 42.7]),
        ("OECD平均", 0, [84.8, 74.4, 72.3, 70.2, 65.1, 60.3]),
    ]
    panels = [
        PanelSpec(
            xlim=(0.0, 5.0),
            ylim=(20.0, 100.0),
            xticks=ticks,
            yticks=[float(v) for v in range(20, 101, 10)],
            xlabel="倍",
            ylabel="%",
            zero_line=False,
            lines=[LineSeries(x=xs, y=ys, label=label, color_idx=idx, width=2.6 if idx == 0 else 2.2) for label, idx, ys in group],
            legend_loc="bottom",
        )
        for group in (left, right)
    ]
    spec = FigureSpec(fig_id="16-4", title="图 16-4 强制参保养老金给付的净养老金替代率", panels=panels, cols=2, width=1000, height=540)
    return render_figure_svg(spec, mode)


def _fig_16_5(mode: ThemeMode = "mono") -> str:
    ages = ["20–24", "25–29", "30–34", "35–39", "40–44", "45–49", "50–54", "55–59", "60–64", "65+"]
    xs = [float(i) for i in range(10)]
    countries = [("日本", 0, "square"), ("韩国", 2, "diamond"), ("法国", 4, "cross"), ("英国", 1, "diamond"), ("美国", 3, "circle")]
    no = None
    panels_data = [
        ("男性 高中以下学历", [
            [82, 100, 116, 121, 129, 140, 148, 144, 100, 82],
            [73, 100, 119, 131, 137, 141, 131, 105, 78, 75],
            [76, 100, 110, 124, 177, 169, 226, 183, no, no],
            [84, 100, 103, 119, 117, 115, 116, 120, 142, 101],
            [86, 100, 107, 118, 122, 117, 113, 118, 119, 102],
        ]),
        ("女性 高中以下学历", [
            [93, 100, 107, 115, 113, 118, 123, 120, 98, 88],
            [94, 100, 97, 104, 107, 111, 109, 95, 80, 88],
            [67, 100, 101, 110, 117, 137, 195, 155, no, no],
            [74, 100, 122, 98, 119, 112, 113, 114, no, no],
            [88, 100, 100, 105, 120, 120, 160, 118, 120, 97],
        ]),
        ("高中学历", [
            [82, 100, 116, 132, 143, 158, 165, 157, 105, 85],
            [69, 100, 121, 139, 149, 150, 143, 110, 87, 91],
            [72, 100, 113, 126, 139, 151, 150, 175, no, no],
            [75, 100, 106, 118, 126, 127, 134, 138, 131, 98],
            [73, 100, 110, 124, 135, 131, 135, 138, 124, 108],
        ]),
        ("高中学历", [
            [88, 100, 107, 111, 112, 115, 116, 114, 98, 96],
            [84, 100, 106, 93, 88, 88, 89, 82, 75, 157],
            [83, 100, 113, 137, 132, 139, 150, 161, no, no],
            [80, 100, 108, 105, 107, 104, 99, 95, no, no],
            [82, 100, 108, 114, 122, 122, 125, 120, 112, 102],
        ]),
        ("高等教育", [
            [77, 100, 132, 158, 176, 193, 217, 207, 150, 147],
            [66, 100, 142, 181, 210, 238, 255, 248, 222, 183],
            [89, 100, 127, 155, 173, 190, 200, 239, no, no],
            [70, 100, 118, 140, 143, 143, 140, 146, 133, 127],
            [69, 100, 117, 137, 159, 144, 141, 150, 145, 122],
        ]),
        ("高等教育", [
            [82, 100, 122, 131, 137, 143, 147, 151, 132, 123],
            [67, 100, 135, 158, 182, 199, 205, 233, 225, 235],
            [78, 100, 126, 149, 141, 157, 185, 172, no, no],
            [75, 100, 121, 123, 129, 127, 124, 138, no, no],
            [74, 100, 117, 117, 121, 119, 121, 129, 117, 89],
        ]),
    ]
    panels = [
        PanelSpec(
            title=title,
            xlim=(-0.5, 9.5),
            ylim=(60.0, 260.0),
            xticks=[(float(i), a) for i, a in enumerate(ages)],
            yticks=[float(v) for v in range(60, 261, 40)],
            ylabel="%",
            zero_line=False,
            lines=[
                LineSeries(x=xs, y=[None if v is None else float(v) for v in ys], label=label, color_idx=idx, marker=marker, width=1.6)
                for (label, idx, marker), ys in zip(countries, rows)
            ],
            legend_loc="bottom" if k >= 4 else "none",
        )
        for k, (title, rows) in enumerate(panels_data)
    ]
    spec = FigureSpec(fig_id="16-5", title="图 16-5 OECD 主要国家按学历划分的年龄工资曲线国际比较", panels=panels, rows=3, cols=2, width=1000, height=1150)
    return render_figure_svg(spec, mode)


ScatterPanel = tuple[str, tuple[float, float], float, str, list[tuple], tuple[float, float, float, float], dict[str, str]]
LABEL_SPOTS: dict[str, tuple[float, float, str]] = {
    "r": (8.0, 0.0, "start"),
    "l": (-8.0, 0.0, "end"),
    "rb": (8.0, 6.0, "start"),
    "lb": (-8.0, 6.0, "end"),
    "b": (0.0, 8.0, "middle"),
    "t": (0.0, -8.0, "middle"),
}


def _scatter_figure(fid: str, title: str, xlim: tuple[float, float], xstep: float, xlabels: tuple[str, str], data: list[ScatterPanel], mode: ThemeMode) -> str:
    panels = []
    for k, (ptitle, ylim, ystep, corr, points, trend, spots) in enumerate(data):
        nx = round((xlim[1] - xlim[0]) / xstep)
        ny = round((ylim[1] - ylim[0]) / ystep)
        x0, y0, x1, y1 = trend
        labels = []
        for name, px, py in points:
            dx, dy, align = LABEL_SPOTS[spots.get(name, "r")]
            labels.append(Annotation(px, py, name, dx=dx, dy=dy, arrow=False, align=align, fontsize=9.0))
        panels.append(
            PanelSpec(
                title=ptitle,
                xlim=xlim,
                ylim=(ylim[0] - 0.06 * (ylim[1] - ylim[0]), ylim[1]),
                xticks=[(xlim[0] + i * xstep, f"{xlim[0] + i * xstep:.1f}") for i in range(nx + 1)],
                yticks=[ylim[0] + i * ystep for i in range(ny + 1)],
                xlabel=xlabels[k // 2],
                zero_line=False,
                lines=[LineSeries(x=[x0, x1], y=[y0, y1], color_idx=5, width=4.0)],
                scatters=[([p[1] for p in points], [p[2] for p in points], [], 0, False)],
                annotations=[
                    Annotation(xlim[0] + 0.02 * (xlim[1] - xlim[0]), ylim[1] - 0.09 * (ylim[1] - ylim[0]), corr, dx=0.0, dy=0.0, arrow=False, align="start", fontsize=10.0),
                    *labels,
                ],
                legend_loc="none",
            )
        )
    spec = FigureSpec(fig_id=fid, title=title, panels=panels, rows=2, cols=2, width=1400, height=1000)
    return render_figure_svg(spec, mode)


def _fig_16_6(mode: ThemeMode = "mono") -> str:
    xlab = "55~59岁／25~29岁男性的工资比率c）"
    data: list[ScatterPanel] = [
        ("50~64岁男性雇员比率（%）a）", (10.0, 80.0), 10.0, "Correlation coefficient: −0.20", [
            ("NOR", 1.241, 65.8), ("SWE", 1.270, 60.2), ("DNK", 1.301, 60.2), ("GBR", 1.160, 53.3), ("CZE", 1.133, 52.9),
            ("AUS", 1.160, 53.3), ("NZD", 1.264, 51.9), ("FIN", 1.270, 46.5), ("CAN", 1.357, 50.9), ("USA", 1.505, 63.4),
            ("CHE", 1.516, 62.0), ("JPN", 1.600, 67.1), ("NLD", 1.535, 54.8), ("LUX", 1.766, 50.5), ("DEU", 1.609, 48.1),
            ("ESP", 1.679, 47.7), ("FRA", 1.655, 44.9), ("IRL", 1.402, 44.7), ("AUT", 1.594, 42.5), ("BFL", 1.607, 41.5),
            ("KOR", 1.314, 39.6), ("HUN", 1.437, 38.2), ("ITA", 1.492, 33.8),
        ], (1.133, 54.0, 1.762, 46.7), {"SWE": "l", "GBR": "t", "CZE": "l", "AUS": "b", "FIN": "lb", "USA": "l", "LUX": "t", "DEU": "l", "AUT": "l", "BFL": "rb", "KOR": "rb", "FRA": "rb"}),
        ("55~59岁男性的5年继续就业率（%）b）", (10.0, 70.0), 10.0, "Correlation coefficient: −0.48**", [
            ("SWE", 1.267, 58.6), ("NOR", 1.242, 56.5), ("IRL", 1.402, 54.5), ("CAN", 1.357, 52.8), ("DNK", 1.302, 49.6),
            ("CHE", 1.514, 49.6), ("AUS", 1.163, 48.2), ("GBR", 1.163, 45.3), ("USA", 1.505, 46.2), ("ESP", 1.675, 47.6),
            ("FIN", 1.272, 43.6), ("ITA", 1.490, 36.7), ("DEU", 1.607, 38.8), ("NDD", 1.536, 32.9), ("HUN", 1.441, 30.0),
            ("KOR", 1.321, 28.1), ("CZE", 1.138, 23.8), ("JPN", 1.593, 21.5), ("BEL", 1.607, 21.5), ("AUT", 1.591, 17.2),
            ("FRA", 1.654, 16.3), ("LUX", 1.762, 18.7),
        ], (1.142, 49.6, 1.762, 24.7), {"NOR": "rb", "CAN": "rb", "DNK": "rb", "AUS": "l", "GBR": "rb", "FIN": "rb", "JPN": "l", "AUT": "l", "LUX": "l"}),
        ("50~64岁男性的录用比率（%）d）", (0.0, 14.0), 2.0, "Correlation coefficient: −0.62***", [
            ("AUS", 1.160, 11.6), ("GBR", 1.160, 10.5), ("USA", 1.502, 10.2), ("CAN", 1.354, 9.6), ("DNK", 1.298, 9.5),
            ("KOR", 1.316, 9.2), ("FIN", 1.270, 8.0), ("ESP", 1.675, 8.2), ("HUN", 1.435, 7.4), ("CZE", 1.133, 6.4),
            ("SWE", 1.264, 6.0), ("CHE", 1.515, 4.3), ("ITA", 1.488, 4.3), ("DEU", 1.604, 5.0), ("FRA", 1.650, 4.5),
            ("NOR", 1.238, 4.5), ("IRL", 1.400, 4.5), ("JPN", 1.597, 4.0), ("AUT", 1.586, 2.9), ("BEL", 1.603, 2.3),
            ("NLD", 1.531, 1.9), ("LUX", 1.759, 1.9),
        ], (1.133, 9.27, 1.752, 2.9), {"DNK": "l", "KOR": "rb", "FIN": "l", "CHE": "t", "ITA": "b", "DEU": "t", "IRL": "b", "AUT": "l", "BEL": "rb", "NLD": "b", "LUX": "b"}),
        ("50~64岁男性的失业率（%）e）", (0.0, 10.0), 1.0, "Correlation coefficient: −0.15", [
            ("FIN", 1.265, 6.8), ("ESP", 1.675, 5.4), ("DNK", 1.297, 4.4), ("DEU", 1.602, 4.3), ("CZE", 1.132, 2.9),
            ("SWE", 1.261, 2.9), ("HUN", 1.438, 2.7), ("ITA", 1.484, 3.2), ("AUT", 1.594, 3.2), ("FRA", 1.653, 3.1),
            ("JPN", 1.594, 2.2), ("GBR", 1.154, 2.4), ("USA", 1.508, 1.8), ("BEL", 1.599, 1.3), ("IRL", 1.374, 1.4),
            ("NOR", 1.237, 1.0), ("LUX", 1.769, 0.8), ("NLD", 1.537, 0.4), ("CHE", 1.508, 0.1),
        ], (1.138, 3.2, 1.755, 2.2), {"CZE": "l", "SWE": "rb", "HUN": "t", "AUT": "t", "LUX": "l", "CHE": "l"}),
    ]
    return _scatter_figure("16-6", "图 16-6 工龄工资和劳动力市场成果", (1.0, 1.8), 0.1, (xlab, xlab), data, mode)


def _fig_16_7(mode: ThemeMode = "mono") -> str:
    data: list[ScatterPanel] = [
        ("50~64岁男性雇员比率（%）a）", (10.0, 80.0), 10.0, "Correlation coefficient: −0.50**", [
            ("USA", 0.731, 63.4), ("CHE", 1.618, 62.6), ("JPN", 1.832, 67.8), ("DNK", 1.832, 61.6), ("NOR", 2.617, 65.0),
            ("SWE", 2.617, 61.6), ("GBR", 1.128, 54.2), ("CAN", 1.128, 50.8), ("AUS", 1.517, 53.4), ("NZL", 1.322, 51.8),
            ("CZE", 1.924, 52.6), ("NLD", 2.331, 54.2), ("SVK", 2.025, 48.2), ("FIN", 2.127, 47.8), ("DEU", 2.534, 47.8),
            ("ESP", 3.107, 47.8), ("IRL", 1.341, 44.4), ("AUT", 2.220, 42.6), ("BEL", 2.534, 41.6), ("FRA", 2.922, 45.0),
            ("MEX", 3.214, 38.6), ("PRT", 3.528, 39.8), ("HUN", 1.725, 38.6), ("KOR", 2.025, 39.0), ("ITA", 2.414, 33.8),
            ("GRC", 2.922, 32.0), ("POL", 2.127, 26.2), ("TUR", 3.542, 13.0),
        ], (0.74, 61.0, 3.477, 35.6), {"CHE": "t", "GBR": "l", "CAN": "lb", "AUS": "t", "NZL": "b", "CZE": "t", "SVK": "l", "IRL": "lb", "AUT": "r", "KOR": "rb", "HUN": "lb", "GRC": "rb", "SWE": "rb", "ESP": "t"}),
        ("55~59岁男性的5年继续就业率（%）b）", (10.0, 70.0), 10.0, "Correlation coefficient: −0.23", [
            ("SWE", 2.622, 58.5), ("NOR", 2.622, 56.1), ("IRL", 1.332, 54.7), ("CAN", 1.100, 53.0), ("CHE", 1.605, 50.4),
            ("DNK", 1.817, 49.6), ("ESP", 3.144, 47.9), ("AUS", 1.503, 46.7), ("USA", 0.717, 46.7), ("GBR", 1.110, 45.5),
            ("PRT", 3.547, 41.5), ("FIN", 2.136, 42.3), ("DEU", 2.502, 37.3), ("ITA", 2.409, 35.0), ("NLD", 2.317, 31.3),
            ("GRC", 2.913, 30.1), ("HUN", 1.697, 28.4), ("KOR", 2.012, 26.4), ("POL", 2.141, 25.3), ("CZE", 1.919, 21.6),
            ("JPN", 1.817, 19.9), ("BEL", 2.516, 19.4), ("AUT", 2.220, 16.5), ("FRA", 2.913, 14.4),
        ], (0.717, 44.5, 3.514, 30.6), {"NOR": "l", "IRL": "t", "CAN": "l", "CHE": "l", "USA": "l", "ITA": "l", "HUN": "l", "KOR": "t", "JPN": "b"}),
        ("50~64岁男性的录用比率（%）d）", (0.0, 14.0), 2.0, "Correlation coefficient: −0.50**", [
            ("USA", 0.694, 10.2), ("GBR", 1.096, 10.5), ("CAN", 1.096, 9.6), ("AUS", 1.494, 11.4), ("DNK", 1.803, 9.3),
            ("POL", 2.104, 10.0), ("KOR", 1.993, 9.2), ("SVK", 1.993, 8.5), ("FIN", 2.104, 7.8), ("ESP", 3.080, 8.1),
            ("HUN", 1.702, 7.4), ("CZE", 1.864, 6.6), ("SWE", 2.580, 5.9), ("DEU", 2.492, 5.1), ("GRC", 2.890, 5.4),
            ("IRL", 1.281, 4.6), ("CHE", 1.577, 4.4), ("PRT", 3.496, 4.6), ("ITA", 2.391, 4.4), ("NOR", 2.603, 4.4),
            ("FRA", 2.890, 4.3), ("JPN", 1.803, 4.0), ("AUT", 2.187, 3.0), ("BEL", 2.492, 2.4), ("NLD", 2.280, 1.9),
        ], (0.708, 9.55, 3.482, 3.56), {"USA": "t", "DNK": "t", "POL": "t", "SVK": "l", "HUN": "l", "CZE": "lb", "SWE": "t", "DEU": "l", "IRL": "l", "CHE": "b", "ITA": "lb", "AUT": "b", "NLD": "b"}),
        ("50~64岁男性的失业率（%）e）", (0.0, 10.0), 1.0, "Correlation coefficient: 0.20", [
            ("POL", 2.074, 9.0), ("FIN", 2.074, 6.7), ("SVK", 2.0, 5.4), ("ESP", 3.067, 5.5), ("DNK", 1.793, 4.4),
            ("DEU", 2.478, 4.2), ("PRT", 3.485, 3.5), ("HUN", 1.678, 2.7), ("CZE", 1.890, 2.9), ("ITA", 2.395, 2.9),
            ("FRA", 2.897, 3.1), ("GRC", 2.897, 2.6), ("SWE", 2.607, 2.6), ("GBR", 1.090, 2.3), ("JPN", 1.779, 2.1),
            ("AUT", 2.193, 2.4), ("USA", 0.690, 1.8), ("IRL", 1.310, 1.3), ("BEL", 2.487, 1.1), ("NOR", 2.589, 0.8),
            ("CHE", 1.600, 0.1), ("NLD", 2.276, 0.3),
        ], (0.713, 2.2, 3.379, 3.9), {"HUN": "t", "CZE": "t", "ITA": "t", "GRC": "rb", "USA": "rb", "BEL": "l", "NOR": "rb"}),
    ]
    return _scatter_figure("16-7", "图 16-7 就业保护规定和劳动力市场成果", (0.0, 4.0), 0.5, ("雇佣保护规制强度c）", "劳动保护规定强度c）"), data, mode)


def _fig_16_9(mode: ThemeMode = "mono") -> str:
    xs = [float(y) for y in range(1968, 2008)]
    men = [
        [1.59, 1.58, 2.14, 2.09, 2.07, 1.6, 2.07, 3.21, 3.17, 3.09, 3.51, 3.72, 3.08, 3.54, 3.82, 4.20, 4.02, 3.86, 4.06, 3.94, 2.99, 2.61, 2.20, 1.75, 1.80, 2.26, 2.46, 2.69, 2.67, 2.61, 3.59, 4.32, 4.46, 4.67, 5.29, 4.92, 4.06, 4.36, 4.05, 3.46],
        [1.4, 1.4, 2.0, 2.0, 2.0, 1.92, 1.95, 3.3, 4.47, 4.62, 5.24, 5.29, 4.58, 5.20, 5.88, 6.49, 6.74, 6.94, 7.11, 7.45, 6.63, 5.78, 5.08, 4.96, 5.04, 6.21, 7.18, 7.63, 8.52, 8.4, 10.02, 10.22, 10.36, 10.19, 9.70, 9.3, 7.02, 6.18, 5.37, 5.1],
        [0.58, 0.57, 0.59, 1.25, 1.2, 1.15, 1.2, 1.75, 2.44, 2.3, 2.25, 2.2, 2.15, 2.55, 2.2, 2.7, 2.15, 2.07, 1.61, 1.59, 1.50, 1.49, 1.40, 1.3, 1.5, 1.58, 1.87, 2.17, 2.07, 2.0, 2.56, 2.88, 3.16, 3.17, 2.93, 3.24, 2.61, 2.55, 2.72, 2.35],
        [1.16, 1.16, 1.16, 1.29, 1.4, 1.35, 1.3, 1.85, 2.14, 2.15, 2.35, 2.15, 2.1, 2.3, 2.4, 2.7, 2.71, 2.67, 2.70, 2.75, 2.44, 2.18, 2.1, 2.0, 2.0, 2.4, 2.78, 3.07, 3.29, 3.40, 4.24, 4.87, 4.99, 5.29, 5.5, 5.5, 4.92, 4.65, 4.35, 3.95],
    ]
    women = [
        [0.89, 0.84, 0.0, 0.84, 0.84, 0.83, 0.84, 1.62, 1.54, 1.51, 1.42, 1.33, 1.33, 1.85, 1.87, 2.33, 2.18, 2.19, 2.17, 2.12, 2.14, 2.07, 1.43, 1.84, 1.32, 1.34, 1.87, 1.69, 2.12, 2.04, 2.76, 2.98, 3.1, 3.21, 3.25, 3.25, 2.8, 2.61, 2.81, 2.17],
        [0.89, 0.84, 0.0, 0.0, 0.0, 1.08, 1.23, 1.21, 1.18, 1.15, 1.12, 1.08, 1.08, 1.06, 1.04, 1.84, 1.77, 1.71, 1.65, 2.41, 1.65, 1.59, 1.53, 1.46, 1.67, 2.0, 2.07, 2.64, 2.65, 2.85, 3.42, 3.97, 4.46, 4.36, 4.27, 4.07, 3.46, 2.86, 3.0, 2.81],
        [0.0] * 13 + [1.06, 0.98, 0.98, 0.93, 0.97, 0.92, 0.88, 0.83, 0.05, 0.05, 0.0, 0.66, 0.63, 0.63, 0.63, 0.64, 0.59, 0.5, 0.57, 1.1, 1.16, 1.1, 1.13, 1.1, 1.13, 1.1, 1.08],
        [1.18, 1.13, 1.12, 1.26, 1.43, 1.25, 1.56, 1.95, 2.0, 2.04, 2.22, 2.13, 2.04, 2.23, 2.48, 2.65, 2.75, 2.74, 2.74, 2.75, 2.51, 2.22, 2.14, 2.19, 2.26, 2.61, 2.96, 3.23, 3.39, 3.61, 4.2, 4.7, 4.75, 5.13, 5.39, 5.37, 4.72, 4.45, 4.19, 3.94],
    ]
    styles = [("55~59岁", 2, "square"), ("60~64岁", 1, None), ("65岁以上", 4, "cross"), ("15岁以上整体", 0, None)]
    panels = [
        PanelSpec(
            title=title,
            xlim=(1967.5, 2007.5),
            ylim=(0.0, 12.0),
            xticks=[float(y) for y in range(1968, 2007, 2)],
            yticks=[float(v) for v in range(0, 13, 2)],
            xlabel="年",
            vspans=[VSpan(*span)],
            lines=[
                LineSeries(x=xs, y=ys, label=label, color_idx=idx, marker=marker, width=2.4 if idx == 0 else 2.0)
                for (label, idx, marker), ys in zip(styles, rows)
            ],
            legend_loc="bottom",
        )
        for title, rows, span in (("男性", men, (1985.45, 1990.45)), ("女性", women, (1985.46, 1990.4)))
    ]
    spec = FigureSpec(fig_id="16-9", title="图 16-9 老年人失业率（1968—2007 年按年龄组和性别划分）", panels=panels, rows=2, width=900, height=1000)
    return render_figure_svg(spec, mode)


def _fig_16_11(mode: ThemeMode = "mono") -> str:
    years = ["1983", "1988", "1992", "1996", "2000", "2004"] * 3
    labels = [("无养老金在职者", 4), ("在职年金领取者", 1), ("无养老金非在职者", 3), ("非在职年金领取者", 0)]
    men = [
        [77.6, 83.5, 88.5, 90, 88.5, 88.5, 27, 28, 32, 31, 29, 24, 5, 5, 6, 5.5, 5, 5.5],
        [8, 5, 5, 3, 2, 2, 46.5, 42, 42, 41, 41, 47, 56, 52, 56.5, 51.5, 49, 48],
        [8, 6.5, 4.5, 5, 8.5, 8, 3, 4, 3, 4, 5, 5, 2, 2, 2, 2, 2, 2],
        [4, 4, 3, 2, 2.5, 1.5, 26.5, 30, 27, 28, 29, 28, 41.5, 46, 42, 46.5, 48.5, 50.5],
    ]
    women = [
        [47.5, 47.5, 51, 54, 58, 60, 16, 17, 20, 21, 23, 19, 4.5, 4.5, 3.5, 5, 4, 4.5],
        [4, 4, 5, 4, 2.5, 3, 24.5, 23.5, 21, 21, 21, 25.5, 28.5, 28, 31, 26.5, 28.5, 28.5],
        [40, 40, 36.5, 35.5, 38, 34.5, 24.5, 25, 25.5, 25.5, 26, 22, 12, 10, 9, 9, 6, 6.5],
        [8.5, 8.5, 7.5, 5.5, 3.5, 4, 37, 37, 36, 34.5, 33.5, 37.5, 61.5, 63.5, 62, 66.5, 69.5, 69.5],
    ]
    w = 0.2
    panels = [
        PanelSpec(
            title=title,
            xlim=(-0.5, 17.5),
            ylim=(0.0, 100.0),
            xticks=[(float(i), y) for i, y in enumerate(years)],
            yticks=[float(v) for v in range(0, 101, 20)],
            vlines=[(5.5, "", "solid"), (11.5, "", "solid")],
            bars=[
                BarSeries(x=[i + (k - 1.5) * w for i in range(18)], y=[float(v) for v in ys], label=label, color_idx=idx, width=w)
                for k, ((label, idx), ys) in enumerate(zip(labels, rows))
            ],
            annotations=[Annotation(2.5 + 6 * g, 92.0, age, dx=0.0, dy=0.0, arrow=False) for g, age in enumerate(["55~59", "60~64", "65~69"])],
            legend_loc="bottom",
            xtick_vertical=True,
        )
        for title, rows in (("男性", men), ("女性", women))
    ]
    spec = FigureSpec(fig_id="16-11", title="图 16-11 老年人就业和养老金的衔接（1983—2004 年按年龄组和性别划分）", panels=panels, cols=2, width=1300, height=620)
    return render_figure_svg(spec, mode)


def _fig_16_12(mode: ThemeMode = "mono") -> str:
    deciles = [(float(i), f"D{i + 1}") for i in range(10)]
    xs = [float(i) for i in range(10)]
    data = [
        (
            "60~64岁",
            [
                [93.4, 79.7, 72.9, 75.5, 68.3, 67.9, 67.6, 69.8, 71.5, 87.5],
                [84.8, 70.0, 60.6, 62.8, 58.6, 63.6, 63.1, 58.4, 66.4, 84.0],
                [79.8, 66.7, 63.6, 63.0, 63.4, 61.3, 64.8, 68.6, 73.4, 89.0],
                [83.1, 71.1, 65.9, 67.6, 65.3, 69.0, 67.8, 75.2, 80.3, 89.8],
                [85.9, 69.0, 68.3, 67.5, 66.3, 65.4, 64.4, 68.9, 73.4, 91.6],
            ],
            [Annotation(2.915, 59.7, "", dx=0.0, dy=-69.0), Annotation(3.21, 71.4, "", dx=0.0, dy=56.0)],
        ),
        (
            "65~69岁",
            [
                [85.0, 72.9, 73.6, 65.5, 64.7, 62.5, 58.6, 66.0, 68.4, 83.5],
                [78.7, 65.2, 59.0, 58.6, 55.5, 52.4, 57.5, 60.5, 60.5, 82.5],
                [73.3, 62.5, 58.0, 52.8, 54.2, 50.5, 57.5, 61.5, 71.3, 92.0],
                [76.5, 61.5, 57.5, 54.7, 56.0, 50.5, 58.5, 60.5, 72.5, 90.5],
                [75.0, 61.0, 58.0, 56.5, 50.3, 58.4, 57.5, 60.8, 74.0, 93.5],
            ],
            [Annotation(1.49, 57.2, "", dx=0.0, dy=-80.0)],
        ),
    ]
    years = ["1982年", "1987年", "1992年", "1997年", "2002年"]
    styles = [5, 2, 4, 3, 0]
    panels = [
        PanelSpec(
            title=f"男性 在职年金领取者 {age} 等价收入中个人劳动性收入比例（按十分位）",
            xlim=(-0.5, 9.5),
            ylim=(30.0, 100.0),
            xticks=deciles,
            yticks=[float(v) for v in range(30, 101, 10)],
            ylabel="%",
            zero_line=False,
            lines=[
                LineSeries(x=xs, y=ys, label=year, color_idx=idx, width=3.0 if idx == 0 else 2.4)
                for year, idx, ys in zip(years, styles, rows)
            ],
            annotations=arrows,
            legend_loc="bottom",
        )
        for age, rows, arrows in data
    ]
    spec = FigureSpec(fig_id="16-12", title="图 16-12 老年人收入中劳动性收入占比", panels=panels, rows=2, width=860, height=980)
    return render_figure_svg(spec, mode)


def _fig_16_13(mode: ThemeMode = "mono") -> str:
    xs = [float(y) for y in range(1974, 2008)]
    series = [
        ("50~54岁", 2, "square", [1.459, 1.455, 1.408, 1.420, 1.427, 1.427, 1.459, 1.473, 1.494, 1.498, 1.534, 1.548, 1.562, 1.579, 1.579, 1.587, 1.587, 1.587, 1.580, 1.600, 1.614, 1.620, 1.629, 1.623, 1.626, 1.627, 1.629, 1.621, 1.614, 1.588, 1.588, 1.613, 1.595, 1.602]),
        ("55~59岁", 1, None, [1.188, 1.212, 1.178, 1.194, 1.225, 1.225, 1.249, 1.265, 1.282, 1.302, 1.332, 1.340, 1.358, 1.374, 1.366, 1.375, 1.385, 1.396, 1.410, 1.435, 1.457, 1.472, 1.486, 1.499, 1.515, 1.529, 1.515, 1.527, 1.537, 1.527, 1.527, 1.536, 1.507, 1.501]),
        ("60~64岁", 4, "cross", [0.990, 1.001, 1.012, 0.990, 0.988, 0.988, 0.999, 1.012, 1.015, 1.037, 1.052, 1.054, 1.096, 1.094, 1.083, 1.062, 1.041, 1.040, 1.056, 1.078, 1.102, 1.121, 1.112, 1.100, 1.112, 1.125, 1.090, 1.136, 1.128, 1.116, 1.138, 1.099, 1.090, 1.110]),
        ("65岁以上", 0, None, [0.843, 0.859, 0.876, 0.902, 0.907, 0.908, 0.924, 0.914, 0.921, 0.942, 0.963, 0.964, 0.965, 0.999, 0.972, 0.953, 0.937, 0.930, 0.931, 0.931, 0.948, 0.974, 0.990, 0.967, 0.950, 0.989, 0.976, 1.043, 1.048, 1.019, 1.038, 0.994, 0.947, 0.986]),
    ]
    panel = PanelSpec(
        xlim=(1973.5, 2007.5),
        ylim=(0.8, 1.8),
        xticks=[float(y) for y in range(1974, 2007, 2)],
        yticks=[(round(0.8 + 0.2 * i, 1), f"{0.8 + 0.2 * i:.1f}") for i in range(6)],
        xlabel="年",
        ylabel="倍",
        zero_line=False,
        vspans=[VSpan(1986.25, 1991.33)],
        lines=[
            LineSeries(x=xs, y=ys, label=label, color_idx=idx, marker=marker, width=2.0)
            for label, idx, marker, ys in series
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="16-13",
        title="图 16-13 工资相对比率（男性 25～29 岁工资 = 1.0，按年龄组划分，1974—2007 年）",
        panels=[panel],
        width=900,
        height=520,
    )
    return render_figure_svg(spec, mode)


def _fig_16_14_15(fid: str, title: str, age: str, emp: list[float], pension: list[float], wage: list[float], span: tuple[float, float], mode: ThemeMode) -> str:
    xs = [float(y) for y in range(1975, 2008)]
    panel = PanelSpec(
        xlim=(1974.5, 2007.5),
        ylim=(0.0, 120.0),
        xticks=[float(y) for y in range(1975, 2006, 3)],
        yticks=[float(v) for v in range(0, 121, 20)],
        xlabel="年",
        ylabel="%",
        vspans=[VSpan(*span)],
        lines=[
            LineSeries(x=xs, y=emp, label=f"男性{age}岁就业率（重新显示）", color_idx=2, marker="diamond", width=2.0),
            LineSeries(x=xs, y=pension, label="厚生年金的养老金替代率（上一年）", color_idx=4, marker="square", width=2.0),
            LineSeries(x=xs, y=wage, label=f"{age}岁工资／25~29岁工资（上一年）", color_idx=0, marker="triangle", width=2.0),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fid, title=title, panels=[panel], width=900, height=540)
    return render_figure_svg(spec, mode)


def _fig_16_14(mode: ThemeMode = "mono") -> str:
    return _fig_16_14_15(
        "16-14",
        "图 16-14 就业率、养老金替代率及工资相对比率（男性 60～64 岁，1974—2007 年）",
        "60~64",
        [77.4, 76.3, 75.1, 74.4, 73.8, 74.1, 72.8, 71.8, 70.2, 68.3, 67.3, 67.4, 66.5, 66.4, 67.4, 69.3, 70.4, 71.9, 71.0, 69.7, 69.3, 68.8, 68.8, 67.5, 66.6, 65.3, 64.9, 64.0, 64.9, 65.9, 66.3, 67.2, 70.8],
        [33.3, 31.7, 31.7, 36.7, 39.5, 40.7, 39.5, 43.5, 45.2, 44.5, 42.8, 42.5, 42.2, 44.5, 43.6, 42.8, 43.6, 42.9, 42.9, 43.0, 42.6, 43.8, 44.7, 44.7, 45.5, 46.0, 48.1, 45.8, 46.5, 47.2, 46.5, 46.5, 45.6],
        [97.2, 99.2, 100.4, 98.2, 98.7, 97.4, 99.8, 100.4, 100.9, 102.6, 104.8, 105.0, 108.5, 108.7, 108.3, 106.1, 103.3, 103.3, 105.1, 107.6, 109.9, 112.1, 111.0, 110.1, 110.8, 112.2, 109.0, 112.6, 112.0, 111.1, 112.4, 109.2, 108.3],
        (1985.95, 1991.27),
        mode,
    )


def _fig_16_15(mode: ThemeMode = "mono") -> str:
    return _fig_16_14_15(
        "16-15",
        "图 16-15 就业率、养老金替代率及工资相对比率（男性 65～69 岁，1974—2007 年）",
        "65~69",
        [62.6, 59.8, 58.1, 58.1, 58.1, 58.0, 57.9, 55.4, 55.3, 53.8, 53.2, 52.9, 52.4, 53.2, 52.9, 53.4, 55.5, 55.2, 54.3, 54.2, 53.2, 52.2, 51.8, 50.9, 50.5, 48.6, 47.7, 46.4, 44.5, 43.3, 44.5, 45.7, 46.8],
        [39.7, 37.0, 37.0, 39.8, 42.0, 43.8, 43.1, 47.4, 49.6, 49.2, 48.0, 47.5, 48.1, 48.4, 49.3, 48.1, 49.4, 49.5, 49.5, 50.9, 50.0, 50.9, 52.0, 52.9, 54.6, 54.1, 54.9, 52.4, 51.6, 53.1, 50.9, 53.4, 55.8],
        [83.1, 85.2, 86.8, 89.8, 90.2, 89.7, 92.3, 89.6, 91.1, 94.1, 96.5, 95.2, 96.2, 100.5, 96.1, 95.0, 92.3, 91.5, 91.9, 92.4, 93.8, 96.7, 97.8, 95.4, 94.2, 97.7, 97.2, 103.2, 103.5, 101.4, 103.6, 99.4, 93.6],
        (1985.0, 1990.45),
        mode,
    )


def _fig_17_1(mode: ThemeMode = "mono") -> str:
    years = ["1982", "1985", "1988", "1991", "1995", "1998", "2001", "2005"]
    xs = [float(i) for i in range(len(years))]
    panel = PanelSpec(
        xlim=(-0.6, len(years) - 0.4),
        ylim=(20.0, 40.0),
        xticks=[(float(i), y) for i, y in enumerate(years)],
        yticks=[float(v) for v in range(20, 41, 2)],
        y2lim=(0.0, 2.0),
        y2ticks=[(0.2 * i, f"{0.2 * i:.1f}") for i in range(11)],
        xlabel="年",
        ylabel="%",
        y2label="1 000日元",
        zero_line=False,
        bars=[
            BarSeries(
                x=xs,
                y=[12.4, 14.2, 18.3, 16.3, 7.0, 9.2, 8.0, 13.3],
                bottom=[20.0] * len(years),
                label="劳动成本总额中教育培训费用所占比例",
                color_idx=1,
                width=0.42,
            )
        ],
        lines=[
            LineSeries(
                x=xs,
                y=[1.31, 1.41, 1.72, 1.73, 1.33, 1.44, 1.26, 1.57],
                label="实际人均教育培训费用（右轴）",
                color_idx=0,
                axis="y2",
                width=2.4,
            )
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="17-1",
        title="图 17-1 劳动成本总额中教育培训费用所占比例以及员工人均实际教育培训费用",
        panels=[panel],
        width=860,
        height=500,
    )
    return render_figure_svg(spec, mode)


def _fig_17_2(mode: ThemeMode = "mono") -> str:
    years = [str(y) for y in range(1986, 2007)]
    ojt = {1987: 73.8, 1993: 74.0, 1994: 54.8, 1997: 29.8, 1998: 40.5, 2000: 41.9, 2001: 45.0, 2002: 42.4, 2003: 46.8, 2004: 49.2, 2005: 54.2, 2006: 45.7}
    either = {1987: 75.6, 1993: 86.4, 1994: 86.4, 1995: 73.5, 1996: 65.9, 1997: 60.4, 1998: 69.4, 2000: 70.7, 2001: 68.6, 2002: 59.4, 2003: 68.6}
    offjt = {1986: 81.4, 1988: 74.7, 1989: 69.9, 1990: 71.2, 1991: 69.9, 1992: 79.0, 1993: 62.8, 1994: 54.8, 1997: 52.3, 2000: 65.9, 2001: 61.3, 2002: 50.2, 2003: 59.4, 2004: 61.4, 2005: 73.8, 2006: 78.5}
    w = 0.28

    def bars(data: dict[int, float], dx: float, label: str, idx: int) -> BarSeries:
        return BarSeries(x=[y - 1986 + dx for y in data], y=list(data.values()), label=label, color_idx=idx, width=w)

    panel = PanelSpec(
        xlim=(-0.6, len(years) - 0.4),
        ylim=(0.0, 100.0),
        xticks=[(float(i), y) for i, y in enumerate(years)],
        yticks=[float(v) for v in range(0, 101, 10)],
        xlabel="年",
        ylabel="%",
        bars=[
            bars(ojt, w, "有计划OJT的实施率", 2),
            bars(either, -w, "OffJT或有计划OJT的实施率", 1),
            bars(offjt, 0.0, "OffJT的实施率", 3),
        ],
        legend_loc="bottom",
        xtick_vertical=True,
    )
    spec = FigureSpec(
        fig_id="17-2",
        title="图 17-2 私营事业所或企业的 Off‑JT 及有计划 OJT 实施率的变化情况",
        panels=[panel],
        width=1320,
        height=600,
    )
    return render_figure_svg(spec, mode)


def _fig_17_3(mode: ThemeMode = "mono") -> str:
    years = [str(y) for y in range(1989, 2007)]
    offjt = {1990: 75.8, 1992: 63.8, 1993: 48.3, 1994: 51.9, 1995: 54.1, 1996: 51.1, 1997: 56.4, 1998: 56.4, 2000: 36.2, 2001: 33.2, 2002: 27.2, 2003: 30.2, 2004: 30.2, 2005: 58.9, 2006: 56.4}
    self_dev = {1989: 55.5, 1990: 51.8, 1991: 64.6, 1993: 54.7, 1994: 57.9, 1995: 56.3, 1996: 55.5, 1997: 60.7, 1998: 57.2, 2000: 37.9, 2001: 34.3, 2002: 36.6, 2003: 37.5, 2004: 46.8, 2005: 46.8, 2006: 57.2}
    w = 0.4
    panel = PanelSpec(
        xlim=(-0.6, len(years) - 0.4),
        ylim=(0.0, 80.0),
        xticks=[(float(i), y) for i, y in enumerate(years)],
        yticks=[float(v) for v in range(0, 81, 10)],
        xlabel="年",
        ylabel="%",
        bars=[
            BarSeries(x=[y - 1989 - w / 2 for y in offjt], y=list(offjt.values()), label="OffJT的实施率", color_idx=2, width=w),
            BarSeries(x=[y - 1989 + w / 2 for y in self_dev], y=list(self_dev.values()), label="自我发展的实施率", color_idx=3, width=w),
        ],
        legend_loc="bottom",
        xtick_vertical=True,
    )
    spec = FigureSpec(
        fig_id="17-3",
        title="图 17-3 私营企业员工（正式员工）中 Off‑JT 及自我发展实施者的比例变化情况",
        panels=[panel],
        width=1160,
        height=560,
    )
    return render_figure_svg(spec, mode)


def _fig_17_4(mode: ThemeMode = "mono") -> str:
    years = ["1992", "1994", "1997", "2000", "2003", "2004", "2005", "2006"]
    xs = [float(i) for i in range(len(years))]
    series = [
        ("建筑", 6, "diamond", [78.7, 58.0, 62.8, 75.6, 56.2, 62.2, 75.7, 80.1]),
        ("制造", 2, "square", [76.6, 60.6, 55.4, 62.6, 59.9, 60.1, 72.3, 74.4]),
        ("运输、通信", 8, "triangle", [73.9, 52.5, 42.9, 55.4, 43.1, 61.0, 70.5, 76.6]),
        ("批发、零售、餐饮", 4, "square", [75.9, 55.4, 46.8, 59.8, 57.9, 61.0, 68.7, 76.4]),
        ("金融、保险、房地产", 1, "square", [96.5, 81.0, 57.1, 75.7, 77.7, 76.9, 77.8, 86.6]),
        ("服务", 0, "circle", [77.8, 73.3, 51.0, 65.6, 62.9, 68.7, 73.5, 78.0]),
    ]
    panel = PanelSpec(
        xlim=(-0.5, len(years) - 0.5),
        ylim=(40.0, 100.0),
        xticks=[(float(i), y) for i, y in enumerate(years)],
        yticks=[float(v) for v in range(40, 101, 10)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=ys, label=label, color_idx=idx, marker=marker, width=2.0)
            for label, idx, marker, ys in series
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="17-4", title="图 17-4 不同行业的事业所（企业）实施 Off‑JT 的比例变化情况", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_17_5(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(2000, 2006)]
    panel = PanelSpec(
        xlim=(1999.5, 2005.5),
        ylim=(0.0, 50.0),
        xticks=years,
        yticks=[float(v) for v in range(0, 51, 5)],
        xlabel="年",
        ylabel="%",
        bars=[
            BarSeries(x=[y + 0.14 for y in years], y=[39.3, 43.1, 36.1, 40.0, 36.3, 46.4], label="重视选拔教育胜过整体水平提升", color_idx=1, width=0.28),
            BarSeries(x=[y - 0.14 for y in years], y=[20.0, 21.3, 18.6, 29.2, 30.8, 30.1], label="个人责任大于企业责任", color_idx=0, width=0.28),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="17-5", title="图 17-5 能力建设方针的变化情况", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_17_6(mode: ThemeMode = "mono") -> str:
    groups = ["正式员工（无职务）", "正式员工（有职务）", "非正式员工"]
    series = [
        ("男性，不满40岁", 2, [29.9, 33.9, 10.2]),
        ("女性，不满40岁", 1, [28.0, 36.3, 22.8]),
        ("男性，40岁以上", 3, [22.0, 36.3, 19.5]),
        ("女性，40岁以上", 0, [20.7, 50.2, 19.5]),
    ]
    w = 0.18
    panel = PanelSpec(
        xlim=(-0.5, 2.5),
        ylim=(0.0, 60.0),
        xticks=[(float(i), g) for i, g in enumerate(groups)],
        yticks=[float(v) for v in range(0, 61, 10)],
        ylabel="%",
        bars=[
            BarSeries(x=[g + (k - 1.5) * w for g in range(3)], y=ys, label=label, color_idx=idx, width=w)
            for k, (label, idx, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="17-6", title="图 17-6 不同就业形态的 Off‑JT 受训率（2004 年）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_17_7(mode: ThemeMode = "mono") -> str:
    groups = ["年轻男性", "中老年男性", "年轻女性", "中老年女性"]
    w = 0.24
    panel = PanelSpec(
        xlim=(-0.5, 3.5),
        ylim=(0.0, 60.0),
        xticks=[(float(i), g) for i, g in enumerate(groups)],
        yticks=[float(v) for v in range(0, 61, 10)],
        ylabel="%",
        bars=[
            BarSeries(x=[i + w / 2 for i in range(4)], y=[50.0, 52.4, 46.0, 46.6], label="正式员工", color_idx=2, width=w),
            BarSeries(x=[i - w / 2 for i in range(4)], y=[25.2, 38.3, 28.1, 24.7], label="非正式员工", color_idx=3, width=w),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="17-7", title="图 17-7 按就业形态划分的自我发展实施率", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


COUNTRY_STYLES = [
    ("Canada", 4, "diamond", 2.0),
    ("Finland", 7, "square", 1.6),
    ("France", 12, "triangle", 1.6),
    ("Germany", 8, "square", 2.0),
    ("Japan", 0, None, 2.8),
    ("Netherlands", 5, "circle", 1.6),
    ("Sweden", 15, "square", 1.6),
    ("United Kingdom", 1, None, 2.0),
    ("United States", 10, None, 2.6),
]
_ = None


def _intl_figure(fid: str, title: str, panels: list[tuple[str, tuple[float, float], dict[str, list[float | None]]]], mode: ThemeMode) -> str:
    xs = [float(y) for y in range(1971, 2008, 3)]
    specs = []
    for k, (ptitle, box, data) in enumerate(panels):
        specs.append(
            PanelSpec(
                title=ptitle,
                xlim=(1970.0, 2008.0),
                ylim=(0.0, 100.0),
                xticks=xs,
                yticks=[float(v) for v in range(0, 101, 10)],
                xlabel="年",
                ylabel="%",
                zero_line=False,
                vspans=[VSpan(*box)],
                lines=[
                    LineSeries(x=xs, y=data[name], label=name, color_idx=idx, marker=marker, width=width)
                    for name, idx, marker, width in COUNTRY_STYLES
                ],
                legend_loc="bottom" if k == len(panels) - 1 else "none",
            )
        )
    spec = FigureSpec(fig_id=fid, title=title, panels=specs, rows=3, cols=1, width=860, height=1250)
    return render_figure_svg(spec, mode)


def _fig_16_1(mode: ThemeMode = "mono") -> str:
    p1 = {
        "Canada": [85.5, 84, 81, 80.5, 75, 72.5, 73.5, 67, 65.5, 65.5, 67, 70, 71.5],
        "Finland": [78.5, 78, 64, 65, 61.5, 59.5, 58, 51.5, 46, 50.5, 61.5, 63.5, 64],
        "France": [81, 80, 80, 78, 66, 63, 62, 61, 59.5, 60, 61, 59, 57.5],
        "Germany": [86.5, 84, 81.5, 80, 73.5, 72, 69, 66.5, 63.5, 64, 66.5, 69.5, 73.5],
        "Japan": [90.5, 90, 88, 88.5, 87.5, 86.5, 88.5, 91, 90.5, 90, 88.5, 88, 88.5],
        "Netherlands": [85, 80, 76.5, 72.5, 61.5, 59, 62, 60.5, 58.5, 62, 71.5, 73.5, 77],
        "Sweden": [89, 88.5, _, _, _, _, 85.5, 82, 76, 77.5, 79, 79, 80.5],
        "United Kingdom": [_, _, _, _, _, 73, 72, 68, 67, 68, 71, 73, 73],
        "United States": [81, 80, 79, 78, 76, 75.5, 76, 74.5, 74.5, 75.5, 75, 74, 75],
    }
    p2 = {
        "Canada": [70, 62, 62.5, 62.5, 55.5, 52, 48.5, 43, 39.5, 41, 42, 48.5, 50],
        "Finland": [64.5, 59, 45, 41.5, 38.5, 33.5, 27.5, 24, 21, 22, 26, 30.5, 38],
        "France": [66, 60, 58, 45, 31.5, 25.5, 22.5, 17.5, 15, 13, 13.5, 13, 15],
        "Germany": [68.5, 62, 45, 42, 35.5, 31.5, 31.5, 27.5, 25.5, 26, 28, 33, 39.5],
        "Japan": [80, 79, 75, 74, 70, 67.5, 67, 70.5, 68.5, 66.5, 63, 64, 69],
        "Netherlands": [72.5, 64, 59, 45.5, 28, 22, 22, 22, 21, 22, 24, 29.5, 38],
        "Sweden": [76, 72.5, _, _, _, _, 61, 58, 50, 49, 54, 60, 63],
        "United Kingdom": [_, _, _, _, _, 48, 47, 46, 44, 44.5, 46.5, 51, 55],
        "United States": [71, 65.5, 60, 59, 54, 52, 52, 50.5, 50.5, 52, 53, 53, 55],
    }
    p3 = {
        "Canada": [19, 17, 15.5, 14.5, 13, 12, 11.5, 11, 10.5, 11, 10, 12.5, 13.5],
        "Finland": [37.5, 34, 22, 17, 13, 10, 9, 8, 7, 7, 8, 9, 10],
        "France": [18, 15, 11, 7.5, 5.5, 5, 4, 4, 3, 2.5, 2, 2, 2],
        "Germany": [16, 12.5, 8.5, 7, 6, 5, 5, 4.5, 4.5, 4.5, 5, 5.5, 6.5],
        "Japan": [47.5, 45, 41.5, 40.5, 38.5, 36.5, 36, 38.5, 37.5, 36, 33, 29.5, 30.5],
        "Netherlands": [17, 13, 10, 8, 6.5, 6, 6, 5.5, 5, 5, 5, 6, 7],
        "Sweden": [26, 21.5, _, _, _, _, 14.5, 14.5, 15, 15, 14, 13.5, 16.5],
        "United Kingdom": [_, _, _, _, _, 7.5, 8, 8.5, 8, 8, 8, 8.5, 10],
        "United States": [25, 22, 20, 19, 17, 16, 16.5, 16, 16.5, 17, 18.5, 20, 21],
    }
    panels = [
        ("55~59岁", (1986.3, 1992.4), p1),
        ("60~64岁", (1986.4, 1992.4), p2),
        ("65岁及以上", (1986.4, 1992.5), p3),
    ]
    return _intl_figure("16-1", "图 16-1 就业率国际比较（男性，1971—2007 年）", panels, mode)


def _fig_16_2(mode: ThemeMode = "mono") -> str:
    p1 = {
        "Canada": [_, _, 36, 38, 37.5, 40, 43.5, 45, 45, 47, 51.5, 57.5, 62],
        "Finland": [57, 58, 52, 54, 58, 53, 57, 55, 51.5, 51.5, 64.5, 68, 71],
        "France": [43.5, 43, 45, 45, 40.5, 40, 41, 41.5, 44, 46, 49, 51, 53],
        "Germany": [35.5, 37, 38, 38, 37, 34.5, 35, 37, 41, 45, 50, 54, 60],
        "Japan": [49.5, 48.5, 49, 49.5, 50.5, 49.5, 52, 55.5, 57, 58.5, 57.5, 59, 61],
        "Netherlands": [17.5, 18, 17, 18.5, 18.5, 17.5, 23.5, 24.5, 28, 32.5, 40, 46.5, 56],
        "Sweden": [53, 58, _, _, _, _, 78, 77.5, 74, 76, 78, 78, 79],
        "United Kingdom": [_, _, _, _, _, 49, 52, 53, 54, 53.5, 57, 61, 65],
        "United States": [47, 46, 46.5, 47, 46.5, 49.5, 53, 55, 57.5, 60, 61, 63, 65],
    }
    p2 = {
        "Canada": [_, _, 24, 25.5, 25, 23, 22.5, 23, 23, 24.5, 27.5, 34, 39.5],
        "Finland": [34, 35.5, 26.5, 26.5, 30.5, 26, 23.5, 21, 17, 17, 24, 28.5, 37],
        "France": [32, 30, 27, 26, 20, 18, 17, 15, 14.5, 14, 14, 14, 16],
        "Germany": [19, 16.5, 12.5, 12, 11.5, 10.5, 10.5, 10, 11, 12, 15, 17.5, 26],
        "Japan": [38.5, 37.5, 38, 38.5, 39.5, 38.5, 39.5, 41, 40, 40.5, 39, 39.5, 42],
        "Netherlands": [12, 11, 10, 10, 9, 5.5, 7, 8, 9, 10, 14, 17, 24.5],
        "Sweden": [34, 35.5, _, _, _, _, 49.5, 51, 45.5, 43.5, 48, 56.5, 58],
        "United Kingdom": [_, _, _, _, _, 19, 23, 23.5, 25.5, 24.5, 27.5, 30, 34.5],
        "United States": [35, 32.5, 31.5, 32, 33, 33, 35.5, 36, 37.5, 39, 42, 44.5, 47.5],
    }
    p3 = {
        "Canada": [5, 4.5, 4.5, 4, 4, 3.5, 3.5, 3, 3, 2.5, 3, 3.5, 4.5],
        "Finland": [11.5, 9, 6, 5.5, 4, 3, 2.5, 2, 2, 2, 2, 2, 2.5],
        "France": [8, 6, 5, 4, 3, 2.5, 2, 1.5, 1.5, 1, 1, 1, 1],
        "Germany": [6, 5, 3.5, 3, 2.5, 2.5, 2, 2, 1.5, 1.5, 1.5, 1.5, 1.5],
        "Japan": [16.5, 15.5, 15, 15, 15.5, 14.5, 15, 16, 14.5, 14, 12.5, 11.5, 11.5],
        "Netherlands": [4, 3, 2.5, 2, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 2, 2.5],
        "Sweden": [9, 8, _, _, _, _, 6, 5, 4.5, 4, 5, 6, 6.5],
        "United Kingdom": [_, _, _, _, _, 3.5, 4.5, 4.5, 4, 4, 4, 4.5, 5],
        "United States": [10, 8, 8, 7.5, 7.5, 7, 8, 8, 8.5, 9, 9.5, 10.5, 11.5],
    }
    panels = [
        ("55~59岁", (1986.4, 1992.5), p1),
        ("60~64岁", (1986.4, 1992.4), p2),
        ("65岁及以上", (1986.3, 1992.3), p3),
    ]
    return _intl_figure("16-2", "图 16-2 就业率国际比较（女性，1971—2007 年）", panels, mode)


def _fig_16_3(mode: ThemeMode = "mono") -> str:
    paths = [
        ("加拿大", 20, "diamond", 1.6, [(9.37, 2.83), (9.59, 3.04), (9.73, 3.25), (9.93, 3.31), (10.03, 3.31), (10.28, 3.53), (10.49, 3.53), (10.69, 3.59), (10.9, 3.59), (11.11, 3.71), (11.29, 3.92), (11.48, 4.19), (11.59, 4.29), (11.69, 4.41), (11.9, 4.29), (12.06, 4.29), (12.24, 4.29), (12.45, 4.19), (12.52, 4.1), (12.63, 3.98), (12.72, 4.04), (12.82, 4.04)]),
        ("法国", 7, "square", 1.4, [(13.9, 7.6), (13.55, 7.75), (13.28, 7.96), (13.0, 8.05), (12.86, 8.45), (13.17, 8.51), (13.39, 8.6), (13.6, 8.72), (13.76, 8.27), (14.04, 9.18), (14.28, 9.42), (14.48, 9.73), (14.66, 10.18), (14.86, 10.33), (15.07, 10.49), (15.28, 10.64), (15.49, 10.64), (15.76, 10.58), (15.87, 10.64), (16.11, 10.49), (16.18, 10.33)]),
        ("德国", 10, "triangle", 1.4, [(14.59, 9.18), (14.8, 10.03), (14.93, 10.18), (15.07, 9.79), (15.28, 9.42), (15.42, 9.88), (15.49, 9.97), (15.58, 9.48), (15.69, 9.73), (15.83, 9.88), (16.11, 10.18), (16.38, 10.49), (16.66, 10.64), (17.21, 10.7), (17.63, 10.79), (18.11, 11.0), (18.59, 11.25)]),
        ("意大利", 5, None, 1.2, [(12.86, 7.3), (12.86, 8.97), (13.21, 9.12), (13.62, 9.18), (14.3, 9.2), (14.66, 8.3), (15.0, 9.2), (15.5, 9.3), (16.1, 9.4), (16.5, 10.6), (16.8, 10.95), (17.35, 11.4), (17.65, 11.35), (18.05, 11.25), (18.2, 11.4)]),
        ("日本", 0, None, 3.0, [(9.06, 2.89), (9.27, 3.22), (9.75, 3.62), (10.44, 4.01), (10.86, 4.14), (11.27, 4.02), (12.38, 4.1), (12.93, 4.04), (13.48, 4.5), (14.04, 4.7), (14.52, 5.15), (15.69, 5.35), (16.25, 5.75), (16.8, 6.1), (17.49, 6.25), (18.18, 6.6), (18.87, 7.0), (19.0, 7.1)]),
        ("瑞典", 15, "circle", 1.4, [(16.27, 6.69), (16.47, 7.14), (16.61, 7.2), (16.8, 7.29), (17.0, 7.05), (17.21, 7.23), (17.28, 7.0), (17.42, 7.23), (17.52, 7.6), (17.63, 7.9), (17.65, 8.2), (17.77, 7.96), (17.79, 7.5), (17.7, 7.14), (17.83, 7.2)]),
        ("英国", 2, "cross", 1.4, [(14.86, 4.26), (14.97, 3.95), (15.07, 4.41), (15.28, 4.26), (15.42, 4.1), (15.56, 3.8), (15.67, 3.65), (15.72, 4.71), (15.8, 5.41), (15.9, 5.23), (15.97, 5.47)]),
        ("美国", 25, "triangle", 1.4, [(11.27, 5.11), (11.37, 5.53), (11.48, 5.71), (11.62, 5.62), (11.76, 5.53), (11.9, 5.41), (12.07, 5.41), (12.24, 5.32), (12.42, 5.32), (12.52, 5.47), (12.63, 5.41), (12.75, 5.53)]),
    ]
    panel = PanelSpec(
        xlim=(8.0, 20.0),
        ylim=(0.0, 12.0),
        xticks=[float(v) for v in range(8, 21, 2)],
        yticks=[(float(v), f"{v:.1f}") for v in range(0, 13, 2)],
        xlabel="%",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=[p[0] for p in pts], y=[p[1] for p in pts], label=label, color_idx=idx, marker=marker, width=width)
            for label, idx, marker, width, pts in paths
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="16-3", title="图 16-3 公共养老金占经济规模比重和老龄化率的关系（1980—2003 年）", panels=[panel], width=900, height=560)
    return render_figure_svg(spec, mode)


DECOMP_TICK_TEXT = ["1976", "1978", "1981", "1982", "1984", "1986", "1988", "1990", "1992", "1994", "1996", "1998", "2000", "2002", "2004", "2006"]


def _decomp_figure(fid: str, title: str, labels: list[str], rows: list[tuple[float, float, float, float, float]], ylim: tuple[float, float], box: tuple[float, float], mode: ThemeMode) -> str:
    xs = [float(y) for y in range(1976, 2008)]
    styles = [(0, False), (1, False), (3, False), (4, False), (2, False)]
    pos = [0.0] * len(xs)
    neg = [0.0] * len(xs)
    bars = []
    for k, (label, (idx, hatch)) in enumerate(zip(labels, styles)):
        ys = [row[k] for row in rows]
        bottoms = []
        for i, v in enumerate(ys):
            if v >= 0:
                bottoms.append(pos[i])
                pos[i] += v
            else:
                bottoms.append(neg[i])
                neg[i] += v
        bars.append(BarSeries(x=xs, y=ys, bottom=bottoms, label=label, color_idx=idx, hatch=hatch, width=0.75, opacity=1.0))
    steps = round((ylim[1] - ylim[0]) / 0.05)
    panel = PanelSpec(
        xlim=(1975.5, 2007.5),
        ylim=ylim,
        xticks=[(1976.0 + 2 * i, text) for i, text in enumerate(DECOMP_TICK_TEXT)],
        yticks=[(round(ylim[0] + 0.05 * i, 2), f"{ylim[0] + 0.05 * i:.2f}") for i in range(steps + 1)],
        xlabel="年",
        zero_line=True,
        vspans=[VSpan(*box)],
        bars=bars,
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fid, title=title, panels=[panel], width=1060, height=580)
    return render_figure_svg(spec, mode)


def _fig_16_16(mode: ThemeMode = "mono") -> str:
    rows = [
        (-0.031, 0.004, 0.037, -0.033, 0.0),
        (-0.032, 0.006, 0.008, -0.025, -0.038),
        (-0.003, 0.007, -0.093, 0.055, -0.003),
        (-0.017, -0.005, -0.035, -0.016, 0.032),
        (-0.002, -0.009, -0.029, 0.022, 0.061),
        (0.020, -0.009, 0.020, -0.039, -0.086),
        (-0.017, 0.005, -0.069, -0.016, 0.051),
        (-0.016, 0.013, -0.027, 0.0, -0.044),
        (-0.016, 0.003, 0.010, -0.044, -0.033),
        (-0.006, 0.009, 0.027, -0.034, -0.041),
        (-0.003, -0.005, 0.0, -0.009, 0.019),
        (0.0, 0.014, 0.010, -0.078, 0.014),
        (-0.018, -0.015, -0.039, 0.002, 0.050),
        (0.018, 0.012, 0.016, 0.015, -0.024),
        (0.018, -0.011, 0.020, 0.043, 0.017),
        (0.018, 0.014, -0.021, 0.044, 0.011),
        (0.003, 0.016, 0.013, 0.010, 0.0),
        (-0.006, 0.009, 0.005, -0.030, -0.004),
        (-0.027, 0.020, 0.0, -0.052, -0.010),
        (-0.027, 0.0, 0.013, -0.049, 0.050),
        (-0.008, 0.016, -0.020, -0.041, 0.017),
        (-0.026, 0.005, -0.009, 0.019, 0.0),
        (0.004, -0.038, 0.0, 0.031, -0.044),
        (-0.042, 0.029, -0.013, -0.011, 0.0),
        (-0.004, -0.004, -0.022, -0.028, -0.005),
        (-0.006, 0.013, -0.036, 0.066, -0.062),
        (0.003, 0.010, 0.045, -0.100, 0.011),
        (0.014, 0.012, -0.012, 0.027, -0.012),
        (0.009, -0.015, -0.016, 0.020, 0.029),
        (0.050, 0.004, 0.017, -0.037, -0.015),
        (0.020, 0.015, 0.0, 0.075, -0.058),
        (0.019, 0.064, 0.0, 0.017, 0.070),
    ]
    labels = ["60~64岁失业率（上一年）", "统一退休制（61岁以上）采用企业比率", "厚生年金的养老金替代率（上一年）", "60~64岁工资／25~29岁工资（上一年）", "其他"]
    return _decomp_figure("16-16", "图 16-16 60～64 岁男性就业率变化因素对各年的贡献", labels, rows, (-0.15, 0.20), (1985.55, 1991.6), mode)


def _fig_16_17(mode: ThemeMode = "mono") -> str:
    rows = [
        (-0.040, -0.005, 0.026, -0.027, -0.067),
        (-0.039, -0.006, 0.003, -0.015, -0.005),
        (0.007, -0.005, -0.040, -0.048, 0.081),
        (0.0, 0.010, -0.024, -0.012, 0.036),
        (0.006, 0.010, -0.020, 0.014, -0.014),
        (0.0, 0.008, 0.018, -0.033, -0.008),
        (-0.027, -0.004, -0.057, 0.025, -0.026),
        (0.029, -0.006, -0.025, -0.010, 0.014),
        (-0.032, 0.0, 0.014, -0.045, -0.004),
        (0.037, 0.0, 0.019, -0.029, -0.028),
        (0.005, 0.005, 0.009, 0.009, -0.068),
        (0.035, -0.010, -0.016, 0.0, -0.030),
        (-0.003, 0.004, 0.0, -0.068, 0.097),
        (0.010, -0.010, -0.010, 0.059, -0.079),
        (0.002, 0.010, 0.018, 0.020, 0.0),
        (0.009, -0.007, -0.020, 0.031, 0.083),
        (0.008, -0.005, 0.007, 0.012, -0.027),
        (-0.019, -0.013, 0.0, -0.007, -0.021),
        (0.0, 0.007, -0.023, 0.0, 0.0),
        (-0.019, -0.009, 0.004, -0.022, 0.017),
        (-0.020, -0.011, -0.010, -0.048, 0.054),
        (0.008, -0.006, 0.0, -0.024, 0.035),
        (0.008, 0.033, -0.007, 0.040, -0.108),
        (-0.036, -0.021, -0.028, 0.028, 0.037),
        (-0.019, 0.010, 0.010, -0.059, 0.0),
        (-0.019, -0.015, -0.013, 0.017, 0.004),
        (0.0, 0.0, 0.040, -0.100, -0.003),
        (0.023, 0.004, 0.0, -0.008, -0.080),
        (-0.027, 0.014, -0.018, 0.043, -0.031),
        (0.050, 0.0, 0.023, -0.029, 0.012),
        (0.008, -0.004, -0.014, 0.062, -0.016),
        (-0.018, -0.040, -0.035, 0.082, 0.067),
    ]
    labels = ["65岁以上失业率（上一年）", "统一退休制（65岁以上）采用企业比率", "厚生年仅的养老金替代率（上一年）", "65~69岁工资／25~29岁工资（上一年）", "其他"]
    return _decomp_figure("16-17", "图 16-17 65～69 岁男性就业率变化因素对各年的贡献", labels, rows, (-0.20, 0.20), (1985.6, 1991.6), mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "16-1": _fig_16_1,
        "16-2": _fig_16_2,
        "16-3": _fig_16_3,
        "16-4": _fig_16_4,
        "16-5": _fig_16_5,
        "16-6": _fig_16_6,
        "16-7": _fig_16_7,
        "16-9": _fig_16_9,
        "16-11": _fig_16_11,
        "16-12": _fig_16_12,
        "16-13": _fig_16_13,
        "16-14": _fig_16_14,
        "16-15": _fig_16_15,
        "16-16": _fig_16_16,
        "16-17": _fig_16_17,
        "17-1": _fig_17_1,
        "17-2": _fig_17_2,
        "17-3": _fig_17_3,
        "17-4": _fig_17_4,
        "17-5": _fig_17_5,
        "17-6": _fig_17_6,
        "17-7": _fig_17_7,
    }
