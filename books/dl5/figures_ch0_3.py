"""3Blue1Brown figures for Chapters 0 to 3 of 《深度学习入门 5 生成模型》."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = [
    "Songti SC", "PingFang SC", "Heiti SC", "Noto Sans CJK SC", "DejaVu Sans"
]
plt.rcParams["axes.unicode_minus"] = False

def _svg_wrap(w: int, h: int, content: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" style="background:#ffffff; font-family:'PingFang SC','Noto Serif CJK SC','Songti SC',sans-serif;">
  <defs>
    <linearGradient id="bgrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#1d4ed8"/></linearGradient>
    <linearGradient id="tgrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#06b6d4"/><stop offset="100%" stop-color="#0e7490"/></linearGradient>
    <linearGradient id="agrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#fbbf24"/><stop offset="100%" stop-color="#d97706"/></linearGradient>
    <linearGradient id="rgrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#fb7185"/><stop offset="100%" stop-color="#e11d48"/></linearGradient>
    <linearGradient id="pgrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#a855f7"/><stop offset="100%" stop-color="#6b21a8"/></linearGradient>
    <linearGradient id="ggrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#34d399"/><stop offset="100%" stop-color="#059669"/></linearGradient>
    <filter id="sh" x="-10%" y="-10%" width="125%" height="125%"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.08"/></filter>
    <marker id="darr" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1.5 L 8 5 L 0 8.5 L 2 5 z" fill="#334155"/></marker>
    <marker id="barr" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1.5 L 8 5 L 0 8.5 L 2 5 z" fill="#2563eb"/></marker>
    <marker id="rarr" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1.5 L 8 5 L 0 8.5 L 2 5 z" fill="#ef4444"/></marker>
  </defs>
  {content}
</svg>"""


def fig_0_1() -> str:
    """Fig 0-1: Cloud service execution workflow."""
    c = """
    <rect x="20" y="20" width="860" height="200" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>
    <rect x="60" y="60" width="200" height="110" rx="10" fill="url(#bgrad)" filter="url(#sh)"/>
    <text x="160" y="110" font-size="17" fill="#ffffff" font-weight="bold" text-anchor="middle">本地计算机</text>
    <text x="160" y="135" font-size="13" fill="#bfdbfe" text-anchor="middle">浏览器 / Web 界面</text>

    <path d="M 270 115 L 350 115" stroke="#2563eb" stroke-width="3" marker-end="url(#barr)"/>
    <text x="310" y="100" font-size="12" fill="#2563eb" font-weight="bold" text-anchor="middle">运行指令</text>

    <rect x="360" y="50" width="480" height="130" rx="12" fill="#ffffff" stroke="#0ea5e9" stroke-width="2" stroke-dasharray="6 4" filter="url(#sh)"/>
    <text x="600" y="80" font-size="15" fill="#0369a1" font-weight="bold" text-anchor="middle">云端 GPU 服务 (Google Colab / 云服务器)</text>

    <rect x="390" y="95" width="200" height="65" rx="8" fill="url(#tgrad)"/>
    <text x="490" y="132" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">PyTorch / GPU 算力</text>

    <rect x="620" y="95" width="190" height="65" rx="8" fill="url(#agrad)"/>
    <text x="715" y="132" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">云端数据集 / 权重</text>
    """
    return _svg_wrap(900, 240, c)


def fig_1_1() -> str:
    """Fig 1-1: Probability distribution, sample and observation."""
    c = """
    <rect x="20" y="20" width="860" height="210" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <g transform="translate(180, 120)">
      <circle cx="0" cy="0" r="70" fill="url(#bgrad)" filter="url(#sh)"/>
      <text x="0" y="-10" font-size="17" fill="#ffffff" font-weight="bold" text-anchor="middle">概率分布</text>
      <text x="0" y="15" font-size="13" fill="#bfdbfe" text-anchor="middle">p(x) (生成源头)</text>
    </g>

    <path d="M 260 120 L 410 120" stroke="#334155" stroke-width="3" marker-end="url(#darr)"/>
    <text x="335" y="105" font-size="14" fill="#2563eb" font-weight="bold" text-anchor="middle">采样 (Sample)</text>

    <g transform="translate(480, 120)">
      <rect x="-60" y="-55" width="120" height="110" rx="10" fill="url(#agrad)" filter="url(#sh)"/>
      <text x="0" y="-5" font-size="16" fill="#ffffff" font-weight="bold" text-anchor="middle">样本</text>
      <text x="0" y="20" font-size="13" fill="#fef3c7" text-anchor="middle">随机变量 X</text>
    </g>

    <path d="M 550 120 L 680 120" stroke="#334155" stroke-width="3" marker-end="url(#darr)"/>
    <text x="615" y="105" font-size="14" fill="#d97706" font-weight="bold" text-anchor="middle">实现 / 观测</text>

    <g transform="translate(750, 120)">
      <circle cx="0" cy="0" r="50" fill="#ffffff" stroke="#10b981" stroke-width="3" filter="url(#sh)"/>
      <text x="0" y="-5" font-size="16" fill="#065f46" font-weight="bold" text-anchor="middle">观测值</text>
      <text x="0" y="18" font-size="14" fill="#047857" font-weight="bold" text-anchor="middle">x = 172.5</text>
    </g>
    """
    return _svg_wrap(900, 250, c)


