"""Google Colab compute: the GPU catalog, a session wrapper over the `colab` CLI, and GPU probes."""

import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Self

from .ocr_models import OCRModel

UPLOAD_CHUNK_MB = 25


@dataclass(frozen=True)
class ColabGPU:
    name: str
    card: str
    vram_gb: float
    compute_capability: float
    cu_per_hour: float | None = None

    @property
    def bf16(self) -> bool:
        return self.compute_capability >= 8.0


COLAB_GPUS: dict[str, ColabGPU] = {
    g.name: g
    for g in (
        ColabGPU("T4", "Tesla T4", 14.6, 7.5, 1.07),
        ColabGPU("L4", "NVIDIA L4", 22.0, 8.9, 1.54),
        ColabGPU("A100", "NVIDIA A100-SXM4-40GB", 39.5, 8.0, 5.3),
        ColabGPU("H100", "NVIDIA H100 80GB HBM3", 80.0, 9.0),
        ColabGPU("G4", "NVIDIA RTX PRO 6000 Blackwell Server Edition", 95.0, 12.0, 8.9),
    )
}


def colab_gpu(name: str) -> ColabGPU:
    try:
        return COLAB_GPUS[name.upper()]
    except KeyError:
        raise ValueError(
            f"Unknown Colab GPU {name!r}; expected one of {sorted(COLAB_GPUS)}"
        ) from None


def fit_problem(model: OCRModel, gpu: ColabGPU) -> str | None:
    """Why `model` cannot run on `gpu`, or None when it fits."""
    if gpu.compute_capability < model.min_compute_capability:
        return f"needs compute capability {model.min_compute_capability}, {gpu.name} has {gpu.compute_capability}"
    if model.needs_bf16 and not gpu.bf16:
        return f"needs bfloat16, which {gpu.name} lacks"
    if model.vram_gb() > gpu.vram_gb:
        return (
            f"needs ~{model.vram_gb():.0f} GB VRAM, {gpu.name} has {gpu.vram_gb:.0f} GB"
        )
    return None


