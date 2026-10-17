"""Comprehensive tests for Universal KISS PDF-to-Markdown Pipeline and Dual-G4 architecture."""

from pathlib import Path

from PIL import Image

from polytypst.cleaner.tex_markdown import TeXMarkdownCleaner
from polytypst.ocr.base import OCRLine
from polytypst.ocr.dual_colab import DualColabG4Cluster
from polytypst.vision.figure_extractor import ExtractedFigure, FigureExtractor


def test_tex_markdown_cleaner_delimiters():
    cleaner = TeXMarkdownCleaner(running_headers=["CALCULUS BOOK"])
    raw = (
        "CALCULUS BOOK\n"
        "123\n"
        "Let us consider a function \\( f(x) \\) such that\n"
        "\\[ f(x) = \\int_0^x t^2 dt \\]\n"
        "with x # 0, where differ-\n"
        "ential elements apply."
    )
    cleaned = cleaner.clean_page(raw, page_num=1)

    assert "CALCULUS BOOK" not in cleaned
    assert "\n123\n" not in cleaned
    assert "$ f(x) $" in cleaned
    assert "$$ f(x) = \\int_0^x t^2 dt $$" in cleaned
    assert "x \\neq 0" in cleaned
    assert "differential" in cleaned


def test_tex_markdown_cleaner_figure_injection():
    cleaner = TeXMarkdownCleaner()
    raw = (
        "We show the tangent line construction below.\n\n"
        "FIG. 1. The geometric derivative.\n\n"
        "As seen from the construction, the tangent slope matches the limit."
    )
    fig = ExtractedFigure(
        figure_id="1",
        caption="FIG. 1. The geometric derivative.",
        image_rel_path="figures/fig_1.png",
        source_page=1,
    )
    cleaned = cleaner.clean_page(raw, page_num=1, page_figures=[fig])

    assert "![FIG. 1. The geometric derivative.](figures/fig_1.png)" in cleaned
    caption_idx = cleaned.find("FIG. 1. The geometric derivative.")
    img_idx = cleaned.find("![FIG. 1. The geometric derivative.](figures/fig_1.png)")
    assert img_idx > caption_idx


def test_tex_markdown_stitcher():
    cleaner = TeXMarkdownCleaner()
    pages = [
        (1, "First page content with a hyper-\n"),
        (2, "bolic equation $$ \\cosh^2 x - \\sinh^2 x = 1 $$ continuing here."),
    ]
    stitched = cleaner.stitch_document(pages)
    assert "hyperbolic equation" in stitched
    assert "$$ \\cosh^2 x - \\sinh^2 x = 1 $$" in stitched


def test_figure_extractor_box_detection():
    lines = [
        OCRLine("Some leading title above", x=0.10, y=0.80, w=0.80, h=0.02),
        OCRLine("Text column line 1", x=0.35, y=0.55, w=0.50, h=0.02),
        OCRLine("Text column line 2", x=0.35, y=0.52, w=0.50, h=0.02),
        OCRLine("FIG. 1", x=0.15, y=0.45, w=0.08, h=0.02),
        OCRLine("Text column line 3", x=0.35, y=0.48, w=0.50, h=0.02),
        OCRLine("Text column line 4", x=0.35, y=0.42, w=0.50, h=0.02),
        OCRLine("Full width closing paragraph below", x=0.10, y=0.30, w=0.80, h=0.02),
    ]
    cap = lines[3]
    box = FigureExtractor.detect_figure_box(lines, cap)
    left, top, right, bottom = box

    assert left < 0.10
    assert right <= 0.35
    assert top < bottom


def test_dual_colab_partitioning(tmp_path: Path):
    dummy_pages = [tmp_path / f"p_{i:03d}.png" for i in range(1, 11)]
    chunks = DualColabG4Cluster.partition_pages(dummy_pages, 2)

    assert len(chunks) == 2
    assert len(chunks[0]) == 5
    assert len(chunks[1]) == 5
    assert chunks[0] + chunks[1] == dummy_pages

    chunks3 = DualColabG4Cluster.partition_pages(dummy_pages, 3)
    assert len(chunks3) == 3
    assert len(chunks3[0]) == 4
    assert len(chunks3[1]) == 3
    assert len(chunks3[2]) == 3


def test_dual_colab_archive_packing(tmp_path: Path):
    img_dir = tmp_path / "imgs"
    img_dir.mkdir()
    p1 = img_dir / "p_001.png"
    p2 = img_dir / "p_002.png"
    Image.new("RGB", (50, 50), color="white").save(p1)
    Image.new("RGB", (50, 50), color="white").save(p2)

    archive = tmp_path / "batch.tar.gz"
    packed = DualColabG4Cluster.pack_archive([p1, p2], archive)
    assert packed.exists()
    assert packed.stat().st_size > 0
