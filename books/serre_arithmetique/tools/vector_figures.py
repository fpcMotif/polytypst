"""Publication-grade vector SVGs for Serre's Cours d'arithmétique: the fundamental domain and the contour."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from polytypst.paths import OUTPUT

# Configure matplotlib for publication styling
plt.rcParams["font.sans-serif"] = ["Songti SC", "PingFang SC", "Heiti SC", "Hiragino Sans GB", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"] = "none"  # Preserve text in SVG


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
    ax.text(0.03, 1.06, "i", style="italic", size=9.5, ha="left", va="bottom", color="#0f172a", bbox={"fc": "white", "ec": "none", "pad": 0.5})
    ax.plot(-0.5, y_s3, "o", color="#0f172a", ms=3.5, zorder=4)
    ax.text(-0.62, y_s3 + 0.08, "ρ", style="italic", size=9.5, ha="center", va="bottom", color="#0f172a")

    ax.text(-1.0, 1.48, "$T^{-1}$", ha="center", va="center", size=9.5, weight="bold", color="#0f172a")
    ax.text(0.0, 1.48, "1", ha="center", va="center", size=10, weight="bold", color="#0f172a", bbox={"fc": "white", "ec": "none", "pad": 1.2})
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
    ax.annotate("", xy=(-0.08, y_top), xytext=(0.1, y_top), arrowprops={"arrowstyle": "->", "lw": 1.3, "color": "#0f172a"})

    ax.plot([-0.5, -0.5], [y_s3 + r_eps, y_top], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(-0.5, 1.55), xytext=(-0.5, 1.75), arrowprops={"arrowstyle": "->", "lw": 1.3, "color": "#0f172a"})

    ax.plot([0.5, 0.5], [y_s3 + r_eps, y_top], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(0.5, 1.75), xytext=(0.5, 1.55), arrowprops={"arrowstyle": "->", "lw": 1.3, "color": "#0f172a"})

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



if __name__ == "__main__":
    generate_serre_vector_figures(OUTPUT / "serre_arithmetique" / "figures")
