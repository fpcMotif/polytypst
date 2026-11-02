"""Self-hosted OCR on Colab GPUs: split pages across VMs, run `gpu_worker`, collect transcripts.

A VM starts once and serves every batch inside `with cluster:`, then stops. A VM that fails
stops at once, and its pages go to the VMs that worked. A run that times out or whose
worker dies still downloads the pages finished so far.
"""

import json
import shutil
import subprocess
import tarfile
import tempfile
import time
import uuid
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from .colab import ColabSession, account_usage, colab_gpu, fit_problem
from .gpu_worker import STATS_NAME, worker_transcript_path
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


def _tail(res: subprocess.CompletedProcess[str]) -> str:
    return (res.stderr.strip() or res.stdout.strip())[-200:]


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
        self.run_id: str = uuid.uuid4().hex[:6]
        self.timeout_sec: float = timeout_sec
        self.prompt: str | None = prompt
        self.model: OCRModel = ocr_model(model)
        self.ready: dict[str, ColabSession] = {}
        self.keep_vms: bool = False

    def __enter__(self) -> Self:
        self.keep_vms = True
        return self

    def __exit__(self, *_exc: object) -> None:
        self.keep_vms = False
        self.stop_vms()

    def stop_vms(self) -> None:
        for session in self.ready.values():
            session.stop()
        self.ready.clear()

    def session_names(self, count: int) -> list[str]:
        """VM names that only this run uses, so that stopping them cannot stop another run's VMs."""
        return [f"{self.session_prefix}-{self.run_id}-{i + 1}" for i in range(count)]

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

    def _start(self, session: ColabSession) -> str | None:
        if session.name in self.ready:
            return None
        if not session.start():
            return "the VM did not start"
        if not session.install(self.model.pip):
            return "the model's packages did not install"
        setup = (
            "import os, pathlib\n"
            f"os.makedirs({REMOTE_PKG!r}, exist_ok=True)\n"
            f"pathlib.Path({REMOTE_PKG!r}, '__init__.py').touch()\n"
        )
        res = session.exec(setup)
        if res.returncode != 0:
            return f"the package folder setup failed: {_tail(res)}"
        for name in ("ocr_models.py", "blank.py", "gpu_worker.py"):
            if not session.upload(OCR_DIR / name, f"{REMOTE_PKG}/{name}"):
                return f"the upload of {name} failed"
        self.ready[session.name] = session
        return None

    def _prepare(
        self, session: ColabSession, pages_archive: Path, scratch: Path
    ) -> str | None:
        reset = (
            "import os, shutil\n"
            "for p in ['/content/markdown.tar.gz', '/content/worker.log', '/content/worker.pid']:\n"
            "    if os.path.exists(p): os.remove(p)\n"
            "for d in ['/content/markdown', '/content/pages']:\n"
            "    if os.path.exists(d): shutil.rmtree(d)\n"
            "os.makedirs('/content/markdown', exist_ok=True)\n"
        )
        res = session.exec(reset)
        if res.returncode != 0:
            return f"clearing the last batch failed: {_tail(res)}"
        uploads = [(pages_archive, "/content/pages.tar.gz")]
        if self.prompt is not None:
            prompt_file = scratch / f"{session.name}.prompt.txt"
            _ = prompt_file.write_text(self.prompt, encoding="utf-8")
            uploads.append((prompt_file, "/content/prompt.txt"))
        for local, remote in uploads:
            if not session.upload(local, remote):
                return f"the upload of {local.name} failed"
        unpack = (
            "import tarfile\n"
            "with tarfile.open('/content/pages.tar.gz') as t:\n"
            "    t.extractall('/content/pages', filter='data')\n"
        )
        res = session.exec(unpack)
        if res.returncode != 0:
            return f"unpacking the pages failed: {_tail(res)}"
        return None

    def _launch(self, session: ColabSession) -> str | None:
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
        print(f"[{session.name}] Launching {self.model.key} on {self.gpu_type}...", flush=True)
        res = session.exec(launch, timeout=30)
        return None if res.returncode == 0 else f"the worker did not launch: {_tail(res)}"

    def _wait(self, session: ColabSession) -> str | None:
        """Poll until the worker archives its output; the reason on timeout or a dead worker, else None."""
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
                return None
            print(
                f"[{session.name}] {state['pages']} pages transcribed ({time.time() - start:.0f}s)",
                flush=True,
            )
            if not state["alive"]:
                print(
                    f"[{session.name}] Worker exited early. Log tail:\n{state['log']}",
                    flush=True,
                )
                return "the worker exited early"
        return f"the worker timed out after {self.timeout_sec:.0f}s"

    def _drop(self, session: ColabSession, problem: str, pages_left: int) -> None:
        print(
            f"[{session.name}] Dropped: {problem}. Its {pages_left} pages go to the other VMs.",
            flush=True,
        )
        _ = self.ready.pop(session.name, None)
        session.stop()

    def _run_node(
        self,
        session: ColabSession,
        node_pages: list[PageImage],
        out_dir: Path,
        scratch: Path,
    ) -> tuple[int, dict[str, object] | None, bool]:
        problem = self._start(session)
        if problem is None:
            pages_archive = self.pack_archive(
                node_pages, scratch / f"{session.name}.pages.tar.gz"
            )
            problem = self._prepare(session, pages_archive, scratch) or self._launch(session)
        if problem is not None:
            self._drop(session, problem, len(node_pages))
            return 0, None, False
        problem = self._wait(session)
        if problem is not None:
            _ = session.exec(PACK_PARTIAL_CODE, timeout=120)
        md_archive = scratch / f"{session.name}.markdown.tar.gz"
        log_copy = out_dir / f"_{session.name}.worker.log"
        _ = session.download("/content/worker.log", log_copy)
        if not session.download("/content/markdown.tar.gz", md_archive):
            self._drop(session, problem or "the transcript download failed", len(node_pages))
            return 0, None, False
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
        if problem is not None:
            self._drop(session, problem, len(node_pages) - len(transcripts))
        return len(transcripts), stats, problem is None

    def _run_round(
        self,
        sessions: list[ColabSession],
        chunks: list[list[PageImage]],
        out_dir: Path,
        scratch: Path,
    ) -> list[tuple[int, dict[str, object] | None, bool]]:
        with ThreadPoolExecutor(max_workers=len(sessions)) as pool:
            return list(
                pool.map(
                    lambda pair: self._run_node(pair[0], pair[1], out_dir, scratch),
                    zip(sessions, chunks, strict=True),
                )
            )

    def run_cluster(self, pages: Sequence[PageImage], out_dir: Path) -> ClusterStats:
        """Transcribe `pages` into `out_dir` on up to `num_workers` VMs at once."""
        out_dir.mkdir(parents=True, exist_ok=True)
        pending = list(pages)
        print(
            f"=== COLAB OCR: {self.model.key} on {self.num_workers}x {self.gpu_type} | "
            f"{len(pending)} pages ===",
            flush=True,
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
            self.ready.get(name) or ColabSession(name, self.gpu_type)
            for name in self.session_names(len(chunks))
        ]
        t0 = time.time()
        try:
            with tempfile.TemporaryDirectory(prefix="colab_ocr_") as tmp:
                scratch = Path(tmp)
                results = self._run_round(sessions, chunks, out_dir, scratch)
                healthy = [s for s, (_, _, ok) in zip(sessions, results, strict=True) if ok]
                left = [
                    p for p in pending if not worker_transcript_path(out_dir, p.number).exists()
                ]
                if left and healthy and len(healthy) < len(sessions):
                    count = min(len(healthy), len(left))
                    retry = self.partition_pages(left, count, interleaved=True)
                    results += self._run_round(healthy[:count], retry, out_dir, scratch)
        finally:
            if not self.keep_vms:
                self.stop_vms()
        duration = time.time() - t0
        completed = sum(n for n, _, _ in results)
        rate = completed / duration if duration > 0 else 0.0
        print(
            f"Cluster finished {completed} pages in {duration:.1f}s ({rate:.2f} pages/s).",
            flush=True,
        )
        return ClusterStats(
            total_pages=len(pending),
            completed_pages=completed,
            duration_sec=duration,
            effective_pages_per_sec=rate,
            active_workers=sum(1 for n, _, _ in results if n),
            worker_stats=[s for _, s, _ in results if s],
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
