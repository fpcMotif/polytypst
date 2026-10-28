import os
import sys
import time

import numpy as np
import polytypst_native as native
import pymupdf

from polytypst.parity.measure import cells, grow, regions
from polytypst.parity.words import INK_LEVEL, PEN_CHROMA, SCAN_DPI

PAGES = [31, 32, 33, 34, 35, 60, 61, 62, 120, 200]


def best(fn, n=5):
    times = []
    for _ in range(n):
        t = time.perf_counter()
        out = fn()
        times.append(time.perf_counter() - t)
    return min(times) * 1000, out


def bench_page(page: pymupdf.Page) -> tuple[float, ...]:
    t_gray, gpix = best(lambda: page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY), 2)
    t_rgb, cpix = best(lambda: page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csRGB, alpha=False), 2)
    gray = np.frombuffer(gpix.samples, np.uint8).reshape(gpix.height, gpix.width)
    rgb = np.frombuffer(cpix.samples, np.uint8).reshape(cpix.height, cpix.width, 3)

    def numpy_mask():
        wide = rgb.astype(np.int16)
        return (gray < INK_LEVEL) & (wide.max(axis=2) - wide.min(axis=2) < PEN_CHROMA)

    t_np, m_np = best(numpy_mask)
    t_rs, m_rs = best(lambda: native.ink_mask(gray, rgb, INK_LEVEL, PEN_CHROMA))
    assert np.array_equal(m_np, m_rs), f"mask differs on page {page.number + 1}"

    grid = np.ascontiguousarray(cells(m_np) & ~grow(np.roll(cells(m_np), 3, axis=1)))
    t_rp, r_py = best(lambda: regions(grid), 3)
    t_rr, r_rs = best(lambda: native.regions(grid), 3)
    assert [tuple(map(int, r)) for r in r_py] == r_rs, f"regions differ on page {page.number + 1}"
    print(f"p{page.number + 1:4d} {gray.shape} regions={len(r_rs):4d}  gray {t_gray:6.1f}  rgb {t_rgb:6.1f}  "
          f"mask np {t_np:6.1f} rs {t_rs:5.1f}  regions py {t_rp:7.1f} rs {t_rr:5.2f} ms")
    return t_gray, t_rgb, t_np, t_rs, t_rp, t_rr


def main(pdf: str) -> None:
    doc = pymupdf.open(pdf)
    names = ("render_gray", "render_rgb", "mask_numpy", "mask_rust", "regions_py", "regions_rust")
    rows = [bench_page(doc[p - 1]) for p in PAGES]
    means = {k: round(sum(col) / len(rows), 2) for k, col in zip(names, zip(*rows, strict=True), strict=True)}
    print(means, "ms/page, all outputs identical")


main(sys.argv[1] if len(sys.argv) > 1 else os.environ["BENCH_PDF"])
