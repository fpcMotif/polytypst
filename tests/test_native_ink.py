import io
from collections import deque

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from PIL import Image
from polytypst_native import encode_png

from polytypst.parity import visual
from polytypst.parity.measure import regions
from polytypst.parity.report import ink_overlay
from polytypst.parity.visual import (
    DUST_LINE_SHARE,
    LAYOUT_COLUMNS,
    LAYOUT_INK_SHARE,
    LINE_GAP_PX,
    LINE_MIN_INK_PX,
    LINE_ROW_MIN_PX,
    MATCH_PT,
    MERGE_X_PT,
    MERGE_Y_PT,
    MIN_AREA_PT2,
    PageVisual,
    Region,
)
from polytypst.parity.words import (
    EDGE_GAP_PT,
    PT_PER_PX,
    line_measure,
    without_edge_lines,
)


def _crop(a, b):
    h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
    return a[:h, :w], b[:h, :w]


def _dilate(img):
    out = img.copy()
    out[1:] |= img[:-1]
    out[:-1] |= img[1:]
    out[:, 1:] |= img[:, :-1]
    out[:, :-1] |= img[:, 1:]
    return out


def _runs(idx, gap):
    return np.split(idx, np.flatnonzero(np.diff(idx) > gap) + 1) if idx.size else []


def _near(ink):
    for _ in range(round(MATCH_PT / PT_PER_PX)):
        ink = _dilate(ink)
    return ink


def _reference_regions(mask, kind):
    out = []
    for band in _runs(np.flatnonzero(mask.any(axis=1)), round(MERGE_Y_PT / PT_PER_PX)):
        rows = mask[band[0] : band[-1] + 1]
        for run in _runs(
            np.flatnonzero(rows.any(axis=0)), round(MERGE_X_PT / PT_PER_PX)
        ):
            block = rows[:, run[0] : run[-1] + 1]
            area = float(block.sum()) * PT_PER_PX**2
            if area < MIN_AREA_PT2:
                continue
            ys = np.flatnonzero(block.any(axis=1)) + band[0]
            box = (
                run[0] * PT_PER_PX,
                ys[0] * PT_PER_PX,
                (run[-1] + 1) * PT_PER_PX,
                (ys[-1] + 1) * PT_PER_PX,
            )
            out.append(
                Region(kind, tuple(round(float(v), 2) for v in box), round(area, 1))
            )
    return out


