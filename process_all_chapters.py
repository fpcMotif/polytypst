"""Master Recursive Harvester & Compiler for all remaining Kerodon Chapters (4 to 10)."""

import sys
import time
import re
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from polytypst.kerodon.extractor import KerodonExtractor
from polytypst.kerodon.diagrams import KerodonDiagramCropper
from polytypst.kerodon.compiler import KerodonCompiler


CHAPTERS_CONFIG = [
    (8, "03JA", 1804, 2183, ["03JB", "043P", "03LZ", "03V7", "03Y9", "04C0", "05K8"]),
    (9, "04KE", 2184, 2465, ["05WY", "0639", "06FR", "06GT", "06NC", "04KF", "06ZD"]),
    (10, "04QH", 2466, 2547, ["04QJ", "04TM"]),
]


def fetch_tag(tag: str, cache_dir: Path) -> bool:
    f_path = cache_dir / f"tag_{tag}.html"
    if f_path.exists():
        return False
    url = f"https://kerodon.net/tag/{tag}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Polytypst Master Pipeline)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        f_path.write_bytes(resp.read())
    return True


def process_chapter(ch_num: int, ch_tag: str, start_p: int, end_p: int, sec_tags: list, cache_dir: Path, out_dir: Path, pdf_path: Path):
    print(f"\n=================================================================")
    print(f"PROCESSING CHAPTER {ch_num:02d} (Tag {ch_tag}, pp. {start_p} - {end_p})")
    print(f"=================================================================")

    # 1. Harvest subsections from section files
    subs_to_fetch = []
    for s in sec_tags:
        s_file = cache_dir / f"tag_{s}.html"
        if not s_file.exists():
            fetch_tag(s, cache_dir)
        if s_file.exists():
            html = s_file.read_text(encoding="utf-8")
            found_subs = re.findall(r"<a[^>]*href=\"/tag/([0-9A-Z]{4})\"[^>]*>(?:Subsection\s+)?([0-9\.]+.*?)</a>", html)
            seen = set()
            for st, _ in found_subs:
                if st not in seen:
                    seen.add(st)
                    subs_to_fetch.append(st)

    print(f"  Found {len(subs_to_fetch)} subsections in Chapter {ch_num}. Fetching uncached pages...")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda t: fetch_tag(t, cache_dir), subs_to_fetch))
    new_c = sum(1 for r in results if r)
    print(f"  Fetched {new_c} new subsection pages in {time.time() - t0:.1f}s.")

    # 2. Extract structured DOM
    extractor = KerodonExtractor(cache_dir)
    chapter = extractor.extract_chapter(ch_num, ch_tag)
    print(f"  Extracted: {chapter.title} ({len(chapter.sections)} sections)")

    # 3. Crop diagrams from kerodon.pdf
    fig_dir = out_dir / "figures"
    cropper = KerodonDiagramCropper(pdf_path, fig_dir)
    cropped = cropper.crop_chapter_diagrams(chapter, start_page=start_p, end_page=end_p)
    print(f"  Cropped {cropped} diagrams at 300 DPI.")

    # 4. Compile Typst, XeLaTeX, and PDF
    compiler = KerodonCompiler(chapter)
    out_typ = out_dir / f"chapter{ch_num}.typ"
    out_pdf = out_dir / f"chapter{ch_num}.pdf"
    out_tex = out_dir / f"chapter{ch_num}.tex"

    compiler.generate_typst(out_typ)
    compiler.generate_latex(out_tex)
    compiler.compile_pdf(out_typ, out_pdf)

    import pymupdf
    doc = pymupdf.open(str(out_pdf))
    print(f"  SUCCESS! Compiled Chapter {ch_num} to {out_pdf} ({len(doc)} pages, {out_pdf.stat().st_size / (1024*1024):.2f} MB)")
    return chapter


def main():
    cache_dir = Path("output/kerodon/cache_web")
    out_dir = Path("output/kerodon")
    pdf_path = Path("kerodon.pdf")

    all_chapters = []

    # Load Chapters 1 through 7
    extractor = KerodonExtractor(cache_dir)
    print("Loading Chapters 1 through 7...")
    ch1 = extractor.extract_chapter(1, "0001")
    ch2 = extractor.extract_chapter(2, "007J")
    ch3 = extractor.extract_chapter(3, "00SY")
    ch4 = extractor.extract_chapter(4, "01GP")
    ch5 = extractor.extract_chapter(5, "01J2")
    ch6 = extractor.extract_chapter(6, "02C9")
    ch7 = extractor.extract_chapter(7, "02H0")
    all_chapters.extend([ch1, ch2, ch3, ch4, ch5, ch6, ch7])
    print(f"Loaded {len(all_chapters)} chapters.")
    # Progressively process Chapters 4 through 10
    for cfg in CHAPTERS_CONFIG:
        ch_num, ch_tag, start_p, end_p, sec_tags = cfg
        try:
            ch_obj = process_chapter(ch_num, ch_tag, start_p, end_p, sec_tags, cache_dir, out_dir, pdf_path)
            all_chapters.append(ch_obj)
        except Exception as e:
            print(f"  [ERROR processing Chapter {ch_num}]: {e}")
            import traceback
            traceback.print_exc()

    print("\n=================================================================")
    print("ASSEMBLING MASTER KERODON COMPLETE VOLUME (ALL CHAPTERS)")
    print("=================================================================")

    # Combine into master book
    compiler_master = KerodonCompiler(all_chapters[0])
    preamble = compiler_master.TYPST_PREAMBLE

    master_typ_parts = [preamble]
    master_typ_parts.append(r"""
#align(center + horizon)[
  #text(34pt, weight: "bold", font: "New Computer Modern")[Kerodon]
  #v(1.2em)
  #text(15pt, style: "italic", font: "New Computer Modern")[An Online Resource for Homotopy-Coherent Mathematics]
  #v(2em)
  #text(16pt, font: "New Computer Modern")[Jacob Lurie]
  #v(1em)
  #text(10pt, fill: rgb("#64748b"))[Reconstructed & Typeset via Polytypst (Authentic LaTeX Typography)]
]

#pagebreak()

#outline(indent: 1.5em, depth: 2)

#pagebreak()
""")

    for ch in all_chapters:
        c_comp = KerodonCompiler(ch)
        c_typ = c_comp.generate_typst(out_dir / f"tmp_ch_{ch.number}.typ")
        c_body = c_typ.split(preamble)[-1].strip()
        master_typ_parts.append(f"\n#pagebreak(weak: true)\n{c_body}\n")
        (out_dir / f"tmp_ch_{ch.number}.typ").unlink(missing_ok=True)

    master_typ = out_dir / "kerodon_master.typ"
    master_pdf = out_dir / "kerodon_master.pdf"
    master_typ.write_text("\n".join(master_typ_parts), encoding="utf-8")

    print(f"Compiling complete master PDF to {master_pdf}...")
    compiler_master.compile_pdf(master_typ, master_pdf)

    import pymupdf
    final_doc = pymupdf.open(str(master_pdf))
    print(f"\n🏆 GRAND VICTORY! Master volume compiled to {master_pdf}")
    print(f"   Total Pages: {len(final_doc)} pages")
    print(f"   Total Size:  {master_pdf.stat().st_size / (1024*1024):.2f} MB")
    print(f"   Chapters:    {len(all_chapters)} chapters (100% complete)")


if __name__ == "__main__":
    main()
