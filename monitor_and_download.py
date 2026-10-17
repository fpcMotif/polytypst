"""Monitors active Dual-G4 Colab sessions, downloads completed archives, and stitches master book.md."""

import subprocess
import tarfile
import time
from pathlib import Path

from polytypst.cleaner.tex_markdown import TeXMarkdownCleaner
from polytypst.vision.figure_extractor import ExtractedFigure

out_dir = Path("output/goursat_colab")
md_dir = out_dir / "markdown_pages"
figs_dir = out_dir / "figures"
md_dir.mkdir(parents=True, exist_ok=True)

sessions = ["g4-goursat-1", "g4-goursat-2"]
target_per_node = 284
total_target = 568

print("=== MONITORING DUAL-G4 COLAB TRANSCRIBING ===")


def count_remote_markdown(session: str) -> int:
    try:
        res = subprocess.run(
            ["colab", "ls", "--session", session, "/content/markdown"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if res.returncode == 0:
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip().endswith(".md")]
            return len(lines)
    except (subprocess.SubprocessError, OSError):
        pass
    return 0


def check_archive_ready(session: str) -> bool:
    try:
        res = subprocess.run(
            ["colab", "ls", "--session", session, "/content"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if res.returncode == 0:
            return "markdown.tar.gz" in res.stdout
    except (subprocess.SubprocessError, OSError):
        pass
    return False


# Monitor loop
start_mon = time.time()
while True:
    c1 = count_remote_markdown("g4-goursat-1")
    c2 = count_remote_markdown("g4-goursat-2")
    tot = c1 + c2
    pct = (tot / total_target) * 100

    r1_done = check_archive_ready("g4-goursat-1") or (c1 >= target_per_node)
    r2_done = check_archive_ready("g4-goursat-2") or (c2 >= (total_target - target_per_node))

    elapsed = time.time() - start_mon
    print(
        f"[{elapsed:5.1f}s] Worker 1: {c1:3d}/{target_per_node} | "
        + f"Worker 2: {c2:3d}/{total_target - target_per_node} | "
        + f"Total: {tot:3d}/{total_target} ({pct:5.1f}%)"
    )
    if r1_done and r2_done:
        print("\nBoth workers finished inference!")
        break

    time.sleep(20)

# Download archives or ensure archive is packed
print("\nFinalizing and downloading markdown archives from workers...")
for idx, s_name in enumerate(sessions):
    if not check_archive_ready(s_name):
        pack_code = (
            "import tarfile, glob\n"
            "with tarfile.open('/content/markdown.tar.gz', 'w:gz') as tar:\n"
            "    for f in sorted(glob.glob('/content/markdown/*.md')):\n"
            "        tar.add(f, arcname=f.split('/')[-1])\n"
            "print('Packaged markdown.')\n"
        )
        _ = subprocess.run(
            ["colab", "exec", "--session", s_name, "--timeout", "60"],
            input=pack_code,
            capture_output=True,
            text=True,
            check=False,
        )

    dest_tar = out_dir / f"markdown_worker_{idx+1}.tar.gz"
    print(f"Downloading {dest_tar.name} from {s_name}...")
    _ = subprocess.run(
        ["colab", "download", "--session", s_name, "/content/markdown.tar.gz", str(dest_tar)],
        capture_output=True,
        text=True,
        check=False,
    )

    if dest_tar.exists():
        with tarfile.open(dest_tar, "r:gz") as tar:
            tar.extractall(md_dir)
        print(f"Extracted {dest_tar.name} into {md_dir}")

# Release sessions
print("\nReleasing Colab sessions...")
for s_name in sessions:
    _ = subprocess.run(
        ["colab", "stop", "--session", s_name],
        capture_output=True,
        text=True,
        check=False,
    )
    print(f"Stopped {s_name}.")

# Stitching
print("\nStitching all pages with extracted figures into master book.md...")
extracted_figures: list[ExtractedFigure] = []
for ff in sorted(figs_dir.glob("*.png")):
    stem = ff.stem.replace("fig_", "")
    extracted_figures.append(ExtractedFigure(
        figure_id=stem,
        caption=f"Figure {stem}",
        image_rel_path=f"figures/{ff.name}",
        source_page=1,
    ))

all_md = sorted(md_dir.glob("p_*.md"))
pages_md: list[tuple[int, str]] = []
for f in all_md:
    try:
        pno = int(f.stem.split("_")[-1])
    except ValueError:
        pno = len(pages_md) + 1
    pages_md.append((pno, f.read_text(encoding="utf-8")))

cleaner = TeXMarkdownCleaner(running_headers=[
    "A COURSE IN MATHEMATICAL ANALYSIS",
    "DERIVATIVES AND DIFFERENTIALS",
    "IMPLICIT FUNCTIONS",
    "FUNCTIONAL DETERMINANTS",
    "CHANGE OF VARIABLE",
    "SERIES",
    "DEFINITE INTEGRALS",
    "APPLICATIONS TO GEOMETRY",
])

master_md = cleaner.stitch_document(pages_md, figures=extracted_figures)
master_file = out_dir / "book.md"
_ = master_file.write_text(master_md, encoding="utf-8")
print(f"\n🎉 SUCCESS: Generated complete TeX-compatible Markdown: {master_file}")
print(f"   Total Pages Transcribed: {len(pages_md)} / {total_target}")
print(f"   Total Figures Grounded: {len(extracted_figures)}")
print(f"   Output File Size: {master_file.stat().st_size / (1024*1024):.2f} MB ({len(master_md)} characters)")
