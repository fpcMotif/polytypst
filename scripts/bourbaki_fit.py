"""Fit each page of the 1970 Bourbaki rebuild to the height its original page fills.

Usage: uv run python scripts/bourbaki_fit.py [ROUNDS]

Every source page is its own output page. Each round compiles the Typst source,
reads the position markers, and solves per-page leading (line spacing) so the
first-to-last text line distance equals the original's. Pages that need less
leading than MIN_LEADING get a slightly smaller font, which re-breaks the lines.
A page whose height does not grow with leading has spare room that its vertical
fill (space around displays and items) already takes, so it keeps the base leading.
A page that ends higher than a full scan page reserves that empty space at its bottom,
so the fill stops at the scan's last line.
"""

import json
import sys

import numpy as np
import pymupdf

from polytypst.bourbaki.pagefit import ORIGINAL, OUT_DIR, query_marks
from polytypst.bourbaki.spec import CHAPTERS

FIT = OUT_DIR / "page_fit.json"
TARGETS = OUT_DIR / "page_targets.json"

BODY_HEIGHT = 609 - 74 - 66
BASE_SIZE, BASE_LEADING = 9.6, 4.3
MIN_LEADING, MAX_LEADING = 3.0, 6.5
MIN_SIZE, SIZE_STEP = 8.8, 0.2
MIN_RESERVE = 6.0
DPI = 150


def text_rows(page: pymupdf.Page) -> list[tuple[float, float, float, float]]:
    """Ink rows on a scan page as (top, bottom, left, right) in pt."""
    pix = page.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    ink = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width) < 128
    on = ink.sum(axis=1) > 1
    rows, start = [], None
    for y, v in enumerate(np.append(on, False)):
        if v and start is None:
            start = y
        elif not v and start is not None:
            if y - start >= 3:
                xs = np.where(ink[start:y].any(axis=0))[0]
                rows.append((start, y, xs.min(), xs.max()))
            start = None
    k = 72 / DPI
    return [(a * k, b * k, c * k, d * k) for a, b, c, d in rows]


def measure_targets(pages: list[int]) -> dict[str, dict[str, float]]:
    """First and last text-line tops on each original page, header and folio removed."""
    doc = pymupdf.open(ORIGINAL)
    targets: dict[str, dict[str, float]] = {}
    for pno in pages:
        rows = text_rows(doc[pno - 1])
        if rows and rows[-1][3] - rows[-1][2] < 25:
            rows = rows[:-1]
        if len(rows) < 3:
            continue
        body = rows[1:]
        targets[str(pno)] = {"top": body[0][0], "last": body[-1][0], "bottom": body[-1][1]}
    return targets


def measured_heights(marks: list[dict]) -> dict[str, float]:
    """Distance from the first-line marker to the last-line marker, counted across overflow pages."""
    tops = {str(m["key"]): m for m in marks if m["kind"] == "top"}
    ends = {str(m["key"]): m for m in marks if m["kind"] == "end"}
    return {
        key: (ends[key]["page"] - top["page"]) * BODY_HEIGHT + ends[key]["y"] - top["y"]
        for key, top in tops.items()
        if key in ends
    }


def bottom_reserves(targets: dict[str, dict[str, float]], keys: list[str]) -> dict[str, float]:
    """Empty space below the last text line that a scan page has beyond a full page's, in pt."""
    doc = pymupdf.open(ORIGINAL)
    gap = {k: doc[int(k) - 1].rect.height - targets[k]["bottom"] for k in keys}
    full = float(np.median(list(gap.values())))
    return {k: round(g - full, 1) if g - full > MIN_RESERVE else 0.0 for k, g in gap.items()}


def write_fit(fit: dict[str, dict[str, float]]) -> None:
    FIT.write_text(json.dumps({"pages": fit}, indent=1), encoding="utf-8")


def main(rounds: int) -> None:
    write_fit({})
    marks = query_marks()
    pages = sorted({int(m["key"]) for m in marks if m["kind"] == "top"})
    if TARGETS.exists():
        targets = json.loads(TARGETS.read_text())
    else:
        targets = measure_targets(pages)
        TARGETS.write_text(json.dumps(targets, indent=1))
    skip = {str(c.start_page) for c in CHAPTERS}
    keys = [str(p) for p in pages if str(p) in targets and str(p) not in skip]
    want = {k: targets[k]["last"] - targets[k]["top"] for k in keys}
    reserves = bottom_reserves(targets, keys)
    fit = {k: {"size": BASE_SIZE, "leading": BASE_LEADING, "reserve": reserves[k]} for k in keys}

    print(f"{len(keys)} pages to fit; {len(skip)} chapter openings kept at defaults", flush=True)
    for rnd in range(rounds):
        write_fit(fit)
        h0 = measured_heights(query_marks())
        print(f"round {rnd + 1}: measured current spacing; {report(keys, want, h0)}", flush=True)
        probe = {k: {**v, "leading": v["leading"] + 1.0} for k, v in fit.items()}
        write_fit(probe)
        h1 = measured_heights(query_marks())
        print(f"round {rnd + 1}: measured probe spacing", flush=True)
        shrunk = 0
        for k in keys:
            if k not in h0 or k not in h1:
                continue
            gaps = h1[k] - h0[k]
            if gaps < 0.5:
                fit[k] = {**fit[k], "leading": BASE_LEADING}
                continue
            leading = fit[k]["leading"] + (want[k] - h0[k]) / gaps
            if leading < MIN_LEADING and fit[k]["size"] > MIN_SIZE:
                fit[k]["size"] = round(fit[k]["size"] - SIZE_STEP, 2)
                fit[k]["leading"] = BASE_LEADING
                shrunk += 1
            else:
                fit[k]["leading"] = round(min(MAX_LEADING, max(MIN_LEADING, leading)), 3)
        write_fit(fit)
        err = report(keys, want, measured_heights(query_marks()))
        print(f"round {rnd + 1}: {shrunk} pages got a smaller font; {err}", flush=True)
        if shrunk == 0:
            break


def report(keys: list[str], want: dict[str, float], got: dict[str, float]) -> str:
    errs = np.array([abs(got[k] - want[k]) for k in keys if k in got])
    return (
        f"{len(errs)} pages, height error median {np.median(errs):.1f}pt, "
        f"<=3pt {np.mean(errs <= 3) * 100:.0f}%, >11pt (a line or more) {np.sum(errs > 11)}"
    )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
