import json
import random
from pathlib import Path
from typing import ClassVar

import pymupdf
import pytest
from PIL import Image, ImageDraw

from polytypst.ocr.base import OCRLine, OCRPage
from polytypst.pipeline import UniversalPDFPipeline
from polytypst.vision import figure_extractor
from polytypst.vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    FigureExtractor,
    find_whitespace_isolated_diagram,
    load_figures_manifest,
    write_figures_manifest,
)


def reference_scan(
    img: Image.Image, cap_top_px: int, upper_bound_px: int, pad_px: int = 18
) -> tuple[int, int, int, int] | None:
    gray = img.convert("L")
    w, h = gray.size
    pixels = gray.load()
    if pixels is None:
        return None
    x_margin = int(w * 0.06)
    scan_bot = max(upper_bound_px + 10, min(h - 1, cap_top_px - 4))
    scan_top = max(int(h * 0.065), upper_bound_px + 4)
    if scan_bot <= scan_top + 20:
        return None
    row_dark: list[int] = []
    for y in range(scan_top, scan_bot):
        cnt = 0
        for x in range(x_margin, w - x_margin, 2):
            val = pixels[x, y]
            if isinstance(val, (int, float)) and val < 190:
                cnt += 1
        row_dark.append(cnt)
    rel_bot = len(row_dark) - 1
    while rel_bot >= 0 and row_dark[rel_bot] <= 1:
        rel_bot -= 1
    if rel_bot < 10:
        return None
    empty_run = 0
    best_top = 0
    for r in range(rel_bot, -1, -1):
        if row_dark[r] == 0:
            empty_run += 1
            if (rel_bot - r) >= 70 and empty_run >= 34:
                best_top = r + empty_run
                break
        else:
            empty_run = 0
            best_top = r
    y0 = scan_top + best_top
    y1 = scan_top + rel_bot + 1
    min_x, max_x, min_y, max_y = w, 0, y1, y0
    for y in range(y0, y1):
        for x in range(x_margin, w - x_margin):
            val = pixels[x, y]
            if isinstance(val, (int, float)) and val < 190:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
    if max_x <= min_x + 15 or max_y <= min_y + 15:
        return None
    return (
        max(0, min_x - pad_px),
        max(0, min_y - pad_px),
        min(w, max_x + pad_px),
        min(h, max_y + pad_px),
    )


def synthetic_page(seed: int) -> tuple[Image.Image, int, int]:
    rng = random.Random(seed)
    w, h = 600, 800
    img = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(img)
    y = 60
    for _ in range(rng.randint(0, 6)):
        draw.rectangle((50, y, 550, y + 6), fill=rng.randint(0, 180))
        y += rng.randint(12, 22)
    upper = y
    y += rng.randint(10, 60)
    for _ in range(rng.randint(0, 4)):
        x0 = rng.randint(40, 400)
        y0 = y + rng.randint(0, 120)
        draw.ellipse(
            (x0, y0, x0 + rng.randint(20, 160), y0 + rng.randint(20, 160)),
            outline=rng.randint(0, 189),
            width=2,
        )
    cap_top = min(h - 20, y + rng.randint(150, 400))
    for _ in range(rng.randint(0, 40)):
        img.putpixel((rng.randrange(w), rng.randrange(h)), rng.randint(0, 255))
    return img, cap_top, upper


@pytest.mark.parametrize("seed", range(40))
def test_whitespace_scan_matches_reference(seed: int) -> None:
    img, cap_top, upper = synthetic_page(seed)
    assert find_whitespace_isolated_diagram(img, cap_top, upper) == reference_scan(
        img, cap_top, upper
    )


def test_whitespace_scan_isolates_diagram_below_prose_gap() -> None:
    img = Image.new("L", (600, 800), 255)
    draw = ImageDraw.Draw(img)
    for y in range(80, 200, 16):
        draw.rectangle((50, y, 550, y + 6), fill=0)
    draw.ellipse((200, 300, 400, 500), outline=0, width=3)
    box = find_whitespace_isolated_diagram(img, cap_top_px=540, upper_bound_px=60)
    assert box == (200 - 18, 300 - 18, 400 + 18, 500 + 18)


def gap_page(gap_rows: int, ink: int) -> Image.Image:
    img = Image.new("L", (600, 800), 255)
    draw = ImageDraw.Draw(img)
    draw.rectangle((100, 200, 500, 203), fill=ink)
    draw.rectangle((150, 204 + gap_rows, 450, 420), outline=ink, width=2)
    return img


@pytest.mark.parametrize("gap_rows", [33, 34, 35])
@pytest.mark.parametrize("ink", [189, 190])
def test_whitespace_scan_matches_reference_at_boundaries(
    gap_rows: int, ink: int
) -> None:
    img = gap_page(gap_rows, ink)
    assert find_whitespace_isolated_diagram(img, 480, 100) == reference_scan(
        img, 480, 100
    )


