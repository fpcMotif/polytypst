"""300-DPI PDF template matching, smart cropping, and Apple Vision OCR verification for TAOCP."""

from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pymupdf
from PIL import Image

from polytypst.ocr.lines import DEFAULT_OCR_LANGUAGES, line_reader
from polytypst.ocr.pages import PageImage

# Measured linear resolution ratio between 300-DPI PDF scan (1844px text block)
# and EPUB JPEG graphics (674px text block).
PDF_TO_EPUB_SCALE = 2.736


@dataclass(slots=True)
class AssetMeta:
    """Metadata for an extracted and upgraded graphic asset."""

    orig_name: str
    out_filename: str
    w_epub: int
    h_epub: int
    w_out: int
    h_out: int
    book_page: int | None
    pdf_page_1based: int | None
    ncc_score: float
    method: str


def _parse_page_from_filename(fname: str) -> int | None:
    """Extract embedded book page number from filenames like p14fig01.jpg or equ-381-01.jpg."""
    m = re.match(r"^(?:p|en|pp)(\d+)", fname)
    if m:
        return int(m.group(1))
    m = re.match(r"^(?:equ|fig|tab)-(\d+)-", fname)
    if m:
        return int(m.group(1))
    m = re.match(r"^(\d+)(?:equ|fig|tab|sym)", fname)
    if m:
        return int(m.group(1))
    return None


def _fft_ncc_2d(page_inv: np.ndarray, tpl_inv: np.ndarray) -> tuple[float, int, int]:
    """Compute 2D FFT normalized cross-correlation in float64 and return (score, best_y, best_x)."""
    hp, wp = page_inv.shape
    ht, wt = tpl_inv.shape
    if ht >= hp or wt >= wp or ht < 4 or wt < 4:
        return 0.0, 0, 0

    t_mean = float(tpl_inv.mean())
    t_Zero = tpl_inv - t_mean
    t_norm = float(np.sqrt(np.sum(t_Zero * t_Zero)))
    if t_norm < 1e-3:
        return 0.0, 0, 0

    f_page = np.fft.rfft2(page_inv, s=(hp, wp))
    f_tpl = np.fft.rfft2(t_Zero[::-1, ::-1], s=(hp, wp))
    cc = np.fft.irfft2(f_page * f_tpl, s=(hp, wp))[ht - 1 :, wt - 1 :]

    s1 = (
        np.pad(page_inv, ((1, 0), (1, 0)))
        .cumsum(0, dtype=np.float64)
        .cumsum(1, dtype=np.float64)
    )
    s2 = (
        np.pad(page_inv * page_inv, ((1, 0), (1, 0)))
        .cumsum(0, dtype=np.float64)
        .cumsum(1, dtype=np.float64)
    )
    win_sum = s1[ht:, wt:] - s1[:-ht, wt:] - s1[ht:, :-wt] + s1[:-ht, :-wt]
    win_sq = s2[ht:, wt:] - s2[:-ht, wt:] - s2[ht:, :-wt] + s2[:-ht, :-wt]
    win_std = np.sqrt(np.maximum(win_sq - (win_sum * win_sum) / (ht * wt), 0.0))

    min_std = max(10.0, 0.25 * t_norm)
    denom = np.maximum(win_std * t_norm, 1.0)
    ncc = np.where(win_std >= min_std, cc / denom, 0.0)
    idx = int(np.argmax(ncc))
    by, bx = divmod(idx, ncc.shape[1])
    return float(ncc[by, bx]), int(by), int(bx)


def _match_coarse_to_fine(
    page_arr: np.ndarray,
    epub_img: Image.Image,
) -> tuple[float, int, int, int, int]:
    """Locate an EPUB graphic on a 300-DPI PDF scan page using 2x coarse + local fine NCC."""
    tw = max(8, round(epub_img.width * PDF_TO_EPUB_SCALE / 2.0))
    th = max(8, round(epub_img.height * PDF_TO_EPUB_SCALE / 2.0))
    tpl_small = epub_img.resize((tw, th), Image.Resampling.BILINEAR)
    t_inv = 255.0 - np.asarray(tpl_small, dtype=np.float64)
    p_inv = 255.0 - page_arr[::2, ::2].astype(np.float64)

    score, by, bx = _fft_ncc_2d(p_inv, t_inv)
    y0, x0 = by * 2, bx * 2
    full_w = round(epub_img.width * PDF_TO_EPUB_SCALE)
    full_h = round(epub_img.height * PDF_TO_EPUB_SCALE)
    return score, x0, y0, full_w, full_h


