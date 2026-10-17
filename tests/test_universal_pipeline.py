"""Comprehensive tests for Universal KISS PDF-to-Markdown Pipeline and Dual-G4 architecture."""

from pathlib import Path

from PIL import Image

from polytypst.cleaner.tex_markdown import TeXMarkdownCleaner
from polytypst.goursat.figures import (
    GOURSAT_SVG_GENERATORS,
    generate_goursat_cover_svg,
    normalize_goursat_markdown,
)
from polytypst.ocr.base import OCRLine
from polytypst.ocr.dual_colab import DualColabG4Cluster
from polytypst.vision.figure_extractor import ExtractedFigure, FigureExtractor


def test_tex_markdown_cleaner_delimiters():
    cleaner = TeXMarkdownCleaner(
        running_headers=["CALCULUS BOOK", "IMPLICIT FUNCTIONS"]
    )
    raw = (
        "CALCULUS BOOK\n"
        "II, § 20] IMPLICIT FUNCTIONS 87\n"
        "123\n"
        "Let us consider a *continuous* function \\( f(x) \\) and $ P(x, y) $ such that\n"
        "(29) \\[ f(x) = \\int_0^x t^2 dt \\]\n"
        "with x # 0, where differ-\n"
        "ential elements apply."
    )
    cleaned = cleaner.clean_page(raw, page_num=1)

    assert "CALCULUS BOOK" not in cleaned
    assert "IMPLICIT FUNCTIONS 87" not in cleaned
    assert "\n123\n" not in cleaned
    assert "*continuous*" in cleaned
    assert "$f(x)$" in cleaned
    assert "$P(x, y)$" in cleaned
    assert "$ f(x) $" not in cleaned
    assert "$ P(x, y) $" not in cleaned
    assert "\\tag{29}" in cleaned
    assert "f(x) = \\int_0^x t^2 \\mathrm{d} t" in cleaned
    assert "x \\neq 0" in cleaned
    assert "differential" in cleaned
    diff_page = cleaner.clean_page(
        "$\\frac{dy}{dx} + \\frac{d^2 y}{dx^2} + d\\alpha$", page_num=2
    )
    assert (
        diff_page
        == "$\\frac{\\mathrm{d} y}{\\mathrm{d} x} + \\frac{\\mathrm{d}^2 y}{\\mathrm{d} x^2} + \\mathrm{d} \\alpha$"
    )


def test_figure_caption_regex_standalone_only():
    assert FigureExtractor.FIGURE_CAPTION_REGEX.match("FIG. 14") is not None
    assert FigureExtractor.FIGURE_CAPTION_REGEX.match("FIO. 22") is not None
    assert FigureExtractor.FIGURE_CAPTION_REGEX.match("FIG. 37, a") is not None
    assert (
        FigureExtractor.FIGURE_CAPTION_REGEX.match(
            "the curve is of the form ACDB (Fig. 14), for instance"
        )
        is None
    )


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
    assert "\\cosh^2 x - \\sinh^2 x = 1" in stitched


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


def test_goursat_svg_generators_complete():
    assert len(GOURSAT_SVG_GENERATORS) == 54
    for gen in GOURSAT_SVG_GENERATORS.values():
        svg = gen()
        assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
        assert "viewBox=" in svg
        assert "width=" in svg
        assert "height=" in svg
        assert "<title>" in svg
        assert svg.endswith("</svg>")


def test_goursat_cover_and_frontmatter_normalization():
    cover = generate_goursat_cover_svg()
    assert cover.startswith('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 432 648"')
    assert "A COURSE IN MATHEMATICAL ANALYSIS" in cover
    assert "VOLUME I" in cover
    assert cover.endswith("</svg>")

    raw_md = (
        "## EXPANSION IN SERIES\nby Edouard Goursat\n\n"
        "## CHAPTER I\n\n### I. FUNCTIONS OF A SINGLE VARIABLE\n\n"
        "#### 1. Limits. Let $y = f(x)$.\n"
    )
    norm_md = normalize_goursat_markdown(raw_md)
    assert norm_md.startswith("# AUTHOR'S PREFACE")
    assert "# TRANSLATOR'S PREFACE" in norm_md
    assert "# CHAPTER I: DERIVATIVES AND DIFFERENTIALS" in norm_md
    assert "## I. FUNCTIONS OF A SINGLE VARIABLE" in norm_md
    assert "**1. Limits.** Let $y = f(x)$." in norm_md



def test_kodaira_svg_generators_complete():
    from polytypst.kodaira import KODAIRA_FIG_TITLES, KODAIRA_SVG_GENERATORS

    assert len(KODAIRA_SVG_GENERATORS) == 116
    assert len(KODAIRA_FIG_TITLES) == 116
    for fid, gen in KODAIRA_SVG_GENERATORS.items():
        svg = gen()
        assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
        assert 'class="layer-grid"' in svg
        assert 'class="layer-region"' in svg
        assert 'class="layer-curve"' in svg
        assert 'class="layer-label"' in svg
        assert svg.endswith("</svg>"), f"Incomplete SVG for {fid}"


def test_three_axis_composition_presets():
    from polytypst.compiler.monograph import MonographCompiler, resolve_monograph_spec
    from polytypst.compiler.presets import (
        DOMAIN_PROFILES,
        LANGUAGE_PROFILES,
        PUBLISHER_PRESETS,
    )

    for pub_key, pub in PUBLISHER_PRESETS.items():
        for lang_key, lang in LANGUAGE_PROFILES.items():
            for dom_key in DOMAIN_PROFILES:
                spec = resolve_monograph_spec(
                    Path("sample.pdf"),
                    120,
                    publisher_key=pub_key,
                    lang=lang_key,
                    domain=dom_key,
                )
                compiler = MonographCompiler(spec)
                preamble = compiler.build_typst_preamble()
                title_page = compiler.build_typst_title_page()
                assert f"width: {pub.width_pt}pt" in preamble
                assert f'lang: "{lang.typst_lang}"' in preamble
                assert pub.cities_line in title_page
                assert f"#outline(title: [{lang.contents_title}]" in title_page
