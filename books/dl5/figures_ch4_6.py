"""3Blue1Brown figures for Chapters 4 to 6 of 《深度学习入门 5 生成模型》."""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .figures_ch0_3 import _svg_wrap

DATA_PATH = Path(__file__).parent / "old_faithful.npy"


def draw_fig_4_4(png_path: Path) -> None:
    """Fig 4-4: Old Faithful Geyser Scatter Plot."""
    fig, ax = plt.subplots(figsize=(6.8, 5.0), dpi=300)
    
    xs = np.load(DATA_PATH)

    ax.scatter(xs[:, 0], xs[:, 1], color="#2563eb", s=48, alpha=0.85, edgecolors="#1e293b", linewidth=0.8, zorder=4)

    ax.set_xlabel("喷发持续时间 / 分钟", fontsize=11.5, color="#334155")
    ax.set_ylabel("喷发间隔时间 / 分钟", fontsize=11.5, color="#334155")
    ax.set_xlim(1.2, 5.5)
    ax.set_ylim(40, 100)
    ax.tick_params(colors="#475569", labelsize=10.5)

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_4_6(png_path: Path) -> None:
    """Fig 4-6: GMM sampled scatter plot showing 2 clusters."""
    fig, ax = plt.subplots(figsize=(6.8, 5.0), dpi=300)
    np.random.seed(42)
    n1, n2 = 95, 177
    c1 = np.random.multivariate_normal([2.0, 54.0], [[0.07, 0.44], [0.44, 33.7]], n1)
    c2 = np.random.multivariate_normal([4.3, 80.0], [[0.17, 0.94], [0.94, 36.0]], n2)

    ax.scatter(c1[:, 0], c1[:, 1], color="#2563eb", s=46, alpha=0.85, edgecolors="#1e40af", linewidth=0.8, label="簇 1 (短期喷发)")
    ax.scatter(c2[:, 0], c2[:, 1], color="#f59e0b", s=46, alpha=0.85, edgecolors="#b45309", linewidth=0.8, label="簇 2 (长期喷发)")

    ax.set_title("由 GMM 生成的样本散点图", fontsize=13.5, fontweight="bold", color="#1e293b", pad=14)
    ax.set_xlabel("喷发持续时间 / 分钟", fontsize=11.5, color="#334155")
    ax.set_ylabel("喷发间隔时间 / 分钟", fontsize=11.5, color="#334155")
    ax.set_xlim(1.2, 5.5)
    ax.set_ylim(40, 100)
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=10.5)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.tick_params(colors="#475569")

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_4_9(png_path: Path) -> None:
    """Fig 4-9: GMM 2D heatmap (left) and contour plot (right) on Old Faithful data."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.5), dpi=300)

    x = np.linspace(1.2, 5.5, 150)
    y = np.linspace(40, 100, 150)
    X, Y = np.meshgrid(x, y)
    pos = np.dstack((X, Y))

    # GMM parameters: phi1=0.35, mu1=[2.0, 54.5], cov1=[[0.07, 0.44], [0.44, 33.7]]
    #                 phi2=0.65, mu2=[4.3, 80.0], cov2=[[0.17, 0.94], [0.94, 36.0]]
    def gmm_pdf(coords):
        mu1, cov1 = np.array([2.0, 54.5]), np.array([[0.07, 0.44], [0.44, 33.7]])
        mu2, cov2 = np.array([4.3, 80.0]), np.array([[0.17, 0.94], [0.94, 36.0]])
        
        diff1 = coords - mu1
        inv1 = np.linalg.inv(cov1)
        det1 = np.linalg.det(cov1)
        z1 = np.exp(-0.5 * np.einsum("...k,kl,...l->...", diff1, inv1, diff1)) / (2 * np.pi * np.sqrt(det1))

        diff2 = coords - mu2
        inv2 = np.linalg.inv(cov2)
        det2 = np.linalg.det(cov2)
        z2 = np.exp(-0.5 * np.einsum("...k,kl,...l->...", diff2, inv2, diff2)) / (2 * np.pi * np.sqrt(det2))

        return 0.35 * z1 + 0.65 * z2

    Z = gmm_pdf(pos)

    im = ax1.imshow(Z, extent=[1.2, 5.5, 40, 100], origin="lower", aspect="auto", cmap="viridis")
    ax1.set_title("GMM 概率密度热力图", fontsize=12.5, fontweight="bold", color="#1e293b", pad=12)
    ax1.set_xlabel("喷发持续时间 (min)", fontsize=10.5, color="#334155")
    ax1.set_ylabel("喷发间隔时间 (min)", fontsize=10.5, color="#334155")
    fig.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)

    if DATA_PATH.exists():
        xs = np.load(DATA_PATH)
        ax2.scatter(xs[:, 0], xs[:, 1], color="#334155", s=18, alpha=0.55, zorder=3)
    ax2.contour(X, Y, Z, levels=10, cmap="viridis", linewidths=1.6)
    ax2.set_title("GMM 等高线与观测数据", fontsize=12.5, fontweight="bold", color="#1e293b", pad=12)
    ax2.set_xlabel("喷发持续时间 (min)", fontsize=10.5, color="#334155")
    ax2.set_ylabel("喷发间隔时间 (min)", fontsize=10.5, color="#334155")
    ax2.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_5_2(png_path: Path) -> None:
    """Fig 5-2: Mode-covering vs Mode-seeking KL Divergences."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.2), dpi=300)
    x = np.linspace(-6, 6, 300)

    # True bimodal p(x): 0.5 N(-2, 0.8^2) + 0.5 N(2, 0.8^2)
    p = 0.5 * (1/(0.8*np.sqrt(2*np.pi))) * np.exp(-(x+2)**2/(2*0.8**2)) + \
        0.5 * (1/(0.8*np.sqrt(2*np.pi))) * np.exp(-(x-2)**2/(2*0.8**2))

    # Mode covering (Forward KL: D_KL(p || q)) -> broad single Gaussian
    q_cov = (1/(2.2*np.sqrt(2*np.pi))) * np.exp(-x**2/(2*2.2**2))

    ax1.plot(x, p, color="#334155", linewidth=2.5, label="真实分布 p(x) (双峰)")
    ax1.plot(x, q_cov, color="#2563eb", linewidth=2.5, linestyle="--", label="前向 KL: q(x) (覆盖两峰)")
    ax1.fill_between(x, q_cov, color="#93c5fd", alpha=0.25)
    ax1.set_title("前向 KL: $D_{KL}(p \\parallel q)$ (Mode-covering)", fontsize=12, fontweight="bold", color="#1e293b")
    ax1.legend(frameon=True, facecolor="#ffffff", fontsize=9.5)
    ax1.grid(True, linestyle="--", alpha=0.3)

    # Mode seeking (Reverse KL: D_KL(q || p)) -> locks onto one mode
    q_seek = (1/(0.8*np.sqrt(2*np.pi))) * np.exp(-(x-2)**2/(2*0.8**2))

    ax2.plot(x, p, color="#334155", linewidth=2.5, label="真实分布 p(x) (双峰)")
    ax2.plot(x, q_seek, color="#ef4444", linewidth=2.5, linestyle="--", label="反向 KL: q(x) (锁定单峰)")
    ax2.fill_between(x, q_seek, color="#fca5a5", alpha=0.25)
    ax2.set_title("反向 KL: $D_{KL}(q \\parallel p)$ (Mode-seeking)", fontsize=12, fontweight="bold", color="#1e293b")
    ax2.legend(frameon=True, facecolor="#ffffff", fontsize=9.5)
    ax2.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_5_12(png_path: Path) -> None:
    """Fig 5-12: Real data vs GMM generated data."""
    fig, ax = plt.subplots(figsize=(6.8, 5.0), dpi=300)

    if DATA_PATH.exists():
        real = np.load(DATA_PATH)
    else:
        np.random.seed(42)
        real = np.random.multivariate_normal([3.5, 70.0], [[0.5, 2.0], [2.0, 15.0]], 272)

    np.random.seed(100)
    n1, n2 = int(0.35 * len(real)), len(real) - int(0.35 * len(real))
    g1 = np.random.multivariate_normal([2.0, 54.5], [[0.07, 0.44], [0.44, 33.7]], n1)
    g2 = np.random.multivariate_normal([4.3, 80.0], [[0.17, 0.94], [0.94, 36.0]], n2)
    generated = np.vstack([g1, g2])

    ax.scatter(real[:, 0], real[:, 1], color="#2563eb", s=40, alpha=0.75, label="真实数据 (Real)", edgecolors="#1e40af")
    ax.scatter(generated[:, 0], generated[:, 1], color="#f59e0b", s=40, alpha=0.75, label="生成数据 (GMM Generated)", edgecolors="#b45309")

    ax.set_title("数据分布对比 (真实数据 vs GMM 生成数据)", fontsize=13.5, fontweight="bold", color="#1e293b", pad=14)
    ax.set_xlabel("喷发持续时间 / 分钟", fontsize=11.5, color="#334155")
    ax.set_ylabel("喷发间隔时间 / 分钟", fontsize=11.5, color="#334155")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=10.5)
    ax.grid(True, linestyle="--", alpha=0.35)

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_6_1(png_path: Path) -> None:
    """Fig 6-1: 3D Rosenbrock Function surface."""
    fig = plt.figure(figsize=(7.2, 5.2), dpi=300)
    ax = fig.add_subplot(111, projection="3d")
    
    x0 = np.linspace(-2.0, 2.0, 140)
    x1 = np.linspace(-1.0, 3.0, 140)
    X0, X1 = np.meshgrid(x0, x1)
    Y = 100 * (X1 - X0**2)**2 + (1 - X0)**2

    surf = ax.plot_surface(X0, X1, Y, cmap="viridis", linewidth=0, antialiased=True, alpha=0.92)
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-1.0, 3.0)
    ax.set_zlim(0, 2500)

    ax.set_xlabel("$x_0$", color="#1e293b", fontsize=11, labelpad=7)
    ax.set_ylabel("$x_1$", color="#1e293b", fontsize=11, labelpad=7)
    ax.set_zlabel("$y = f(x_0, x_1)$", color="#1e293b", fontsize=10.5, labelpad=7)
    ax.set_title("Rosenbrock 函数三维曲面", fontsize=13, fontweight="bold", color="#1e293b", pad=12)

    ax.view_init(elev=28, azim=-62)
    ax.tick_params(colors="#475569", labelsize=8.5)
    cbar = fig.colorbar(surf, ax=ax, shrink=0.72, aspect=18, pad=0.08)
    cbar.set_label("$y = f(x_0, x_1)$", color="#1e293b", fontsize=10)

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)

