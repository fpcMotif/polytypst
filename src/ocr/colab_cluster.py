"""Self-hosted OCR on Colab GPUs: split pages across VMs, run `gpu_worker`, collect transcripts.

Every VM is a `ColabSession`, so it stops even when a node fails. A run that times out
or whose worker dies still downloads the pages finished so far.
"""

import json
import shutil
import tarfile
import tempfile
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from .colab import ColabSession, account_usage, colab_gpu, fit_problem
from .gpu_worker import STATS_NAME
from .ocr_models import DEFAULT_OCR_MODEL, OCRModel, ocr_model
from .pages import PageImage

OCR_DIR = Path(__file__).resolve().parent
REMOTE_PKG = "/content/ocrpkg"
POLL_SEC = 15

PACK_PARTIAL_CODE = (
    "import pathlib, tarfile\n"
    "files = sorted(pathlib.Path('/content/markdown').glob('*.md'))\n"
    "with tarfile.open('/content/markdown.tar.gz', 'w:gz') as t:\n"
    "    for f in files:\n"
    "        t.add(f, arcname=f.name)\n"
    "print(len(files))\n"
)

POLL_CODE = (
    "import json, os, pathlib\n"
    "pid = int(open('/content/worker.pid').read())\n"
    "stat = pathlib.Path(f'/proc/{pid}/stat')\n"
    "alive = stat.exists() and stat.read_text().split()[2] != 'Z'\n"
    "log = pathlib.Path('/content/worker.log')\n"
    "print(json.dumps({'done': os.path.exists('/content/markdown.tar.gz'), 'alive': alive,"
    " 'pages': len(list(pathlib.Path('/content/markdown').glob('*.md'))),"
    " 'log': log.read_text()[-600:] if log.exists() else ''}))\n"
)


@dataclass
class ClusterStats:
    total_pages: int
    completed_pages: int
    duration_sec: float
    effective_pages_per_sec: float
    active_workers: int
    worker_stats: list[dict[str, object]] = field(default_factory=list)