def fig_2_2() -> str:
    """Fig 2-2: Population and samples relationship."""
    c = """
    <rect x="20" y="20" width="860" height="220" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Population -->
    <ellipse cx="230" cy="130" rx="160" ry="85" fill="#eff6ff" stroke="#3b82f6" stroke-width="2.5" filter="url(#sh)"/>
    <text x="230" y="75" font-size="17" fill="#1e40af" font-weight="bold" text-anchor="middle">总体 (Population)</text>
    <text x="230" y="98" font-size="12" fill="#64748b" text-anchor="middle">所有的可能对象 (大小 N → ∞)</text>
    
    <!-- Mini dots inside population -->
    <circle cx="150" cy="130" r="5" fill="#93c5fd"/><circle cx="180" cy="150" r="5" fill="#93c5fd"/>
    <circle cx="210" cy="120" r="5" fill="#93c5fd"/><circle cx="250" cy="140" r="5" fill="#93c5fd"/>
    <circle cx="280" cy="115" r="5" fill="#93c5fd"/><circle cx="310" cy="150" r="5" fill="#93c5fd"/>

    <!-- Sampling arrow -->
    <path d="M 400 115 C 470 70, 530 70, 590 110" fill="none" stroke="#2563eb" stroke-width="3" marker-end="url(#barr)"/>
    <text x="495" y="70" font-size="14" fill="#2563eb" font-weight="bold" text-anchor="middle">抽样 (Sampling)</text>

    <!-- Estimation arrow -->
    <path d="M 590 150 C 530 190, 470 190, 405 150" fill="none" stroke="#d97706" stroke-width="2.5" stroke-dasharray="5 4" marker-end="url(#darr)"/>
    <text x="495" y="200" font-size="13" fill="#d97706" font-weight="bold" text-anchor="middle">推断 / 参数估计</text>

    <!-- Samples -->
    <ellipse cx="690" cy="130" rx="110" ry="70" fill="#fef3c7" stroke="#f59e0b" stroke-width="2.5" filter="url(#sh)"/>
    <text x="690" y="85" font-size="16" fill="#b45309" font-weight="bold" text-anchor="middle">样本 (Sample)</text>
    <text x="690" y="105" font-size="12" fill="#92400e" text-anchor="middle">观测到的数据 (大小 n)</text>
    <circle cx="650" cy="135" r="5" fill="#f59e0b"/><circle cx="680" cy="150" r="5" fill="#f59e0b"/><circle cx="710" cy="130" r="5" fill="#f59e0b"/><circle cx="730" cy="145" r="5" fill="#f59e0b"/>
    """
    return _svg_wrap(900, 260, c)


