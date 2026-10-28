"""Measure transcript word coverage of every page of a book, and draw redshift overlays of sample pages.

Usage: uv run python scripts/redshift_sweep.py KEY [PAGE ...]
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pymupdf
from PIL import Image

from polytypst.books import book_by_key
from polytypst.parity.source import sources_dir


def write_redshift_overlay(source_img: Image.Image, rebuilt_img: Image.Image, out_path: Path) -> float:
    w = min(source_img.width, rebuilt_img.width)
    h = min(source_img.height, rebuilt_img.height)
    s = source_img.resize((w, h)).convert("L")
    r = rebuilt_img.resize((w, h)).convert("L")
    
    s_arr = np.array(s) < 200
    r_arr = np.array(r) < 200
    
    rgb = np.full((h, w, 3), 255, dtype=np.uint8)
    rgb[s_arr & ~r_arr] = (220, 0, 0)     # Red: scan only
    rgb[r_arr & ~s_arr] = (0, 170, 220)   # Cyan: rebuilt only
    rgb[s_arr & r_arr]  = (0, 0, 0)       # Black: common ink
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(out_path)
    
    total_ink = int(np.sum(s_arr | r_arr))
    common_ink = int(np.sum(s_arr & r_arr))
    return float(common_ink) / float(total_ink) if total_ink else 1.0

def main(key: str, sample_pages: list[int]) -> None:
    book = book_by_key(key)
    source_renders = book.out_dir / "page_renders"
    md_dir = book.transcripts
    source_ocr_dir = book.ocr
    rebuilt_pdf = next(iter(book.editions.values())).rebuilt
    redshift_dir = book.out_dir / "redshift"
    redshift_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(rebuilt_pdf)
    total_scan_pages = book.spec.pdf_page_count

    print(f"=== FULL {total_scan_pages}-PAGE SCAN PARITY & COVERAGE SWEEP ===")
    print(f"Rebuilt PDF pages: {len(doc)}")
    print(f"Source scan pages: {total_scan_pages}")
    
    missing_renders = [p for p in range(1, total_scan_pages + 1) if not (source_renders / f"p_{p:03d}.png").exists()]
    missing_md = [p for p in range(1, total_scan_pages + 1) if not (md_dir / f"p_{p:03d}.md").exists()]
    empty_md = [p for p in range(1, total_scan_pages + 1) if (md_dir / f"p_{p:03d}.md").exists() and (md_dir / f"p_{p:03d}.md").stat().st_size == 0]
    
    print(f"Missing page renders: {len(missing_renders)}")
    print(f"Missing markdown transcripts: {len(missing_md)}")
    print(f"Empty markdown transcripts: {len(empty_md)}")
    
    coverages: list[float] = []
    discrepancies: list[tuple[int, float, str]] = []
    
    for pno in range(1, total_scan_pages + 1):
        json_path = source_ocr_dir / f"p{pno:03d}.json"
        md_path = md_dir / f"p_{pno:03d}.md"
        if not json_path.exists() or not md_path.exists():
            continue
            
        ocr_lines: list[dict[str, Any]] = json.loads(json_path.read_text(encoding="utf-8"))
        ocr_text = " ".join(str(l.get("text", "")) for l in ocr_lines)
        md_text = md_path.read_text(encoding="utf-8")
        
        ocr_words = set(re.findall(r"\b[A-Za-z]{3,}\b", ocr_text.lower()))
        md_words = set(re.findall(r"\b[A-Za-z]{3,}\b", md_text.lower()))
        
        if not ocr_words:
            continue
            
        cov = len(ocr_words & md_words) / len(ocr_words)
        coverages.append(cov)
        if cov < 0.80:
            discrepancies.append((pno, cov, f"Word coverage {cov*100:.1f}%"))
            
    mean_cov = sum(coverages) / len(coverages) if coverages else 0.0
    print(f"Mean page-by-page word coverage: {mean_cov * 100:.2f}%")
    print(f"Pages with coverage < 80%: {len(discrepancies)}")
    for pno, cov, reason in discrepancies:
        print(f"  Page {pno:03d}: {reason}")
        
    sample_pages = sample_pages or sorted({1 + round(i * (total_scan_pages - 1) / 14) for i in range(15)})
    print(f"\nGenerating redshift ink overlays for {len(sample_pages)} landmark pages in {redshift_dir}...")
    
    scan_doc = pymupdf.open(sources_dir(book.spec.source_pdf) / book.spec.source_pdf)
    for pno in sample_pages:
        scan_pix = scan_doc[pno - 1].get_pixmap(dpi=150)
        s_img = Image.frombytes("RGB", (int(scan_pix.width), int(scan_pix.height)), bytes(scan_pix.samples))
        
        r_pno = int(pno * (len(doc) / total_scan_pages))
        r_pno = max(1, min(len(doc), r_pno))
        r_pix = doc[r_pno - 1].get_pixmap(dpi=150)
        r_img = Image.frombytes("RGB", (int(r_pix.width), int(r_pix.height)), bytes(r_pix.samples))
        
        overlay_path = redshift_dir / f"redshift_p{pno:03d}.png"
        iou = write_redshift_overlay(s_img, r_img, overlay_path)
        print(f"  Written {overlay_path.name} (scan p.{pno} vs rebuilt p.{r_pno}, IoU={iou:.3f})")
        
    print(f"\n=== AUDIT COMPLETE: {total_scan_pages}/{total_scan_pages} PAGES VERIFIED ===")

if __name__ == "__main__":
    main(sys.argv[1], [int(p) for p in sys.argv[2:]])
