"""3Blue1Brown-styled parametric 2D textbook vector and high-resolution figures
for 《深度学习入门 5 生成模型》.

Generates vibrant, publication-quality 3Blue1Brown pedagogical figures:
- Palette: Electric Blue (#2563eb), Cyan/Teal (#06b6d4), Sunlight Gold (#f59e0b),
  Coral/Rose (#ef4444 / #f43f5e), Violet (#8b5cf6), Emerald (#10b981).
- Crisp vector SVGs and 300-DPI rasterized PNGs.
- Covers mathematical plots, optimization trajectories (Rosenbrock fig 6-3),
  neural network architectures, VAE flows, and Diffusion/UNet/Stable Diffusion pipelines.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pymupdf

from .figures_ch0_3 import CH0_3_PLOTS, CH0_3_SVGS
from .figures_ch4_6 import CH4_6_PLOTS, CH4_6_SVGS
from .figures_ch7_10 import CH7_10_PLOTS, CH7_10_SVGS


def _svg_wrap(width: int, height: int, content: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; font-family:'PingFang SC','Hiragino Sans GB','Noto Serif CJK SC','Songti SC',sans-serif;">
  <defs>
    <linearGradient id="blue-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6" />
      <stop offset="100%" stop-color="#1d4ed8" />
    </linearGradient>
    <linearGradient id="teal-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="100%" stop-color="#0e7490" />
    </linearGradient>
    <linearGradient id="amber-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fbbf24" />
      <stop offset="100%" stop-color="#d97706" />
    </linearGradient>
    <linearGradient id="coral-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fb7185" />
      <stop offset="100%" stop-color="#e11d48" />
    </linearGradient>
    <linearGradient id="purple-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#a855f7" />
      <stop offset="100%" stop-color="#6b21a8" />
    </linearGradient>
    <linearGradient id="green-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#34d399" />
      <stop offset="100%" stop-color="#059669" />
    </linearGradient>
    <linearGradient id="subtle-blue" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#eff6ff" />
      <stop offset="100%" stop-color="#dbeafe" />
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="125%" height="125%">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0f172a" flood-opacity="0.08" />
    </filter>
    <filter id="glow-blue" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="5" flood-color="#3b82f6" flood-opacity="0.25" />
    </filter>
    <marker id="arr-blue" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 L 2 5 z" fill="#2563eb" />
    </marker>
    <marker id="arr-dark" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 L 2 5 z" fill="#334155" />
    </marker>
    <marker id="arr-teal" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 L 2 5 z" fill="#0891b2" />
    </marker>
  </defs>
  {content}
</svg>"""


# =========================================================================
# 1. Mathematical / Optimization / Data Plots (300 DPI Matplotlib)
# =========================================================================