class ColabOCRCluster:
    """Transcribe pages on `num_workers` Colab VMs of one GPU type with one OCR model."""

    def __init__(
        self,
        gpu_type: str = "G4",
        num_workers: int = 2,
        shards_per_gpu: int = 3,
        session_prefix: str = "ocr",
        timeout_sec: float = 7200.0,
        prompt: str | None = None,
        model: str = DEFAULT_OCR_MODEL,
    ):
        self.gpu_type: str = gpu_type
        self.num_workers: int = num_workers
        self.shards_per_gpu: int = shards_per_gpu
        self.session_prefix: str = session_prefix
        self.timeout_sec: float = timeout_sec
        self.prompt: str | None = prompt
        self.model: OCRModel = ocr_model(model)

    @staticmethod
    def is_colab_available() -> bool:
        return account_usage() is not None

    @staticmethod
    def partition_pages(
        pages: list[PageImage], num_chunks: int, interleaved: bool = False
    ) -> list[list[PageImage]]:
        """Split a list of pages into balanced chunks."""
        if not pages or num_chunks <= 1:
            return [pages]
        if interleaved:
            return [
                pages[i::num_chunks] for i in range(num_chunks) if pages[i::num_chunks]
            ]
        k, m = divmod(len(pages), num_chunks)
        chunks: list[list[PageImage]] = []
        for i in range(num_chunks):
            start = i * k + min(i, m)
            end = (i + 1) * k + min(i + 1, m)
            chunks.append(pages[start:end])
        return [c for c in chunks if len(c) > 0]

    @staticmethod
    def pack_archive(pages: Sequence[PageImage], dest_archive: Path) -> Path:
        """Create a compressed tar.gz of page images named `p_NNN<suffix>` for the worker."""
        dest_archive.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(dest_archive, "w:gz") as tar:
            for page in pages:
                suffix = page.path.suffix.lower()
                tar.add(page.path, arcname=f"p_{page.number:03d}{suffix}")
        return dest_archive

    def _prepare(
        self, session: ColabSession, pages_archive: Path, scratch: Path
    ) -> bool:
        if not session.start() or not session.install(self.model.pip):
            return False
        setup = (
            "import os, pathlib, shutil, tarfile\n"
            f"os.makedirs({REMOTE_PKG!r}, exist_ok=True)\n"
            f"pathlib.Path({REMOTE_PKG!r}, '__init__.py').touch()\n"
            "for p in ['/content/markdown.tar.gz', '/content/worker.log', '/content/worker.pid']:\n"
            "    if os.path.exists(p): os.remove(p)\n"
            "if os.path.exists('/content/markdown'): shutil.rmtree('/content/markdown')\n"
            "if os.path.exists('/content/pages'): shutil.rmtree('/content/pages')\n"
            "os.makedirs('/content/markdown', exist_ok=True)\n"
        )
        if session.exec(setup).returncode != 0:
            return False
        uploads = [
            (pages_archive, "/content/pages.tar.gz"),
            (OCR_DIR / "ocr_models.py", f"{REMOTE_PKG}/ocr_models.py"),
            (OCR_DIR / "blank.py", f"{REMOTE_PKG}/blank.py"),
            (OCR_DIR / "gpu_worker.py", f"{REMOTE_PKG}/gpu_worker.py"),
        ]
        if self.prompt is not None:
            prompt_file = scratch / f"{session.name}.prompt.txt"
            _ = prompt_file.write_text(self.prompt, encoding="utf-8")
            uploads.append((prompt_file, "/content/prompt.txt"))
        for local, remote in uploads:
            if not session.upload(local, remote):
                print(f"[{session.name}] Failed to upload {local.name}.")
                return False
        unpack = (
            "import tarfile\n"
            "with tarfile.open('/content/pages.tar.gz') as t:\n"
            "    t.extractall('/content/pages', filter='data')\n"
        )
        return session.exec(unpack).returncode == 0

    def _launch(self, session: ColabSession) -> bool:
        args = [
            "-m",
            "ocrpkg.gpu_worker",
            "--pages",
            "/content/pages",
            "--out",
            "/content/markdown",
            "--shards",
            str(self.shards_per_gpu),
            "--model",
            self.model.key,
        ]
        if self.prompt is not None:
            args += ["--prompt-file", "/content/prompt.txt"]
        launch = (
            "import subprocess, sys\n"
            "log = open('/content/worker.log', 'w')\n"
            f"p = subprocess.Popen([sys.executable, *{args!r}], cwd='/content',"
            " stdout=log, stderr=subprocess.STDOUT)\n"
            "open('/content/worker.pid', 'w').write(str(p.pid))\n"
        )
        print(f"[{session.name}] Launching {self.model.key} on {self.gpu_type}...")
        return session.exec(launch, timeout=30).returncode == 0

    def _wait(self, session: ColabSession) -> bool:
        """Poll until the worker archives its output; False on timeout or a dead worker."""
        start = time.time()
        while time.time() - start < self.timeout_sec:
            time.sleep(POLL_SEC)
            lines = [
                l
                for l in session.exec(POLL_CODE, timeout=30).stdout.splitlines()
                if l.startswith("{")
            ]
            if not lines:
                continue
            state = json.loads(lines[-1])
            if state["done"]:
                return True
            print(
                f"[{session.name}] {state['pages']} pages transcribed ({time.time() - start:.0f}s)"
            )
            if not state["alive"]:
                print(
                    f"[{session.name}] Worker exited early. Log tail:\n{state['log']}"
                )
                return False
        print(f"[{session.name}] Timed out after {self.timeout_sec:.0f}s.")
        return False

    def _run_node(
        self,
        session: ColabSession,
        node_pages: list[PageImage],
        out_dir: Path,
        scratch: Path,
    ) -> tuple[int, dict[str, object] | None]:
        pages_archive = self.pack_archive(
            node_pages, scratch / f"{session.name}.pages.tar.gz"
        )
        with session:
            if not self._prepare(session, pages_archive, scratch) or not self._launch(
                session
            ):
                return 0, None
            if not self._wait(session):
                _ = session.exec(PACK_PARTIAL_CODE, timeout=120)
            md_archive = scratch / f"{session.name}.markdown.tar.gz"
            log_copy = out_dir / f"_{session.name}.worker.log"
            _ = session.download("/content/worker.log", log_copy)
            if not session.download("/content/markdown.tar.gz", md_archive):
                print(f"[{session.name}] Download failed.")
                return 0, None
        node_dir = scratch / session.name
        with tarfile.open(md_archive, "r:gz") as tar:
            tar.extractall(node_dir, filter="data")
        stats_file = node_dir / STATS_NAME
        stats = (
            json.loads(stats_file.read_text(encoding="utf-8"))
            if stats_file.exists()
            else None
        )
        transcripts = sorted(node_dir.glob("p_*.md"))
        for md in transcripts:
            _ = shutil.move(md, out_dir / md.name)
        return len(transcripts), stats

    def run_cluster(self, pages: Sequence[PageImage], out_dir: Path) -> ClusterStats:
        """Transcribe `pages` into `out_dir` on up to `num_workers` VMs at once."""
        out_dir.mkdir(parents=True, exist_ok=True)
        pending = list(pages)
        print(
            f"=== COLAB OCR: {self.model.key} on {self.num_workers}x {self.gpu_type} | "
            f"{len(pending)} pages ==="
        )
        if not pending:
            return ClusterStats(0, 0, 0.0, 0.0, 0)
        problem = fit_problem(self.model, colab_gpu(self.gpu_type))
        if problem:
            raise ValueError(
                f"{self.model.key} cannot run on {self.gpu_type}: {problem}"
            )

        chunks = self.partition_pages(
            pending, min(self.num_workers, len(pending)), interleaved=True
        )
        sessions = [
            ColabSession(f"{self.session_prefix}-{i + 1}", self.gpu_type)
            for i in range(len(chunks))
        ]
        t0 = time.time()
        with tempfile.TemporaryDirectory(prefix="colab_ocr_") as tmp:
            scratch = Path(tmp)
            with ThreadPoolExecutor(max_workers=len(sessions)) as pool:
                results = list(
                    pool.map(
                        lambda pair: self._run_node(pair[0], pair[1], out_dir, scratch),
                        zip(sessions, chunks, strict=True),
                    )
                )
        duration = time.time() - t0
        completed = sum(n for n, _ in results)
        rate = completed / duration if duration > 0 else 0.0
        print(
            f"Cluster finished {completed} pages in {duration:.1f}s ({rate:.2f} pages/s)."
        )
        return ClusterStats(
            total_pages=len(pending),
            completed_pages=completed,
            duration_sec=duration,
            effective_pages_per_sec=rate,
            active_workers=sum(1 for n, _ in results if n),
            worker_stats=[s for _, s in results if s],
        )