def fig_5_5() -> str:
    """Fig 5-5 / 5-14: Intractable p_theta(z|x) (Spiky Urchin) and its tractable surrogate q(z) (Friendly Face)."""
    points = []
    for i in range(32):
        angle = i * (2 * math.pi / 32)
        r = 62 if i % 2 == 0 else 36
        px = 220 + r * math.cos(angle)
        py = 110 + r * math.sin(angle)
        points.append(f"{px:.1f},{py:.1f}")
    urchin_pts = " ".join(points)

    c = f"""
    <rect x="20" y="20" width="860" height="380" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Top Row: Spiky Urchin p_theta(z|x) -->
    <g>
      <!-- Spiky body -->
      <polygon points="{urchin_pts}" fill="#1e293b" stroke="#0f172a" stroke-width="2" filter="url(#sh)"/>
      <!-- Angry eyes -->
      <line x1="202" y1="98" x2="214" y2="105" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
      <line x1="238" y1="98" x2="226" y2="105" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
      <circle cx="210" cy="106" r="3.5" fill="#ef4444"/>
      <circle cx="230" cy="106" r="3.5" fill="#ef4444"/>
      <!-- Angry mouth -->
      <path d="M 212 124 L 216 118 L 220 124 L 224 118 L 228 124" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>

      <!-- Big formula label -->
      <text x="380" y="125" font-size="44" fill="#1e293b" font-weight="bold" font-style="italic">p_θ(z | x)</text>
      <text x="610" y="105" font-size="16" fill="#dc2626" font-weight="bold">棘手的后验分布</text>
      <text x="610" y="132" font-size="13" fill="#64748b">分母包含对所有 z 的积分，无法直接计算</text>
    </g>

    <line x1="100" y1="210" x2="800" y2="210" stroke="#e2e8f0" stroke-width="1.5" stroke-dasharray="6 4"/>

    <!-- Bottom Row: Friendly Face q(z) -->
    <g transform="translate(0, 190)">
      <!-- Friendly body -->
      <circle cx="220" cy="110" r="50" fill="url(#agrad)" stroke="#d97706" stroke-width="2.5" filter="url(#sh)"/>
      <!-- Happy eyes -->
      <circle cx="202" cy="100" r="5" fill="#78350f"/>
      <circle cx="238" cy="100" r="5" fill="#78350f"/>
      <!-- Big happy smile -->
      <path d="M 198 118 C 210 138, 230 138, 242 118" fill="none" stroke="#78350f" stroke-width="4" stroke-linecap="round"/>

      <!-- Big formula label -->
      <text x="380" y="125" font-size="44" fill="#047857" font-weight="bold" font-style="italic">q(z)</text>
      <text x="560" y="105" font-size="16" fill="#059669" font-weight="bold">可处理的替代分布 (变分近似)</text>
      <text x="560" y="132" font-size="13" fill="#64748b">易于采样和求解的高斯分布族，用于逼近真实后验</text>
    </g>
    """
    return _svg_wrap(900, 420, c)


CH4_6_SVGS = {
    "5-5": fig_5_5,
}

CH4_6_PLOTS = {
    "4-4": draw_fig_4_4,
    "4-6": draw_fig_4_6,
    "4-9": draw_fig_4_9,
    "5-2": draw_fig_5_2,
    "5-12": draw_fig_5_12,
    "6-1": draw_fig_6_1,
}