def test_whitespace_scan_gap_threshold_splits_at_34_rows() -> None:
    joined = find_whitespace_isolated_diagram(gap_page(33, 0), 480, 100)
    split = find_whitespace_isolated_diagram(gap_page(34, 0), 480, 100)
    assert joined is not None and joined[1] == 200 - 18
    assert split is not None and split[1] == 204 + 34 - 18


def test_whitespace_scan_ignores_gray_190() -> None:
    assert find_whitespace_isolated_diagram(gap_page(40, 190), 480, 100) is None


def test_manifest_round_trip_keeps_box(tmp_path: Path) -> None:
    figs = [
        ExtractedFigure("1_1", "Fig. 1.1", "figures/fig_1_1.png", 14),
        ExtractedFigure(
            "2", "FIG. 2", "figures/fig_2.png", 30, (0.1, 0.2, 0.9, 0.5), 400, 200
        ),
    ]
    path = tmp_path / FIGURES_MANIFEST_NAME
    write_figures_manifest(path, figs)
    assert load_figures_manifest(path) == figs


def test_manifest_loader_rejects_legacy_kodaira_keys(tmp_path: Path) -> None:
    path = tmp_path / FIGURES_MANIFEST_NAME
    _ = path.write_text(
        json.dumps(
            [
                {
                    "fig_id": "1_1",
                    "fig_label": "Fig. 1.1",
                    "pdf_page": 14,
                    "image_rel_path": "figures/fig_1_1.png",
                }
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(KeyError):
        _ = load_figures_manifest(path)


def pdf_with_raster(tmp_path: Path) -> Path:
    raster = Image.new("RGB", (120, 90), (40, 40, 40))
    raster_path = tmp_path / "raster.png"
    raster.save(raster_path)
    pdf_path = tmp_path / "doc.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_image(pymupdf.Rect(100, 100, 220, 190), filename=str(raster_path))
    page.draw_circle(pymupdf.Point(300, 500), 60)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_extract_all_returns_digital_and_scanned_figures(tmp_path: Path) -> None:
    caption = OCRLine("FIG. 1", x=0.45, y=0.3, w=0.08, h=0.02)
    ocr_pages = [OCRPage(page_number=1, width=612, height=792, lines=[caption])]
    out_dir = tmp_path / "book" / "figures"

    figs = FigureExtractor(pdf_with_raster(tmp_path)).extract_all(
        out_dir, ocr_pages=ocr_pages
    )

    assert [f.figure_id for f in figs] == ["p1_1", "1"]
    assert all((out_dir.parent / f.image_rel_path).exists() for f in figs)


class RecordingVision:
    calls: ClassVar[list[int]] = []

    def __init__(self, languages: list[str]) -> None:
        _ = languages

    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        _ = image_path
        RecordingVision.calls.append(page_number)
        return OCRPage(page_number=page_number, width=0, height=0)


@pytest.fixture
def five_page_book(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(figure_extractor, "AppleVisionOCREngine", RecordingVision)
    RecordingVision.calls = []
    pdf_path = tmp_path / "book.pdf"
    doc = pymupdf.open()
    renders = tmp_path / "renders"
    renders.mkdir()
    for pno in range(1, 6):
        page = doc.new_page(width=612, height=792)
        if pno in (2, 4):
            _ = page.insert_text((72, 300), "See Fig. 1.1 for the contour.")
        Image.new("L", (100, 130), 255).save(renders / f"p_{pno:03d}.png")
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_whitespace_extraction_clamps_neighbors_to_pages(five_page_book: Path) -> None:
    out_dir = five_page_book.parent / "out" / "figures"
    _ = FigureExtractor(five_page_book).extract_whitespace_isolated_figures(
        five_page_book.parent / "renders", out_dir, pages=range(2, 5)
    )
    assert RecordingVision.calls == [2, 3, 4]


def test_pipeline_figure_cache_requires_every_listed_file(
    five_page_book: Path,
) -> None:
    pipeline = UniversalPDFPipeline(five_page_book, five_page_book.parent / "out")
    pipeline.renders_dir = five_page_book.parent / "renders"
    manifest = pipeline.output_dir / FIGURES_MANIFEST_NAME
    pipeline.figures_dir.mkdir(parents=True)
    _ = (pipeline.figures_dir / "fig_1_1.png").write_bytes(b"png")
    complete = [ExtractedFigure("1_1", "Fig. 1.1", "figures/fig_1_1.png", 2)]
    partial = [*complete, ExtractedFigure("1_2", "Fig. 1.2", "figures/fig_1_2.png", 4)]

    write_figures_manifest(manifest, partial)
    assert pipeline.extract_figures(rendered_pages=[]) == []
    assert RecordingVision.calls != []
    assert load_figures_manifest(manifest) == []

    write_figures_manifest(manifest, complete)
    RecordingVision.calls = []
    assert pipeline.extract_figures(rendered_pages=[]) == complete
    assert RecordingVision.calls == []