def fig_2_3() -> str:
    """Fig 2-3: True distribution vs sample data in generative models."""
    c = """
    <rect x="20" y="20" width="860" height="210" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <g transform="translate(180, 120)">
      <rect x="-110" y="-60" width="220" height="120" rx="12" fill="url(#bgrad)" filter="url(#sh)"/>
      <text x="0" y="-15" font-size="16" fill="#ffffff" font-weight="bold" text-anchor="middle">真实的概率分布</text>
      <text x="0" y="10" font-size="15" fill="#dbeafe" text-anchor="middle">p_data(x)</text>
      <text x="0" y="35" font-size="12" fill="#bfdbfe" text-anchor="middle">未知的自然界生成机制</text>
    </g>

    <path d="M 300 120 L 410 120" stroke="#334155" stroke-width="3" marker-end="url(#darr)"/>
    <text x="355" y="105" font-size="13" fill="#2563eb" font-weight="bold" text-anchor="middle">数据采集</text>

    <g transform="translate(530, 120)">
      <rect x="-100" y="-60" width="200" height="120" rx="12" fill="url(#agrad)" filter="url(#sh)"/>
      <text x="0" y="-15" font-size="16" fill="#ffffff" font-weight="bold" text-anchor="middle">训练数据集</text>
      <text x="0" y="10" font-size="14" fill="#fef3c7" text-anchor="middle">D = {x₁, x₂, ..., x_N}</text>
      <text x="0" y="35" font-size="12" fill="#fde68a" text-anchor="middle">离散的观测样本</text>
    </g>

    <path d="M 640 120 L 730 120" stroke="#334155" stroke-width="3" marker-end="url(#darr)"/>
    <text x="685" y="105" font-size="13" fill="#059669" font-weight="bold" text-anchor="middle">训练学习</text>

    <g transform="translate(800, 120)">
      <circle cx="0" cy="0" r="55" fill="#ecfdf5" stroke="#10b981" stroke-width="2.5" filter="url(#sh)"/>
      <text x="0" y="-5" font-size="14" fill="#065f46" font-weight="bold" text-anchor="middle">生成模型</text>
      <text x="0" y="18" font-size="14" fill="#047857" font-weight="bold" text-anchor="middle">p_θ(x) ≈ p_data</text>
    </g>
    """
    return _svg_wrap(900, 250, c)


def fig_3_1() -> str:
    """Fig 3-1: Scalar, Vector, and Matrix."""
    c = """
    <rect x="20" y="20" width="860" height="200" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Scalar -->
    <g transform="translate(150, 120)">
      <rect x="-80" y="-60" width="160" height="120" rx="10" fill="#ffffff" stroke="#3b82f6" stroke-width="2" filter="url(#sh)"/>
      <text x="0" y="-25" font-size="16" fill="#1e40af" font-weight="bold" text-anchor="middle">标量 (Scalar)</text>
      <text x="0" y="10" font-size="24" fill="#2563eb" font-weight="bold" text-anchor="middle">x = 5</text>
      <text x="0" y="38" font-size="12" fill="#64748b" text-anchor="middle">单一数值 (0维)</text>
    </g>

    <!-- Vector -->
    <g transform="translate(420, 120)">
      <rect x="-100" y="-60" width="200" height="120" rx="10" fill="#ffffff" stroke="#0ea5e9" stroke-width="2" filter="url(#sh)"/>
      <text x="0" y="-25" font-size="16" fill="#0369a1" font-weight="bold" text-anchor="middle">向量 (Vector)</text>
      <text x="0" y="12" font-size="20" fill="#0284c7" font-weight="bold" text-anchor="middle">x = [1, 2, 3]ᵀ</text>
      <text x="0" y="38" font-size="12" fill="#64748b" text-anchor="middle">一维数组 (1维)</text>
    </g>

    <!-- Matrix -->
    <g transform="translate(710, 120)">
      <rect x="-120" y="-60" width="240" height="120" rx="10" fill="#ffffff" stroke="#f59e0b" stroke-width="2" filter="url(#sh)"/>
      <text x="0" y="-25" font-size="16" fill="#b45309" font-weight="bold" text-anchor="middle">矩阵 (Matrix)</text>
      <text x="0" y="10" font-size="18" fill="#d97706" font-weight="bold" text-anchor="middle">X ∈ ℝ^{M × N}</text>
      <text x="0" y="38" font-size="12" fill="#64748b" text-anchor="middle">二维网格阵列 (2维)</text>
    </g>
    """
    return _svg_wrap(900, 240, c)


