"""High-elegance vector diagram generator producing publication-grade SVGs for John Roberts' The Modern Firm."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Configure matplotlib for publication styling
plt.rcParams["font.sans-serif"] = ["Songti SC", "PingFang SC", "Heiti SC", "Hiragino Sans GB", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"] = "none"  # Preserve text in SVG


def generate_figure_1(out_path: Path) -> None:
    """Figure 1: Organization Design Model Flowchart."""
    fig, ax = plt.subplots(figsize=(6.4, 3.2), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.6)
    ax.axis("off")

    box_blue = dict(boxstyle="round,pad=0.42,rounding_size=0.15", fc="#f0f7ff", ec="#0284c7", lw=1.2)
    box_gray = dict(boxstyle="round,pad=0.42,rounding_size=0.15", fc="#f8fafc", ec="#475569", lw=1.2)
    box_amber = dict(boxstyle="round,pad=0.42,rounding_size=0.15", fc="#fffbeb", ec="#d97706", lw=1.2)
    box_green = dict(boxstyle="round,pad=0.42,rounding_size=0.15", fc="#f0fdf4", ec="#16a34a", lw=1.4)

    ax.text(5.0, 4.85, "设计者 (Designer)", ha="center", va="center", size=10.5, weight="bold", color="#0369a1", bbox=box_blue)
    ax.text(2.0, 3.2, "战略 (Strategy)", ha="center", va="center", size=10, weight="bold", color="#1e293b", bbox=box_gray)
    ax.text(5.0, 3.2, "活动 (Activities)", ha="center", va="center", size=10, weight="bold", color="#b45309", bbox=box_amber)
    ax.text(8.0, 3.2, "组织 (Organization)", ha="center", va="center", size=10, weight="bold", color="#1e293b", bbox=box_gray)

    ax.text(2.0, 1.15, "环境 (Environment)", ha="center", va="center", size=10, weight="bold", color="#475569", bbox=box_gray)
    ax.text(6.6, 1.15, "绩效 (Performance)", ha="center", va="center", size=11, weight="bold", color="#15803d", bbox=box_green)

    arrow_subtle = dict(arrowstyle="->", lw=1.2, color="#475569", shrinkA=6, shrinkB=6)

    ax.annotate("", xy=(2.2, 3.65), xytext=(4.4, 4.45), arrowprops=arrow_subtle)
    ax.annotate("", xy=(7.8, 3.65), xytext=(5.6, 4.45), arrowprops=arrow_subtle)

    ax.annotate("", xy=(3.85, 3.2), xytext=(3.15, 3.2), arrowprops=arrow_subtle)
    ax.annotate("", xy=(6.65, 3.2), xytext=(6.15, 3.2), arrowprops=arrow_subtle)

    ax.annotate("", xy=(5.85, 1.62), xytext=(2.6, 2.75), arrowprops=arrow_subtle)
    ax.annotate("", xy=(6.35, 1.62), xytext=(5.0, 2.75), arrowprops=arrow_subtle)
    ax.annotate("", xy=(7.05, 1.62), xytext=(7.7, 2.75), arrowprops=arrow_subtle)

    ax.annotate(
        "",
        xy=(5.25, 1.15),
        xytext=(3.35, 1.15),
        arrowprops=dict(
            arrowstyle="simple,tail_width=1.6,head_width=5.2,head_length=5.2",
            fc="#94a3b8",
            ec="#475569",
            lw=0.8,
        ),
    )

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_figure_2(out_path: Path):
    """Figure 2: 2x2 Matrix of Complementarity (Ford vs Toyota)."""
    fig, ax = plt.subplots(figsize=(5.4, 3.6), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    # Outer and inner grid lines
    ax.plot([3, 9], [2, 2], color="#334155", lw=1.5)
    ax.plot([3, 9], [4.8, 4.8], color="#94a3b8", lw=1.0)
    ax.plot([3, 9], [7.6, 7.6], color="#334155", lw=1.5)

    ax.plot([3, 3], [2, 7.6], color="#334155", lw=1.5)
    ax.plot([6, 6], [2, 7.6], color="#94a3b8", lw=1.0)
    ax.plot([9, 9], [2, 7.6], color="#334155", lw=1.5)

    # Background fills for cells
    rect_tl = plt.Rectangle((3.05, 4.85), 2.9, 2.7, fc="#f8fafc", zorder=0)
    rect_tr = plt.Rectangle((6.05, 4.85), 2.9, 2.7, fc="#eff6ff", zorder=0)
    rect_bl = plt.Rectangle((3.05, 2.05), 2.9, 2.7, fc="#fefce8", zorder=0)
    rect_br = plt.Rectangle((6.05, 2.05), 2.9, 2.7, fc="#f8fafc", zorder=0)

    for r in [rect_tl, rect_tr, rect_bl, rect_br]:
        ax.add_patch(r)

    # Cell texts
    ax.text(4.5, 6.2, "通用汽车", ha="center", va="center", size=11.5, weight="bold", color="#1e293b")
    ax.text(7.5, 6.2, "丰田", ha="center", va="center", size=12, weight="bold", color="#1d4ed8")
    ax.text(7.5, 5.4, "(现代互补模式)", ha="center", va="center", size=8.5, color="#3b82f6")

    ax.text(4.5, 3.4, "福特", ha="center", va="center", size=12, weight="bold", color="#b45309")
    ax.text(4.5, 2.6, "(传统大批量生产)", ha="center", va="center", size=8.5, color="#d97706")

    ax.text(7.5, 3.4, "？", ha="center", va="center", size=14, weight="bold", color="#94a3b8")
    ax.text(7.5, 2.6, "(非匹配选择)", ha="center", va="center", size=8.5, color="#94a3b8")

    # Axis indicators
    ax.text(2.4, 6.2, "高", ha="center", va="center", size=10, color="#475569")
    ax.text(2.4, 3.4, "低", ha="center", va="center", size=10, color="#475569")
    ax.text(1.5, 4.8, "柔性", ha="center", va="center", size=11, weight="bold", color="#1e293b", rotation=90)

    ax.text(4.5, 1.4, "低", ha="center", va="center", size=10, color="#475569")
    ax.text(7.5, 1.4, "高", ha="center", va="center", size=10, color="#475569")
    ax.text(6.0, 0.6, "多样性", ha="center", va="center", size=11, weight="bold", color="#1e293b")

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_figure_3(out_path: Path):
    """Figure 3: Classical Concave Relationship."""
    fig, ax = plt.subplots(figsize=(5.5, 3.4), dpi=300)
    x = np.linspace(0.8, 5.2, 200)
    y = -0.55 * (x - 3.2)**2 + 4.2

    ax.plot(x, y, color="#1e293b", lw=2.0)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 5.0)

    ax.plot(3.2, 4.2, "o", color="#1e293b", ms=5)
    ax.text(3.2, 4.5, "X (最优选择)", ha="center", va="bottom", size=10.5, weight="bold", color="#0f172a")
    ax.plot([3.2, 3.2], [0, 4.2], ":", color="#94a3b8", lw=1.0)

    ax.plot(1.8, 3.12, "o", color="#b45309", ms=5)
    ax.text(1.7, 3.4, "Y (次优点)", ha="right", va="bottom", size=10, weight="bold", color="#b45309")
    ax.plot([1.8, 1.8], [0, 3.12], ":", color="#94a3b8", lw=1.0)

    # Arrow from Y to X indicating improvement
    ax.annotate("局部渐进改进 (kaizen)", xy=(2.9, 4.1), xytext=(1.9, 4.2),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="#0284c7"),
                size=8.5, color="#0284c7")

    ax.set_xlabel("选择水平 (Choice Level)", size=10, labelpad=6, color="#334155")
    ax.set_ylabel("绩效 (Performance)", size=10, labelpad=6, color="#334155")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#64748b")
    ax.spines["bottom"].set_color("#64748b")
    ax.set_xticks([])
    ax.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_figure_4(out_path: Path):
    """Figure 4: Shifted Relationship."""
    fig, ax = plt.subplots(figsize=(5.5, 3.4), dpi=300)
    x = np.linspace(0.8, 5.4, 200)
    y1 = -0.65 * (x - 2.6)**2 + 4.0
    y2 = -0.55 * (x - 4.1)**2 + 4.6

    ax.plot(x, y1, color="#475569", lw=1.8, label="初始环境关系")
    ax.plot(x, y2, color="#0284c7", lw=2.0, linestyle="--", label="新环境关系")
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 5.2)

    ax.plot(2.6, 4.0, "o", color="#475569", ms=5)
    ax.text(2.6, 4.3, "X", ha="center", va="bottom", size=10.5, weight="bold", color="#334155")

    ax.plot(4.1, 4.6, "o", color="#0284c7", ms=5)
    ax.text(4.1, 4.9, "X' (新最佳点)", ha="center", va="bottom", size=10.5, weight="bold", color="#0284c7")

    # Shift arrow
    ax.annotate("", xy=(3.9, 4.5), xytext=(2.8, 4.1),
                arrowprops=dict(arrowstyle="->", lw=1.2, color="#0284c7", linestyle="--"))

    ax.set_xlabel("选择水平 (Choice Level)", size=10, labelpad=6, color="#334155")
    ax.set_ylabel("绩效 (Performance)", size=10, labelpad=6, color="#334155")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#64748b")
    ax.spines["bottom"].set_color("#64748b")
    ax.set_xticks([])
    ax.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_figure_5(out_path: Path):
    """Figure 5: Non-Concave Relationship (Multiple Local Optima)."""
    fig, ax = plt.subplots(figsize=(5.5, 3.4), dpi=300)
    x = np.linspace(0.8, 5.2, 300)
    y = 2.0 + 1.7 * np.sin(x * 1.9 - 0.6) + 0.5 * x

    ax.plot(x, y, color="#1e293b", lw=2.0)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 5.8)

    ax.plot(1.8, 3.9, "o", color="#d97706", ms=5)
    ax.text(1.8, 4.2, "Y (局部最佳)", ha="center", va="bottom", size=9.5, weight="bold", color="#d97706")

    ax.plot(3.1, 2.3, "o", color="#ef4444", ms=5)
    ax.text(3.1, 1.8, "Z (内在不匹配)", ha="center", va="top", size=9.5, weight="bold", color="#ef4444")

    ax.plot(4.8, 5.2, "o", color="#16a34a", ms=5)
    ax.text(4.8, 5.5, "X (全局最佳)", ha="center", va="bottom", size=9.5, weight="bold", color="#16a34a")

    ax.set_xlabel("选择水平 (Choice Level)", size=10, labelpad=6, color="#334155")
    ax.set_ylabel("绩效 (Performance)", size=10, labelpad=6, color="#334155")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#64748b")
    ax.spines["bottom"].set_color("#64748b")
    ax.set_xticks([])
    ax.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_figure_6(out_path: Path):
    """Figure 6: 2D Contour Map with Peaks A and B."""
    fig, ax = plt.subplots(figsize=(5.2, 3.6), dpi=300)
    x = np.linspace(-3, 3, 200)
    y = np.linspace(-3, 3, 200)
    X, Y = np.meshgrid(x, y)
    Z = np.exp(-((X - 1.2)**2 + (Y - 1.2)**2)) + 0.7 * np.exp(-((X + 1.2)**2 + (Y + 1.2)**2))

    cs = ax.contour(X, Y, Z, levels=7, colors="#475569", linewidths=1.1)
    ax.clabel(cs, inline=True, fontsize=7.5, fmt="%.1f")

    ax.plot(1.2, 1.2, "o", color="#16a34a", ms=6)
    ax.text(1.4, 1.2, "A (丰田模式峰值)", size=10, weight="bold", color="#15803d")

    ax.plot(-1.2, -1.2, "o", color="#d97706", ms=6)
    ax.text(-1.0, -1.2, "B (福特模式峰值)", size=10, weight="bold", color="#b45309")

    ax.set_xlabel("选择维度 1 (多样性)", size=10, color="#334155")
    ax.set_ylabel("选择维度 2 (柔性)", size=10, color="#334155")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_figure_7(out_path: Path):
    """Figure 7: Discontinuous Jump in Optimal Choice Over Time."""
    fig, ax = plt.subplots(figsize=(5.5, 3.4), dpi=300)
    t = np.linspace(0, 10, 200)
    p_incumbent = 3.0 + 0.15 * t
    p_modern = 1.2 + 0.45 * t

    ax.plot(t, p_incumbent, color="#94a3b8", lw=1.8, linestyle="--", label="传统模式 (福特式)")
    ax.plot(t, p_modern, color="#0284c7", lw=2.2, label="现代模式 (丰田式)")

    t_cross = (3.0 - 1.2) / (0.45 - 0.15)
    p_cross = 3.0 + 0.15 * t_cross
    ax.plot(t_cross, p_cross, "o", color="#e11d48", ms=6)
    ax.annotate("突破点 / 范式转移", xy=(t_cross, p_cross), xytext=(t_cross - 2.8, p_cross + 0.9),
                arrowprops=dict(arrowstyle="->", lw=1.1, color="#e11d48"),
                size=9.5, weight="bold", color="#e11d48")

    ax.set_xlabel("时间 / 环境变迁", size=10, labelpad=6, color="#334155")
    ax.set_ylabel("实现绩效", size=10, labelpad=6, color="#334155")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#64748b")
    ax.spines["bottom"].set_color("#64748b")
    ax.set_xticks([])
    ax.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_figure_8(out_path: Path):
    """Figure 8: Feasible Frontier of Cooperation and Initiative."""
    fig, ax = plt.subplots(figsize=(5.5, 3.4), dpi=300)
    c = np.linspace(0.5, 4.5, 200)
    i_frontier = 4.5 - 0.3 * c**1.8

    ax.plot(c, i_frontier, color="#1e293b", lw=2.0)
    ax.fill_between(c, 0, i_frontier, color="#f1f5f9", alpha=0.8)

    ax.plot(0.8, 4.25, "o", color="#0284c7", ms=5)
    ax.text(1.0, 4.25, "市场交易 (高主动，低合作)", size=9.5, weight="bold", color="#0369a1")

    ax.plot(4.0, 1.0, "o", color="#b45309", ms=5)
    ax.text(2.4, 0.7, "内部科层 (高合作，低主动)", size=9.5, weight="bold", color="#b45309")

    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)
    ax.set_xlabel("合作行为 (Cooperation)", size=10, labelpad=6, color="#334155")
    ax.set_ylabel("主动行为 (Initiative)", size=10, labelpad=6, color="#334155")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#64748b")
    ax.spines["bottom"].set_color("#64748b")
    ax.set_xticks([])
    ax.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def generate_figure_9(out_path: Path):
    """Figure 9: Expanded Frontier via Relational Contracts."""
    fig, ax = plt.subplots(figsize=(5.5, 3.4), dpi=300)
    c = np.linspace(0.5, 4.5, 200)
    i1 = 4.0 - 0.3 * c**1.8
    i2 = 4.8 - 0.25 * c**1.7

    ax.plot(c, i1, color="#94a3b8", lw=1.6, linestyle="--", label="单期边界 (市场/科层二分)")
    ax.plot(c, i2, color="#0284c7", lw=2.2, label="长期关系边界 (关系型契约)")

    ax.plot(2.5, 3.2, "o", color="#16a34a", ms=6)
    ax.text(2.6, 3.3, "R (关系型契约双高点)", size=10, weight="bold", color="#15803d")

    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5.2)
    ax.set_xlabel("合作行为 (Cooperation)", size=10, labelpad=6, color="#334155")
    ax.set_ylabel("主动行为 (Initiative)", size=10, labelpad=6, color="#334155")
    ax.legend(frameon=False, loc="upper right", fontsize=8.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#64748b")
    ax.spines["bottom"].set_color("#64748b")
    ax.set_xticks([])
    ax.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


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

