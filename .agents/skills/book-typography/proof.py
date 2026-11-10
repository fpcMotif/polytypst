"""Measure a book PDF against the book-typography bar and render its spreads.

Usage: uv run --project <polytypst root> python proof.py BOOK.pdf [--out DIR] [--pages A-B]

Prints one line per measure with PASS, WARN or FAIL and the pages involved.
With --out it also writes spread-NNN.png images (verso and recto side by side).
"""

import argparse
import itertools
import statistics
from collections import Counter
from pathlib import Path

import pymupdf


def body_size(doc, pages):
    sizes = Counter()
    for pno in pages:
        for block in doc[pno].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    sizes[round(span["size"], 1)] += len(span["text"].strip())
    return sizes.most_common(1)[0][0]


def body_lines(page, size):
    """Lines whose dominant span is body size, as (baseline, x0, x1, text, words)."""
    rows = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            main = max(spans, key=lambda s: len(s["text"]))
            if abs(main["size"] - size) > 0.3 or line["dir"] != (1.0, 0.0):
                continue
            text = "".join(s["text"] for s in line["spans"])
            rows.append(
                (round(main["origin"][1], 2), line["bbox"][0], line["bbox"][2], text)
            )
    rows.sort()
    merged = []
    for row in rows:
        if merged and abs(merged[-1][0] - row[0]) < 1.0:
            b, x0, x1, t = merged[-1]
            merged[-1] = (b, min(x0, row[1]), max(x1, row[2]), t + " " + row[3])
        else:
            merged.append(row)
    return merged


def last_text_baseline(page, size):
    """Baseline of the lowest line of body or note text, folios excluded."""
    lowest = None
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = [s for s in line["spans"] if s["text"].strip()]
            text = "".join(s["text"] for s in spans).strip()
            if (
                not spans
                or text.isdigit()
                or max(s["size"] for s in spans) < size * 0.7
            ):
                continue
            y = max(s["origin"][1] for s in spans)
            lowest = y if lowest is None else max(lowest, y)
    return lowest


def word_gaps(page, size, block_x0, block_x1):
    """Inter-word gaps in em on lines that fill the measure (justified lines)."""
    lines = {}
    for x0, y0, x1, y1, word, b, ln, wn in page.get_text("words"):
        if abs((y1 - y0) - size * 1.2) > size * 0.8:
            continue
        lines.setdefault((b, ln), []).append((x0, x1))
    gaps = []
    for words in lines.values():
        words.sort()
        if (
            len(words) < 4
            or words[0][0] > block_x0 + size * 2.5
            or words[-1][1] < block_x1 - size * 0.3
        ):
            continue
        gaps += [
            (b0 - a1) / size
            for (_, a1), (b0, _) in itertools.pairwise(words)
            if b0 > a1
        ]
    return gaps


