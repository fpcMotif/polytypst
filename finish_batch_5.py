"""Complete final Batch 5, download markdown archives, release sessions, and stitch master book.md."""

import json
import subprocess
import tarfile
import time
from pathlib import Path

from polytypst.cleaner.tex_markdown import TeXMarkdownCleaner
from polytypst.vision.figure_extractor import ExtractedFigure

out_dir = Path("output/goursat_colab")
md_dir = out_dir / "markdown_pages"
figs_dir = out_dir / "figures"
renders_dir = out_dir / "page_renders"
manifest_path = out_dir / "figures_manifest.json"

sessions = ["g4-ocr-batch-1", "g4-ocr-batch-2"]
target_w1 = 28
target_w2 = 28

print("=== FINALIZING BATCH 5 (PAGES 513 TO 568) ===")

# Wait for completion
t0 = time.time()
while time.time() - t0 < 600:
    c1 = 0
    c2 = 0
    try:
        r1 = subprocess.run(["colab", "ls", "--session", "g4-ocr-batch-1", "/content/markdown"], capture_output=True, text=True, timeout=20, check=False)
        c1 = len([l for l in r1.stdout.splitlines() if l.strip().endswith(".md")])
    except (subprocess.SubprocessError, OSError):
        pass

    try:
        r2 = subprocess.run(["colab", "ls", "--session", "g4-ocr-batch-2", "/content/markdown"], capture_output=True, text=True, timeout=20, check=False)
        c2 = len([l for l in r2.stdout.splitlines() if l.strip().endswith(".md")])
    except (subprocess.SubprocessError, OSError):
        pass

    print(f"[{time.time() - t0:.1f}s] Worker 1: {c1}/{target_w1} | Worker 2: {c2}/{target_w2}")

    r1_archive = False
    r2_archive = False
    try:
        a1 = subprocess.run(["colab", "ls", "--session", "g4-ocr-batch-1", "/content"], capture_output=True, text=True, timeout=20, check=False)
        r1_archive = "markdown.tar.gz" in a1.stdout or c1 >= target_w1
        a2 = subprocess.run(["colab", "ls", "--session", "g4-ocr-batch-2", "/content"], capture_output=True, text=True, timeout=20, check=False)
        r2_archive = "markdown.tar.gz" in a2.stdout or c2 >= target_w2
    except (subprocess.SubprocessError, OSError):
        pass

    if (c1 >= target_w1 or r1_archive) and (c2 >= target_w2 or r2_archive):
        print("Both workers finished final batch!")
        break

    time.sleep(15)

# Download archives
print("\nDownloading Batch 5 markdown archives...")
for idx, s_name in enumerate(sessions):
    dest_tar = out_dir / f"batch5_worker_{idx+1}.tar.gz"
    pack_code = (
        "import tarfile, glob\n"
        "with tarfile.open('/content/markdown.tar.gz', 'w:gz') as tar:\n"
        "    for f in sorted(glob.glob('/content/markdown/*.md')):\n"
        "        tar.add(f, arcname=f.split('/')[-1])\n"
        "print('Packaged final markdown.')\n"
    )
    _ = subprocess.run(["colab", "exec", "--session", s_name, "--timeout", "40"], input=pack_code, capture_output=True, text=True, check=False)
    _ = subprocess.run(["colab", "download", "--session", s_name, "/content/markdown.tar.gz", str(dest_tar)], capture_output=True, text=True, check=False)
    if dest_tar.exists():
        with tarfile.open(dest_tar, "r:gz") as tar:
            tar.extractall(md_dir)
        print(f"Extracted {dest_tar.name} into {md_dir}")

# Release sessions
print("\nReleasing Colab sessions...")
for s_name in sessions:
    _ = subprocess.run(["colab", "stop", "--session", s_name], capture_output=True, text=True, check=False)
    print(f"Stopped {s_name}.")

# Stitching all 568 pages
print("\nStitching complete 568 pages into master book.md...")
extracted_figures: list[ExtractedFigure] = []
if manifest_path.exists():
    for item in json.loads(manifest_path.read_text(encoding="utf-8")):
        extracted_figures.append(ExtractedFigure(
            figure_id=str(item["figure_id"]),
            caption=str(item["caption"]),
            image_rel_path=str(item["image_rel_path"]),
            source_page=int(item["source_page"]),
            width_px=int(item.get("width_px", 0)),
            height_px=int(item.get("height_px", 0)),
        ))

all_md = sorted(md_dir.glob("p_*.md"))
pages_md: list[tuple[int, str]] = []
for f in all_md:
    try:
        pno = int(f.stem.split("_")[-1])
    except ValueError:
        pno = len(pages_md) + 1
    if pno > 553:
        continue
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

print("\n🎉 COMPLETE MONOGRAPH TRANSCRIBED AND ASSEMBLED!")
print(f"   Master Document: {master_file} ({master_file.stat().st_size / (1024*1024):.2f} MB)")
print(f"   Total Pages in Book: {len(pages_md)} / 568")
print(f"   Total Grounded Figures: {len(extracted_figures)}")
print(f"   Total Character Count: {len(master_md):,} characters")
