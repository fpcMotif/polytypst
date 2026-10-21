"""End-to-end extraction, 300-DPI PDF NCC + Apple Vision OCR reconciliation, and Typst/LaTeX compilation for TAOCP Vol. 3."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pymupdf

from polytypst.parity.source import sources_dir
from polytypst.taocp.compiler import TaocpBookCompiler
from polytypst.taocp.extractor import TaocpExtractor
from polytypst.taocp.figures import TaocpAssetProcessor

PDF_NAME = "Art of Computer Programming, The Volume 3 Sorting and Searching (Donald E. Knuth).pdf"
EPUB_NAME = "The Art of Computer Programming, Vol. 03 Sorting and Searching (Donald E. Knuth).epub"
DEFAULT_OUT_DIR = Path("output/taocp")


def main() -> None:
    t0 = time.perf_counter()
    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[1/5] Scanning EPUB spine, anchor IDs, and required graphic assets...")
    epub_path = sources_dir(EPUB_NAME) / EPUB_NAME
    pdf_path = sources_dir(PDF_NAME) / PDF_NAME
    extractor = TaocpExtractor(epub_path)
    spine_hrefs, valid_ids, required_images = extractor.scan_spine()
    print(
        f"      Found {len(spine_hrefs)} spine sections, {len(valid_ids)} unique anchors, "
        f"and {len(required_images)} graphic assets to extract."
    )

    print(
        "[2/5] Extracting & upgrading graphic assets via 300-DPI PDF FFT-NCC matching..."
    )
    processor = TaocpAssetProcessor(epub_path, pdf_path, out_dir)
    assets = processor.process_assets(required_images)
    n_pdf_matched = sum(1 for a in assets.values() if a.method == "pdf_300dpi_ncc")
    n_upscaled = sum(1 for a in assets.values() if a.method == "epub_upscaled")
    print(
        f"      Processed {len(assets)} assets: {n_pdf_matched} upgraded from 300-DPI PDF scan, "
        f"{n_upscaled} contrast-cleaned 2x Lanczos upscaled."
    )

    print(
        "[3/5] Running Apple Silicon Vision OCR verification across PDF checkpoints..."
    )
    ocr_summary = processor.run_ocr_verification()
    print(
        f"      Verified {ocr_summary['verified_checkpoints']} PDF page checkpoints via AppleVisionOCREngine."
    )

    print(
        "[4/5] Converting EPUB DOM + native math symbols + 300-DPI plates to Typst & LaTeX..."
    )
    sections = extractor.extract_sections(assets)
    compiler = TaocpBookCompiler(out_dir)
    typ_path, tex_path = compiler.write_sources(sections)
    print(f"      Wrote Typst source: {typ_path} ({typ_path.stat().st_size:,} bytes)")
    print(f"      Wrote LaTeX source: {tex_path} ({tex_path.stat().st_size:,} bytes)")

    print("[5/5] Compiling publication PDF via Typst...")
    pdf_path = compiler.compile_typst_pdf()
    with pymupdf.open(pdf_path) as out_doc:
        page_count = len(out_doc)
        toc_entries = out_doc.get_toc()

    elapsed = round(time.perf_counter() - t0, 2)
    report = {
        "title": "The Art of Computer Programming, Volume 3: Sorting and Searching (Second Edition)",
        "author": "Donald E. Knuth",
        "typst_source": str(typ_path),
        "latex_source": str(tex_path),
        "compiled_pdf": str(pdf_path),
        "compiled_pdf_pages": page_count,
        "compiled_pdf_toc_entries": len(toc_entries),
        "spine_sections": len(sections),
        "unique_anchors": len(valid_ids),
        "total_assets_extracted": len(assets),
        "assets_300dpi_pdf_ncc": n_pdf_matched,
        "assets_epub_2x_lanczos": n_upscaled,
        "ocr_verified_checkpoints": ocr_summary["verified_checkpoints"],
        "elapsed_seconds": elapsed,
    }
    report_path = out_dir / "build_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Done in {elapsed}s! Compiled {pdf_path} ({page_count} pages, {len(toc_entries)} TOC entries)."
    )


if __name__ == "__main__":
    main()
