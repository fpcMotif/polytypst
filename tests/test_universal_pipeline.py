"""Comprehensive tests for Universal KISS PDF-to-Markdown Pipeline and Dual-G4 architecture."""

from dataclasses import replace
from pathlib import Path

from polytypst.goursat.build import goursat_markdown
from polytypst.goursat.figures import (
    GOURSAT_SVG_GENERATORS,
    generate_goursat_cover_svg,
    normalize_goursat_markdown,
)
from polytypst.ocr.colab_cluster import ColabOCRCluster
from polytypst.ocr.pages import OcrLine, PageImage
from polytypst.vision.figure_extractor import ExtractedFigure, FigureExtractor


def test_tex_markdown_cleaner_delimiters():
    raw = (
        "A COURSE IN MATHEMATICAL ANALYSIS\n"
        "II, § 20] IMPLICIT FUNCTIONS 87\n"
        "123\n"
        "Let us consider a *continuous* function \\( f(x) \\) and $ P(x, y) $ such that\n"
        "(29) \\[ f(x) = \\int_0^x t^2 dt \\]\n"
        "with x # 0, where differ-\n"
        "ential elements apply."
    )
    cleaned = goursat_markdown([(1, raw)], [])

    assert "A COURSE IN MATHEMATICAL ANALYSIS" not in cleaned
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
    diff_page = goursat_markdown([(2, "$\\frac{dy}{dx} + \\frac{d^2 y}{dx^2} + d\\alpha$")], [])
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
    cleaned = goursat_markdown([(1, raw)], [fig])

    assert "![FIG. 1. The geometric derivative.](figures/fig_1.png)" in cleaned
    caption_idx = cleaned.find("FIG. 1. The geometric derivative.")
    img_idx = cleaned.find("![FIG. 1. The geometric derivative.](figures/fig_1.png)")
    assert img_idx > caption_idx


def test_tex_markdown_stitcher():
    pages = [
        (1, "First page content with a hyper-\n"),
        (2, "bolic equation $$ \\cosh^2 x - \\sinh^2 x = 1 $$ continuing here."),
    ]
    stitched = goursat_markdown(pages, [])
    assert "hyperbolic equation" in stitched
    assert "\\cosh^2 x - \\sinh^2 x = 1" in stitched


def test_stitcher_joins_inline_math_split_across_pages():
    pages = [
        (1, "パラメータ $t = (t_1, t_2, \\cdots,"),
        (2, "$t_m$) と共に変わるものが多い．"),
    ]
    stitched = goursat_markdown(pages, [])
    assert "$t = (t_1, t_2, \\cdots, t_m$)" in stitched
    assert stitched.count("$") % 2 == 0


def test_stitcher_closes_gaps_in_equation_numbers():
    stitched = goursat_markdown([(1, "次式を得る (5. 83) である.")], [])
    assert "(5.83)" in stitched


def test_cross_page_join_repairs_math_split_by_page_break():
    from polytypst.compiler.monograph import join_cross_page_text

    joined = join_cross_page_text("パラメータ $t = (t_1,", "$t_2)$ と共に")
    assert "$t = (t_1, t_2)$" in joined
    assert joined.count("$") % 2 == 0


def test_double_backslash_before_macro_is_collapsed():
    from polytypst.compiler.page_cleaner import _DOUBLE_BACKSLASH_MACRO_RE

    assert _DOUBLE_BACKSLASH_MACRO_RE.sub(r"\\", r"\\mathcal{A} \\ x") == r"\mathcal{A} \\ x"


def test_figure_extractor_box_detection():
    lines = [
        OcrLine("Some leading title above", x=0.10, y=0.80, w=0.80, h=0.02),
        OcrLine("Text column line 1", x=0.35, y=0.55, w=0.50, h=0.02),
        OcrLine("Text column line 2", x=0.35, y=0.52, w=0.50, h=0.02),
        OcrLine("FIG. 1", x=0.15, y=0.45, w=0.08, h=0.02),
        OcrLine("Text column line 3", x=0.35, y=0.48, w=0.50, h=0.02),
        OcrLine("Text column line 4", x=0.35, y=0.42, w=0.50, h=0.02),
        OcrLine("Full width closing paragraph below", x=0.10, y=0.30, w=0.80, h=0.02),
    ]
    cap = lines[3]
    box = FigureExtractor.detect_figure_box(lines, cap)
    left, top, right, bottom = box

    assert left < 0.10
    assert right <= 0.35
    assert top < bottom