def verdict(ok, warn=False):
    return "PASS" if ok else ("WARN" if warn else "FAIL")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out")
    ap.add_argument("--pages", help="1-based range such as 5-40")
    ap.add_argument(
        "--streak",
        type=int,
        default=2,
        help="most consecutive hyphenated lines allowed",
    )
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    if args.pages:
        a, b = (int(x) for x in args.pages.split("-"))
        pages = list(range(a - 1, min(b, len(doc))))
    else:
        pages = list(range(len(doc)))
    size = body_size(doc, pages)
    per_page = {pno: body_lines(doc[pno], size) for pno in pages}

    steps = Counter()
    for rows in per_page.values():
        for (b0, *_), (b1, *_) in itertools.pairwise(rows):
            steps[round(b1 - b0, 1)] += 1
    pitch = steps.most_common(1)[0][0]
    all_rows = [r for rows in per_page.values() for r in rows]
    block_x0 = (
        statistics.median(r[1] for r in all_rows if r[2] - r[1] > 0) if all_rows else 0
    )
    widths = sorted(r[2] - r[1] for r in all_rows)
    full = widths[int(len(widths) * 0.9)] if widths else 0

    print(
        f"body {size} pt, pitch {pitch} pt ({pitch / size:.2f}), measure {full:.0f} pt"
    )
    lengths = [len(r[3]) for r in all_rows if r[2] - r[1] > full * 0.97]
    if lengths:
        chars = statistics.median(lengths)
        print(
            f"{verdict(45 <= chars <= 75)} measure: median {chars:.0f} characters per full line (45-75)"
        )
    print(
        f"{verdict(1.15 <= pitch / size <= 1.5, pitch / size <= 1.9)} leading: pitch/size {pitch / size:.2f} (1.15-1.5 Latin, 1.4-1.8 CJK)"
    )

    off_grid, streak_pages, streak_max, depth_fail, widows, orphans = (
        [],
        [],
        0,
        [],
        [],
        [],
    )
    gaps = []
    for pno, rows in per_page.items():
        if not rows:
            continue
        # Prose lines only: centred displays and table rows may sit between grid lines.
        prose = [r for r in rows if r[1] - block_x0 < size * 2.5]
        top = prose[0][0] if prose else rows[0][0]
        if any(
            abs(((b - top) / pitch) - round((b - top) / pitch)) * pitch > 0.75
            for b, *_ in prose
        ):
            off_grid.append(pno + 1)
        run = 0
        for _, _, _, text in rows:
            run = run + 1 if text.rstrip().endswith(("-", "­")) else 0
            if run > args.streak:
                streak_pages.append(pno + 1)
            streak_max = max(streak_max, run)
        first, last = rows[0], rows[-1]
        if (
            first[2] - first[1] < full * 0.6
            and len(rows) > 3
            and rows[1][1] - block_x0 > size * 0.5
        ):
            widows.append(pno + 1)
        if (
            last[1] - block_x0 > size * 0.5
            and last[1] - block_x0 < size * 3
            and len(rows) > 3
        ):
            orphans.append(pno + 1)
        page = doc[pno]
        bx1 = max(r[2] for r in rows)
        gaps += word_gaps(page, size, block_x0, bx1)

    # A spread is measured to the lowest text line, notes included. A chapter
    # opening (first line sunk 3+ lines below the usual top) and the page before
    # an opening or a blank page run short by design, so those spreads are skipped.
    tops = [r[0][0] for r in per_page.values() if r]
    usual_top = statistics.median(tops) if tops else 0

    def opens_or_blank(pno):
        rows = per_page.get(pno)
        return rows is not None and (not rows or rows[0][0] > usual_top + 3 * pitch)

    for verso in pages:
        recto = verso + 1
        if (
            verso % 2 == 0
            or recto not in per_page
            or not per_page[verso]
            or not per_page[recto]
        ):
            continue
        last_page = recto + 1 >= len(doc)
        if last_page or opens_or_blank(recto) or opens_or_blank(recto + 1):
            continue
        a, b = (
            last_text_baseline(doc[verso], size),
            last_text_baseline(doc[recto], size),
        )
        diff = abs(a - b) / pitch
        if diff > 1.05:
            depth_fail.append(f"{verso + 1}-{recto + 1} ({diff:.1f} lines)")

    print(
        f"{verdict(not off_grid, len(off_grid) <= len(pages) // 5)} baseline grid: {len(off_grid)} pages off the grid {off_grid[:12]}"
    )
    print(
        f"{verdict(not depth_fail, len(depth_fail) <= 2)} spreads: {len(depth_fail)} spreads differ by more than one line {depth_fail[:8]}"
    )
    print(
        f"{verdict(not streak_pages)} hyphens: longest streak {streak_max}, limit {args.streak} {sorted(set(streak_pages))[:12]}"
    )
    print(
        f"{verdict(not widows, True)} widows (page opens on a short last line): {widows[:12]}"
    )
    print(
        f"{verdict(not orphans, True)} orphans (page ends on an indented first line): {orphans[:12]}"
    )
    if gaps:
        gaps.sort()
        q = lambda f: gaps[int(f * (len(gaps) - 1))]
        # 0.005 em of slack absorbs coordinate rounding at the exact limits.
        wide = sum(g > 0.505 for g in gaps) / len(gaps)
        tight = sum(g < 0.195 for g in gaps) / len(gaps)
        print(
            f"{verdict(wide < 0.02 and tight < 0.02, wide < 0.05 and tight < 0.05)} word spaces: "
            f"median {q(0.5):.2f} em, p5 {q(0.05):.2f}, p95 {q(0.95):.2f}; "
            f"{wide:.1%} over 0.5 em, {tight:.1%} under 0.2 em (justified lines only)"
        )

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for verso in pages:
            if verso % 2 == 0 and verso != 0:
                continue
            spread = pymupdf.open()
            w, h = doc[verso].rect.width, doc[verso].rect.height
            sheet = spread.new_page(width=2 * w, height=h)
            sheet.show_pdf_page(pymupdf.Rect(0, 0, w, h), doc, verso)
            if verso + 1 < len(doc) and verso != 0:
                sheet.show_pdf_page(pymupdf.Rect(w, 0, 2 * w, h), doc, verso + 1)
            sheet.draw_line((w, 0), (w, h), color=(0.6, 0.6, 0.6), width=0.3)
            sheet.get_pixmap(dpi=90).save(out / f"spread-{verso + 1:03d}.png")
        print(f"spreads written to {out}")


if __name__ == "__main__":
    main()