def fig_3_6() -> str:
    """Fig 3-6: Covariance matrix elements with variance diagonal and covariance off-diagonals."""
    c = """
    <rect x="20" y="20" width="860" height="310" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <g transform="translate(450, 170)">
      <!-- Big Formula Title -->
      <text x="-310" y="10" font-size="28" fill="#1e293b" font-weight="bold" font-style="italic">Σ =</text>

      <!-- Matrix left bracket -->
      <path d="M -230 -110 C -255 -60, -255 60, -230 110" fill="none" stroke="#334155" stroke-width="3.5"/>
      <!-- Matrix right bracket -->
      <path d="M 230 -110 C 255 -60, 255 60, 230 110" fill="none" stroke="#334155" stroke-width="3.5"/>

      <!-- Diagonal highlight pill: Variance -->
      <path d="M -185 -105 L 185 85" stroke="#fef3c7" stroke-width="48" stroke-linecap="round"/>
      <path d="M -185 -105 L 185 85" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="6 4" stroke-linecap="round"/>
      
      <!-- Upper triangular highlight: Covariance -->
      <path d="M -70 -90 L 170 -90 L 170 30 Z" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="5 3"/>

      <!-- Lower triangular highlight: Covariance -->
      <path d="M -170 -30 L -170 90 L 70 90 Z" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="5 3"/>

      <!-- Variance Label Callout -->
      <path d="M -160 -95 C -190 -125, -200 -130, -210 -135" fill="none" stroke="#d97706" stroke-width="2" marker-end="url(#darr)"/>
      <rect x="-275" y="-155" width="75" height="30" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
      <text x="-237" y="-135" font-size="14" fill="#b45309" font-weight="bold" text-anchor="middle">方差</text>

      <!-- Upper Covariance Label Callout -->
      <rect x="30" y="-65" width="90" height="28" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
      <text x="75" y="-46" font-size="13" fill="#1e40af" font-weight="bold" text-anchor="middle">协方差</text>

      <!-- Lower Covariance Label Callout -->
      <rect x="-120" y="35" width="90" height="28" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
      <text x="-75" y="54" font-size="13" fill="#1e40af" font-weight="bold" text-anchor="middle">协方差</text>

      <!-- Matrix Elements Text -->
      <!-- Row 1 -->
      <text x="-160" y="-70" font-size="20" fill="#b45309" font-weight="bold" text-anchor="middle">σ₁₁</text>
      <text x="-60" y="-70" font-size="19" fill="#1e40af" text-anchor="middle">σ₁₂</text>
      <text x="40" y="-70" font-size="18" fill="#64748b" text-anchor="middle">···</text>
      <text x="140" y="-70" font-size="19" fill="#1e40af" text-anchor="middle">σ₁_D</text>

      <!-- Row 2 -->
      <text x="-160" y="-15" font-size="19" fill="#1e40af" text-anchor="middle">σ₂₁</text>
      <text x="-60" y="-15" font-size="20" fill="#b45309" font-weight="bold" text-anchor="middle">σ₂₂</text>
      <text x="40" y="-15" font-size="18" fill="#64748b" text-anchor="middle">···</text>
      <text x="140" y="-15" font-size="19" fill="#1e40af" text-anchor="middle">σ₂_D</text>

      <!-- Row 3: dots -->
      <text x="-160" y="35" font-size="20" fill="#64748b" text-anchor="middle">⋮</text>
      <text x="-60" y="35" font-size="20" fill="#64748b" text-anchor="middle">⋮</text>
      <text x="40" y="35" font-size="22" fill="#b45309" font-weight="bold" text-anchor="middle">⋱</text>
      <text x="140" y="35" font-size="20" fill="#64748b" text-anchor="middle">⋮</text>

      <!-- Row 4 -->
      <text x="-160" y="80" font-size="19" fill="#1e40af" text-anchor="middle">σ_D1</text>
      <text x="-60" y="80" font-size="19" fill="#1e40af" text-anchor="middle">σ_D2</text>
      <text x="40" y="80" font-size="18" fill="#64748b" text-anchor="middle">···</text>
      <text x="140" y="80" font-size="20" fill="#b45309" font-weight="bold" text-anchor="middle">σ_DD</text>
    </g>
    """
    return _svg_wrap(900, 350, c)
