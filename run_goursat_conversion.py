"""Master conversion script for Edouard Goursat's Course in Mathematical Analysis via Dual-G4 Colab."""

import json
import time
from pathlib import Path

from polytypst.cleaner.tex_markdown import TeXMarkdownCleaner
from polytypst.goursat.figures import (
    export_goursat_figures,
    export_goursat_web_gallery,
    normalize_goursat_markdown,
)
from polytypst.ocr.apple_vision import AppleVisionOCREngine
from polytypst.ocr.dual_colab import DualColabG4Cluster
from polytypst.vision.figure_extractor import ExtractedFigure, FigureExtractor
from polytypst.vision.typesafe_jev import TypeSafeJevVision

pdf_path = Path("/Users/martinfan/Downloads/A course in mathematical analysis - Applications to Geometry, Expansion in Series, Definite Integrals, Derivatives and… (Edouard Goursat).pdf")
out_dir = Path("output/goursat_colab")
renders_dir = out_dir / "page_renders"
figs_dir = out_dir / "figures"
md_dir = out_dir / "markdown_pages"
manifest_path = out_dir / "figures_manifest.json"

out_dir.mkdir(parents=True, exist_ok=True)
renders_dir.mkdir(parents=True, exist_ok=True)
figs_dir.mkdir(parents=True, exist_ok=True)
md_dir.mkdir(parents=True, exist_ok=True)

print("=== GOURSAT DUAL-G4 BLACKWELL CONVERSION ===")
print(f"Target document: {pdf_path.name}")
print(f"Total rendered pages: {len(list(renders_dir.glob('*.png')))}")
print(f"Total extracted figures: {len(list(figs_dir.glob('*.png')))}")

# 1. Run figure extraction if not already present
extracted_figures: list[ExtractedFigure] = []
extractor = FigureExtractor(pdf_path)
fig_files = list(figs_dir.glob("*.png"))
if len(fig_files) < 50 or not manifest_path.exists():
    print("Running Apple Vision OCR and Figure Extractor on all 568 pages...")
    all_imgs = sorted(renders_dir.glob("*.png"))
    apple_engine = AppleVisionOCREngine(languages=["en-US"])
    ocr_pages = apple_engine.recognize_document(all_imgs)
    extracted_figures = extractor.extract_figures_from_ocr_pages(ocr_pages, figs_dir, dpi=300)
    print(f"Extracted {len(extracted_figures)} figures into {figs_dir}.")
else:
    print(f"Reusing {len(fig_files)} existing extracted figures from {manifest_path}.")
    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in raw_manifest:
        rel_path = str(item["image_rel_path"])
        ok, reasons = TypeSafeJevVision.verify_cropped_diagram(out_dir / rel_path)
        if not ok:
            print(f"Warning: {rel_path} failed crop check: {reasons}")
        extracted_figures.append(ExtractedFigure(
            figure_id=str(item["figure_id"]),
            caption=str(item["caption"]),
            image_rel_path=rel_path,
            source_page=int(item["source_page"]),
            width_px=int(item.get("width_px", 0)),
            height_px=int(item.get("height_px", 0)),
        ))

# 2. Launch Dual-G4 Colab Cluster for Jina OCR v1
print("\nStarting Dual-G4 Colab Cluster (NVIDIA Blackwell 95GB VRAM nodes)...")
cluster = DualColabG4Cluster(
    gpu_type="G4",
    num_workers=2,
    session_prefix="g4-goursat",
    timeout_sec=7200.0,
)

t0 = time.time()
stats = cluster.run_cluster(renders_dir, md_dir)
print(f"\nCluster finished {stats.completed_pages}/{stats.total_pages} pages in {stats.duration_sec:.2f}s ({stats.effective_pages_per_sec:.2f} pages/s)!")

# 3. Clean, ground figures, and stitch into master TeX Markdown
print("\nCleaning math formulas, grounding figures, and stitching master book.md...")
all_md_files = sorted(md_dir.glob("p_*.md"))
pages_md: list[tuple[int, str]] = []
for f in all_md_files:
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

master_md = normalize_goursat_markdown(
    cleaner.stitch_document(pages_md, figures=extracted_figures)
)
master_path = out_dir / "book.md"
_ = master_path.write_text(master_md, encoding="utf-8")
exported_svgs = export_goursat_figures(figs_dir)
gallery_path = export_goursat_web_gallery(out_dir / "web_figures" / "index.html")
print(f"Exported {len(exported_svgs)} vector SVG/PNG figures to {figs_dir} and web gallery to {gallery_path}")
print(f"SUCCESS: Generated complete TeX-compatible Markdown: {master_path} ({len(master_md)} characters, {master_path.stat().st_size / (1024*1024):.2f} MB)")
