"""Dual-G4 Blackwell Colab Cluster Orchestrator for Jina OCR v1.

Manages ephemeral Colab sessions with Blackwell / G4 / L4 accelerators:
1. Partitions document pages into balanced worker chunks.
2. Compresses & uploads page packages to Colab sessions via colab CLI.
3. Launches concurrent high-throughput inference on Jina OCR v1.
4. Downloads resulting Markdown archives and unpacks to local storage.
5. Guaranteed session release in finally block to conserve compute units.
"""

import shutil
import subprocess
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClusterStats:
    total_pages: int
    completed_pages: int
    duration_sec: float
    effective_pages_per_sec: float
    active_workers: int


class DualColabG4Cluster:
    """Orchestrates multi-node Colab GPU clusters for parallel document OCR."""

    def __init__(
        self,
        gpu_type: str = "G4",
        num_workers: int = 2,
        session_prefix: str = "g4-jina",
        timeout_sec: float = 7200.0,
    ):
        self.gpu_type: str = gpu_type
        self.num_workers: int = num_workers
        self.session_prefix: str = session_prefix
        self.timeout_sec: float = timeout_sec

    @staticmethod
    def is_colab_available() -> bool:
        """Check if colab CLI is installed and configured."""
        try:
            res = subprocess.run(
                ["colab", "usage"],
                capture_output=True,
                text=True,
                timeout=12,
                check=False,
            )
            return "Current balance:" in res.stdout
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    @staticmethod
    def get_balance() -> float | None:
        """Query available Google Colab compute units."""
        try:
            res = subprocess.run(
                ["colab", "usage"],
                capture_output=True,
                text=True,
                timeout=12,
                check=False,
            )
            for line in res.stdout.splitlines():
                if "Current balance:" in line:
                    val = line.split(":", 1)[1].replace("compute units", "").strip()
                    return float(val)
        except (subprocess.SubprocessError, ValueError, OSError):
            pass
        return None

    @staticmethod
    def partition_pages(pages: list[Path], num_chunks: int) -> list[list[Path]]:
        """Split a list of page paths into balanced chunks."""
        if not pages or num_chunks <= 1:
            return [pages]
        k, m = divmod(len(pages), num_chunks)
        chunks: list[list[Path]] = []
        for i in range(num_chunks):
            start = i * k + min(i, m)
            end = (i + 1) * k + min(i + 1, m)
            chunks.append(pages[start:end])
        return [c for c in chunks if len(c) > 0]

    @staticmethod
    def pack_archive(page_files: list[Path], dest_archive: Path) -> Path:
        """Create a compressed tar.gz archive of page image files."""
        dest_archive.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(dest_archive, "w:gz") as tar:
            for p in page_files:
                tar.add(p, arcname=p.name)
        return dest_archive

    def _start_session(self, session_name: str) -> bool:
        """Create a fresh Colab session with specified GPU accelerator."""
        cmd = ["colab", "new", "--session", session_name, "--gpu", self.gpu_type]
        print(f"[{session_name}] Launching Colab VM ({self.gpu_type})...")
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            print(f"[{session_name}] Warning: Session creation error: {res.stderr.strip() or res.stdout.strip()}")
            return False
        return True

    @staticmethod
    def _stop_session(session_name: str) -> None:
        """Release Colab session and stop compute billing."""
        cmd = ["colab", "stop", "--session", session_name]
        try:
            _ = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
            print(f"[{session_name}] Session stopped successfully.")
        except (subprocess.SubprocessError, OSError) as e:
            print(f"[{session_name}] Failed to stop session: {e}")

    @staticmethod
    def _upload_archive(
        session_name: str,
        archive_path: Path,
        remote_dest: str = "/content/pages.tar.gz",
        chunk_size_mb: int = 25,
    ) -> bool:
        """Upload large archives in safe <= 25MB chunks to avoid Colab Jupyter HTTP 400 payload limit."""
        size = archive_path.stat().st_size
        chunk_size_bytes = chunk_size_mb * 1024 * 1024

        if size <= chunk_size_bytes:
            res = subprocess.run(
                ["colab", "upload", "--session", session_name, str(archive_path), remote_dest],
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0

        data = archive_path.read_bytes()
        parts = [data[i:i + chunk_size_bytes] for i in range(0, len(data), chunk_size_bytes)]
        temp_dir = archive_path.parent / f"_parts_{session_name}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            for idx, pt in enumerate(parts):
                p_file = temp_dir / f"part_{idx:03d}.bin"
                _ = p_file.write_bytes(pt)
                res = subprocess.run(
                    ["colab", "upload", "--session", session_name, str(p_file), f"/content/part_{idx:03d}.bin"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                p_file.unlink()
                if res.returncode != 0:
                    return False

            reassemble_code = (
                "import glob, os\n"
                "pfs = sorted(glob.glob('/content/part_*.bin'))\n"
                f"with open('{remote_dest}', 'wb') as out_f:\n"
                "    for pf in pfs:\n"
                "        with open(pf, 'rb') as in_f:\n"
                "            out_f.write(in_f.read())\n"
                "for pf in pfs:\n"
                "    os.remove(pf)\n"
                "print(f'Reassembled {len(pfs)} parts.')\n"
            )
            res_ex = subprocess.run(
                ["colab", "exec", "--session", session_name, "--timeout", "60"],
                input=reassemble_code,
                capture_output=True,
                text=True,
                check=False,
            )
            return res_ex.returncode == 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _execute_worker_pipeline(
        self,
        session_name: str,
        archive_path: Path,
        worker_script_path: Path,
        out_archive_path: Path,
    ) -> bool:
        """Upload assets, run Jina OCR v1, and retrieve generated markdown archive."""
        t0 = time.time()
        print(f"[{session_name}] Uploading page archive ({archive_path.stat().st_size / 1024:.1f} KB)...")
        if not self._upload_archive(session_name, archive_path, "/content/pages.tar.gz"):
            print(f"[{session_name}] Failed to upload page archive.")
            return False

        up_script = subprocess.run(
            ["colab", "upload", "--session", session_name, str(worker_script_path), "/content/worker.py"],
            capture_output=True,
            text=True,
            check=False,
        )
        if up_script.returncode != 0:
            print(f"[{session_name}] Failed to upload worker script: {up_script.stderr}")
            return False

        # Setup directories and extract pages
        setup_code = (
            "import os, tarfile\n"
            "os.makedirs('/content/pages', exist_ok=True)\n"
            "os.makedirs('/content/markdown', exist_ok=True)\n"
            "with tarfile.open('/content/pages.tar.gz') as t:\n"
            "    t.extractall('/content/pages')\n"
            "print(f'Unpacked {len(os.listdir(\"/content/pages\"))} pages.')\n"
        )
        _ = subprocess.run(
            ["colab", "exec", "--session", session_name, "--timeout", "60"],
            input=setup_code,
            capture_output=True,
            text=True,
            check=False,
        )

        # Launch worker asynchronously on remote VM
        launch_code = (
            "import subprocess, sys\n"
            "p = subprocess.Popen([sys.executable, '/content/worker.py', '--pages', '/content/pages', '--out', '/content/markdown'])\n"
            "print('Launched worker PID:', p.pid)\n"
        )
        print(f"[{session_name}] Launching Jina OCR v1 worker on {self.gpu_type}...")
        _ = subprocess.run(
            ["colab", "exec", "--session", session_name, "--timeout", "30"],
            input=launch_code,
            capture_output=True,
            text=True,
            check=False,
        )

        # Poll for completion via colab ls
        print(f"[{session_name}] Monitoring transcription progress...")
        poll_start = time.time()
        archive_ready = False
        while time.time() - poll_start < self.timeout_sec:
            time.sleep(12)
            try:
                ls_res = subprocess.run(
                    ["colab", "ls", "--session", session_name, "/content"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                if "markdown.tar.gz" in ls_res.stdout:
                    archive_ready = True
                    break

                ls_md = subprocess.run(
                    ["colab", "ls", "--session", session_name, "/content/markdown"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                page_count = len([l for l in ls_md.stdout.splitlines() if l.strip().endswith(".md")])
                print(f"[{session_name}] Progress: {page_count} pages transcribed ({time.time() - poll_start:.1f}s)")
            except (subprocess.SubprocessError, OSError) as e:
                print(f"[{session_name}] Polling notice: {e}, retrying...")
        if not archive_ready:
            print(f"[{session_name}] Timeout waiting for markdown archive.")
            return False

        # Download markdown archive
        print(f"[{session_name}] Downloading transcribed markdown archive...")
        dl_res = subprocess.run(
            ["colab", "download", "--session", session_name, "/content/markdown.tar.gz", str(out_archive_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if dl_res.returncode != 0 or not out_archive_path.exists():
            print(f"[{session_name}] Download failed: {dl_res.stderr}")
            return False

        dur = time.time() - t0
        print(f"[{session_name}] Completed pipeline in {dur:.2f}s.")
        return True

    def run_cluster(
        self,
        pages_dir: Path,
        out_dir: Path,
        worker_script_path: Path | None = None,
    ) -> ClusterStats:
        """Run dual-node accelerated batch transcription on Colab."""
        pages_dir = Path(pages_dir)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if worker_script_path is None:
            worker_script_path = Path(__file__).resolve().parent / "jina_worker.py"

        all_pages = sorted(pages_dir.glob("*.png"))
        if not all_pages:
            print(f"No page renders found in {pages_dir}!")
            return ClusterStats(0, 0, 0.0, 0.0, 0)

        # Identify pending pages
        pending_pages: list[Path] = []
        for p in all_pages:
            # Check if corresponding .md exists
            stem = p.stem
            parts = stem.split("_")
            try:
                p_num = int(parts[-1])
                out_f = out_dir / f"p_{p_num:03d}.md"
            except ValueError:
                out_f = out_dir / f"{stem}.md"

            if not out_f.exists() or out_f.stat().st_size < 30:
                pending_pages.append(p)

        print("=== DUAL-G4 COLAB CLUSTER ===")
        print(f"Total pages: {len(all_pages)} | Already done: {len(all_pages) - len(pending_pages)} | Pending: {len(pending_pages)}")

        if not pending_pages:
            print("All pages already processed.")
            return ClusterStats(len(all_pages), len(all_pages), 0.0, 0.0, 0)

        num_nodes = min(self.num_workers, len(pending_pages))
        chunks = self.partition_pages(pending_pages, num_nodes)

        t_cluster_start = time.time()
        active_sessions = [f"{self.session_prefix}-{i+1}" for i in range(len(chunks))]
        temp_dir = out_dir / "_cluster_tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Start all sessions
            print(f"Spawning {len(active_sessions)} Colab {self.gpu_type} nodes...")
            with ThreadPoolExecutor(max_workers=len(active_sessions)) as ex:
                session_ready = list(ex.map(self._start_session, active_sessions))

            valid_nodes = [s for s, ok in zip(active_sessions, session_ready) if ok]
            if not valid_nodes:
                raise RuntimeError("Failed to start any Colab accelerator sessions.")

            # If fewer sessions succeeded, repartition
            if len(valid_nodes) < len(chunks):
                chunks = self.partition_pages(pending_pages, len(valid_nodes))

            # 2. Package and upload to each node
            def process_node(node_idx: int):
                s_name = valid_nodes[node_idx]
                node_pages = chunks[node_idx]
                tar_path = temp_dir / f"batch_node_{node_idx}.tar.gz"
                out_tar = temp_dir / f"markdown_node_{node_idx}.tar.gz"

                _ = self.pack_archive(node_pages, tar_path)
                ok = self._execute_worker_pipeline(s_name, tar_path, worker_script_path, out_tar)
                if ok and out_tar.exists():
                    # Unpack into out_dir
                    with tarfile.open(out_tar, "r:gz") as tar:
                        tar.extractall(out_dir)
                    return len(node_pages)
                return 0

            # 3. Run in parallel
            with ThreadPoolExecutor(max_workers=len(valid_nodes)) as ex:
                results = list(ex.map(process_node, range(len(valid_nodes))))

            total_completed = sum(results)

        finally:
            # Guaranteed session termination to prevent credit drain
            print("Stopping all active Colab sessions...")
            for s in active_sessions:
                self._stop_session(s)
            # Cleanup temp files
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

        dur_all = time.time() - t_cluster_start
        rate = total_completed / dur_all if dur_all > 0 else 0
        print(f"Cluster finished {total_completed} pages in {dur_all:.2f}s ({rate:.2f} pages/s)!")
        return ClusterStats(
            total_pages=len(all_pages),
            completed_pages=total_completed,
            duration_sec=dur_all,
            effective_pages_per_sec=rate,
            active_workers=len(valid_nodes) if "valid_nodes" in locals() else 0,
        )