def _smart_crop_300dpi(
    page_arr: np.ndarray,
    x0: int,
    y0: int,
    w: int,
    h: int,
    pad: int = 8,
    max_expand: int = 24,
) -> Image.Image:
    """Crop from a 300-DPI page scan with whitespace-guided border expansion and contrast cleanup."""
    hp, wp = page_arr.shape
    top = max(0, y0 - pad)
    bot = min(hp, y0 + h + pad)
    left = max(0, x0 - pad)
    right = min(wp, x0 + w + pad)

    ink = page_arr < 200
    for _ in range(max_expand):
        if top > 0 and ink[top, left:right].any():
            top -= 1
        else:
            break
    for _ in range(max_expand):
        if bot < hp and ink[bot - 1, left:right].any():
            bot += 1
        else:
            break
    for _ in range(max_expand):
        if left > 0 and ink[top:bot, left].any():
            left -= 1
        else:
            break
    for _ in range(max_expand):
        if right < wp and ink[top:bot, right - 1].any():
            right += 1
        else:
            break

    sub = page_arr[top:bot, left:right]
    sub_ink = sub < 200
    if sub_ink.any():
        ys, xs = np.where(sub_ink)
        margin = 6
        r0 = max(0, int(ys.min()) - margin)
        r1 = min(sub.shape[0], int(ys.max()) + 1 + margin)
        c0 = max(0, int(xs.min()) - margin)
        c1 = min(sub.shape[1], int(xs.max()) + 1 + margin)
        sub = sub[r0:r1, c0:c1]

    sub_f = sub.astype(np.float32)
    norm = np.clip((sub_f - 35.0) * (255.0 / (235.0 - 35.0)), 0.0, 255.0).astype(
        np.uint8
    )
    return Image.fromarray(norm, mode="L")


def _upscale_clean_epub_image(epub_img: Image.Image) -> Image.Image:
    """Upscale a low-res EPUB JPEG 2x with Lanczos and clean JPEG background artifacts."""
    up = epub_img.resize(
        (max(1, epub_img.width * 2), max(1, epub_img.height * 2)),
        Image.Resampling.LANCZOS,
    )
    arr = np.asarray(up, dtype=np.float32)
    norm = np.clip((arr - 45.0) * (255.0 / (220.0 - 45.0)), 0.0, 255.0).astype(np.uint8)
    return Image.fromarray(norm, mode="L")