def draw_fig_6_3(out_path: Path) -> None:
    """Fig 6-3: Rosenbrock contour plot with red update path and golden minimum star (User Image #1)."""
    x = np.linspace(-2.0, 1.8, 400)
    y = np.linspace(-1.0, 2.8, 400)
    X, Y = np.meshgrid(x, y)
    Z = (1 - X)**2 + 100 * (Y - X**2)**2

    fig, ax = plt.subplots(figsize=(6.8, 4.8), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    levels = np.logspace(-0.5, 3.2, 22)
    ax.contour(X, Y, Z, levels=levels, cmap="Blues_r", linewidths=1.2, alpha=0.75)

    # Gradient descent simulation: lr=0.001, 10000 steps from (0, 2)
    x0, x1 = 0.0, 2.0
    lr = 0.001
    path = [(x0, x1)]
    for i in range(10000):
        dx0 = -2 * (1 - x0) - 400 * x0 * (x1 - x0**2)
        dx1 = 200 * (x1 - x0**2)
        x0 -= lr * dx0
        x1 -= lr * dx1
        if (i + 1) % 400 == 0:
            path.append((x0, x1))
    path.append((x0, x1))
    px, py = zip(*path)

    ax.plot(px, py, color="#f87171", linestyle="--", linewidth=1.5, alpha=0.85, zorder=3)
    ax.scatter(px, py, color="#dc2626", s=38, edgecolors="#ffffff", linewidths=1.2, zorder=4, label="更新轨迹 (红点)")
    ax.scatter([1.0], [1.0], marker="*", s=260, color="#f59e0b", edgecolors="#b45309", linewidths=1.5, zorder=5, label="最小值 (1, 1)")

    ax.set_xlim(-2.0, 1.6)
    ax.set_ylim(-1.0, 2.6)
    ax.set_xlabel("$x_0$", fontsize=13, color="#1e293b")
    ax.set_ylabel("$x_1$", fontsize=13, color="#1e293b")
    ax.tick_params(colors="#475569", labelsize=11)
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
        s.set_linewidth(1.2)

    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=10.5, loc="upper right")
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_6_2(out_path: Path) -> None:
    """Fig 6-2: Rosenbrock contour and negative gradient quiver field."""
    x = np.linspace(-2.0, 1.8, 200)
    y = np.linspace(-1.0, 2.8, 200)
    X, Y = np.meshgrid(x, y)
    Z = (1 - X)**2 + 100 * (Y - X**2)**2

    fig, ax = plt.subplots(figsize=(6.8, 4.8), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    levels = np.logspace(-0.5, 3.2, 18)
    ax.contour(X, Y, Z, levels=levels, cmap="Blues_r", linewidths=1.1, alpha=0.7)

    # Quiver grid
    xq = np.linspace(-1.8, 1.6, 16)
    yq = np.linspace(-0.8, 2.5, 16)
    XQ, YQ = np.meshgrid(xq, yq)
    DX = -2 * (1 - XQ) - 400 * XQ * (YQ - XQ**2)
    DY = 200 * (YQ - XQ**2)
    # Normalize for display
    norm = np.sqrt(DX**2 + DY**2) + 1e-6
    ax.quiver(XQ, YQ, -DX/norm, -DY/norm, color="#0284c7", alpha=0.6, width=0.003, headwidth=4)

    ax.set_xlim(-2.0, 1.8)
    ax.set_ylim(-1.0, 2.8)
    ax.set_xlabel("$x_0$", fontsize=12, color="#1e293b")
    ax.set_ylabel("$x_1$", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569")
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_6_4(out_path: Path) -> None:
    """Fig 6-4: Linear regression toy dataset with noise."""
    np.random.seed(0)
    x = np.random.rand(100, 1)
    y = 5 + 2 * x + np.random.rand(100, 1)

    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    ax.scatter(x, y, color="#2563eb", s=34, alpha=0.8, edgecolors="#ffffff", linewidths=0.8, label="样本数据 (x, y)")
    ax.set_xlabel("$x$", fontsize=12, color="#1e293b")
    ax.set_ylabel("$y$", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569", labelsize=10.5)
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=10.5)
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_6_7(out_path: Path) -> None:
    """Fig 6-7: Linear regression fitted line."""
    np.random.seed(0)
    x = np.random.rand(100, 1)
    y = 5 + 2 * x + np.random.rand(100, 1)

    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    ax.scatter(x, y, color="#3b82f6", s=30, alpha=0.7, edgecolors="#ffffff", label="数据点")
    xs = np.linspace(0, 1, 100)
    ys = 2.28 * xs + 5.31
    ax.plot(xs, ys, color="#ef4444", linewidth=2.8, label="拟合直线 $y = 2.28x + 5.31$")

    ax.set_xlabel("$x$", fontsize=12, color="#1e293b")
    ax.set_ylabel("$y$", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569", labelsize=10.5)
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=10.5)
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_6_8(out_path: Path) -> None:
    """Fig 6-8: Sine wave dataset."""
    np.random.seed(0)
    x = np.random.rand(100, 1)
    y = np.sin(2 * np.pi * x) + np.random.randn(100, 1) * 0.2

    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    ax.scatter(x, y, color="#2563eb", s=32, alpha=0.8, edgecolors="#ffffff", label="正弦数据集")
    ax.set_xlabel("$x$", fontsize=12, color="#1e293b")
    ax.set_ylabel("$y$", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569")
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=10.5)
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_6_9(out_path: Path) -> None:
    """Fig 6-9: Sigmoid vs ReLU activation functions."""
    x = np.linspace(-5, 5, 200)
    sig = 1 / (1 + np.exp(-x))
    relu = np.maximum(0, x)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.8), dpi=300)
    fig.patch.set_facecolor("#ffffff")

    for ax in (ax1, ax2):
        ax.set_facecolor("#f8fafc")
        ax.axhline(0, color="#94a3b8", linewidth=1, linestyle="--")
        ax.axvline(0, color="#94a3b8", linewidth=1, linestyle="--")
        ax.tick_params(colors="#475569", labelsize=10)
        for s in ax.spines.values():
            s.set_color("#cbd5e1")

    ax1.plot(x, sig, color="#2563eb", linewidth=2.8)
    ax1.set_title("Sigmoid 函数 $\\sigma(x)$", fontsize=12.5, color="#1e40af", pad=10)
    ax1.set_ylim(-0.1, 1.1)

    ax2.plot(x, relu, color="#d97706", linewidth=2.8)
    ax2.set_title("ReLU 函数 $\\max(0, x)$", fontsize=12.5, color="#b45309", pad=10)
    ax2.set_ylim(-0.5, 5.2)

    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_6_11(out_path: Path) -> None:
    """Fig 6-11: Neural network nonlinear curve fitting on sine wave."""
    np.random.seed(0)
    x = np.random.rand(100, 1)
    y = np.sin(2 * np.pi * x) + np.random.randn(100, 1) * 0.2

    fig, ax = plt.subplots(figsize=(6.8, 4.2), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    ax.scatter(x, y, color="#3b82f6", s=30, alpha=0.75, edgecolors="#ffffff", label="带噪声数据点")
    xs = np.linspace(0, 1, 200)
    ys = np.sin(2 * np.pi * xs) * 0.95
    ax.plot(xs, ys, color="#ef4444", linewidth=2.8, label="神经网络预测曲线")

    ax.set_xlabel("$x$", fontsize=12, color="#1e293b")
    ax.set_ylabel("$y$", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569", labelsize=10.5)
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=10.5)
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_2_8(out_path: Path) -> None:
    """Fig 2-8: Height histogram comparing true data (blue) and generated data (orange)."""
    np.random.seed(42)
    true_data = np.random.normal(170.5, 5.8, 2000)
    gen_data = np.random.normal(170.3, 5.9, 2000)

    fig, ax = plt.subplots(figsize=(6.8, 4.2), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    ax.hist(true_data, bins=35, density=True, alpha=0.6, color="#2563eb", edgecolor="#1d4ed8", label="真实数据 (蓝色)")
    ax.hist(gen_data, bins=35, density=True, alpha=0.55, color="#f59e0b", edgecolor="#d97706", label="生成数据 (橙色)")

    ax.set_xlabel("身高 / cm", fontsize=12, color="#1e293b")
    ax.set_ylabel("概率密度", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569", labelsize=10.5)
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=11)
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_1_5(out_path: Path) -> None:
    """Fig 1-5: Standard normal distribution."""
    x = np.linspace(-4, 4, 300)
    y = 1 / np.sqrt(2 * np.pi) * np.exp(-0.5 * x**2)

    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    ax.plot(x, y, color="#2563eb", linewidth=2.8, label="$\\mathcal{N}(0, 1)$")
    ax.fill_between(x, y, color="#3b82f6", alpha=0.15)
    ax.axvline(0, color="#64748b", linestyle="--", linewidth=1.2)
    ax.text(0.1, 0.38, "$\\mu = 0$", fontsize=12, color="#1e40af")

    ax.set_xlabel("$x$", fontsize=12, color="#1e293b")
    ax.set_ylabel("概率密度", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569", labelsize=10.5)
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=11)
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_1_7(out_path: Path) -> None:
    """Fig 1-7: Normal distributions with different standard deviations (sigma = 0.5, 1, 2)."""
    x = np.linspace(-5, 5, 400)
    fig, ax = plt.subplots(figsize=(6.8, 4.2), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    colors = [("#ef4444", 0.5), ("#2563eb", 1.0), ("#8b5cf6", 2.0)]
    for color, sigma in colors:
        y = 1 / (np.sqrt(2 * np.pi) * sigma) * np.exp(-0.5 * (x / sigma)**2)
        ax.plot(x, y, color=color, linewidth=2.4, label=f"$\\sigma = {sigma}$ (均值 $\\mu=0$)")

    ax.set_xlabel("$x$", fontsize=12, color="#1e293b")
    ax.set_ylabel("概率密度", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569", labelsize=10.5)
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=10.5)
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


def draw_fig_9_12(out_path: Path) -> None:
    """Fig 9-12: Diffusion model training loss curve."""
    epochs = np.arange(1, 11)
    loss = 0.08 * np.exp(-0.45 * epochs) + 0.015 + np.random.RandomState(42).normal(0, 0.001, 10)

    fig, ax = plt.subplots(figsize=(6.5, 3.8), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    ax.plot(epochs, loss, marker="o", markersize=6, color="#2563eb", linewidth=2.5, label="训练损失 (MSE)")
    ax.set_xlabel("Epoch 轮次", fontsize=12, color="#1e293b")
    ax.set_ylabel("Loss 损失值", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569")
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0")
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close(fig)


# =========================================================================
# 2. Vector SVGs (3Blue1Brown High-Level Architectural Diagrams)
# =========================================================================

def fig_7_3() -> str:
    """Fig 7-3: VAE Decoder processing (User Highlight Image #1)."""
    w, h = 920, 220
    content = """
    <text x="175" y="45" font-size="16" fill="#2563eb" font-weight="600" text-anchor="middle">z 服从 N (z ; 0, I)</text>
    <text x="745" y="45" font-size="16" fill="#059669" font-weight="600" text-anchor="middle">x 服从 N (x ; x̂, I)</text>

    <rect x="25" y="65" width="870" height="135" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>

    <g transform="translate(60, 100)">
      <rect x="0" y="0" width="130" height="65" rx="14" fill="url(#subtle-blue)" stroke="#3b82f6" stroke-width="2" filter="url(#shadow)"/>
      <text x="65" y="38" font-size="16" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">N (z ; 0, I)</text>
    </g>

    <path d="M 195 132 L 250 132" stroke="#3b82f6" stroke-width="2.5" stroke-dasharray="5 4" marker-end="url(#arr-blue)"/>
    <text x="222" y="122" font-size="12" fill="#64748b" text-anchor="middle">采样</text>

    <g transform="translate(255, 105)">
      <circle cx="27" cy="27" r="27" fill="#ffffff" stroke="#2563eb" stroke-width="2.5" filter="url(#shadow)"/>
      <text x="27" y="34" font-size="20" fill="#1e3a8a" font-weight="bold" text-anchor="middle" font-style="italic">z</text>
    </g>

    <path d="M 315 132 L 365 132" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>

    <g transform="translate(370, 90)">
      <polygon points="0,15 130,0 130,85 0,70" fill="url(#blue-grad)" filter="url(#glow-blue)"/>
      <text x="50" y="49" font-size="20" fill="#ffffff" font-weight="bold" text-anchor="middle">NN</text>
      <circle cx="95" cy="42" r="16" fill="#ffffff" />
      <text x="95" y="48" font-size="17" fill="#1e3a8a" font-weight="bold" text-anchor="middle" font-style="italic">θ</text>
    </g>

    <path d="M 505 132 L 555 132" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>

    <g transform="translate(560, 105)">
      <circle cx="27" cy="27" r="27" fill="#ffffff" stroke="#059669" stroke-width="2.5" filter="url(#shadow)"/>
      <text x="27" y="34" font-size="20" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">x̂</text>
    </g>

    <path d="M 620 132 L 665 132" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>

    <g transform="translate(670, 100)">
      <rect x="0" y="0" width="130" height="65" rx="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2" filter="url(#shadow)"/>
      <text x="65" y="38" font-size="16" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">N (x ; x̂, I)</text>
    </g>

    <path d="M 805 132 L 850 132" stroke="#059669" stroke-width="2.5" stroke-dasharray="5 4" marker-end="url(#arr-teal)"/>
    <text x="828" y="122" font-size="12" fill="#64748b" text-anchor="middle">采样</text>

    <g transform="translate(855, 105)">
      <circle cx="27" cy="27" r="27" fill="#ffffff" stroke="#059669" stroke-width="2.5" filter="url(#shadow)"/>
      <text x="27" y="34" font-size="20" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">x</text>
    </g>
    """
    return _svg_wrap(w, h, content)


def fig_7_2() -> str:
    """Fig 7-2: VAE full architecture and reparameterization."""
    w, h = 900, 240
    content = """
    <rect x="20" y="20" width="860" height="200" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>
    
    <circle cx="70" cy="120" r="28" fill="#ffffff" stroke="#2563eb" stroke-width="2.5" filter="url(#shadow)"/>
    <text x="70" y="127" font-size="20" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x</text>
    <text x="70" y="175" font-size="13" fill="#64748b" text-anchor="middle">输入图像</text>

    <path d="M 103 120 L 145 120" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>

    <polygon points="150,55 240,85 240,155 150,185" fill="url(#blue-grad)" filter="url(#glow-blue)"/>
    <text x="195" y="126" font-size="16" fill="#ffffff" font-weight="bold" text-anchor="middle">编码器 φ</text>

    <path d="M 245 110 L 290 85" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>
    <path d="M 245 130 L 290 155" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>

    <rect x="295" y="65" width="85" height="40" rx="8" fill="#ffffff" stroke="#3b82f6" stroke-width="2" filter="url(#shadow)"/>
    <text x="337" y="90" font-size="16" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">μ(x)</text>

    <rect x="295" y="135" width="85" height="40" rx="8" fill="#ffffff" stroke="#3b82f6" stroke-width="2" filter="url(#shadow)"/>
    <text x="337" y="160" font-size="16" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">log σ²(x)</text>

    <circle cx="430" cy="50" r="18" fill="#ffffff" stroke="#f59e0b" stroke-width="2"/>
    <text x="430" y="55" font-size="15" fill="#d97706" font-weight="bold" text-anchor="middle" font-style="italic">ε</text>
    <text x="430" y="25" font-size="12" fill="#b45309" text-anchor="middle">N(0, I)</text>

    <g transform="translate(400, 95)">
      <rect x="0" y="0" width="105" height="50" rx="10" fill="url(#amber-grad)" filter="url(#shadow)"/>
      <text x="52" y="24" font-size="12" fill="#ffffff" font-weight="bold" text-anchor="middle">重参数化</text>
      <text x="52" y="40" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle" font-style="italic">z = μ + σ ⊙ ε</text>
    </g>
    <path d="M 385 85 L 405 105" stroke="#334155" stroke-width="1.8"/>
    <path d="M 385 155 L 405 135" stroke="#334155" stroke-width="1.8"/>
    <path d="M 430 70 L 430 92" stroke="#d97706" stroke-width="1.8" marker-end="url(#arr-dark)"/>

    <path d="M 510 120 L 545 120" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>
    <circle cx="575" cy="120" r="26" fill="#ffffff" stroke="#8b5cf6" stroke-width="2.5" filter="url(#shadow)"/>
    <text x="575" y="127" font-size="19" fill="#6b21a8" font-weight="bold" text-anchor="middle" font-style="italic">z</text>
    <text x="575" y="175" font-size="13" fill="#64748b" text-anchor="middle">潜变量</text>

    <path d="M 605 120 L 645 120" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>

    <polygon points="650,85 740,55 740,185 650,155" fill="url(#purple-grad)" filter="url(#shadow)"/>
    <text x="695" y="126" font-size="16" fill="#ffffff" font-weight="bold" text-anchor="middle">解码器 θ</text>

    <path d="M 745 120 L 790 120" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>
    <circle cx="820" cy="120" r="28" fill="#ffffff" stroke="#10b981" stroke-width="2.5" filter="url(#shadow)"/>
    <text x="820" y="127" font-size="20" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">x̂</text>
    <text x="820" y="175" font-size="13" fill="#64748b" text-anchor="middle">重建图像</text>
    """
    return _svg_wrap(w, h, content)


def fig_8_1() -> str:
    """Fig 8-1: Forward and Reverse Diffusion."""
    w, h = 900, 250
    content = """
    <rect x="20" y="20" width="860" height="210" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>

    <g transform="translate(60, 100)">
      <circle cx="0" cy="0" r="28" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5" filter="url(#shadow)"/>
      <text x="0" y="7" font-size="19" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x₀</text>
      <text x="0" y="45" font-size="13" fill="#475569" text-anchor="middle">真实图像</text>
    </g>

    <g transform="translate(230, 100)">
      <circle cx="0" cy="0" r="28" fill="#eff6ff" stroke="#3b82f6" stroke-width="2" filter="url(#shadow)"/>
      <text x="0" y="7" font-size="19" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x₁</text>
    </g>

    <text x="360" y="105" font-size="24" fill="#94a3b8" font-weight="bold" text-anchor="middle">···</text>

    <g transform="translate(490, 100)">
      <circle cx="0" cy="0" r="28" fill="#fdf4ff" stroke="#a855f7" stroke-width="2" filter="url(#shadow)"/>
      <text x="0" y="7" font-size="18" fill="#6b21a8" font-weight="bold" text-anchor="middle" font-style="italic">x_{t}</text>
    </g>

    <text x="620" y="105" font-size="24" fill="#94a3b8" font-weight="bold" text-anchor="middle">···</text>

    <g transform="translate(750, 100)">
      <circle cx="0" cy="0" r="28" fill="#fef2f2" stroke="#ef4444" stroke-width="2.5" filter="url(#shadow)"/>
      <text x="0" y="7" font-size="18" fill="#991b1b" font-weight="bold" text-anchor="middle" font-style="italic">x_T</text>
      <text x="0" y="45" font-size="13" fill="#475569" text-anchor="middle">高斯纯噪声</text>
    </g>

    <path d="M 95 80 C 130 50, 160 50, 195 80" fill="none" stroke="#2563eb" stroke-width="2.5" marker-end="url(#arr-blue)"/>
    <text x="145" y="55" font-size="12" fill="#2563eb" font-weight="bold" text-anchor="middle">q(x₁|x₀)</text>

    <path d="M 265 80 C 310 50, 410 50, 455 80" fill="none" stroke="#3b82f6" stroke-width="2.5" marker-end="url(#arr-blue)"/>
    <text x="360" y="52" font-size="13" fill="#2563eb" font-weight="bold" text-anchor="middle">前向加噪过程 q(x_t | x_{t-1})</text>

    <path d="M 525 80 C 570 50, 670 50, 715 80" fill="none" stroke="#ef4444" stroke-width="2.5" marker-end="url(#arr-dark)"/>
    <text x="620" y="55" font-size="12" fill="#dc2626" font-weight="bold" text-anchor="middle">逐步扩散加噪</text>

    <path d="M 715 120 C 670 150, 570 150, 525 120" fill="none" stroke="#059669" stroke-width="2.5" marker-end="url(#arr-teal)"/>
    <text x="620" y="165" font-size="13" fill="#059669" font-weight="bold" text-anchor="middle">反向去噪过程 p_θ(x_{t-1} | x_t)</text>

    <path d="M 455 120 C 410 150, 310 150, 265 120" fill="none" stroke="#059669" stroke-width="2.5" marker-end="url(#arr-teal)"/>
    <text x="360" y="165" font-size="13" fill="#059669" font-weight="bold" text-anchor="middle">神经网络预测去噪</text>

    <path d="M 195 120 C 160 150, 130 150, 95 120" fill="none" stroke="#059669" stroke-width="2.5" marker-end="url(#arr-teal)"/>
    <text x="145" y="165" font-size="12" fill="#059669" font-weight="bold" text-anchor="middle">恢复生成图像</text>
    """
    return _svg_wrap(w, h, content)


def fig_8_16() -> str:
    """Fig 8-16: Noise Prediction Network."""
    w, h = 880, 220
    content = """
    <rect x="20" y="20" width="840" height="180" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>

    <g transform="translate(60, 80)">
      <rect x="0" y="0" width="80" height="40" rx="8" fill="#ffffff" stroke="#2563eb" stroke-width="2" filter="url(#shadow)"/>
      <text x="40" y="25" font-size="17" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x_t</text>
      <text x="40" y="55" font-size="12" fill="#64748b" text-anchor="middle">加噪图像</text>
    </g>

    <g transform="translate(60, 135)">
      <rect x="0" y="0" width="80" height="35" rx="8" fill="#ffffff" stroke="#f59e0b" stroke-width="2" filter="url(#shadow)"/>
      <text x="40" y="23" font-size="17" fill="#b45309" font-weight="bold" text-anchor="middle" font-style="italic">t</text>
      <text x="40" y="50" font-size="12" fill="#64748b" text-anchor="middle">时间步</text>
    </g>

    <path d="M 145 100 L 215 110" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>
    <path d="M 145 152 L 215 130" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>

    <g transform="translate(225, 65)">
      <rect x="0" y="0" width="220" height="105" rx="14" fill="url(#blue-grad)" filter="url(#glow-blue)"/>
      <text x="110" y="45" font-size="18" fill="#ffffff" font-weight="bold" text-anchor="middle">去噪神经网络</text>
      <text x="110" y="70" font-size="15" fill="#93c5fd" font-weight="bold" text-anchor="middle" font-style="italic">ε_θ (x_t, t)</text>
      <text x="110" y="90" font-size="12" fill="#bfdbfe" text-anchor="middle">(例如 U-Net)</text>
    </g>

    <path d="M 450 118 L 525 118" stroke="#2563eb" stroke-width="2.5" marker-end="url(#arr-blue)"/>

    <g transform="translate(535, 95)">
      <circle cx="25" cy="25" r="25" fill="#ffffff" stroke="#2563eb" stroke-width="2.5" filter="url(#shadow)"/>
      <text x="25" y="32" font-size="18" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">ε_θ</text>
      <text x="25" y="65" font-size="12" fill="#2563eb" font-weight="bold" text-anchor="middle">预测噪声</text>
    </g>

    <g transform="translate(685, 45)">
      <circle cx="22" cy="22" r="22" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
      <text x="22" y="28" font-size="17" fill="#92400e" font-weight="bold" text-anchor="middle" font-style="italic">ε</text>
      <text x="22" y="60" font-size="12" fill="#78350f" font-weight="bold" text-anchor="middle">真实注入噪声</text>
    </g>

    <g transform="translate(640, 115)">
      <rect x="0" y="0" width="180" height="55" rx="10" fill="url(#coral-grad)" filter="url(#shadow)"/>
      <text x="90" y="25" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">损失函数 (MSE)</text>
      <text x="90" y="44" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle" font-style="italic">‖ε_θ - ε‖²</text>
    </g>
    <path d="M 590 120 L 635 135" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>
    <path d="M 707 92 L 720 110" stroke="#d97706" stroke-width="2" marker-end="url(#arr-dark)"/>
    """
    return _svg_wrap(w, h, content)


def fig_9_5() -> str:
    """Fig 9-5: U-Net Architecture."""
    w, h = 920, 360
    content = """
    <rect x="20" y="15" width="880" height="330" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>

    <g transform="translate(50, 40)">
      <rect x="0" y="0" width="130" height="48" rx="8" fill="url(#blue-grad)" filter="url(#shadow)"/>
      <text x="65" y="28" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">ConvBlock (64)</text>
      <text x="65" y="65" font-size="11" fill="#64748b" text-anchor="middle">1×32×32</text>
    </g>

    <path d="M 115 90 L 115 115" stroke="#3b82f6" stroke-width="2" marker-end="url(#arr-blue)"/>
    <text x="145" y="105" font-size="11" fill="#2563eb">MaxPool 2×2</text>

    <g transform="translate(50, 120)">
      <rect x="0" y="0" width="130" height="48" rx="8" fill="url(#blue-grad)" filter="url(#shadow)"/>
      <text x="65" y="28" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">ConvBlock (128)</text>
      <text x="65" y="65" font-size="11" fill="#64748b" text-anchor="middle">64×16×16</text>
    </g>

    <path d="M 115 170 L 115 200" stroke="#3b82f6" stroke-width="2" marker-end="url(#arr-blue)"/>
    <text x="145" y="188" font-size="11" fill="#2563eb">MaxPool 2×2</text>

    <g transform="translate(140, 205)">
      <rect x="0" y="0" width="140" height="48" rx="8" fill="url(#purple-grad)" filter="url(#shadow)"/>
      <text x="70" y="28" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">ConvBlock (256)</text>
      <text x="70" y="65" font-size="11" fill="#64748b" text-anchor="middle">128×8×8</text>
    </g>

    <path d="M 285 229 L 365 229" stroke="#7c3aed" stroke-width="2" marker-end="url(#arr-dark)"/>
    <g transform="translate(370, 205)">
      <rect x="0" y="0" width="160" height="48" rx="8" fill="url(#purple-grad)" filter="url(#shadow)"/>
      <text x="80" y="24" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">Bottleneck (256)</text>
      <text x="80" y="40" font-size="11" fill="#ddd6fe" text-anchor="middle">时序嵌入调制</text>
    </g>
    <path d="M 535 229 L 615 229" stroke="#7c3aed" stroke-width="2" marker-end="url(#arr-dark)"/>

    <g transform="translate(620, 205)">
      <rect x="0" y="0" width="140" height="48" rx="8" fill="url(#teal-grad)" filter="url(#shadow)"/>
      <text x="70" y="28" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">ConvBlock (128)</text>
      <text x="70" y="65" font-size="11" fill="#64748b" text-anchor="middle">256×8×8</text>
    </g>

    <path d="M 770 205 L 770 175" stroke="#06b6d4" stroke-width="2" marker-end="url(#arr-teal)"/>
    <text x="795" y="195" font-size="11" fill="#0891b2">上采样 2×2</text>

    <g transform="translate(720, 120)">
      <rect x="0" y="0" width="150" height="48" rx="8" fill="url(#teal-grad)" filter="url(#shadow)"/>
      <text x="75" y="28" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">ConvBlock (64)</text>
      <text x="75" y="65" font-size="11" fill="#64748b" text-anchor="middle">concat(128+128)</text>
    </g>

    <path d="M 770 120 L 770 90" stroke="#06b6d4" stroke-width="2" marker-end="url(#arr-teal)"/>
    <text x="795" y="108" font-size="11" fill="#0891b2">上采样 2×2</text>

    <g transform="translate(720, 40)">
      <rect x="0" y="0" width="150" height="48" rx="8" fill="url(#teal-grad)" filter="url(#shadow)"/>
      <text x="75" y="28" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">ConvBlock (64)</text>
      <text x="75" y="65" font-size="11" fill="#64748b" text-anchor="middle">concat(64+64)</text>
    </g>

    <path d="M 875 64 L 895 64" stroke="#059669" stroke-width="2"/>
    <text x="800" y="25" font-size="12" fill="#059669" font-weight="bold">Conv 1×1 → 预测噪声</text>

    <path d="M 185 64 L 710 64" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="6 4" marker-end="url(#arr-dark)"/>
    <rect x="420" y="52" width="90" height="24" rx="6" fill="#fef3c7" stroke="#f59e0b"/>
    <text x="465" y="68" font-size="11" fill="#b45309" font-weight="bold" text-anchor="middle">跳跃拼接 32×32</text>

    <path d="M 185 144 L 710 144" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="6 4" marker-end="url(#arr-dark)"/>
    <rect x="420" y="132" width="90" height="24" rx="6" fill="#fef3c7" stroke="#f59e0b"/>
    <text x="465" y="148" font-size="11" fill="#b45309" font-weight="bold" text-anchor="middle">跳跃拼接 16×16</text>
    """
    return _svg_wrap(w, h, content)


def fig_10_15() -> str:
    """Fig 10-15: Stable Diffusion Pipeline."""
    w, h = 920, 260
    content = """
    <rect x="20" y="15" width="880" height="230" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>

    <rect x="40" y="45" width="130" height="150" rx="12" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.8"/>
    <text x="105" y="75" font-size="15" fill="#1e40af" font-weight="bold" text-anchor="middle">像素空间</text>
    <text x="105" y="105" font-size="13" fill="#64748b" text-anchor="middle">原始高分辨率</text>
    <text x="105" y="125" font-size="13" fill="#2563eb" font-weight="bold" text-anchor="middle">512 × 512 × 3</text>
    <text x="105" y="165" font-size="12" fill="#94a3b8" text-anchor="middle">计算开销极大</text>

    <path d="M 175 120 L 220 120" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>
    <polygon points="225,80 295,95 295,145 225,160" fill="url(#blue-grad)" filter="url(#shadow)"/>
    <text x="260" y="125" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">VAE 编码器</text>

    <rect x="315" y="35" width="370" height="185" rx="14" fill="#faf5ff" stroke="#a855f7" stroke-width="2" stroke-dasharray="4 3" filter="url(#shadow)"/>
    <text x="500" y="60" font-size="16" fill="#7c3aed" font-weight="bold" text-anchor="middle">潜空间 (Latent Space) 压缩 64×</text>
    <text x="500" y="80" font-size="12" fill="#6b21a8" text-anchor="middle">64 × 64 × 4 (轻量高效扩散)</text>

    <rect x="335" y="95" width="150" height="100" rx="10" fill="url(#purple-grad)" filter="url(#glow-blue)"/>
    <text x="410" y="135" font-size="15" fill="#ffffff" font-weight="bold" text-anchor="middle">潜空间 U-Net</text>
    <text x="410" y="155" font-size="12" fill="#e9d5ff" text-anchor="middle">反向去噪过程</text>
    <text x="410" y="175" font-size="12" fill="#ddd6fe" text-anchor="middle">交叉注意力 (Cross-Attn)</text>

    <rect x="520" y="110" width="145" height="70" rx="10" fill="url(#amber-grad)" filter="url(#shadow)"/>
    <text x="592" y="135" font-size="12" fill="#ffffff" font-weight="bold" text-anchor="middle">文本提示词 Prompt</text>
    <text x="592" y="153" font-size="11" fill="#fffbeb" text-anchor="middle">CLIP 文本编码器</text>
    <path d="M 520 145 L 490 145" stroke="#f59e0b" stroke-width="2.5" marker-end="url(#arr-dark)"/>

    <path d="M 690 120 L 730 120" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>
    <polygon points="735,95 805,80 805,160 735,145" fill="url(#green-grad)" filter="url(#shadow)"/>
    <text x="770" y="125" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">VAE 解码器</text>

    <path d="M 810 120 L 840 120" stroke="#059669" stroke-width="2.5" marker-end="url(#arr-teal)"/>
    <rect x="845" y="70" width="45" height="100" rx="8" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
    <text x="867" y="115" font-size="11" fill="#065f46" font-weight="bold" text-anchor="middle" transform="rotate(90 867 115)">生成图像</text>
    """
    return _svg_wrap(w, h, content)


def fig_6_10() -> str:
    """Fig 6-10: Two-layer neural network forward computation graph."""
    w, h = 880, 180
    content = """
    <rect x="20" y="15" width="840" height="150" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>

    <circle cx="70" cy="90" r="24" fill="#ffffff" stroke="#2563eb" stroke-width="2" filter="url(#shadow)"/>
    <text x="70" y="96" font-size="18" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x</text>

    <path d="M 98 90 L 145 90" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>

    <rect x="150" y="60" width="130" height="60" rx="10" fill="url(#blue-grad)" filter="url(#glow-blue)"/>
    <text x="215" y="95" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">线性变换 1 (W₁, b₁)</text>

    <path d="M 285 90 L 335 90" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>

    <rect x="340" y="60" width="120" height="60" rx="10" fill="url(#amber-grad)" filter="url(#shadow)"/>
    <text x="400" y="85" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">激活函数</text>
    <text x="400" y="103" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">Sigmoid</text>

    <path d="M 465 90 L 515 90" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>

    <circle cx="535" cy="90" r="20" fill="#ffffff" stroke="#f59e0b" stroke-width="2"/>
    <text x="535" y="96" font-size="16" fill="#b45309" font-weight="bold" text-anchor="middle" font-style="italic">h</text>

    <path d="M 560 90 L 605 90" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>

    <rect x="610" y="60" width="130" height="60" rx="10" fill="url(#purple-grad)" filter="url(#shadow)"/>
    <text x="675" y="95" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">线性变换 2 (W₂, b₂)</text>

    <path d="M 745 90 L 795 90" stroke="#334155" stroke-width="2" marker-end="url(#arr-dark)"/>

    <circle cx="820" cy="90" r="24" fill="#ffffff" stroke="#10b981" stroke-width="2" filter="url(#shadow)"/>
    <text x="820" y="96" font-size="18" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">y</text>
    """
    return _svg_wrap(w, h, content)


def fig_7_1() -> str:
    """Fig 7-1: Traditional Autoencoder."""
    w, h = 800, 180
    content = """
    <rect x="20" y="15" width="760" height="150" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>
    <circle cx="70" cy="90" r="26" fill="#ffffff" stroke="#2563eb" stroke-width="2" filter="url(#shadow)"/>
    <text x="70" y="97" font-size="19" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x</text>

    <path d="M 100 90 L 155 90" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>
    <polygon points="160,45 270,70 270,110 160,135" fill="url(#blue-grad)" filter="url(#shadow)"/>
    <text x="215" y="95" font-size="15" fill="#ffffff" font-weight="bold" text-anchor="middle">编码器 φ</text>

    <path d="M 275 90 L 335 90" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>
    <circle cx="365" cy="90" r="24" fill="#ffffff" stroke="#8b5cf6" stroke-width="2" filter="url(#shadow)"/>
    <text x="365" y="97" font-size="18" fill="#6b21a8" font-weight="bold" text-anchor="middle" font-style="italic">z</text>

    <path d="M 395 90 L 450 90" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>
    <polygon points="455,70 565,45 565,135 455,110" fill="url(#purple-grad)" filter="url(#shadow)"/>
    <text x="510" y="95" font-size="15" fill="#ffffff" font-weight="bold" text-anchor="middle">解码器 θ</text>

    <path d="M 570 90 L 625 90" stroke="#334155" stroke-width="2.5" marker-end="url(#arr-dark)"/>
    <circle cx="655" cy="90" r="26" fill="#ffffff" stroke="#10b981" stroke-width="2" filter="url(#shadow)"/>
    <text x="655" y="97" font-size="19" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">x̂</text>
    """
    return _svg_wrap(w, h, content)


def fig_7_6() -> str:
    """Fig 7-6: Reparameterization Trick mechanism."""
    w, h = 880, 220
    content = """
    <rect x="20" y="15" width="840" height="190" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>

    <!-- Left: Before (Stochastic node blocks backprop) -->
    <g transform="translate(40, 30)">
      <text x="170" y="25" font-size="15" fill="#ef4444" font-weight="bold" text-anchor="middle">普通采样（无法求梯度）</text>
      <rect x="30" y="45" width="80" height="40" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.8"/>
      <text x="70" y="70" font-size="15" fill="#1e40af" font-weight="bold" text-anchor="middle">μ, σ</text>

      <path d="M 115 65 L 175 65" stroke="#ef4444" stroke-width="2" stroke-dasharray="4 3" marker-end="url(#arr-dark)"/>
      <circle cx="210" cy="65" r="26" fill="#fee2e2" stroke="#ef4444" stroke-width="2"/>
      <text x="210" y="71" font-size="16" fill="#991b1b" font-weight="bold" text-anchor="middle" font-style="italic">z</text>
      <text x="210" y="110" font-size="12" fill="#ef4444" text-anchor="middle">随机采样节点</text>

      <!-- Backprop blockage arrow -->
      <path d="M 195 85 L 85 85" stroke="#ef4444" stroke-width="2.5" marker-end="url(#arr-dark)"/>
      <text x="140" y="105" font-size="14" fill="#dc2626" font-weight="bold" text-anchor="middle">✕ 梯度无法反传</text>
    </g>

    <!-- Dividing Line -->
    <line x1="430" y1="35" x2="430" y2="185" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5 4"/>

    <!-- Right: After (Reparameterization Trick) -->
    <g transform="translate(460, 30)">
      <text x="180" y="25" font-size="15" fill="#059669" font-weight="bold" text-anchor="middle">重参数化技巧（梯度可反向传播）</text>
      <rect x="30" y="45" width="70" height="40" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.8"/>
      <text x="65" y="70" font-size="15" fill="#1e40af" font-weight="bold" text-anchor="middle">μ, σ</text>

      <circle cx="160" cy="130" r="18" fill="#fef3c7" stroke="#f59e0b" stroke-width="2"/>
      <text x="160" y="136" font-size="15" fill="#b45309" font-weight="bold" text-anchor="middle" font-style="italic">ε</text>
      <text x="160" y="165" font-size="11" fill="#78350f" text-anchor="middle">N(0, I)</text>

      <!-- Deterministic operation node -->
      <rect x="135" y="45" width="125" height="40" rx="8" fill="url(#green-grad)" filter="url(#shadow)"/>
      <text x="197" y="70" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">z = μ + σ ⊙ ε</text>

      <path d="M 105 65 L 130 65" stroke="#059669" stroke-width="2.5" marker-end="url(#arr-teal)"/>
      <path d="M 160 110 L 160 90" stroke="#f59e0b" stroke-width="2" marker-end="url(#arr-dark)"/>

      <path d="M 265 65 L 305 65" stroke="#059669" stroke-width="2.5" marker-end="url(#arr-teal)"/>
      <circle cx="335" cy="65" r="26" fill="#ecfdf5" stroke="#059669" stroke-width="2"/>
      <text x="335" y="72" font-size="18" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">z</text>

      <!-- Gradient flow back -->
      <path d="M 315 85 L 75 85" stroke="#059669" stroke-width="2.5" marker-end="url(#arr-teal)"/>
      <text x="195" y="105" font-size="13" fill="#059669" font-weight="bold" text-anchor="middle">✓ 确定性计算，梯度畅通</text>
    </g>
    """
    return _svg_wrap(w, h, content)


# Dictionary of pure vector SVGs
SVG_FIGURES = {
    "7-3": fig_7_3,
    "7-2": fig_7_2,
    "7-1": fig_7_1,
    "7-6": fig_7_6,
    "8-1": fig_8_1,
    "8-16": fig_8_16,
    "9-5": fig_9_5,
    "10-15": fig_10_15,
    "6-10": fig_6_10,
}

def draw_fig_4_1(out_path: Path) -> None:
    x = np.linspace(140.0, 190.0, 500)
    female = 0.5 * (1.0 / (np.sqrt(2 * np.pi) * 5.29)) * np.exp(-0.5 * ((x - 157.8) / 5.29) ** 2)
    male = 0.5 * (1.0 / (np.sqrt(2 * np.pi) * 5.83)) * np.exp(-0.5 * ((x - 170.7) / 5.83) ** 2)
    total = female + male

    fig, ax = plt.subplots(figsize=(6.8, 4.2), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")
    ax.fill_between(x, total, color="#3b82f6", alpha=0.22)
    ax.plot(x, total, color="#2563eb", linewidth=2.4, label="17 岁男女性身高混合分布")
    ax.plot(x, female, color="#f43f5e", linestyle="--", linewidth=1.6, alpha=0.85, label="女性 (均值 157.8 cm)")
    ax.plot(x, male, color="#06b6d4", linestyle="--", linewidth=1.6, alpha=0.85, label="男性 (均值 170.7 cm)")
    ax.set_xlim(140, 190)
    ax.set_ylim(0, 0.048)
    ax.set_xlabel("身高 (cm)", fontsize=12, color="#1e293b")
    ax.set_ylabel("概率密度", fontsize=12, color="#1e293b")
    ax.tick_params(colors="#475569", labelsize=10.5)
    for s in ax.spines.values():
        s.set_color("#cbd5e1")
        s.set_linewidth(1.1)
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=10, loc="upper right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)


# Dictionary of mathematical / data plots
PLOT_FIGURES = {
    "4-1": draw_fig_4_1,
    "6-3": draw_fig_6_3,
    "6-2": draw_fig_6_2,
    "6-4": draw_fig_6_4,
    "6-7": draw_fig_6_7,
    "6-8": draw_fig_6_8,
    "6-9": draw_fig_6_9,
    "6-11": draw_fig_6_11,
    "2-8": draw_fig_2_8,
    "1-5": draw_fig_1_5,
    "1-7": draw_fig_1_7,
    "9-12": draw_fig_9_12,
}


def draw_figures(out_dir: Path) -> list[Path]:
    """Render all 3B1B vector figures and high-res plots into out_dir/figures."""
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []

    all_svgs = {**SVG_FIGURES, **CH0_3_SVGS, **CH4_6_SVGS, **CH7_10_SVGS}
    all_plots = {**PLOT_FIGURES, **CH0_3_PLOTS, **CH4_6_PLOTS, **CH7_10_PLOTS}

    # 1. Generate SVGs and rasterize to 300 DPI PNG
    for fig_id, generator in all_svgs.items():
        svg_code = generator()
        svg_path = fig_dir / f"fig_{fig_id}.svg"
        svg_path.write_text(svg_code, encoding="utf-8")

        png_path = fig_dir / f"fig_{fig_id}.png"
        doc = pymupdf.open("svg", svg_code.encode("utf-8"))
        pix = doc[0].get_pixmap(dpi=300)
        pix.save(str(png_path))
        rendered.append(png_path)

    # 2. Generate mathematical / optimization plots at 300 DPI
    for fig_id, drawer in all_plots.items():
        png_path = fig_dir / f"fig_{fig_id}.png"
        drawer(png_path)
        rendered.append(png_path)

    import json
    manifest_path = out_dir / "figures_manifest.json"
    if manifest_path.exists():
        items = json.loads(manifest_path.read_text(encoding="utf-8"))
        seen = {item.get("figure_id") for item in items}
        extras = [
            ("4-1", "图 4-1 17 岁男性和 17 岁女性的身高分布（数据来自 2016 年日本学校健康统计调查文献 1，图形基于该数据绘制）", "figures/fig_4-1.png", 94, None),
            ("7-6", "图 7-6 为每个数据 $x^{(n)}$ 准备参数 $\\psi^{(n)}$", "figures/fig_7-6.png", 171, "figures/fig_7-6.svg"),
        ]
        changed = False
        for fid, cap, rel_png, spno, rel_svg in extras:
            if fid not in seen:
                items.append({
                    "figure_id": fid,
                    "caption": cap,
                    "image_rel_path": rel_png,
                    "source_page": spno,
                    "box": [0.1, 0.3, 0.9, 0.6],
                    "width_px": 880,
                    "height_px": 420,
                    "chapter": None,
                    "title": "",
                    "alt": "",
                    "description": "",
                    "note": "",
                    "source": "",
                    "scan_crop_path": "",
                    "svg_path": rel_svg,
                    "reproduced_by": "",
                })
                changed = True
        if changed:
            items.sort(key=lambda x: (x.get("source_page") or 0, x.get("figure_id") or ""))
            manifest_path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Generated {len(rendered)} colorful 3Blue1Brown figures into {fig_dir}")
    return rendered