def fig_3_2() -> str:
    """Fig 3-2: Representation of vectors: Column Vector vs Row Vector."""
    c = """
    <rect x="20" y="20" width="860" height="220" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Left Card: Column Vector -->
    <g transform="translate(230, 125)">
      <rect x="-140" y="-85" width="280" height="170" rx="12" fill="#ffffff" stroke="#2563eb" stroke-width="2" filter="url(#sh)"/>
      <rect x="-140" y="-85" width="280" height="36" rx="12" fill="#eff6ff"/>
      <text x="0" y="-62" font-size="14.5" fill="#1e40af" font-weight="bold" text-anchor="middle">列向量 (Column Vector)</text>

      <!-- Left Bracket -->
      <path d="M -50 -25 C -65 -10, -65 30, -50 45" fill="none" stroke="#1e293b" stroke-width="2.5"/>
      <!-- Right Bracket -->
      <path d="M 50 -25 C 65 -10, 65 30, 50 45" fill="none" stroke="#1e293b" stroke-width="2.5"/>

      <text x="0" y="-8" font-size="20" fill="#2563eb" font-weight="bold" text-anchor="middle">1</text>
      <text x="0" y="16" font-size="20" fill="#2563eb" font-weight="bold" text-anchor="middle">2</text>
      <text x="0" y="40" font-size="20" fill="#2563eb" font-weight="bold" text-anchor="middle">3</text>
    </g>

    <!-- Arrow between them -->
    <path d="M 400 125 L 470 125" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4 3"/>
    <text x="435" y="115" font-size="12" fill="#64748b" text-anchor="middle">或</text>

    <!-- Right Card: Row Vector -->
    <g transform="translate(640, 125)">
      <rect x="-170" y="-85" width="340" height="170" rx="12" fill="#ffffff" stroke="#f59e0b" stroke-width="2" filter="url(#sh)"/>
      <rect x="-170" y="-85" width="340" height="36" rx="12" fill="#fef3c7"/>
      <text x="0" y="-62" font-size="14.5" fill="#b45309" font-weight="bold" text-anchor="middle">行向量 (Row Vector)</text>

      <!-- Left Bracket -->
      <path d="M -90 -5 C -105 10, -105 20, -90 35" fill="none" stroke="#1e293b" stroke-width="2.5"/>
      <!-- Right Bracket -->
      <path d="M 90 -5 C 105 10, 105 20, 90 35" fill="none" stroke="#1e293b" stroke-width="2.5"/>

      <text x="-50" y="22" font-size="22" fill="#d97706" font-weight="bold" text-anchor="middle">1</text>
      <text x="0" y="22" font-size="22" fill="#d97706" font-weight="bold" text-anchor="middle">2</text>
      <text x="50" y="22" font-size="22" fill="#d97706" font-weight="bold" text-anchor="middle">3</text>
    </g>
    """
    return _svg_wrap(900, 260, c)


def fig_3_7() -> str:
    """Fig 3-7: Matrix transpose illustration with color-coded rows becoming columns."""
    c = """
    <rect x="20" y="20" width="860" height="230" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Left Matrix: X (3 x 2) -->
    <g transform="translate(220, 125)">
      <text x="-120" y="8" font-size="24" fill="#1e293b" font-weight="bold" font-style="italic">X =</text>
      
      <!-- Brackets -->
      <path d="M -75 -65 C -90 -30, -90 30, -75 65" fill="none" stroke="#334155" stroke-width="3"/>
      <path d="M 75 -65 C 90 -30, 90 30, 75 65" fill="none" stroke="#334155" stroke-width="3"/>

      <!-- Row 1: Blue -->
      <rect x="-65" y="-55" width="130" height="32" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
      <text x="-32" y="-33" font-size="18" fill="#1e40af" font-weight="bold" text-anchor="middle">1</text>
      <text x="32" y="-33" font-size="18" fill="#1e40af" font-weight="bold" text-anchor="middle">2</text>

      <!-- Row 2: Amber -->
      <rect x="-65" y="-16" width="130" height="32" rx="6" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.5"/>
      <text x="-32" y="6" font-size="18" fill="#b45309" font-weight="bold" text-anchor="middle">3</text>
      <text x="32" y="6" font-size="18" fill="#b45309" font-weight="bold" text-anchor="middle">4</text>

      <!-- Row 3: Emerald -->
      <rect x="-65" y="23" width="130" height="32" rx="6" fill="#ecfdf5" stroke="#10b981" stroke-width="1.5"/>
      <text x="-32" y="45" font-size="18" fill="#047857" font-weight="bold" text-anchor="middle">5</text>
      <text x="32" y="45" font-size="18" fill="#047857" font-weight="bold" text-anchor="middle">6</text>

      <text x="0" y="90" font-size="13" fill="#64748b" text-anchor="middle">3 行 2 列 (3 × 2)</text>
    </g>

    <!-- Arrow with Transpose symbol -->
    <g transform="translate(420, 125)">
      <path d="M 0 0 L 70 0" stroke="#334155" stroke-width="3" marker-end="url(#darr)"/>
      <text x="35" y="-15" font-size="15" fill="#2563eb" font-weight="bold" text-anchor="middle">转置 ⊤</text>
      <text x="35" y="22" font-size="12" fill="#64748b" text-anchor="middle">行与列互换</text>
    </g>

    <!-- Right Matrix: X^T (2 x 3) -->
    <g transform="translate(670, 125)">
      <text x="-165" y="8" font-size="24" fill="#1e293b" font-weight="bold" font-style="italic">Xᵀ =</text>

      <!-- Brackets -->
      <path d="M -115 -50 C -130 -20, -130 20, -115 50" fill="none" stroke="#334155" stroke-width="3"/>
      <path d="M 115 -50 C 130 -20, 130 20, 115 50" fill="none" stroke="#334155" stroke-width="3"/>

      <!-- Col 1: Blue -->
      <rect x="-105" y="-38" width="60" height="76" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
      <text x="-75" y="-12" font-size="18" fill="#1e40af" font-weight="bold" text-anchor="middle">1</text>
      <text x="-75" y="24" font-size="18" fill="#1e40af" font-weight="bold" text-anchor="middle">2</text>

      <!-- Col 2: Amber -->
      <rect x="-30" y="-38" width="60" height="76" rx="6" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.5"/>
      <text x="0" y="-12" font-size="18" fill="#b45309" font-weight="bold" text-anchor="middle">3</text>
      <text x="0" y="24" font-size="18" fill="#b45309" font-weight="bold" text-anchor="middle">4</text>

      <!-- Col 3: Emerald -->
      <rect x="45" y="-38" width="60" height="76" rx="6" fill="#ecfdf5" stroke="#10b981" stroke-width="1.5"/>
      <text x="75" y="-12" font-size="18" fill="#047857" font-weight="bold" text-anchor="middle">5</text>
      <text x="75" y="24" font-size="18" fill="#047857" font-weight="bold" text-anchor="middle">6</text>

      <text x="0" y="80" font-size="13" fill="#64748b" text-anchor="middle">2 行 3 列 (2 × 3)</text>
    </g>
    """
    return _svg_wrap(900, 270, c)