def _reference_layout(source, rebuilt):
    a, b = _crop(source, rebuilt)
    cell = max(1, a.shape[1] // LAYOUT_COLUMNS)

    def inked(ink):
        h, w = ink.shape[0] // cell * cell, ink.shape[1] // cell * cell
        return (
            ink[:h, :w].reshape(h // cell, cell, w // cell, cell).mean(axis=(1, 3))
            >= LAYOUT_INK_SHARE
        )

    ca, cb = inked(a), inked(b)
    union = int((ca | cb).sum())
    return round(float((ca ^ cb).sum() / union), 4) if union else 0.0


def _reference_edges(ink):
    rows = np.flatnonzero(ink.sum(axis=1) > LINE_ROW_MIN_PX)
    bands = [(int(r[0]), int(r[-1]) + 1) for r in _runs(rows, LINE_GAP_PX)]
    bands = [(a, b) for a, b in bands if ink[a:b].sum() > LINE_MIN_INK_PX]
    if not bands:
        return (0.0, 0.0, 0.0, 0.0)
    height = float(np.median([b - a for a, b in bands]))
    while len(bands) > 1 and bands[0][1] - bands[0][0] < DUST_LINE_SHARE * height:
        bands.pop(0)
    while len(bands) > 1 and bands[-1][1] - bands[-1][0] < DUST_LINE_SHARE * height:
        bands.pop()
    extents = []
    for a, b in bands:
        band = ink[a:b]
        runs = [
            r
            for r in _runs(
                np.flatnonzero(band.any(axis=0)), round(EDGE_GAP_PT / PT_PER_PX)
            )
            if band[:, r[0] : r[-1] + 1].sum() > LINE_MIN_INK_PX
        ]
        if runs:
            extents.append((int(runs[0][0]), int(runs[-1][-1])))
    if not extents:
        return (0.0, 0.0, 0.0, 0.0)
    starts, ends = zip(*extents, strict=True)
    left, right = line_measure(list(starts), [e + 1 for e in ends])
    return (
        left * PT_PER_PX,
        bands[0][0] * PT_PER_PX,
        right * PT_PER_PX,
        bands[-1][1] * PT_PER_PX,
    )


def _reference_shift(source, rebuilt):
    a, b = _crop(without_edge_lines(source), without_edge_lines(rebuilt))
    sa, sb = _reference_edges(a), _reference_edges(b)
    return tuple(round(y - x, 1) for x, y in zip(sa, sb, strict=True))


def reference_page_visual(source, rebuilt):
    a, b = _crop(source, rebuilt)
    extra, missing = b & ~_near(a), a & ~_near(b)
    found = sorted(
        _reference_regions(extra, "extra") + _reference_regions(missing, "missing"),
        key=lambda r: -r.area_pt2,
    )
    return PageVisual(
        1,
        1,
        round(float(extra.sum() / max(1, b.sum())), 4),
        round(float(missing.sum() / max(1, a.sum())), 4),
        tuple(found),
        _reference_layout(source, rebuilt),
        _reference_shift(source, rebuilt),
    )


def reference_regions(grid):
    seen = np.zeros_like(grid)
    found = []
    for y, x in zip(*np.nonzero(grid), strict=True):
        if seen[y, x]:
            continue
        queue, box, n = deque([(y, x)]), [y, x, y, x], 0
        seen[y, x] = True
        while queue:
            cy, cx = queue.popleft()
            n += 1
            box = [min(box[0], cy), min(box[1], cx), max(box[2], cy), max(box[3], cx)]
            for ny in range(max(cy - 1, 0), min(cy + 2, grid.shape[0])):
                for nx in range(max(cx - 1, 0), min(cx + 2, grid.shape[1])):
                    if grid[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
        found.append(tuple(int(v) for v in (*box, n)))
    return found


def text_page(rng, h, w, density):
    ink = rng.random((h, w)) < density / 20
    for top in range(int(rng.integers(0, 12)), h - 8, int(rng.integers(10, 30))):
        x = int(rng.integers(0, 40))
        while x < w - 10:
            width = int(rng.integers(5, 60))
            ink[top : top + int(rng.integers(3, 9)), x : x + width] |= (
                rng.random((1, 1)) < 0.9
            )
            ink[top : top + 8, x : x + width] &= (
                rng.random((min(8, h - top), min(width, w - x))) < density * 4 + 0.3
            )
            x += width + int(rng.integers(2, 40))
    if rng.random() < 0.3:
        ink[:, int(rng.integers(0, w))] = True
    return ink


pages = st.tuples(
    st.integers(0, 2**32 - 1),
    st.integers(7, 260),
    st.integers(7, 420),
    st.floats(0.0, 0.3),
)


@pytest.mark.slow
@settings(max_examples=150, deadline=None)
@given(pages, pages, st.integers(0, 6), st.integers(0, 6), st.booleans())
def test_page_visual_equals_the_numpy_reference(scan, built, dy, dx, strided):
    s = text_page(np.random.default_rng(scan[0]), *scan[1:])
    b = text_page(np.random.default_rng(built[0]), *built[1:])
    if strided:
        s, b = s[dy:, dx:], b[: b.shape[0] - dy, : b.shape[1] - dx]
    assert visual.page_visual(s, b, 1, 1) == reference_page_visual(s, b)


@pytest.mark.slow
@settings(max_examples=150, deadline=None)
@given(
    st.integers(0, 2**32 - 1),
    st.integers(1, 80),
    st.integers(1, 80),
    st.floats(0.0, 0.7),
)
def test_regions_equal_the_breadth_first_reference(seed, h, w, density):
    grid = np.random.default_rng(seed).random((h, w)) < density
    assert regions(grid) == reference_regions(grid)


def test_overlay_colours_ink_by_page(tmp_path):
    scan = np.array([[True, True, False, False]])
    rebuilt = np.array([[True, False, True, False, True]])
    ink_overlay(scan, rebuilt, tmp_path / "o.png")
    pixels = np.asarray(Image.open(tmp_path / "o.png").convert("RGB"))
    assert pixels.tolist() == [[[0, 0, 0], [220, 0, 0], [0, 170, 220], [255, 255, 255]]]


@settings(max_examples=60, deadline=None)
@given(
    st.integers(0, 2**32 - 1), st.integers(1, 90), st.integers(1, 90), st.integers(1, 4)
)
def test_encoded_png_decodes_to_the_same_samples(seed, h, w, channels):
    samples = np.random.default_rng(seed).integers(
        0, 256, (h, w, channels), dtype=np.uint8
    )
    decoded = np.asarray(
        Image.open(io.BytesIO(encode_png(samples.tobytes(), w, h, channels)))
    )
    assert np.array_equal(decoded.reshape(h, w, channels), samples)


@pytest.mark.parametrize(("size", "channels"), [(11, 3), (12, 5), (12, 0)])
def test_encode_png_rejects_a_wrong_shape(size, channels):
    with pytest.raises(ValueError):
        encode_png(bytes(size), 2, 2, channels)
