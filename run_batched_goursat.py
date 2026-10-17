"""Batched high-throughput Dual-G4 Colab converter for Edouard Goursat's 568-page monograph."""

import shutil
from pathlib import Path

from polytypst.cleaner.tex_markdown import TeXMarkdownCleaner
from polytypst.ocr.dual_colab import DualColabG4Cluster
from polytypst.vision.figure_extractor import ExtractedFigure

pdf_path = Path("/Users/martinfan/Downloads/A course in mathematical analysis - Applications to Geometry, Expansion in Series, Definite Integrals, Derivatives and… (Edouard Goursat).pdf")
out_dir = Path("output/goursat_colab")
renders_dir = out_dir / "page_renders"
figs_dir = out_dir / "figures"
md_dir = out_dir / "markdown_pages"

out_dir.mkdir(parents=True, exist_ok=True)
md_dir.mkdir(parents=True, exist_ok=True)

all_page_files: list[Path] = sorted(renders_dir.glob("p_*.png"))
total_pages = len(all_page_files)

print("=== BATCHED DUAL-G4 BLACKWELL ORCHESTRATOR ===")
print(f"Total Pages in Book: {total_pages}")


def get_pending() -> list[Path]:
    pending: list[Path] = []
    for p in all_page_files:
        stem = p.stem
        pno = int(stem.split("_")[-1])
        out_f = md_dir / f"p_{pno:03d}.md"
        if not out_f.exists() or out_f.stat().st_size < 30:
            pending.append(p)
    return pending


pending: list[Path] = get_pending()
print(f"Already Completed: {total_pages - len(pending)} | Pending: {len(pending)}")

# Process in chunks of 70 pages (35 pages per G4 worker node)
chunk_size = 70
batch_num = 1
cluster = DualColabG4Cluster(gpu_type="G4", num_workers=2, session_prefix="g4-ocr-batch")

while pending:
    batch_pages: list[Path] = pending[:chunk_size]
    print(
        f"\n--- Batch {batch_num}: Processing {len(batch_pages)} pages "
        + f"({batch_pages[0].stem} to {batch_pages[-1].stem}) ---"
    )

    batch_tmp = out_dir / f"_batch_run_{batch_num}"
    batch_tmp.mkdir(parents=True, exist_ok=True)
    for p in batch_pages:
        _ = shutil.copy2(p, batch_tmp / p.name)

    _ = cluster.run_cluster(batch_tmp, md_dir)
    shutil.rmtree(batch_tmp, ignore_errors=True)

    pending = get_pending()
    done = total_pages - len(pending)
    pct = (done / total_pages) * 100
    print(f"Progress after Batch {batch_num}: {done}/{total_pages} pages done ({pct:.1f}%)")
    batch_num += 1

print("\nAll 568 pages transcribed on Dual G4 Blackwell cluster!")

# Load extracted figures
extracted_figures: list[ExtractedFigure] = []
for ff in sorted(figs_dir.glob("*.png")):
    stem = ff.stem.replace("fig_", "")
    extracted_figures.append(ExtractedFigure(
        figure_id=stem,
        caption=f"Figure {stem}",
        image_rel_path=f"figures/{ff.name}",
        source_page=1,
    ))

print(f"Grounded {len(extracted_figures)} figures.")
print("Stitching all 568 pages into master TeX-compatible Markdown: book.md...")

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

print("\n🎉 CONVERSION COMPLETE!")
print(f"   Master Document: {master_file} ({master_file.stat().st_size / (1024*1024):.2f} MB)")
print(f"   Total Pages: {len(pages_md)}")
print(f"   Total Characters: {len(master_md)}")
print(f"   Total Figures Grounded: {len(extracted_figures)}")
