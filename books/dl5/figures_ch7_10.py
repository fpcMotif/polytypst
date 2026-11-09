"""3Blue1Brown figures for Chapters 7 to 10 of 《深度学习入门 5 生成模型》."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .figures_ch0_3 import _svg_wrap


def fig_7_7() -> str:
    """Fig 7-7: Dual-head encoder network for mu and log sigma^2."""
    c = """
    <rect x="20" y="15" width="860" height="200" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>
    <circle cx="70" cy="115" r="26" fill="#ffffff" stroke="#2563eb" stroke-width="2.5" filter="url(#sh)"/>
    <text x="70" y="122" font-size="20" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x</text>

    <path d="M 100 115 L 145 115" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <rect x="150" y="75" width="160" height="80" rx="10" fill="url(#bgrad)" filter="url(#sh)"/>
    <text x="230" y="110" font-size="15" fill="#ffffff" font-weight="bold" text-anchor="middle">骨干网络</text>
    <text x="230" y="132" font-size="12" fill="#bfdbfe" text-anchor="middle">Linear + ReLU</text>

    <path d="M 315 100 L 400 70" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>
    <path d="M 315 130 L 400 160" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <rect x="405" y="45" width="160" height="50" rx="8" fill="url(#tgrad)" filter="url(#sh)"/>
    <text x="485" y="75" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">linear_mu (全连接)</text>

    <rect x="405" y="135" width="160" height="50" rx="8" fill="url(#pgrad)" filter="url(#sh)"/>
    <text x="485" y="165" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">linear_logvar (全连接)</text>

    <path d="M 570 70 L 640 70" stroke="#0891b2" stroke-width="2.5" marker-end="url(#barr)"/>
    <circle cx="675" cy="70" r="26" fill="#ecfeff" stroke="#0891b2" stroke-width="2.5"/>
    <text x="675" y="77" font-size="18" fill="#155e75" font-weight="bold" text-anchor="middle" font-style="italic">μ</text>

    <path d="M 570 160 L 640 160" stroke="#7c3aed" stroke-width="2.5" marker-end="url(#darr)"/>
    <circle cx="675" cy="160" r="26" fill="#faf5ff" stroke="#7c3aed" stroke-width="2.5"/>
    <text x="675" y="166" font-size="16" fill="#6b21a8" font-weight="bold" text-anchor="middle" font-style="italic">log σ²</text>
    """
    return _svg_wrap(900, 230, c)


def fig_7_13() -> str:
    """Fig 7-13: Encoder forward computation graph and PyTorch code."""
    c = """
    <rect x="20" y="15" width="860" height="230" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <g transform="translate(40, 40)">
      <rect x="0" y="0" width="380" height="170" rx="10" fill="#1e293b" filter="url(#sh)"/>
      <text x="18" y="28" font-size="12" fill="#94a3b8" font-family="monospace"># Encoder forward pass</text>
      <text x="18" y="55" font-size="13" fill="#60a5fa" font-family="monospace">def forward(self, x):</text>
      <text x="36" y="80" font-size="13" fill="#f8fafc" font-family="monospace">h = F.relu(self.linear(x))</text>
      <text x="36" y="105" font-size="13" fill="#38bdf8" font-family="monospace">mu = self.linear_mu(h)</text>
      <text x="36" y="130" font-size="13" fill="#c084fc" font-family="monospace">logvar = self.linear_logvar(h)</text>
      <text x="36" y="155" font-size="13" fill="#fbbf24" font-family="monospace">return mu, logvar</text>
    </g>

    <!-- Flow Diagram on the Right -->
    <g transform="translate(480, 50)">
      <circle cx="30" cy="75" r="22" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5"/>
      <text x="30" y="81" font-size="16" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x</text>

      <path d="M 55 75 L 85 75" stroke="#334155" stroke-width="2" marker-end="url(#darr)"/>

      <rect x="90" y="50" width="90" height="50" rx="8" fill="url(#bgrad)"/>
      <text x="135" y="80" font-size="12" fill="#ffffff" font-weight="bold" text-anchor="middle">Linear+ReLU</text>

      <path d="M 185 65 L 225 45" stroke="#334155" stroke-width="2" marker-end="url(#darr)"/>
      <path d="M 185 85 L 225 105" stroke="#334155" stroke-width="2" marker-end="url(#darr)"/>

      <rect x="230" y="25" width="85" height="38" rx="6" fill="url(#tgrad)"/>
      <text x="272" y="49" font-size="11" fill="#ffffff" font-weight="bold" text-anchor="middle">linear_mu</text>

      <rect x="230" y="85" width="85" height="38" rx="6" fill="url(#pgrad)"/>
      <text x="272" y="109" font-size="10.5" fill="#ffffff" font-weight="bold" text-anchor="middle">linear_logvar</text>

      <circle cx="355" cy="44" r="18" fill="#ecfeff" stroke="#0891b2" stroke-width="2"/>
      <text x="355" y="50" font-size="14" fill="#0891b2" font-weight="bold" text-anchor="middle" font-style="italic">μ</text>

      <circle cx="355" cy="104" r="18" fill="#faf5ff" stroke="#8b5cf6" stroke-width="2"/>
      <text x="355" y="109" font-size="12" fill="#7c3aed" font-weight="bold" text-anchor="middle" font-style="italic">log σ²</text>
    </g>
    """
    return _svg_wrap(900, 260, c)


def fig_8_2() -> str:
    """Fig 8-2: Hierarchical VAE Model Diagram (分层 VAE 的模型图)."""
    c = """
    <rect x="20" y="15" width="860" height="230" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Nodes: z_T, z_{T-1}, ..., z_2, z_1, x -->
    <!-- z_T -->
    <circle cx="100" cy="120" r="28" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5" filter="url(#sh)"/>
    <text x="100" y="127" font-size="18" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">z_T</text>

    <!-- z_{T-1} -->
    <circle cx="260" cy="120" r="28" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5" filter="url(#sh)"/>
    <text x="260" y="127" font-size="17" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">z_{T-1}</text>

    <!-- Dots -->
    <text x="360" y="126" font-size="28" fill="#94a3b8" font-weight="bold" text-anchor="middle">···</text>

    <!-- z_2 -->
    <circle cx="460" cy="120" r="28" fill="#eff6ff" stroke="#3b82f6" stroke-width="2.5" filter="url(#sh)"/>
    <text x="460" y="127" font-size="18" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">z₂</text>

    <!-- z_1 -->
    <circle cx="620" cy="120" r="28" fill="#fdf4ff" stroke="#8b5cf6" stroke-width="2.5" filter="url(#sh)"/>
    <text x="620" y="127" font-size="18" fill="#6b21a8" font-weight="bold" text-anchor="middle" font-style="italic">z₁</text>

    <!-- x -->
    <circle cx="780" cy="120" r="28" fill="#ecfdf5" stroke="#10b981" stroke-width="2.5" filter="url(#sh)"/>
    <text x="780" y="127" font-size="20" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">x</text>

    <!-- Top Forward/Generative Transitions: p_theta -->
    <path d="M 235 98 C 200 68, 160 68, 125 98" fill="none" stroke="#2563eb" stroke-width="2.5" marker-end="url(#barr)"/>
    <text x="180" y="60" font-size="13" fill="#1e40af" font-weight="bold" text-anchor="middle">p_{θ_T}(z_{T-1} | z_T)</text>

    <path d="M 595 98 C 555 68, 525 68, 485 98" fill="none" stroke="#3b82f6" stroke-width="2.5" marker-end="url(#barr)"/>
    <text x="540" y="60" font-size="13" fill="#1e40af" font-weight="bold" text-anchor="middle">p_{θ₂}(z₁ | z₂)</text>

    <path d="M 755 98 C 720 68, 680 68, 645 98" fill="none" stroke="#10b981" stroke-width="2.5" marker-end="url(#barr)"/>
    <text x="700" y="60" font-size="13.5" fill="#047857" font-weight="bold" text-anchor="middle">p_{θ₁}(x | z₁)</text>

    <!-- Bottom Inference Transitions: q_phi -->
    <path d="M 125 142 C 160 172, 200 172, 235 142" fill="none" stroke="#f59e0b" stroke-width="2.5" marker-end="url(#darr)"/>
    <text x="180" y="195" font-size="13" fill="#b45309" font-weight="bold" text-anchor="middle">q_{ϕ_T}(z_T | z_{T-1})</text>

    <path d="M 485 142 C 525 172, 555 172, 595 142" fill="none" stroke="#f59e0b" stroke-width="2.5" marker-end="url(#darr)"/>
    <text x="540" y="195" font-size="13" fill="#b45309" font-weight="bold" text-anchor="middle">q_{ϕ₂}(z₂ | z₁)</text>

    <path d="M 645 142 C 680 172, 720 172, 755 142" fill="none" stroke="#f59e0b" stroke-width="2.5" marker-end="url(#darr)"/>
    <text x="700" y="195" font-size="13.5" fill="#b45309" font-weight="bold" text-anchor="middle">q_{ϕ₁}(z₁ | x)</text>
    """
    return _svg_wrap(900, 250, c)


def fig_8_3() -> str:
    """Fig 8-3: Diffusion Model Overview (扩散模型的模型图)."""
    c = """
    <rect x="20" y="15" width="860" height="260" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Labels -->
    <text x="450" y="45" font-size="14" fill="#2563eb" font-weight="bold" text-anchor="middle">去除噪声 (逆扩散 / 生成过程 p_θ)</text>
    <text x="450" y="225" font-size="14" fill="#ef4444" font-weight="bold" text-anchor="middle">添加噪声 (前向扩散过程 q)</text>

    <!-- Nodes -->
    <circle cx="100" cy="125" r="28" fill="#fef2f2" stroke="#ef4444" stroke-width="2.5" filter="url(#sh)"/>
    <text x="100" y="132" font-size="18" fill="#991b1b" font-weight="bold" text-anchor="middle" font-style="italic">x_T</text>

    <text x="220" y="130" font-size="28" fill="#94a3b8" font-weight="bold" text-anchor="middle">···</text>

    <circle cx="340" cy="125" r="28" fill="#fff7ed" stroke="#f97316" stroke-width="2.5" filter="url(#sh)"/>
    <text x="340" y="132" font-size="18" fill="#c2410c" font-weight="bold" text-anchor="middle" font-style="italic">x_t</text>

    <circle cx="560" cy="125" r="28" fill="#eff6ff" stroke="#3b82f6" stroke-width="2.5" filter="url(#sh)"/>
    <text x="560" y="132" font-size="17" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x_{t-1}</text>

    <text x="680" y="130" font-size="28" fill="#94a3b8" font-weight="bold" text-anchor="middle">···</text>

    <circle cx="790" cy="125" r="28" fill="#ecfdf5" stroke="#10b981" stroke-width="2.5" filter="url(#sh)"/>
    <text x="790" y="132" font-size="19" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">x₀</text>

    <!-- Top Denoising Arrows (p_theta) -->
    <path d="M 530 105 C 475 75, 425 75, 370 105" fill="none" stroke="#2563eb" stroke-width="3" marker-end="url(#barr)"/>
    <rect x="400" y="65" width="100" height="28" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.2"/>
    <text x="450" y="84" font-size="12" fill="#1e40af" font-weight="bold" text-anchor="middle">p_θ(x_{t-1} | x_t)</text>

    <!-- Bottom Noise Arrows (q) -->
    <path d="M 370 145 C 425 175, 475 175, 530 145" fill="none" stroke="#ef4444" stroke-width="3" marker-end="url(#rarr)"/>
    <rect x="405" y="160" width="90" height="28" rx="6" fill="#fef2f2" stroke="#ef4444" stroke-width="1.2"/>
    <text x="450" y="179" font-size="12" fill="#991b1b" font-weight="bold" text-anchor="middle">q(x_t | x_{t-1})</text>
    """
    return _svg_wrap(900, 270, c)


def fig_8_4() -> str:
    """Fig 8-4: Forward Diffusion Process (扩散过程)."""
    c = """
    <rect x="20" y="15" width="860" height="200" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <text x="450" y="45" font-size="14.5" fill="#ef4444" font-weight="bold" text-anchor="middle">前向加噪过程 (添加高斯噪声)</text>

    <!-- Nodes from x_0 to x_T -->
    <circle cx="100" cy="115" r="26" fill="#ecfdf5" stroke="#10b981" stroke-width="2.5" filter="url(#sh)"/>
    <text x="100" y="122" font-size="18" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">x₀</text>

    <path d="M 130 115 L 200 115" stroke="#ef4444" stroke-width="2.5" marker-end="url(#rarr)"/>
    <text x="250" y="120" font-size="26" fill="#94a3b8" font-weight="bold" text-anchor="middle">···</text>
    <path d="M 290 115 L 360 115" stroke="#ef4444" stroke-width="2.5" marker-end="url(#rarr)"/>

    <circle cx="400" cy="115" r="26" fill="#fff7ed" stroke="#f97316" stroke-width="2.5" filter="url(#sh)"/>
    <text x="400" y="122" font-size="17" fill="#c2410c" font-weight="bold" text-anchor="middle" font-style="italic">x_{t-1}</text>

    <path d="M 430 115 L 530 115" stroke="#ef4444" stroke-width="3" marker-end="url(#rarr)"/>
    <rect x="440" y="70" width="80" height="26" rx="6" fill="#fef2f2" stroke="#ef4444" stroke-width="1.2"/>
    <text x="480" y="88" font-size="11.5" fill="#991b1b" font-weight="bold" text-anchor="middle">q(x_t|x_{t-1})</text>

    <circle cx="570" cy="115" r="26" fill="#fef2f2" stroke="#ef4444" stroke-width="2.5" filter="url(#sh)"/>
    <text x="570" y="122" font-size="17" fill="#991b1b" font-weight="bold" text-anchor="middle" font-style="italic">x_t</text>

    <path d="M 600 115 L 670 115" stroke="#ef4444" stroke-width="2.5" marker-end="url(#rarr)"/>
    <text x="715" y="120" font-size="26" fill="#94a3b8" font-weight="bold" text-anchor="middle">···</text>
    <path d="M 750 115 L 810 115" stroke="#ef4444" stroke-width="2.5" marker-end="url(#rarr)"/>

    <circle cx="840" cy="115" r="26" fill="#fef2f2" stroke="#991b1b" stroke-width="2.5" filter="url(#sh)"/>
    <text x="840" y="122" font-size="17" fill="#7f1d1d" font-weight="bold" text-anchor="middle" font-style="italic">x_T</text>
    """
    return _svg_wrap(900, 210, c)


def fig_8_5() -> str:
    """Fig 8-5: Reverse Denoising Process (逆扩散过程)."""
    c = """
    <rect x="20" y="15" width="860" height="200" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <text x="450" y="45" font-size="14.5" fill="#2563eb" font-weight="bold" text-anchor="middle">逆扩散去噪过程 (神经网络逐步去除噪声)</text>

    <!-- Nodes from x_T to x_0 -->
    <circle cx="100" cy="115" r="26" fill="#fef2f2" stroke="#991b1b" stroke-width="2.5" filter="url(#sh)"/>
    <text x="100" y="122" font-size="17" fill="#7f1d1d" font-weight="bold" text-anchor="middle" font-style="italic">x_T</text>

    <path d="M 130 115 L 200 115" stroke="#2563eb" stroke-width="2.5" marker-end="url(#barr)"/>
    <text x="250" y="120" font-size="26" fill="#94a3b8" font-weight="bold" text-anchor="middle">···</text>
    <path d="M 290 115 L 360 115" stroke="#2563eb" stroke-width="2.5" marker-end="url(#barr)"/>

    <circle cx="400" cy="115" r="26" fill="#fff7ed" stroke="#f97316" stroke-width="2.5" filter="url(#sh)"/>
    <text x="400" y="122" font-size="17" fill="#c2410c" font-weight="bold" text-anchor="middle" font-style="italic">x_t</text>

    <path d="M 430 115 L 530 115" stroke="#2563eb" stroke-width="3" marker-end="url(#barr)"/>
    <rect x="435" y="70" width="90" height="26" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.2"/>
    <text x="480" y="88" font-size="11.5" fill="#1e40af" font-weight="bold" text-anchor="middle">p_θ(x_{t-1}|x_t)</text>

    <circle cx="570" cy="115" r="26" fill="#eff6ff" stroke="#3b82f6" stroke-width="2.5" filter="url(#sh)"/>
    <text x="570" y="122" font-size="17" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x_{t-1}</text>

    <path d="M 600 115 L 670 115" stroke="#2563eb" stroke-width="2.5" marker-end="url(#barr)"/>
    <text x="715" y="120" font-size="26" fill="#94a3b8" font-weight="bold" text-anchor="middle">···</text>
    <path d="M 750 115 L 810 115" stroke="#2563eb" stroke-width="2.5" marker-end="url(#barr)"/>

    <circle cx="840" cy="115" r="26" fill="#ecfdf5" stroke="#10b981" stroke-width="2.5" filter="url(#sh)"/>
    <text x="840" y="122" font-size="18" fill="#065f46" font-weight="bold" text-anchor="middle" font-style="italic">x₀</text>
    """
    return _svg_wrap(900, 210, c)


def fig_8_6() -> str:
    """Fig 8-6: Denoising Neural Network Block (进行噪声去除的神经网络)."""
    c = """
    <rect x="20" y="15" width="860" height="220" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Input 1: x_t -->
    <circle cx="160" cy="80" r="28" fill="#fef2f2" stroke="#ef4444" stroke-width="2.5" filter="url(#sh)"/>
    <text x="160" y="87" font-size="19" fill="#991b1b" font-weight="bold" text-anchor="middle" font-style="italic">x_t</text>
    <text x="160" y="128" font-size="12" fill="#64748b" text-anchor="middle">当前噪声图像</text>

    <!-- Input 2: t -->
    <circle cx="160" cy="170" r="24" fill="#f1f5f9" stroke="#64748b" stroke-width="2.5" filter="url(#sh)"/>
    <text x="160" y="177" font-size="18" fill="#334155" font-weight="bold" text-anchor="middle" font-style="italic">t</text>
    <text x="160" y="210" font-size="12" fill="#64748b" text-anchor="middle">时刻步 (Timestep)</text>

    <!-- Arrows to Network -->
    <path d="M 195 80 L 320 105" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>
    <path d="M 190 170 L 320 135" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <!-- Neural Network NN(theta) -->
    <polygon points="330,70 470,90 470,150 330,170" fill="url(#bgrad)" filter="url(#sh)"/>
    <text x="400" y="125" font-size="17" fill="#ffffff" font-weight="bold" text-anchor="middle">NN(θ)</text>
    <text x="400" y="195" font-size="13" fill="#1e40af" font-weight="bold" text-anchor="middle">去噪神经网络 (U-Net)</text>

    <!-- Arrow to Output -->
    <path d="M 475 120 L 590 120" stroke="#2563eb" stroke-width="3" marker-end="url(#barr)"/>

    <!-- Output: xhat_{t-1} -->
    <circle cx="630" cy="120" r="28" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5" filter="url(#sh)"/>
    <text x="630" y="127" font-size="19" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x̂_{t-1}</text>
    <text x="630" y="170" font-size="13" fill="#1e40af" font-weight="bold" text-anchor="middle">预测的高斯均值向量 μ_θ</text>
    """
    return _svg_wrap(900, 240, c)


def fig_8_7() -> str:
    """Fig 8-7: ELBO Roadmap Simplification Diagram (ELBO 计算的改进路线图)."""
    c = """
    <rect x="20" y="15" width="860" height="230" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Step 1: Raw ELBO -->
    <g transform="translate(60, 60)">
      <rect x="0" y="0" width="220" height="120" rx="10" fill="#ffffff" stroke="#ef4444" stroke-width="2" filter="url(#sh)"/>
      <text x="110" y="30" font-size="14" fill="#991b1b" font-weight="bold" text-anchor="middle">① 原始 ELBO 目标</text>
      <text x="110" y="65" font-size="12" fill="#334155" text-anchor="middle">𝔼_q [log (p(x_{0:T}) / q(x_{1:T}|x₀))]</text>
      <text x="110" y="95" font-size="11" fill="#64748b" text-anchor="middle">方差极大，难以直接优化</text>
    </g>

    <path d="M 290 120 L 340 120" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <!-- Step 2: Decomposition via Bayes -->
    <g transform="translate(350, 60)">
      <rect x="0" y="0" width="230" height="120" rx="10" fill="#ffffff" stroke="#f59e0b" stroke-width="2" filter="url(#sh)"/>
      <text x="115" y="30" font-size="14" fill="#b45309" font-weight="bold" text-anchor="middle">② 贝叶斯法则分解项</text>
      <text x="115" y="65" font-size="12" fill="#334155" text-anchor="middle">∑ D_KL(q(x_t|x_{t-1},x₀) ∥ p_θ)</text>
      <text x="115" y="95" font-size="11" fill="#64748b" text-anchor="middle">将全局联合化为单步 KL 散度</text>
    </g>

    <path d="M 590 120 L 640 120" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <!-- Step 3: Closed-form Gaussians -->
    <g transform="translate(650, 60)">
      <rect x="0" y="0" width="210" height="120" rx="10" fill="#ecfdf5" stroke="#10b981" stroke-width="2" filter="url(#sh)"/>
      <text x="105" y="30" font-size="14" fill="#065f46" font-weight="bold" text-anchor="middle">③ 高斯闭式解优化</text>
      <text x="105" y="65" font-size="13" fill="#047857" font-weight="bold" text-anchor="middle">MSE 损失函数 ‖ε - ε_θ‖²</text>
      <text x="105" y="95" font-size="11" fill="#059669" text-anchor="middle">高效且训练稳定的核心损失</text>
    </g>
    """
    return _svg_wrap(900, 250, c)

def fig_7_10() -> str:
    """Fig 7-10: ELBO Computation Flow Diagram (计算 ELBO 的流程)."""
    c = """
    <rect x="20" y="15" width="860" height="230" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <!-- Input x -->
    <circle cx="70" cy="115" r="24" fill="#ffffff" stroke="#2563eb" stroke-width="2.5" filter="url(#sh)"/>
    <text x="70" y="122" font-size="19" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x</text>

    <path d="M 98 115 L 140 115" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <!-- Encoder q_psi -->
    <polygon points="145,75 235,55 235,175 145,155" fill="url(#bgrad)" filter="url(#sh)"/>
    <text x="190" y="112" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">编码器</text>
    <text x="190" y="132" font-size="12" fill="#bfdbfe" text-anchor="middle">q_ψ(z|x)</text>

    <path d="M 240 115 L 290 115" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <!-- Latent code z -->
    <circle cx="320" cy="115" r="24" fill="#ffffff" stroke="#8b5cf6" stroke-width="2.5" filter="url(#sh)"/>
    <text x="320" y="122" font-size="19" fill="#6b21a8" font-weight="bold" text-anchor="middle" font-style="italic">z</text>

    <!-- Branch 1: Decoder p_theta to Reconstruction Loss -->
    <path d="M 350 100 L 410 75" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <polygon points="415,50 505,30 505,120 415,100" fill="url(#pgrad)" filter="url(#sh)"/>
    <text x="460" y="72" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">解码器</text>
    <text x="460" y="92" font-size="12" fill="#e9d5ff" text-anchor="middle">p_θ(x|z)</text>

    <path d="M 510 75 L 560 75" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <rect x="565" y="50" width="130" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
    <text x="630" y="73" font-size="13" fill="#1e40af" font-weight="bold" text-anchor="middle">重建损失项</text>
    <text x="630" y="91" font-size="11.5" fill="#2563eb" text-anchor="middle">𝔼_q [log p_θ(x|z)]</text>

    <!-- Branch 2: Prior p(z) to KL Penalty -->
    <path d="M 350 135 L 560 170" stroke="#f59e0b" stroke-width="2.5" marker-end="url(#darr)"/>
    
    <rect x="565" y="145" width="130" height="50" rx="8" fill="#fef3c7" stroke="#f59e0b" stroke-width="2"/>
    <text x="630" y="168" font-size="13" fill="#b45309" font-weight="bold" text-anchor="middle">KL 正则化项</text>
    <text x="630" y="186" font-size="11" fill="#b45309" text-anchor="middle">-D_KL(q_ψ ∥ p(z))</text>

    <!-- Sum to ELBO -->
    <path d="M 700 75 L 755 105" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>
    <path d="M 700 170 L 755 125" stroke="#334155" stroke-width="2.5" marker-end="url(#darr)"/>

    <rect x="760" y="90" width="105" height="50" rx="10" fill="#ecfdf5" stroke="#10b981" stroke-width="2.5"/>
    <text x="812" y="115" font-size="15" fill="#065f46" font-weight="bold" text-anchor="middle">ELBO</text>
    <text x="812" y="132" font-size="11" fill="#047857" text-anchor="middle">证据下界</text>
    """
    return _svg_wrap(900, 250, c)


def fig_8_13() -> str:
    """Fig 8-13: Internal division point representation in image space."""
    c = """
    <rect x="20" y="15" width="860" height="190" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <line x1="120" y1="120" x2="760" y2="120" stroke="#334155" stroke-width="3"/>

    <circle cx="120" cy="120" r="14" fill="#2563eb" stroke="#ffffff" stroke-width="3" filter="url(#sh)"/>
    <text x="120" y="90" font-size="18" fill="#1e40af" font-weight="bold" text-anchor="middle" font-style="italic">x₀</text>
    <text x="120" y="160" font-size="13" fill="#475569" text-anchor="middle">原始无噪图像</text>

    <circle cx="760" cy="120" r="14" fill="#ef4444" stroke="#ffffff" stroke-width="3" filter="url(#sh)"/>
    <text x="760" y="90" font-size="18" fill="#991b1b" font-weight="bold" text-anchor="middle" font-style="italic">x_t</text>
    <text x="760" y="160" font-size="13" fill="#475569" text-anchor="middle">当前加噪图像</text>

    <circle cx="500" cy="120" r="15" fill="#f59e0b" stroke="#ffffff" stroke-width="3" filter="url(#sh)"/>
    <text x="500" y="80" font-size="17" fill="#b45309" font-weight="bold" text-anchor="middle" font-style="italic">μ_q(x_t, x₀)</text>
    <text x="500" y="165" font-size="13" fill="#b45309" font-weight="bold" text-anchor="middle">后验均值 (内分点)</text>

    <path d="M 140 105 C 260 65, 380 65, 480 105" fill="none" stroke="#2563eb" stroke-width="2" stroke-dasharray="4 3" marker-end="url(#barr)"/>
    <text x="310" y="65" font-size="12" fill="#2563eb" font-weight="bold" text-anchor="middle">权重: √ᾱ_{t-1} (1-α_t)</text>

    <path d="M 740 105 C 660 65, 580 65, 520 105" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="4 3" marker-end="url(#darr)"/>
    <text x="630" y="65" font-size="12" fill="#dc2626" font-weight="bold" text-anchor="middle">权重: √α_t (1-ᾱ_{t-1})</text>
    """
    return _svg_wrap(900, 210, c)


def fig_9_6() -> str:
    """Fig 9-6: ConvBlock internal layers structure."""
    c = """
    <rect x="20" y="15" width="860" height="150" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <rect x="50" y="50" width="115" height="75" rx="8" fill="url(#bgrad)" filter="url(#sh)"/>
    <text x="107" y="85" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">Conv2d</text>
    <text x="107" y="105" font-size="11" fill="#bfdbfe" text-anchor="middle">3×3, pad 1</text>

    <path d="M 170 87 L 195 87" stroke="#334155" stroke-width="2" marker-end="url(#darr)"/>

    <rect x="200" y="50" width="115" height="75" rx="8" fill="url(#tgrad)" filter="url(#sh)"/>
    <text x="257" y="85" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">BatchNorm</text>
    <text x="257" y="105" font-size="11" fill="#cffafe" text-anchor="middle">归一化</text>

    <path d="M 320 87 L 345 87" stroke="#334155" stroke-width="2" marker-end="url(#darr)"/>

    <rect x="350" y="50" width="80" height="75" rx="8" fill="url(#agrad)" filter="url(#sh)"/>
    <text x="390" y="92" font-size="15" fill="#ffffff" font-weight="bold" text-anchor="middle">ReLU</text>

    <path d="M 435 87 L 465 87" stroke="#334155" stroke-width="2" marker-end="url(#darr)"/>

    <rect x="470" y="50" width="115" height="75" rx="8" fill="url(#bgrad)" filter="url(#sh)"/>
    <text x="527" y="85" font-size="14" fill="#ffffff" font-weight="bold" text-anchor="middle">Conv2d</text>
    <text x="527" y="105" font-size="11" fill="#bfdbfe" text-anchor="middle">3×3, pad 1</text>

    <path d="M 590 87 L 615 87" stroke="#334155" stroke-width="2" marker-end="url(#darr)"/>

    <rect x="620" y="50" width="115" height="75" rx="8" fill="url(#tgrad)" filter="url(#sh)"/>
    <text x="677" y="85" font-size="13" fill="#ffffff" font-weight="bold" text-anchor="middle">BatchNorm</text>
    <text x="677" y="105" font-size="11" fill="#cffafe" text-anchor="middle">归一化</text>

    <path d="M 740 87 L 765 87" stroke="#334155" stroke-width="2" marker-end="url(#darr)"/>

    <rect x="770" y="50" width="80" height="75" rx="8" fill="url(#agrad)" filter="url(#sh)"/>
    <text x="810" y="92" font-size="15" fill="#ffffff" font-weight="bold" text-anchor="middle">ReLU</text>
    """
    return _svg_wrap(900, 180, c)


def fig_10_11() -> str:
    """Fig 10-11: Classifier-Free Guidance extrapolation vector diagram."""
    c = """
    <rect x="20" y="15" width="860" height="230" rx="14" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5" filter="url(#sh)"/>

    <circle cx="100" cy="180" r="6" fill="#334155"/>
    <text x="80" y="185" font-size="14" fill="#334155" font-weight="bold">原点</text>

    <line x1="100" y1="180" x2="380" y2="130" stroke="#3b82f6" stroke-width="3" marker-end="url(#barr)"/>
    <text x="240" y="170" font-size="14" fill="#1e40af" font-weight="bold">无条件得分: s_θ(x_t, ∅)</text>

    <line x1="100" y1="180" x2="480" y2="80" stroke="#f59e0b" stroke-width="3" marker-end="url(#darr)"/>
    <text x="290" y="110" font-size="14" fill="#b45309" font-weight="bold">条件得分: s_θ(x_t, y)</text>

    <line x1="380" y1="130" x2="480" y2="80" stroke="#10b981" stroke-width="2.5" stroke-dasharray="4 3" marker-end="url(#darr)"/>
    <text x="445" y="125" font-size="13" fill="#065f46" font-weight="bold">差向量 Δ</text>

    <line x1="380" y1="130" x2="720" y2="-40" stroke="#ef4444" stroke-width="3.5" marker-end="url(#darr)"/>
    
    <g transform="translate(560, 40)">
      <rect x="0" y="0" width="280" height="65" rx="8" fill="#fef2f2" stroke="#ef4444" stroke-width="2"/>
      <text x="140" y="28" font-size="13" fill="#991b1b" font-weight="bold" text-anchor="middle">无分类器指引得分 (γ &gt; 1)</text>
      <text x="140" y="48" font-size="12" fill="#b91c1c" text-anchor="middle">s̃ = s_θ(x_t, ∅) + γ [s_θ(x_t, y) - s_θ(x_t, ∅)]</text>
    </g>
    """
    return _svg_wrap(900, 260, c)


def draw_fig_9_10(png_path: Path) -> None:
    """Fig 9-10: Sinusoidal Positional Embeddings waveforms."""
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=300)
    t = np.arange(0, 100)
    
    dim = 64
    for i, color, label in [
        (0, "#2563eb", "dim = 0 (高频基波)"),
        (4, "#06b6d4", "dim = 4 (中高频)"),
        (16, "#f59e0b", "dim = 16 (中低频)"),
        (32, "#8b5cf6", "dim = 32 (低频慢波)"),
    ]:
        freq = 1 / (10000 ** (2 * i / dim))
        y = np.sin(t * freq)
        ax.plot(t, y, color=color, linewidth=2.2, label=label)

    ax.set_xlabel("时刻 t (Timestep)", fontsize=11, color="#334155")
    ax.set_ylabel("编码值 (Value)", fontsize=11, color="#334155")
    ax.set_xlim(0, 100)
    ax.set_ylim(-1.25, 1.25)
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=10)
    ax.tick_params(colors="#475569")

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


def draw_fig_9_13(png_path: Path) -> None:
    """Fig 9-13: Diffusion Model training loss convergence curve."""
    fig, ax = plt.subplots(figsize=(6.8, 4.2), dpi=300)
    epochs = np.arange(1, 21)
    
    np.random.seed(42)
    loss = 0.02 + 0.18 * np.exp(-epochs / 4.5) + np.random.normal(0, 0.003, len(epochs))

    ax.plot(epochs, loss, color="#2563eb", linewidth=2.5, marker="o", markersize=5, label="训练损失 (MSE Loss)")
    ax.set_xlabel("Epoch", fontsize=11, color="#334155")
    ax.set_ylabel("Loss", fontsize=11, color="#334155")
    ax.set_xticks(range(2, 21, 2))
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=10.5)
    ax.tick_params(colors="#475569")

    plt.tight_layout()
    plt.savefig(png_path)
    plt.close(fig)


CH7_10_SVGS = {
    "7-7": fig_7_7,
    "7-10": fig_7_10,
    "7-13": fig_7_13,
    "8-2": fig_8_2,
    "8-3": fig_8_3,
    "8-4": fig_8_4,
    "8-5": fig_8_5,
    "8-6": fig_8_6,
    "8-7": fig_8_7,
    "8-11": fig_8_7,
    "8-13": fig_8_13,
    "9-6": fig_9_6,
    "10-11": fig_10_11,
}

CH7_10_PLOTS = {
    "9-10": draw_fig_9_10,
    "9-13": draw_fig_9_13,
}
