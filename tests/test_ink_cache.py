import os
from pathlib import Path

import numpy as np
import pymupdf
import pytest

from polytypst.parity.ink_cache import InkCache
from polytypst.parity.words import page_ink


def scan(path: Path, box: tuple[float, float, float, float], mtime: int) -> Path:
    doc = pymupdf.open()
    page = doc.new_page(width=100, height=100)
    page.draw_rect(pymupdf.Rect(*box), color=(0, 0, 0), fill=(0, 0, 0))
    doc.save(path)
    os.utime(path, ns=(mtime, mtime))
    return path


def test_a_cached_page_loads_the_ink_it_drew(tmp_path: Path) -> None:
    source = scan(tmp_path / "scan.pdf", (10, 10, 40, 30), 1_000_000_000)
    drawn = InkCache(source, tmp_path / "ink", page_ink)(1)
    loaded = InkCache(source, tmp_path / "ink", page_ink)(1)
    assert np.array_equal(drawn, page_ink(pymupdf.open(source)[0]))
    assert np.array_equal(loaded, drawn)
    with pytest.raises(ValueError):
        loaded[0, 0] = True


def test_a_changed_scan_draws_its_pages_again(tmp_path: Path) -> None:
    source = scan(tmp_path / "scan.pdf", (10, 10, 40, 30), 1_000_000_000)
    old = InkCache(source, tmp_path / "ink", page_ink)(1)
    scan(source, (50, 50, 90, 90), 2_000_000_000)
    new = InkCache(source, tmp_path / "ink", page_ink)(1)
    assert np.array_equal(new, page_ink(pymupdf.open(source)[0]))
    assert not np.array_equal(new, old)
