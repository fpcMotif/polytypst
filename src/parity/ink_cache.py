"""Ink rasters of a scan's pages, each drawn once and kept on disk: the scan does not change between builds."""

import hashlib
import inspect
from collections import OrderedDict
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pymupdf

MEMO_PAGES = 8


class InkCache:
    """`draw` applied to each page of the `source` scan, kept in `folder` as packed bits and the last `MEMO_PAGES`
    pages in memory, read-only as callers share them. The folder name hashes the scan file's path, size and change time and the source of the module
    that defines `draw`, so a new scan, a changed threshold or a changed function draws the pages again."""

    def __init__(self, source: Path, folder: Path, draw: Callable[[pymupdf.Page], np.ndarray]) -> None:
        stat = source.stat()
        code = inspect.getsource(inspect.getmodule(draw) or draw)
        key = hashlib.sha1(f"{source.resolve()}|{stat.st_size}|{stat.st_mtime_ns}|{code}".encode()).hexdigest()[:16]
        self.folder = folder / f"{draw.__name__}_{key}"
        self.source = source
        self.draw = draw
        self._doc: pymupdf.Document | None = None
        self._memo: OrderedDict[int, np.ndarray] = OrderedDict()

    def __getstate__(self) -> dict:
        return {**self.__dict__, "_doc": None, "_memo": OrderedDict()}

    def __call__(self, page: int) -> np.ndarray:
        """The ink of 1-based `page`."""
        if (ink := self._memo.get(page)) is not None:
            self._memo.move_to_end(page)
            return ink
        path = self.folder / f"p_{page:04d}.npz"
        if path.exists():
            with np.load(path) as stored:
                shape = tuple(int(v) for v in stored["shape"])
                ink = np.unpackbits(stored["bits"], count=shape[0] * shape[1]).reshape(shape).astype(bool)
        else:
            if self._doc is None:
                self._doc = pymupdf.open(self.source)
            ink = self.draw(self._doc[page - 1])
            self.folder.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix(".part.npz")
            np.savez_compressed(partial, bits=np.packbits(ink), shape=np.array(ink.shape))
            partial.replace(path)
        ink.flags.writeable = False
        self._memo[page] = ink
        if len(self._memo) > MEMO_PAGES:
            self._memo.popitem(last=False)
        return ink