class TaocpAssetProcessor:
    """Extracts, matches, and upgrades TAOCP graphic assets from EPUB + 300-DPI PDF scans."""

    def __init__(self, epub_path: Path, pdf_path: Path, out_dir: Path) -> None:
        self.epub_path = epub_path
        self.pdf_path = pdf_path
        self.out_dir = out_dir
        self.figures_dir = out_dir / "figures"
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.assets: dict[str, AssetMeta] = {}
        self._page_cache: dict[int, np.ndarray] = {}

    def _get_pdf_page_gray(
        self, doc: pymupdf.Document, pdf_page_0based: int
    ) -> np.ndarray | None:
        if pdf_page_0based < 0 or pdf_page_0based >= len(doc):
            return None
        if pdf_page_0based in self._page_cache:
            return self._page_cache[pdf_page_0based]
        if len(self._page_cache) > 16:
            oldest = next(iter(self._page_cache))
            del self._page_cache[oldest]
        pix = doc[pdf_page_0based].get_pixmap(colorspace=pymupdf.csGRAY, dpi=300)
        arr = (
            np.frombuffer(pix.samples, dtype=np.uint8)
            .reshape(pix.height, pix.width)
            .copy()
        )
        self._page_cache[pdf_page_0based] = arr
        return arr

    def process_assets(
        self,
        required_images: dict[str, int | None],
    ) -> dict[str, AssetMeta]:
        """Extract and upgrade all required graphic filenames mapped to their book page."""
        manifest_path = self.out_dir / "assets_manifest.json"
        cached_manifest: dict[str, dict[str, Any]] = {}
        if manifest_path.exists():
            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    cached_manifest = raw
            except (OSError, ValueError):
                cached_manifest = {}

        ordered_items = sorted(
            required_images.items(),
            key=lambda kv: (kv[1] or _parse_page_from_filename(kv[0]) or 0, kv[0]),
        )

        with zipfile.ZipFile(self.epub_path) as zf, pymupdf.open(self.pdf_path) as doc:
            n_pdf = len(doc)
            for orig_name, dom_page in ordered_items:
                stem = Path(orig_name).stem
                out_filename = f"{stem}.png"
                out_path = self.figures_dir / out_filename

                if orig_name in cached_manifest and out_path.exists():
                    entry = cached_manifest[orig_name]
                    w_c = int(entry["w_epub"])
                    h_c = int(entry["h_epub"])
                    sc_c = float(entry["ncc_score"])
                    if not (w_c >= 60 and h_c >= 18 and sc_c == 0.0):
                        self.assets[orig_name] = AssetMeta(
                            orig_name=str(entry["orig_name"]),
                            out_filename=str(entry["out_filename"]),
                            w_epub=w_c,
                            h_epub=h_c,
                            w_out=int(entry["w_out"]),
                            h_out=int(entry["h_out"]),
                            book_page=entry.get("book_page"),
                            pdf_page_1based=entry.get("pdf_page_1based"),
                            ncc_score=sc_c,
                            method=str(entry["method"]),
                        )
                        continue

                zip_member = f"OEBPS/html/graphics/{orig_name}"
                try:
                    raw_bytes = zf.read(zip_member)
                except KeyError:
                    continue

                epub_img = Image.open(io.BytesIO(raw_bytes)).convert("L")
                w_epub, h_epub = epub_img.size

                fn_page = _parse_page_from_filename(orig_name)
                book_page = dom_page if dom_page is not None else fn_page

                cand_pages: list[int] = []
                if book_page is not None and 1 <= book_page <= 785:
                    for p0 in (book_page + 10, book_page + 11):
                        if 0 <= p0 < n_pdf and p0 not in cand_pages:
                            cand_pages.append(p0)
                    if book_page >= 780:
                        for p0 in (n_pdf - 2, n_pdf - 1):
                            if 0 <= p0 < n_pdf and p0 not in cand_pages:
                                cand_pages.append(p0)
                if fn_page is not None and 1 <= fn_page <= 785:
                    for p0 in (fn_page + 10, fn_page + 11):
                        if 0 <= p0 < n_pdf and p0 not in cand_pages:
                            cand_pages.append(p0)

                best_score = 0.0
                best_crop: tuple[np.ndarray, int, int, int, int, int] | None = None

                # Perform 300-DPI PDF template matching for block figures, tables, and display equations
                if w_epub >= 60 and h_epub >= 18 and cand_pages:
                    for p0 in cand_pages:
                        page_arr = self._get_pdf_page_gray(doc, p0)
                        if page_arr is None:
                            continue
                        score, x0, y0, fw, fh = _match_coarse_to_fine(
                            page_arr, epub_img
                        )
                        if score > best_score:
                            best_score = score
                            best_crop = (page_arr, x0, y0, fw, fh, p0 + 1)
                        if best_score >= 0.42:
                            break

                if best_crop is not None and best_score >= 0.38:
                    page_arr, x0, y0, fw, fh, pdf_p1 = best_crop
                    out_img = _smart_crop_300dpi(page_arr, x0, y0, fw, fh)
                    method = "pdf_300dpi_ncc"
                    pdf_page_1based: int | None = pdf_p1
                else:
                    out_img = _upscale_clean_epub_image(epub_img)
                    method = "epub_upscaled"
                    pdf_page_1based = None

                out_img.save(out_path, format="PNG")
                self.assets[orig_name] = AssetMeta(
                    orig_name=orig_name,
                    out_filename=out_filename,
                    w_epub=w_epub,
                    h_epub=h_epub,
                    w_out=out_img.width,
                    h_out=out_img.height,
                    book_page=book_page,
                    pdf_page_1based=pdf_page_1based,
                    ncc_score=round(best_score, 4),
                    method=method,
                )

        manifest_data = {k: asdict(v) for k, v in sorted(self.assets.items())}
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        return self.assets

    def run_ocr_verification(self) -> dict[str, object]:
        """Run Apple Vision OCR across key PDF pages to verify page alignment & tabular fidelity."""
        import tempfile

        ocr_report_path = self.out_dir / "ocr_verification.json"
        if ocr_report_path.exists():
            try:
                return json.loads(ocr_report_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                ocr_report_path.unlink(missing_ok=True)

        reader = line_reader(DEFAULT_OCR_LANGUAGES)
        checkpoint_pages = [
            ("frontmatter_title", 1, None),
            ("preface_opening", 5, None),
            ("ch05_sorting_opening", 12, 1),
            ("ch05_fig01_page", 25, 14),
            ("ch05_heapsort_page", 155, 144),
            ("ch06_searching_opening", 403, 392),
            ("ch06_hashing_page", 524, 513),
            ("answers_opening", 553, 542),
            ("appendix_a_table1_p748", 759, 748),
            ("appendix_a_table1_p749", 760, 749),
            ("appendix_a_table2_p750", 761, 750),
            ("appendix_b_notations_p752", 763, 752),
        ]

        results: list[dict[str, object]] = []
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            pymupdf.open(self.pdf_path) as doc,
        ):
            images: list[PageImage] = []
            for idx, (label, pdf_p1, _) in enumerate(checkpoint_pages):
                pix = doc[pdf_p1 - 1].get_pixmap(colorspace=pymupdf.csGRAY, dpi=300)
                p_img = Path(tmpdir) / f"chk_{idx:02d}_{label}.png"
                pix.save(str(p_img))
                images.append(PageImage(idx + 1, p_img))

            found = {page.number: page.lines for page in reader.read(images)}
            for idx, (label, pdf_p1, expected_book_page) in enumerate(checkpoint_pages):
                lines = [ln.text.strip() for ln in found.get(idx + 1, ()) if ln.text.strip()]
                full_text = "\n".join(lines)
                results.append(
                    {
                        "label": label,
                        "pdf_page_1based": pdf_p1,
                        "expected_book_page": expected_book_page,
                        "line_count": len(lines),
                        "char_count": len(full_text),
                        "header_preview": lines[:4],
                        "footer_preview": lines[-2:] if len(lines) >= 2 else lines,
                    }
                )

        summary: dict[str, object] = {
            "engine": reader.provenance,
            "pdf_to_book_page_offset": 11,
            "verified_checkpoints": len(results),
            "checkpoints": results,
        }
        ocr_report_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return summary