def fig_3_8() -> str:
    """Fig 3-8: Vector transpose illustration."""
    c = """
    <rect x="20" y="20" width="860" height="200" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Left: Column vector x -->
    <g transform="translate(260, 115)">
      <text x="-90" y="8" font-size="24" fill="#1e293b" font-weight="bold" font-style="italic">x =</text>
      
      <path d="M -50 -55 C -65 -25, -65 25, -50 55" fill="none" stroke="#334155" stroke-width="2.5"/>
      <path d="M 50 -55 C 65 -25, 65 25, 50 55" fill="none" stroke="#334155" stroke-width="2.5"/>

      <text x="0" y="-30" font-size="18" fill="#2563eb" font-weight="bold" text-anchor="middle">1</text>
      <text x="0" y="6" font-size="18" fill="#2563eb" font-weight="bold" text-anchor="middle">2</text>
      <text x="0" y="42" font-size="18" fill="#2563eb" font-weight="bold" text-anchor="middle">3</text>

      <text x="0" y="80" font-size="13" fill="#64748b" text-anchor="middle">列向量 (3 × 1)</text>
    </g>

    <!-- Arrow with Transpose symbol -->
    <g transform="translate(430, 115)">
      <path d="M 0 0 L 70 0" stroke="#334155" stroke-width="3" marker-end="url(#darr)"/>
      <text x="35" y="-15" font-size="15" fill="#2563eb" font-weight="bold" text-anchor="middle">转置 ⊤</text>
    </g>

    <!-- Right: Row vector x^T -->
    <g transform="translate(640, 115)">
      <text x="-120" y="8" font-size="24" fill="#1e293b" font-weight="bold" font-style="italic">xᵀ =</text>

      <path d="M -75 -25 C -90 -10, -90 15, -75 30" fill="none" stroke="#334155" stroke-width="2.5"/>
      <path d="M 75 -25 C 90 -10, 90 15, 75 30" fill="none" stroke="#334155" stroke-width="2.5"/>

      <text x="-40" y="8" font-size="20" fill="#10b981" font-weight="bold" text-anchor="middle">1</text>
      <text x="0" y="8" font-size="20" fill="#10b981" font-weight="bold" text-anchor="middle">2</text>
      <text x="40" y="8" font-size="20" fill="#10b981" font-weight="bold" text-anchor="middle">3</text>

      <text x="0" y="60" font-size="13" fill="#64748b" text-anchor="middle">行向量 (1 × 3)</text>
    </g>
    """
    return _svg_wrap(900, 240, c)