def colab_cli(
    *args: str, stdin: str | None = None, timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the CLI; a call that hangs returns status 124 instead of stalling the run."""
    command = ["colab", *args]
    try:
        return subprocess.run(
            command,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        out = e.stdout if isinstance(e.stdout, str) else ""
        err = e.stderr if isinstance(e.stderr, str) else ""
        return subprocess.CompletedProcess(command, 124, out, err)


@dataclass(frozen=True)
class AccountUsage:
    balance: float
    rate_per_hour: float
    active_assignments: int


def _number_after(label: str, text: str) -> float | None:
    for line in text.splitlines():
        if line.strip().startswith(label):
            value = line.split(":", 1)[1].split()[0].removesuffix("/hr")
            return float(value)
    return None


def account_usage() -> AccountUsage | None:
    """Compute-unit balance and burn rate, or None when the CLI is missing or signed out."""
    if shutil.which("colab") is None:
        return None
    try:
        out = colab_cli("usage", timeout=20).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    balance = _number_after("Current balance", out)
    if balance is None:
        return None
    return AccountUsage(
        balance=balance,
        rate_per_hour=_number_after("Usage rate", out) or 0.0,
        active_assignments=int(_number_after("Active assignments", out) or 0),
    )


class ColabSession:
    """One named Colab VM. Use it as a context manager so the VM always stops."""

    def __init__(self, name: str, gpu: str) -> None:
        self.name = name
        self.gpu = gpu

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.stop()

    def _log(self, message: str) -> None:
        print(f"[{self.name}] {message}", flush=True)

    def start(self) -> bool:
        self._log(f"Launching Colab VM ({self.gpu})...")
        res = colab_cli("new", "--session", self.name, "--gpu", self.gpu, timeout=900)
        if res.returncode != 0:
            self._log(
                f"Session creation error: {res.stderr.strip() or res.stdout.strip()}"
            )
        return res.returncode == 0

    def install(self, packages: tuple[str, ...]) -> bool:
        if not packages:
            return True
        self._log(f"Installing {' '.join(packages)}...")
        for attempt in range(1, 4):
            res = colab_cli("install", "--session", self.name, *packages, timeout=900)
            if res.returncode == 0:
                return True
            self._log(f"Install attempt {attempt} failed: {res.stderr.strip()[-200:] or res.stdout.strip()[-200:]}")
            time.sleep(5)
            exec_res = self.exec(
                f"import subprocess, sys\nsubprocess.run([sys.executable, '-m', 'pip', 'install', *{list(packages)!r}], check=True)\n",
                timeout=600,
            )
            if exec_res.returncode == 0:
                self._log("Install succeeded via pip fallback.")
                return True
        return False
    def exec(self, code: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
        return colab_cli(
            "exec",
            "--session",
            self.name,
            "--timeout",
            str(timeout),
            stdin=code,
            timeout=timeout + 60,
        )

    def ls(self, remote_dir: str) -> list[str]:
        res = colab_cli("ls", "--session", self.name, remote_dir, timeout=90)
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]

    def download(self, remote: str, local: Path) -> bool:
        res = colab_cli(
            "download", "--session", self.name, remote, str(local), timeout=1800
        )
        return res.returncode == 0 and local.exists()

    def upload(self, local: Path, remote: str) -> bool:
        """Upload in chunks of at most 25 MB; larger Jupyter payloads fail with HTTP 400."""
        chunk = UPLOAD_CHUNK_MB * 1024 * 1024
        if local.stat().st_size <= chunk:
            res = colab_cli(
                "upload", "--session", self.name, str(local), remote, timeout=900
            )
            return res.returncode == 0
        data = local.read_bytes()
        parts_dir = local.parent / f"_parts_{self.name}"
        parts_dir.mkdir(parents=True, exist_ok=True)
        try:
            for idx, start in enumerate(range(0, len(data), chunk)):
                part = parts_dir / f"part_{idx:03d}.bin"
                _ = part.write_bytes(data[start : start + chunk])
                res = colab_cli(
                    "upload",
                    "--session",
                    self.name,
                    str(part),
                    f"/content/part_{idx:03d}.bin",
                    timeout=900,
                )
                part.unlink()
                if res.returncode != 0:
                    return False
            reassemble = (
                "import glob, os\n"
                "parts = sorted(glob.glob('/content/part_*.bin'))\n"
                f"with open({remote!r}, 'wb') as out:\n"
                "    for p in parts:\n"
                "        out.write(open(p, 'rb').read())\n"
                "        os.remove(p)\n"
            )
            return self.exec(reassemble).returncode == 0
        finally:
            shutil.rmtree(parts_dir, ignore_errors=True)

    def stop(self) -> None:
        try:
            _ = colab_cli("stop", "--session", self.name, timeout=30)
            self._log("Session stopped.")
        except (subprocess.SubprocessError, OSError) as e:
            self._log(f"Failed to stop session: {e}")


PROBE_CODE = (
    "import json, torch\n"
    "p = torch.cuda.get_device_properties(0)\n"
    "print(json.dumps({'card': p.name, 'vram_gb': round(p.total_memory / 2**30, 1),"
    " 'compute_capability': float(f'{p.major}.{p.minor}'), 'torch': torch.__version__}))\n"
)


@dataclass(frozen=True)
class GPUProbe:
    gpu: str
    card: str = ""
    vram_gb: float = 0.0
    compute_capability: float = 0.0
    cu_per_hour: float | None = None
    startup_sec: float = 0.0
    torch: str = ""
    error: str = ""


def probe_gpu(gpu: str) -> GPUProbe:
    """Start one VM, read its card and compute-unit burn rate, then stop it."""
    before = account_usage()
    t0 = time.time()
    with ColabSession(f"probe-{gpu.lower()}", gpu) as session:
        if not session.start():
            return GPUProbe(gpu, error="no VM available for this account or tier")
        startup = time.time() - t0
        res = session.exec(PROBE_CODE, timeout=120)
        after = account_usage()
    lines = [l for l in res.stdout.splitlines() if l.startswith("{")]
    if not lines:
        return GPUProbe(gpu, startup_sec=startup, error=res.stderr.strip()[-300:])
    info = json.loads(lines[-1])
    rate = None
    if before is not None and after is not None:
        rate = round(after.rate_per_hour - before.rate_per_hour, 2)
    return GPUProbe(gpu=gpu, cu_per_hour=rate, startup_sec=round(startup, 1), **info)


def write_probes(probes: list[GPUProbe], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(
        json.dumps([asdict(p) for p in probes], indent=2) + "\n", encoding="utf-8"
    )
