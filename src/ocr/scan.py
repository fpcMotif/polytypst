import hashlib
import io
import json
import re
import shutil
from collections.abc import Iterable
from functools import cached_property
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageOps

from .pages import PageImage

SCAN_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"})
RENDERS_MANIFEST = "renders.json"
_NATIVE_MIN_WIDTH = 1000
_EXIF_ORIENTATION = 0x0112
_RENDER_SUFFIXES = (".png", ".jpg")


class SourceScanError(RuntimeError):
    pass


def _natural_key(path: Path) -> list[int | str]:
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def _orientation(im: Image.Image) -> int:
    return int(im.getexif().get(_EXIF_ORIENTATION, 1))


class SourceScan:
    """A source scan as numbered page images: a PDF, a folder of page images, or one image.

    Spreads scanned two pages to a sheet are split down the spine, so page numbers count book pages.
    """

    def __init__(self, path: Path, split: bool | None = None) -> None:
        self.path: Path = Path(path)
        self._images: list[Path] | None = None
        if not self.path.exists():
            raise SourceScanError(f"source scan not found: {self.path}")
        if self.path.is_dir():
            self._images = sorted(
                (
                    p
                    for p in self.path.iterdir()
                    if p.suffix.lower() in SCAN_IMAGE_SUFFIXES
                    and not p.name.startswith(".")
                ),
                key=_natural_key,
            )
            if not self._images:
                raise SourceScanError(
                    f"{self.path} holds no page images ({', '.join(sorted(SCAN_IMAGE_SUFFIXES))})"
                )
        elif self.path.suffix.lower() in SCAN_IMAGE_SUFFIXES:
            self._images = [self.path]
        elif self.path.suffix.lower() != ".pdf":
            raise SourceScanError(
                f"{self.path} is not a PDF, an image or a folder of images"
            )
        sizes = self._sheet_sizes()
        if split is None:
            split = sum(1 for w, h in sizes[:5] if w > h * 1.1) >= 3
        self.split: bool = split
        halves: tuple[int | None, ...] = (0, 1) if split else (None,)
        self._pages: list[tuple[int, int | None]] = [
            (sheet, half) for sheet in range(len(sizes)) for half in halves
        ]

    @property
    def page_count(self) -> int:
        return len(self._pages)

    @property
    def pdf(self) -> Path | None:
        """The PDF whose page N is scan page N, for passes that read its text layer or embedded images."""
        return self.path if self._images is None and not self.split else None

    @cached_property
    def _doc(self) -> pymupdf.Document:
        return pymupdf.open(self.path)

    def _sheet_sizes(self) -> list[tuple[float, float]]:
        if self._images is None:
            return [(page.rect.width, page.rect.height) for page in self._doc]
        sizes: list[tuple[float, float]] = []
        for path in self._images:
            with Image.open(path) as im:
                w, h = im.size
                sizes.append((h, w) if _orientation(im) in (5, 6, 7, 8) else (w, h))
        return sizes

    @cached_property
    def fingerprint(self) -> str:
        digest = hashlib.sha256()
        for path in self._images or [self.path]:
            digest.update(path.name.encode())
            with path.open("rb") as f:
                while chunk := f.read(1 << 20):
                    digest.update(chunk)
        return digest.hexdigest()

    def pages(
        self,
        out_dir: Path,
        dpi: int = 200,
        grey: bool = False,
        numbers: Iterable[int] | None = None,
    ) -> list[PageImage]:
        """Page images in `out_dir` as `p_NNN.png` or `.jpg`, rendering only the pages that lack one.

        `dpi` applies to PDF pages. A render made from another source or with other settings is redone.
        """
        out_dir.mkdir(parents=True, exist_ok=True)
        key = {
            "source": self.fingerprint,
            "dpi": dpi,
            "grey": grey,
            "split": self.split,
            "pages": self.page_count,
        }
        manifest = out_dir / RENDERS_MANIFEST
        if (
            manifest.exists()
            and json.loads(manifest.read_text(encoding="utf-8")) != key
        ):
            for old in out_dir.glob("p_*"):
                if old.suffix in _RENDER_SUFFIXES:
                    old.unlink()
        found: list[PageImage] = []
        for number in range(1, self.page_count + 1) if numbers is None else numbers:
            if not 1 <= number <= self.page_count:
                raise SourceScanError(
                    f"{self.path} has no page {number}; it has {self.page_count}"
                )
            path = next(
                (
                    p
                    for s in _RENDER_SUFFIXES
                    if (p := out_dir / f"p_{number:03d}{s}").exists()
                ),
                None,
            )
            found.append(
                PageImage(number, path or self._render(number, out_dir, dpi, grey))
            )
        _ = manifest.write_text(json.dumps(key, indent=1) + "\n", encoding="utf-8")
        return found

    def _render(self, number: int, out_dir: Path, dpi: int, grey: bool) -> Path:
        sheet, half = self._pages[number - 1]
        stem = out_dir / f"p_{number:03d}"
        if self._images is None:
            return self._render_pdf(sheet, half, stem, dpi, grey)
        return self._render_image(self._images[sheet], half, stem, grey)

    def _render_pdf(
        self, sheet: int, half: int | None, stem: Path, dpi: int, grey: bool
    ) -> Path:
        page = self._doc[sheet]
        if (
            half is None
            and not grey
            and (native := self._native_image(page)) is not None
        ):
            data, suffix = native
            dest = stem.with_suffix(suffix)
            _ = dest.write_bytes(data)
            return dest
        options: dict[str, object] = {"dpi": dpi}
        if grey:
            options["colorspace"] = pymupdf.csGRAY
        if half is not None:
            r = page.rect
            options["clip"] = pymupdf.Rect(
                r.x0 + r.width * half / 2, r.y0, r.x0 + r.width * (half + 1) / 2, r.y1
            )
        dest = stem.with_suffix(".png")
        page.get_pixmap(**options).save(dest)
        return dest

    def _native_image(self, page: pymupdf.Page) -> tuple[bytes, str] | None:
        """The page's only embedded image when it is a large PNG, or an RGB or grey JPEG, as stored."""
        images = page.get_images()
        if len(images) != 1:
            return None
        image = self._doc.extract_image(images[0][0])
        if not image or int(image.get("width", 0)) < _NATIVE_MIN_WIDTH:
            return None
        ext = str(image.get("ext", ""))
        if ext == "png":
            data = bytes(image["image"])
            with Image.open(io.BytesIO(data)) as im:
                if np.array(im.convert("L")).mean() < 128:
                    return None
            return data, ".png"
        if ext in ("jpeg", "jpg") and int(image.get("colorspace", 0)) in (1, 3):
            return bytes(image["image"]), ".jpg"
        return None

    def _render_image(
        self, source: Path, half: int | None, stem: Path, grey: bool
    ) -> Path:
        with Image.open(source) as im:
            if (
                half is None
                and not grey
                and source.suffix.lower() in (".png", ".jpg", ".jpeg")
                and _orientation(im) == 1
            ):
                dest = stem.with_suffix(
                    ".png" if source.suffix.lower() == ".png" else ".jpg"
                )
                _ = shutil.copyfile(source, dest)
                return dest
            page = ImageOps.exif_transpose(im)
        if half is not None:
            w, h = page.size
            page = page.crop((w * half // 2, 0, w * (half + 1) // 2, h))
        if grey:
            page = page.convert("L")
        elif page.mode not in ("RGB", "L"):
            page = page.convert("RGB")
        dest = stem.with_suffix(".png")
        page.save(dest)
        return dest