def test_dual_colab_partitioning(tmp_path: Path):
    dummy_pages = [PageImage(i, tmp_path / f"p_{i:03d}.png") for i in range(1, 11)]
    chunks = ColabOCRCluster.partition_pages(dummy_pages, 2)

    assert len(chunks) == 2
    assert len(chunks[0]) == 5
    assert len(chunks[1]) == 5
    assert chunks[0] + chunks[1] == dummy_pages

    chunks3 = ColabOCRCluster.partition_pages(dummy_pages, 3)
    assert len(chunks3) == 3
    assert len(chunks3[0]) == 4
    assert len(chunks3[1]) == 3
    assert len(chunks3[2]) == 3


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
    assert cover.startswith(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 432 648"'
    )
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

    linked = normalize_goursat_markdown(
        "## CHAPTER I\n\n![FIG. 1](figures/fig_1.png){#fig:1}\n\n![FIG. 99](figures/fig_99.png){#fig:99}\n"
    )
    assert "(figures/fig_1.svg)" in linked
    assert "(figures/fig_99.png)" in linked


def test_kodaira_svg_generators_complete():
    from polytypst.books import module

    kodaira = module("kodaira", None)
    KODAIRA_FIG_TITLES, KODAIRA_SVG_GENERATORS = kodaira.KODAIRA_FIG_TITLES, kodaira.KODAIRA_SVG_GENERATORS

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
    from polytypst.compiler.monograph import MonographCompiler, adhoc_spec
    from polytypst.compiler.presets import (
        DOMAIN_PROFILES,
        LANGUAGE_PROFILES,
        PUBLISHER_PRESETS,
    )

    for pub_key, pub in PUBLISHER_PRESETS.items():
        for lang_key, lang in LANGUAGE_PROFILES.items():
            for dom_key in DOMAIN_PROFILES:
                spec = adhoc_spec(
                    Path("sample.pdf"),
                    120,
                    publisher_key=pub_key,
                    lang=lang_key,
                    domain=dom_key,
                )
                compiler = MonographCompiler(replace(spec, publisher=pub.imprint_name))
                preamble = compiler.build_typst_preamble()
                title_page = compiler.build_typst_title_page()
                assert f"width: {pub.width_pt}pt" in preamble
                assert f'lang: "{lang.typst_lang}"' in preamble
                assert pub.cities_line in title_page
                assert f"#outline(title: [{lang.contents_title}]" in title_page


def test_spec_less_book_names_no_invented_publisher_or_author():
    from polytypst.compiler.monograph import MonographCompiler, adhoc_spec

    spec = adhoc_spec(Path("Lectures on Moduli.pdf"), 7)
    title_page = MonographCompiler(spec).build_typst_title_page()
    assert "LECTURES ON MODULI" in title_page
    for invented in ("Cambridge", "CAMBRIDGE", "Author", "New York"):
        assert invented not in title_page


def test_markdown_pages_merge_when_inline_math_straddles_pages():
    from polytypst.compiler.monograph import join_markdown_pages

    merged = join_markdown_pages(["本文 $t = (t_1,", "$t_2)$ の続き"])
    assert len(merged) == 1
    assert "$t = (t_1, t_2)$" in merged[0]


def test_a_paragraph_that_runs_across_a_page_stays_one_paragraph_ahead_of_the_figures():
    from polytypst.compiler.monograph import join_markdown_pages

    merged = join_markdown_pages([
        "前文。\n\n相对就业（图\n\n![图 7-11 a](figures/fig_7-11.svg)",
        "![图 7-13 b](figures/fig_7-13.svg)\n\n7-12)。因此可以节省。\n\n## 5 结束语",
    ])
    assert merged == [
        (
            "前文。\n\n相对就业（图 7-12)。因此可以节省。\n\n![图 7-11 a](figures/fig_7-11.svg)\n\n"
            "![图 7-13 b](figures/fig_7-13.svg)\n\n## 5 结束语"
        )
    ]
    assert join_markdown_pages(["第一段。", "第二段。"]) == ["第一段。", "第二段。"]


def test_two_chinese_characters_join_across_a_page_without_a_space():
    from polytypst.compiler.monograph import join_cross_page_text

    assert join_cross_page_text("劳动力供给制", "约逐渐加强") == "劳动力供给制约逐渐加强"
    assert join_cross_page_text("相对就业（图", "7-12)") == "相对就业（图 7-12)"


def test_missing_ocr_image_refs_are_dropped_but_real_ones_kept(tmp_path):
    from polytypst.books import book_specs
    from polytypst.compiler.page_cleaner import PageCleaner

    spec = book_specs()["kodaira_complex_analysis"]
    cleaner = PageCleaner.for_spec(spec, tmp_path)
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "fig_1_1.png").write_bytes(b"x")
    text = "A\n\n![Diagram](image)\n\nB\n\n![real](figures/fig_1_1.png)\n"
    out = cleaner._drop_missing_images(text)
    assert "![Diagram](image)" not in out
    assert "![real](figures/fig_1_1.png)" in out


def test_latex_safe_markdown_braces_group_superscripts():
    from polytypst.compiler.monograph import latex_safe_markdown

    out = latex_safe_markdown(r"d\bar{z}_j{}^\alpha \wedge x{}^2")
    assert r"{}^{\alpha}" in out
    assert r"{}^{2}" in out
    assert r"{}^\alpha" not in out