@dataclass(frozen=True)
class BenchResult:
    gpu: str
    model: str
    pages: int
    completed: int
    wall_sec: float
    worker: dict[str, object] | None
    cu_per_hour: float | None

    @property
    def pages_per_sec(self) -> float:
        rate = (self.worker or {}).get("pages_per_sec")
        return float(rate) if isinstance(rate, (int, float)) else 0.0

    @property
    def cu_per_1000_pages(self) -> float | None:
        if not self.cu_per_hour or not self.pages_per_sec:
            return None
        return self.cu_per_hour * 1000 / self.pages_per_sec / 3600


def benchmark(
    gpu: str,
    model: str,
    pages: Sequence[PageImage],
    out_dir: Path,
    prompt: str | None = None,
) -> BenchResult:
    """Transcribe `pages` on one fresh VM and report steady-state pages/s and cost."""
    cluster = ColabOCRCluster(
        gpu_type=gpu,
        num_workers=1,
        session_prefix=f"bench-{gpu.lower()}-{model}",
        timeout_sec=3600,
        prompt=prompt,
        model=model,
    )
    stats = cluster.run_cluster(pages, out_dir)
    return BenchResult(
        gpu=gpu,
        model=model,
        pages=len(pages),
        completed=stats.completed_pages,
        wall_sec=round(stats.duration_sec, 1),
        worker=stats.worker_stats[0] if stats.worker_stats else None,
        cu_per_hour=colab_gpu(gpu).cu_per_hour,
    )
