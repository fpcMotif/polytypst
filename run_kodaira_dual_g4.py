"""Dual-G4 Blackwell Colab Cluster Orchestrator for Kunihiko Kodaira's Complex Analysis.

Deploys jinaai/jina-ocr-v1 across two Google Colab G4 (RTX PRO 6000 Blackwell 95GB) VMs,
running 3 parallel GPU worker shards per G4 node (6 concurrent Jina OCR v1 workers total).
"""

import shutil
import subprocess
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def run_cmd(cmd: list[str], input_text: str | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def upload_archive(session: str, local_path: Path, remote_dest: str = "/content/pages.tar.gz") -> bool:
    size = local_path.stat().st_size
    chunk_bytes = 22 * 1024 * 1024
    if size <= chunk_bytes:
        r = run_cmd(["colab", "upload", "--session", session, str(local_path), remote_dest], timeout=180)
        return r.returncode == 0

    data = local_path.read_bytes()
    parts = [data[i : i + chunk_bytes] for i in range(0, len(data), chunk_bytes)]
    tmp_dir = local_path.parent / f"_parts_{session}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        for idx, pt in enumerate(parts):
            pf = tmp_dir / f"part_{idx:03d}.bin"
            pf.write_bytes(pt)
            r = run_cmd(
                ["colab", "upload", "--session", session, str(pf), f"/content/part_{idx:03d}.bin"],
                timeout=180,
            )
            pf.unlink(missing_ok=True)
            if r.returncode != 0:
                return False
        reassemble = (
            "import glob, os\n"
            "pfs = sorted(glob.glob('/content/part_*.bin'))\n"
            f"with open('{remote_dest}', 'wb') as out_f:\n"
            "    for pf in pfs:\n"
            "        with open(pf, 'rb') as in_f:\n"
            "            out_f.write(in_f.read())\n"
            "for pf in pfs:\n"
            "    os.remove(pf)\n"
            "print('Reassembled', len(pfs))\n"
        )
        r_ex = run_cmd(["colab", "exec", "--session", session, "--timeout", "60"], input_text=reassemble, timeout=90)
        return r_ex.returncode == 0
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def setup_and_launch_node(
    session: str,
    page_files: list[Path],
    worker_script: Path,
    tmp_dir: Path,
    num_shards: int = 3,
) -> int:
    print(f"[{session}] Creating Colab G4 session...", flush=True)
    r_new = run_cmd(["colab", "new", "--session", session, "--gpu", "G4"], timeout=120)
    if r_new.returncode != 0:
        raise RuntimeError(f"[{session}] Failed to allocate G4 VM: {r_new.stderr or r_new.stdout}")

    print(f"[{session}] Installing dependencies (transformers, accelerate, einops, timm, pillow)...", flush=True)
    _ = run_cmd(
        ["colab", "install", "--session", session, "transformers", "accelerate", "einops", "timm", "pillow"],
        timeout=180,
    )

    tar_path = tmp_dir / f"{session}_pages.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for p in page_files:
            tar.add(p, arcname=p.name)

    print(
        f"[{session}] Uploading {len(page_files)} pages ({tar_path.stat().st_size / (1024*1024):.2f} MB)...",
        flush=True,
    )
    if not upload_archive(session, tar_path, "/content/pages.tar.gz"):
        raise RuntimeError(f"[{session}] Failed to upload pages archive.")

    r_up = run_cmd(
        ["colab", "upload", "--session", session, str(worker_script), "/content/kodaira_g4_worker.py"],
        timeout=60,
    )
    if r_up.returncode != 0:
        raise RuntimeError(f"[{session}] Failed to upload worker script: {r_up.stderr}")

    launch_py = (
        "import os, tarfile, subprocess, sys\n"
        "os.makedirs('/content/pages', exist_ok=True)\n"
        "os.makedirs('/content/markdown', exist_ok=True)\n"
        "with tarfile.open('/content/pages.tar.gz') as t:\n"
        "    t.extractall('/content/pages')\n"
        "log_f = open('/content/worker.log', 'w')\n"
        f"p = subprocess.Popen([sys.executable, '/content/kodaira_g4_worker.py', '--pages', '/content/pages', '--out', '/content/markdown', '--shards', '{num_shards}'], stdout=log_f, stderr=subprocess.STDOUT)\n"
        "print('Launched PID:', p.pid)\n"
    )
    r_launch = run_cmd(["colab", "exec", "--session", session, "--timeout", "60"], input_text=launch_py, timeout=90)
    print(f"[{session}] Worker launched: {r_launch.stdout.strip()}", flush=True)
    return len(page_files)


def poll_node_status(session: str) -> tuple[int, bool, str]:
    check_py = (
        "import os, glob\n"
        "mds = [f for f in glob.glob('/content/markdown/p_*.md') if os.path.getsize(f) >= 0]\n"
        "done = os.path.exists('/content/markdown.tar.gz')\n"
        "tail = ''\n"
        "if os.path.exists('/content/worker.log'):\n"
        "    lines = open('/content/worker.log').read().splitlines()\n"
        "    tail = ' | '.join(lines[-2:]) if lines else ''\n"
        "print(f'STATUS:{len(mds)}:{int(done)}:{tail}')\n"
    )
    r = run_cmd(["colab", "exec", "--session", session, "--timeout", "30"], input_text=check_py, timeout=45)
    for line in r.stdout.splitlines():
        if line.startswith("STATUS:"):
            parts = line.split(":", 3)
            return int(parts[1]), bool(int(parts[2])), parts[3]
    return 0, False, ""


def download_node_results(session: str, out_md_dir: Path, tmp_dir: Path) -> int:
    pack_py = (
        "import tarfile, glob, os\n"
        "if not os.path.exists('/content/markdown.tar.gz'):\n"
        "    with tarfile.open('/content/markdown.tar.gz', 'w:gz') as tar:\n"
        "        for f in sorted(glob.glob('/content/markdown/p_*.md')):\n"
        "            tar.add(f, arcname=os.path.basename(f))\n"
        "print('Archive ready:', os.path.getsize('/content/markdown.tar.gz'))\n"
    )
    _ = run_cmd(["colab", "exec", "--session", session, "--timeout", "60"], input_text=pack_py, timeout=90)
    local_tar = tmp_dir / f"{session}_markdown.tar.gz"
    r_dl = run_cmd(
        ["colab", "download", "--session", session, "/content/markdown.tar.gz", str(local_tar)],
        timeout=180,
    )
    if r_dl.returncode == 0 and local_tar.exists():
        with tarfile.open(local_tar, "r:gz") as tar:
            tar.extractall(out_md_dir)
        return len(list(out_md_dir.glob("p_*.md")))
    return 0


def main() -> None:
    out_dir = Path("output/kodaira")
    renders_dir = out_dir / "page_renders"
    md_dir = out_dir / "markdown_pages"
    tmp_dir = out_dir / "_cluster_tmp"
    worker_script = Path("kodaira_g4_worker.py").resolve()

    md_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    all_pages = sorted(renders_dir.glob("p_*.png"))
    pending: list[Path] = []
    for p in all_pages:
        pno = int(p.stem.split("_")[-1])
        md_f = md_dir / f"p_{pno:03d}.md"
        if not md_f.exists() or md_f.stat().st_size < 15:
            pending.append(p)

    print(
        f"=== KODAIRA DUAL-G4 JINA OCR V1 CLUSTER ===\n"
        f"Total content pages: {len(all_pages)} | Already done: {len(all_pages) - len(pending)} | Pending: {len(pending)}",
        flush=True,
    )
    if not pending:
        print("All pages already transcribed!", flush=True)
        return

    # Interleave pages across the 2 nodes so both nodes get an identical mix of dense/light pages
    node1_pages = pending[0::2]
    node2_pages = pending[1::2]
    sessions = ["g4-kodaira-1", "g4-kodaira-2"]
    node_chunks = [node1_pages, node2_pages]

    t_start = time.time()
    try:
        with ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(setup_and_launch_node, sessions[0], node_chunks[0], worker_script, tmp_dir, 3)
            f2 = ex.submit(setup_and_launch_node, sessions[1], node_chunks[1], worker_script, tmp_dir, 3)
            target_1 = f1.result()
            target_2 = f2.result()

        total_target = target_1 + target_2
        print(f"\nBoth G4 nodes running (3 shards/GPU = 6 parallel workers)! Target: {total_target} pages.", flush=True)

        while time.time() - t_start < 5400:
            time.sleep(15)
            c1, d1, tail1 = poll_node_status(sessions[0])
            c2, d2, tail2 = poll_node_status(sessions[1])
            tot = c1 + c2
            elapsed = time.time() - t_start
            rate = tot / elapsed if elapsed > 0 else 0.0
            eta_min = (total_target - tot) / rate / 60.0 if rate > 0 else 0.0
            print(
                f"[{elapsed:5.1f}s] {sessions[0]}: {c1:3d}/{target_1} ({tail1[-45:]}) | "
                f"{sessions[1]}: {c2:3d}/{target_2} ({tail2[-45:]}) | "
                f"Total: {tot:3d}/{total_target} ({tot/total_target*100:5.1f}%) | "
                f"{rate:.2f} pg/s | ETA: {eta_min:.1f}m",
                flush=True,
            )
            if (d1 or c1 >= target_1) and (d2 or c2 >= target_2):
                print("\nBoth G4 nodes completed all assigned pages!", flush=True)
                break

        for s in sessions:
            print(f"[{s}] Downloading markdown archive...", flush=True)
            download_node_results(s, md_dir, tmp_dir)

    finally:
        print("\nStopping Dual-G4 Colab sessions...", flush=True)
        for s in sessions:
            _ = run_cmd(["colab", "stop", "--session", s], timeout=45)
            print(f"[{s}] Stopped.", flush=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    final_count = len(list(md_dir.glob("p_*.md")))
    print(
        f"\nSUCCESS: Transcribed {final_count}/{len(all_pages)} pages in {time.time() - t_start:.1f}s!",
        flush=True,
    )


if __name__ == "__main__":
    main()