def draw_fig_1_2(png_path: Path) -> None:
    """Fig 1-2: Discrete vs Continuous Probability Distributions."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.2), dpi=300)
    
    x_d = np.arange(1, 7)
    p_d = np.full(6, 1/6)
    bars = ax1.bar(x_d, p_d, width=0.55, color="#3b82f6", edgecolor="#1d4ed8", alpha=0.85)
    ax1.set_title("离散型概率分布 (掷骰子)", fontsize=13, fontweight="bold", color="#1e293b", pad=12)
    ax1.set_xlabel("点数 x", fontsize=11, color="#334155")
    ax1.set_ylabel("概率 P(X = x)", fontsize=11, color="#334155")
    ax1.set_ylim(0, 0.25)
    ax1.grid(True, linestyle="--", alpha=0.3)
    ax1.tick_params(colors="#475569")
    for b in bars:
        ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 0.008, "1/6", ha="center", fontsize=10, color="#1e40af", fontweight="bold")

    x_c = np.linspace(-4, 4, 200)
    p_c = (1 / np.sqrt(2 * np.pi)) * np.exp(-x_c**2 / 2)
    ax2.plot(x_c, p_c, color="#2563eb", linewidth=2.5)
    ax2.fill_between(x_c, p_c, color="#93c5fd", alpha=0.35)
    ax2.set_title("连续型概率分布 (正态分布)", fontsize=13, fontweight="bold", color="#1e293b", pad=12)
    ax2.set_xlabel("实数值 x", fontsize=11, color="#334155")
    ax2.set_ylabel("概率密度 p(x)", fontsize=11, color="#334155")
    ax2.grid(True, linestyle="--", alpha=0.3)
    ax2.tick_params(colors="#475569")

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_1_3(png_path: Path) -> None:
    """Fig 1-3: Area under curve for interval [170, 180]."""
    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)
    mu, sigma = 172.7, 4.83
    x = np.linspace(150, 195, 300)
    y = (1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-(x - mu)**2 / (2 * sigma**2))

    ax.plot(x, y, color="#2563eb", linewidth=2.5, label="正态分布 N(172.7, 4.83²)")
    
    mask = (x >= 170) & (x <= 180)
    ax.fill_between(x[mask], y[mask], color="#38bdf8", alpha=0.5, label="区间概率 P(170 ≤ x ≤ 180)")

    ax.axvline(170, color="#0284c7", linestyle="--", alpha=0.8)
    ax.axvline(180, color="#0284c7", linestyle="--", alpha=0.8)
    ax.set_title("曲线下面积表示落在区间的概率", fontsize=12.5, fontweight="bold", color="#1e293b", pad=12)
    ax.set_xlabel("身高 x (cm)", fontsize=11, color="#334155")
    ax.set_ylabel("概率密度 p(x)", fontsize=11, color="#334155")
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.tick_params(colors="#475569")

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_1_4(png_path: Path) -> None:
    """Fig 1-4: Standard normal curve with mu, mu +- sigma, mu +- 2sigma."""
    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)
    x = np.linspace(-3.5, 3.5, 300)
    y = (1 / np.sqrt(2 * np.pi)) * np.exp(-x**2 / 2)
    ax.plot(x, y, color="#2563eb", linewidth=2.5)

    m1 = (x >= -1) & (x <= 1)
    ax.fill_between(x[m1], y[m1], color="#93c5fd", alpha=0.45, label="68.3% (μ ± σ)")
    
    m2 = (x >= -2) & (x <= 2)
    ax.fill_between(x[m2], y[m2], color="#bfdbfe", alpha=0.25, label="95.4% (μ ± 2σ)")

    ax.set_xticks([-2, -1, 0, 1, 2])
    ax.set_xticklabels(["μ - 2σ", "μ - σ", "μ", "μ + σ", "μ + 2σ"], fontsize=11)
    ax.set_title("正态分布的标准差与概率覆盖范围", fontsize=12.5, fontweight="bold", color="#1e293b", pad=12)
    ax.set_ylabel("概率密度", fontsize=11, color="#334155")
    ax.legend(frameon=True, facecolor="#ffffff")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.tick_params(colors="#475569")

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_2_6(png_path: Path) -> None:
    """Fig 2-6: Height dataset histogram and fitted normal distribution."""
    fig, ax = plt.subplots(figsize=(6.8, 4.5), dpi=300)
    
    # Synthesize heights matching Japanese 17-year-old male statistics: N=25000, mu=172.7, sigma=4.83
    np.random.seed(42)
    mu, sigma = 172.7, 4.83
    data = np.random.normal(mu, sigma, 25000)

    ax.hist(data, bins=80, density=True, color="#38bdf8", edgecolor="#0284c7", alpha=0.7, label="身高数据集直方图")

    x = np.linspace(150, 195, 300)
    y = (1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-(x - mu)**2 / (2 * sigma**2))
    ax.plot(x, y, color="#1e40af", linewidth=2.8, label=f"拟合的正态分布 (μ={mu}, σ={sigma})")

    ax.set_xlabel("身高 / 厘米", fontsize=11, color="#334155")
    ax.set_ylabel("概率密度", fontsize=11, color="#334155")
    ax.set_xlim(150, 195)
    ax.set_ylim(0, 0.09)
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=10.5)
    ax.tick_params(colors="#475569", labelsize=10)

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_2_4(png_path: Path) -> None:
    """Fig 2-4: Height dataset histogram only."""
    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)
    np.random.seed(42)
    data = np.random.normal(172.7, 4.83, 25000)
    ax.hist(data, bins=80, density=True, color="#38bdf8", edgecolor="#0284c7", alpha=0.75)
    ax.set_xlabel("身高 / 厘米", fontsize=11, color="#334155")
    ax.set_ylabel("概率密度", fontsize=11, color="#334155")
    ax.set_xlim(150, 195)
    ax.tick_params(colors="#475569")

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_2_7(png_path: Path) -> None:
    """Fig 2-7: Derivative and Tangent Lines on Parabola y = -2x^2 + 3x + 4."""
    fig, ax = plt.subplots(figsize=(6.8, 4.5), dpi=300)
    
    x = np.linspace(-1.5, 3.0, 300)
    y = -2 * x**2 + 3 * x + 4
    ax.plot(x, y, color="#1e293b", linewidth=2.8, label="$y = -2x^2 + 3x + 4$")

    # Vertex point at x=0.75, y=5.125 where dy/dx = 0
    x_v, y_v = 0.75, 5.125
    ax.scatter([x_v], [y_v], color="#2563eb", s=65, zorder=5)
    x_t1 = np.linspace(-0.5, 2.0, 100)
    ax.plot(x_t1, np.full_like(x_t1, y_v), color="#3b82f6", linestyle="--", linewidth=1.8, label="切线 (斜率 $\\frac{dy}{dx} = 0$)")
    ax.annotate("切线的斜率: $\\frac{dy}{dx} = 0$", xy=(x_v, y_v), xytext=(x_v + 0.6, y_v + 1.2),
                arrowprops={"arrowstyle": "->", "color": "#2563eb", "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
                fontsize=11.5, fontweight="bold", color="#1e40af")

    # Point with positive slope at x = -0.5, y = 2.0, slope = -4(-0.5)+3 = 5 > 0
    x_p, y_p = -0.5, 2.0
    slope_p = -4 * x_p + 3
    ax.scatter([x_p], [y_p], color="#d97706", s=65, zorder=5)
    x_t2 = np.linspace(-1.2, 0.4, 100)
    y_t2 = y_p + slope_p * (x_t2 - x_p)
    ax.plot(x_t2, y_t2, color="#f59e0b", linestyle="-", linewidth=1.8, label="切线 (斜率 $\\frac{dy}{dx} > 0$)")
    ax.annotate("切线的斜率: $\\frac{dy}{dx} > 0$", xy=(x_p, y_p), xytext=(x_p - 0.7, y_p + 3.5),
                arrowprops={"arrowstyle": "->", "color": "#d97706", "lw": 1.5, "connectionstyle": "arc3,rad=0.2"},
                fontsize=11.5, fontweight="bold", color="#b45309")

    ax.text(1.3, 0.5, "$y = -2x^2 + 3x + 4$", fontsize=13, color="#334155", fontweight="bold")

    ax.set_xlim(-1.6, 3.2)
    ax.set_ylim(-3.0, 7.5)
    ax.axhline(0, color="#cbd5e1", linewidth=1.0, linestyle="--")
    ax.axvline(0, color="#cbd5e1", linewidth=1.0, linestyle="--")
    ax.tick_params(colors="#475569", labelsize=10)
    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


CH0_3_SVGS = {
    "0-1": fig_0_1,
    "1-1": fig_1_1,
    "2-2": fig_2_2,
    "2-3": fig_2_3,
    "3-1": fig_3_1,
    "3-2": fig_3_2,
    "3-6": fig_3_6,
    "3-7": fig_3_7,
    "3-8": fig_3_8,
}

CH0_3_PLOTS = {
    "1-2": draw_fig_1_2,
    "1-3": draw_fig_1_3,
    "1-4": draw_fig_1_4,
    "2-4": draw_fig_2_4,
    "2-6": draw_fig_2_6,
    "2-7": draw_fig_2_7,
}
