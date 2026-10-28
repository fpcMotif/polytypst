import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import polytypst_native as native
import pymupdf

from polytypst.compiler.typst_math import REPO_FONTS_DIR

OUT = Path(sys.argv[1])


def timed(fn):
    t = time.perf_counter()
    out = fn()
    return time.perf_counter() - t, out


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["typst", *args[:1], "--font-path", str(REPO_FONTS_DIR), *args[1:]],
                          check=True, capture_output=True, text=True)


def pixels(pdf: pymupdf.Document, page: int) -> np.ndarray:
    pix = pdf[page].get_pixmap(dpi=72, colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, np.uint8)


def same_pdf(a: Path, b: Path) -> str:
    da, db = pymupdf.open(a), pymupdf.open(b)
    if len(da) != len(db):
        return f"page count {len(da)} != {len(db)}"
    text = sum(da[i].get_text() != db[i].get_text() for i in range(len(da)))
    ink = sum(not np.array_equal(pixels(da, i), pixels(db, i)) for i in range(len(da)))
    return f"{len(da)} pages, text differs on {text}, pixels differ on {ink}"


def main() -> None:
    typ = OUT / "bourbaki/bourbaki_1970_facsimile.typ"
    t_cli, _ = timed(lambda: cli("compile", "--root", "/", "--no-pdf-tags", str(typ), str(OUT / "cli.pdf")))
    t_fonts, typst = timed(lambda: native.Typst([str(REPO_FONTS_DIR)]))
    runs = []
    for _ in range(3):
        t, (pdf, _warn) = timed(lambda: typst.compile(str(typ), root="/", pdf_tags=False))
        runs.append(t)
    (OUT / "embedded.pdf").write_bytes(pdf)
    print(f"facsimile: cli {t_cli:.2f}s | font scan {t_fonts:.2f}s | embedded {', '.join(f'{t:.2f}s' for t in runs)}")
    print("facsimile pdf:", same_pdf(OUT / "cli.pdf", OUT / "embedded.pdf"))

    vintage = OUT / "bourbaki/bourbaki_1970_vintage.typ"
    t_cli, res = timed(lambda: cli("query", str(vintage), "<src-mark>", "--field", "value"))
    q = [timed(lambda: typst.query(str(vintage), "<src-mark>", field="value"))[0] for _ in range(3)]
    marks = typst.query(str(vintage), "<src-mark>", field="value")
    print(f"vintage query: cli {t_cli:.2f}s | embedded {', '.join(f'{t:.2f}s' for t in q)} | "
          f"same marks: {json.loads(res.stdout) == json.loads(marks)} ({len(json.loads(marks))})")

    harness = Path("src/parity/diagram_harness.typ").resolve()
    snippet = next(Path("src/bourbaki/diagrams").glob("fig_*.typ")).resolve()
    inputs = {"snippet": str(snippet), "font": "New Computer Modern", "size": "10", "weight": "400"}
    flags = [a for k, v in inputs.items() for a in ("--input", f"{k}={v}")]
    t_cli, _ = timed(lambda: cli("compile", "--root", "/", *flags, "--ppi", "300", str(harness), str(OUT / "cli.png")))
    t_emb, (png, _) = timed(lambda: typst.compile(str(harness), root="/", inputs=inputs, format="png", ppi=300))
    (OUT / "embedded.png").write_bytes(png)
    print(f"diagram png: cli {t_cli:.2f}s | embedded {t_emb:.2f}s | "
          f"identical bytes: {(OUT / 'cli.png').read_bytes() == png}")

    bad = OUT / "bad.typ"
    bad.write_text("ok\n\n$ x + #nosuch $\n", encoding="utf-8")
    try:
        typst.compile(str(bad), format="none")
    except native.TypstError as e:
        print("error text:", str(e).strip().splitlines()[0])


main()
