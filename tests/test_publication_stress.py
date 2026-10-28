import re
import zipfile
from pathlib import Path

import pymupdf
import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
SERRE_DIR = ROOT_DIR / "output" / "serre_arithmetique"
ROBERTS_DIR = ROOT_DIR / "output" / "modern_firm"


def test_serre_all_target_artifacts_exist_and_nonempty() -> None:
    expected = [
        "combined_serre.md",
        "serre_cours_darithmetique.typ",
        "serre_cours_darithmetique.pdf",
        "serre_cours_darithmetique.tex",
        "serre_cours_darithmetique.epub",
    ]
    for name in expected:
        p = SERRE_DIR / name
        assert p.exists(), f"Missing Serre artifact: {p}"
        assert p.stat().st_size > 50_000, f"Artifact {p} is unexpectedly small ({p.stat().st_size} bytes)"


def test_serre_typst_zero_escaped_latex_or_raw_macros() -> None:
    typ_text = (SERRE_DIR / "serre_cours_darithmetique.typ").read_text(encoding="utf-8")

    escaped_dollars = re.findall(r".{0,30}\\\$.{0,40}", typ_text)
    assert not escaped_dollars, f"Found unparsed LaTeX math leaked as \\$ in Typst: {escaped_dollars[:5]}"

    forbidden_macros = [
        r"\\varprojlim",
        r"\\varinjlim",
        r"\\cotg",
        r"\\mathbf",
        r"\\sum",
        r"\\frac",
        r"\\prod",
        r"\\begin\{array\}",
        r"\\begin\{pmatrix\}",
    ]
    for pat in forbidden_macros:
        matches = re.findall(pat, typ_text)
        assert not matches, f"Found raw LaTeX macro {pat} leaked into Typst: {matches[:5]}"


def test_serre_pdf_zero_raw_latex_or_ocr_corruption() -> None:
    doc = pymupdf.open(SERRE_DIR / "serre_cours_darithmetique.pdf")
    assert len(doc) >= 108, f"Serre PDF too short: {len(doc)} pages"

    full_pdf_text = "\n".join(page.get_text() for page in doc)

    forbidden_pdf_strings = [
        r"\mathbf",
        r"\varprojlim",
        r"\cotg",
        r"\sum_",
        r"\frac{",
        r"\Lambda_n",
        "$\\mathbf",
        "$$",
    ]
    for bad in forbidden_pdf_strings:
        assert bad not in full_pdf_text, f"Raw LaTeX/OCR artifact '{bad}' rendered visibly in Serre PDF"

    ocr_typos = {
        "métromorphe": "méromorphe",
        "nizéro": "ni zéro",
        "JACONI": "JACOBI",
        "PRACIAR": "PRACHAR",
        "A. WELL": "A. WEIL",
        "Geometrie Algebra": "Geometric Algebra",
        "algebraischer Zahlkörper": "algebraischen Zahlkörper",
    }
    for typo, correction in ocr_typos.items():
        assert typo not in full_pdf_text, f"OCR typo '{typo}' (should be '{correction}') found in Serre PDF"
        assert correction in full_pdf_text, f"Expected canonical text '{correction}' missing from Serre PDF"


def test_serre_canonical_mathematics_integrity() -> None:
    md_text = (SERRE_DIR / "combined_serre.md").read_text(encoding="utf-8")
    typ_text = (SERRE_DIR / "serre_cours_darithmetique.typ").read_text(encoding="utf-8")

    assert r"\left(\frac{\ell}{p}\right) = \left(\frac{p}{\ell}\right)" in md_text
    assert "$-1$ est un carré" in md_text

    assert "(1 - q)^n$24" not in md_text, "Corrupted Jacobi product exponent `(1 - q)^n$24` in Serre markdown"
    assert "(1 - q^n)^{24}" in md_text, "Canonical Jacobi product `(1 - q^n)^{24}` missing in Serre markdown"

    assert "g_3^2 - 27g_3^2" not in md_text, "Corrupted discriminant `g_3^2 - 27g_3^2` in Index des Notations"
    assert "g_2^3 - 27g_3^2" in md_text, "Canonical discriminant `g_2^3 - 27g_3^2` missing"
    assert r"e^{2\pi i\varepsilon}" not in md_text, "Corrupted q-expansion `e^{2\\pi i\\varepsilon}` in Index"
    assert r"\Gamma_{S}" not in md_text and r"\Gamma_{S^n}" not in md_text, "Corrupted lattice notation \\Gamma_S"
    assert r"\Gamma_8" in md_text and r"\Gamma_{16}" in md_text, "Canonical lattices \\Gamma_8, \\Gamma_{16} missing"
    assert r"\binom{x}{p}" not in md_text, "Legendre symbol mis-transcribed as \\binom{x}{p} in Index"

    assert "Dirichlet (série de —) : IV.2.2" not in md_text, "Wrong reference IV.2.2 for Série de Dirichlet"
    assert "Dirichlet (série de —) : VI.2.2" in md_text, "Expected VI.2.2 for Série de Dirichlet"

    assert r"\int_{E}^{A}" in md_text or r"\int_E^A" in md_text, "Missing upper limit A in contour integral \\int_E^A"

    assert "lim" in typ_text and "Lambda_n" not in typ_text


def test_serre_canonical_heading_hierarchy_and_toc() -> None:
    doc = pymupdf.open(SERRE_DIR / "serre_cours_darithmetique.pdf")
    toc = doc.get_toc()

    level_1_titles = [t.strip() for lvl, t, _ in toc if lvl == 1]
    level_2_titles = [t.strip() for lvl, t, _ in toc if lvl == 2]
    all_titles = [t.strip() for _, t, _ in toc]

    assert "CHAPITRE I" not in level_1_titles, f"Split chapter heading in TOC: {level_1_titles}"
    assert "CORPS FINIS" not in level_1_titles, f"Orphan chapter title in TOC: {level_1_titles}"
    assert "SYMBOLE DE HILBERT" not in level_1_titles, f"Leaked running header in Level 1 TOC: {level_1_titles}"

    expected_l1_substrings = [
        "INTRODUCTION",
        "PREMIÈRE PARTIE",
        "CHAPITRE I — CORPS FINIS",
        "CHAPITRE II — CORPS",
        "CHAPITRE III — SYMBOLE DE HILBERT",
        "CHAPITRE IV — FORMES QUADRATIQUES SUR",
        "CHAPITRE V — FORMES QUADRATIQUES ENTIÈRES",
        "DEUXIÈME PARTIE",
        "CHAPITRE VI — LE THÉORÈME DE LA PROGRESSION ARITHMÉTIQUE",
        "CHAPITRE VII — FORMES MODULAIRES",
        "BIBLIOGRAPHIE",
        "INDEX DES NOTATIONS",
        "INDEX TERMINOLOGIQUE",
    ]
    for exp in expected_l1_substrings:
        matches = [t for t in level_1_titles if exp in t.upper()]
        assert len(matches) == 1, f"Expected exactly 1 Level-1 TOC entry matching '{exp}', got {matches} in {level_1_titles}"

    para_sections = [t for t in level_2_titles if t.startswith("§")]
    assert len(para_sections) == 24, f"Expected all 24 canonical § sections at Level 2, got {len(para_sections)}: {para_sections}"

    for bad_toc in ["Démonstration des théorèmes 1 et 2", "iii)", "i) Le cas", "1.3.1."]:
        leaked = [t for t in all_titles if bad_toc in t]
        assert not leaked, f"Non-heading line '{bad_toc}' leaked into TOC: {leaked}"


def test_serre_zero_leaked_running_headers_or_signatures() -> None:
    md_text = (SERRE_DIR / "combined_serre.md").read_text(encoding="utf-8")
    for line in md_text.splitlines():
        s = line.strip()
        assert not re.match(r"^J\.-P\.\s*SERRE\s*\d*$", s, re.IGNORECASE), f"Leaked printer signature in Serre: {s}"
        assert not re.match(r"^\d+\s+COURS D'ARITHMÉTIQUE$", s, re.IGNORECASE), f"Leaked running header in Serre: {s}"
        assert not re.match(r"^(?:CORPS\s+.*|SYMBOLE DE HILBERT|FORMES\s+.*)\s+\d+$", s, re.IGNORECASE), (
            f"Leaked running header with page number in Serre: {s}"
        )


def test_serre_cross_page_stitching_continuity() -> None:
    md_text = (SERRE_DIR / "combined_serre.md").read_text(encoding="utf-8")

    for whole_word in ["convergerait", "naturelle", "réseaux", "bilinéaire"]:
        assert whole_word in md_text, f"Cross-page hyphenated word '{whole_word}' was not stitched"
    for broken in ["conver-\n", "natu-\n", "ré-\n", "bili-\n"]:
        assert broken not in md_text, f"Broken cross-page hyphen '{broken.strip()}' still present"

    stitched_phrases = [
        "tout corps à $p^f$ éléments",
        "montre que $\\mathbf{U} = \\mathbf{V}",
        "appelé le radical (ou le noyau) de $V$",
        "autrement dit si $f$ a un signe constant",
        "Comme cette méthode nous entraînerait trop loin",
    ]
    normalized = re.sub(r"[ \t]+", " ", md_text)
    for phrase in stitched_phrases:
        assert phrase in normalized, f"Cross-page sentence continuation broken for: '{phrase}'"


def test_serre_semantic_theorem_and_proof_environments() -> None:
    typ_text = (SERRE_DIR / "serre_cours_darithmetique.typ").read_text(encoding="utf-8")
    assert typ_text.count("#theorem(") + typ_text.count("#theorem[") >= 25, "Expected structured #theorem blocks in Serre Typst"
    assert typ_text.count("#proposition(") + typ_text.count("#proposition[") >= 35, "Expected structured #proposition blocks in Serre Typst"
    assert typ_text.count("#lemma(") + typ_text.count("#lemma[") >= 20, "Expected structured #lemma blocks in Serre Typst"
    assert typ_text.count("#corollary(") + typ_text.count("#corollary[") >= 15, "Expected structured #corollary blocks in Serre Typst"
    assert typ_text.count("#definition(") + typ_text.count("#definition[") >= 10, "Expected structured #definition blocks in Serre Typst"
    for callout_color in ("#2563eb", "#4f46e5", "#f8fafc"):
        assert callout_color not in typ_text, f"Non-monograph callout color {callout_color} in Serre Typst"
    assert '<séries-de-dirichlet-à-coefficients-positifs.>\n\n#proposition[\n#strong[PROPOSITION 7.]' in typ_text
    assert "upright(A r g)" not in typ_text and 'upright("Arg")' in typ_text
    assert "bb(R) \\( z - z_0 \\)" not in typ_text and "R \\( z - z_0 \\)" in typ_text
    assert "lr(|z - 1|)" in typ_text


def test_serre_vector_figures_embedded() -> None:
    fig1 = SERRE_DIR / "figures" / "serre_fig_1_domaine_fondamental.svg"
    fig2 = SERRE_DIR / "figures" / "serre_fig_2_contour.svg"
    assert fig1.exists() and fig1.stat().st_size > 2_000, "Missing Serre Figure 1 SVG (Domaine fondamental)"
    assert fig2.exists() and fig2.stat().st_size > 2_000, "Missing Serre Figure 2 SVG (Contour C)"

    typ_text = (SERRE_DIR / "serre_cours_darithmetique.typ").read_text(encoding="utf-8")
    assert "serre_fig_1_domaine_fondamental.svg" in typ_text
    assert "serre_fig_2_contour.svg" in typ_text


def test_serre_running_headers_and_epub_latex_validity() -> None:
    epub_path = SERRE_DIR / "serre_cours_darithmetique.epub"
    with zipfile.ZipFile(epub_path, "r") as z:
        names = z.namelist()
        assert "META-INF/container.xml" in names
        xhtml_files = [n for n in names if n.endswith((".xhtml", ".html"))]
        assert len(xhtml_files) >= 5
        for xf in xhtml_files:
            content = z.read(xf).decode("utf-8", errors="ignore")
            assert r"\varprojlim" not in content and r"\cotg" not in content

    tex_text = (SERRE_DIR / "serre_cours_darithmetique.tex").read_text(encoding="utf-8")
    assert r"\documentclass" in tex_text
    assert r"\begin{document}" in tex_text and r"\end{document}" in tex_text


def test_roberts_all_target_artifacts_exist_and_nonempty() -> None:
    expected = ["book.md", "book.typ", "book.pdf", "book.tex", "book.epub"]
    for name in expected:
        p = ROBERTS_DIR / name
        assert p.exists(), f"Missing Roberts artifact: {p}"
        assert p.stat().st_size > 100_000, f"Artifact {p} is unexpectedly small ({p.stat().st_size} bytes)"


def test_roberts_canonical_toc_and_heading_hierarchy() -> None:
    doc = pymupdf.open(ROBERTS_DIR / "book.pdf")
    toc = doc.get_toc()

    l1_titles = [t.strip() for lvl, t, _ in toc if lvl == 1]
    l2_titles = [t.strip() for lvl, t, _ in toc if lvl == 2]

    expected_l1 = [
        "出版说明",
        "前言",
        "第1章 战略与组织",
        "第2章 组织设计的关键概念",
        "第3章 公司的本质与宗旨",
        "第4章 现代企业中的激励问题",
        "第5章 为绩效进行组织",
        "第6章 为增长和创新进行组织",
        "第7章 创建现代企业：对管理和领导的挑战",
        "参考文献",
    ]
    assert l1_titles == expected_l1, f"Roberts Level-1 TOC mismatch:\n  Got: {l1_titles}\n  Expected: {expected_l1}"

    expected_sections = [
        "战略、组织和环境",
        "设计问题：设定战略和组织",
        "战略变革与组织变革",
        "动荡环境中的战略和组织",
        "互补性",
        "非凸性与非凹性",
        "紧密耦合和松散耦合",
        "市场失灵的原因和本质",
        "公司与市场",
        "公司的本质",
        "合作和主动",
        "激励问题的原因和本质",
        "简单代理理论",
        "绩效测量选择",
        "代理关系中的多重任务",
        "团体绩效报酬",
        "操控绩效测量",
        "主观评估",
        "名声",
        "PARC 和激励",
        "垂直范围",
        "水平范围",
        "内部组织和绩效",
        "整体系统",
        "收购性增长",
        "在已有公司中的创新：探索和开发",
        "多任务情况下的工作设计",
    ]
    for sec in expected_sections:
        assert any(sec in t for t in l2_titles), f"Missing canonical section '{sec}' at Level 2 in Roberts TOC"


def test_roberts_zero_leaked_running_headers_or_page_numbers() -> None:
    md_text = (ROBERTS_DIR / "book.md").read_text(encoding="utf-8")
    body_lines = [l.strip() for l in md_text.splitlines() if l.strip() and not l.startswith(("#", "%", "*"))]
    for line in body_lines:
        assert line != "现代企业：基于绩效与增长的组织设计", "Leaked even-page running header in Roberts body"
        assert not re.match(r"^第\s*[1-7]\s*章\s+\S+$", line), f"Leaked odd-page running header in Roberts body: {line}"


def test_roberts_cross_page_paragraph_stitching() -> None:
    md_text = (ROBERTS_DIR / "book.md").read_text(encoding="utf-8")
    cross_page_sentences = [
        "本书将以非专业的风格讲述和呈现基本概念与理论",
        "福特的工厂只为生产 T 型车服务",
        "但这加剧了控制和在群体间有效分配",
        "管理层可开始测量经营绩效",
    ]
    for sent in cross_page_sentences:
        pattern = r"\s*".join(re.escape(part) for part in sent.split())
        assert re.search(pattern, md_text), f"Cross-page sentence broken across paragraph boundary: '{sent}'"


def test_roberts_all_9_vector_figures_grounded_and_clean() -> None:
    typ_text = (ROBERTS_DIR / "book.typ").read_text(encoding="utf-8")
    md_text = (ROBERTS_DIR / "book.md").read_text(encoding="utf-8")

    for fig_id in range(1, 10):
        svg_path = ROBERTS_DIR / "figures" / f"fig_{fig_id}.svg"
        assert svg_path.exists() and svg_path.stat().st_size > 2_000, f"Missing vector SVG: {svg_path}"
        assert f"figures/fig_{fig_id}.svg" in typ_text, f"Figure {fig_id} not grounded in book.typ"
        assert f"figures/fig_{fig_id}.svg" in md_text, f"Figure {fig_id} not grounded in book.md"
        assert f"<fig-{fig_id}>" in typ_text, f"Missing label <fig-{fig_id}> in book.typ"


def test_roberts_zero_ocr_typos_and_clean_cjk_typography() -> None:
    doc = pymupdf.open(ROBERTS_DIR / "book.pdf")
    full_pdf_text = "\n".join(page.get_text() for page in doc)
    normalized_pdf_text = re.sub(r"(?<=[\u4e00-\u9fff“”])\s+(?=[\u4e00-\u9fff“”])", "", full_pdf_text)

    forbidden_typos = {
        "日益凸品": "日益凸显",
        "企业钓现状": "企业的现状",
        "介绍“如何做”书": "介绍“如何做”的书",
        "埃瑞克。布林约尔弗松": "埃瑞克·布林约尔弗松",
        "American Economic Reviere": "American Economic Review",
        "Empirical Eixamination": "Empirical Examination",
        "同事 [ ]": "同事",
    }
    for typo, fix in forbidden_typos.items():
        assert typo not in normalized_pdf_text, f"OCR corruption '{typo}' (should be '{fix}') present in Roberts PDF"
        assert fix in normalized_pdf_text, f"Expected clean text '{fix}' missing from Roberts PDF"


def test_roberts_bibliography_completeness_and_formatting() -> None:
    typ_text = (ROBERTS_DIR / "book.typ").read_text(encoding="utf-8")
    md_text = (ROBERTS_DIR / "book.md").read_text(encoding="utf-8")

    assert ", and Schmittlein, D. C. (1984)" not in md_text.replace("——, and Schmittlein", "").replace(
        "———, and Schmittlein", ""
    ).replace("Anderson, E., and Schmittlein", ""), "Merged repeat-author citation Schmittlein (1984)"

    assert "Alchian, A., and Demsetz, H. (1972)" in md_text
    assert "Production, Information Costs, and Economic Organization" in md_text

    for journal in ["Econometrica", "American Economic Review", "Quarterly Journal of Economics", "Marketing Science"]:
        assert f"*{journal}*" in md_text, f"Journal '{journal}' is not italicized in book.md bibliography"

    bib_part = md_text.split("# 参考文献", 1)[1]
    bib_entries = [l for l in bib_part.splitlines() if l.strip().startswith("* ")]
    assert len(bib_entries) >= 145, f"Expected >= 145 bibliography entries (A-Z), got {len(bib_entries)}"
    assert "核对了书中的参考文献" in bib_part, "Missing bibliography acknowledgement in book.md"
    assert "特别鸣谢" in typ_text, "Missing bibliography acknowledgement box in book.typ"


def test_roberts_pdf_running_headers_and_epub_latex_validity() -> None:
    doc = pymupdf.open(ROBERTS_DIR / "book.pdf")
    odd_page_headers = [doc[p].get_text().splitlines()[0] for p in range(10, 40, 2) if doc[p].get_text().splitlines()]
    assert any("章" in h for h in odd_page_headers), f"Odd-page running headers missing chapter title: {odd_page_headers[:5]}"

    epub_path = ROBERTS_DIR / "book.epub"
    with zipfile.ZipFile(epub_path, "r") as z:
        names = z.namelist()
        assert "META-INF/container.xml" in names
        svg_or_img = [n for n in names if n.endswith((".svg", ".png"))]
        assert len(svg_or_img) >= 9, f"Expected >= 9 embedded figures in Roberts EPUB, got {len(svg_or_img)}"

    tex_text = (ROBERTS_DIR / "book.tex").read_text(encoding="utf-8")
    assert r"\documentclass" in tex_text and "ctexbook" in tex_text
    assert r"\begin{document}" in tex_text and r"\end{document}" in tex_text


def test_roberts_mathematical_symbols_and_variables_in_math_mode() -> None:
    md_text = (ROBERTS_DIR / "book.md").read_text(encoding="utf-8")
    typ_text = (ROBERTS_DIR / "book.typ").read_text(encoding="utf-8")
    tex_text = (ROBERTS_DIR / "book.tex").read_text(encoding="utf-8")

    expected_md_math_phrases = [
        "并在标记为 $X$ 的选择水平达到最大值",
        "（在图中所标记的 $X$）",
        "中的 $Y$ 点，任何朝向 $X$ 的变化都能够提高绩效",
        "最佳的战略和组织 $X$ 点",
        "在此例中，$X$ 点的绩效并未改变",
        "新的最佳点位于 $X'$ 处",
        "通过在 $X$ 点细微地改变选择",
        "$Z$ 点内在不相互匹配，从 $Z$ 点的任何小变化确实都会提高绩效。有两个独特的点，即 $X$ 点和 $Y$ 点，从这两点的较小变化无法提高绩效，因此其符合内在相互匹配的局部最佳标准。但是，$Y$ 点显然具有很好的绩效。",
        "都在水平 $2$ 上操作",
        "增加前两项活动的水平到 $3$",
        "其中一个（标记为 $A$）的选择水平较低，另一个，即 $B$，其两个选择维度的水平都更高。它们是峰。$A$ 和 $B$ 都具有内在相互匹配的第一个要素特征",
        "如果组织无法立即从 $X$ 转变到 $Y$",
        "之前不可能实现的 $R$ 点等现在是可行的了",
    ]
    for phrase in expected_md_math_phrases:
        assert phrase in md_text, f"Missing math-mode phrase in book.md: '{phrase}'"

    forbidden_plain_vars = [
        "Z 点",
        "Z点",
        "X 点",
        "X点",
        "Y 点",
        "Y点",
        "R 点",
        "R点",
        "标记为X",
        "标记为 X",
        "标记为A",
        "标记为 A",
        "即B",
        "A和B",
        "从X转变到Y",
        "从 X 转变到 Y",
        "位于 X' 处",
    ]
    for bad in forbidden_plain_vars:
        assert bad not in md_text, f"Un-mathified variable '{bad}' found in book.md"
        assert bad not in typ_text, f"Un-mathified variable '{bad}' found in book.typ"
        assert bad not in tex_text, f"Un-mathified variable '{bad}' found in book.tex"

    assert re.search(r"(\\\(Z\\\)|\$Z\$)\s+点内在不相互匹配", tex_text)


def test_roberts_figure_and_table_semantic_cross_references() -> None:
    md_text = (ROBERTS_DIR / "book.md").read_text(encoding="utf-8")
    typ_text = (ROBERTS_DIR / "book.typ").read_text(encoding="utf-8")
    tex_text = (ROBERTS_DIR / "book.tex").read_text(encoding="utf-8")

    for fig_id in range(1, 10):
        assert f"[图 {fig_id}](#fig:{fig_id})" in md_text, f"Missing markdown link [图 {fig_id}](#fig:{fig_id}) in book.md"
        assert f"{{#fig:{fig_id}}}" in md_text, f"Missing figure anchor {{#fig:{fig_id}}} in book.md"
        assert f"@fig-{fig_id}" in typ_text, f"Missing semantic @fig-{fig_id} cross-reference in book.typ"
        assert f"<fig-{fig_id}>" in typ_text, f"Missing label <fig-{fig_id}> in book.typ"
        assert rf"\label{{fig:{fig_id}}}" in tex_text, f"Missing \\label{{fig:{fig_id}}} in book.tex"
        assert rf"图~\ref{{fig:{fig_id}}}" in tex_text, f"Missing semantic 图~\\ref{{fig:{fig_id}}} in book.tex"
        assert rf"\caption{{图 {fig_id}" not in tex_text, f"Duplicate hardcoded '图 {fig_id}' inside LaTeX \\caption in book.tex"

    for tab_id in (1, 2):
        assert f"[表 {tab_id}](#tab:{tab_id})" in md_text, f"Missing markdown link [表 {tab_id}](#tab:{tab_id}) in book.md"
        assert f"@tab-{tab_id}" in typ_text, f"Missing semantic @tab-{tab_id} cross-reference in book.typ"
        assert f"<tab-{tab_id}>" in typ_text, f"Missing label <tab-{tab_id}> in book.typ"
        assert rf"\label{{tab:{tab_id}}}" in tex_text, f"Missing \\label{{tab:{tab_id}}} in book.tex"
        assert rf"表~\ref{{tab:{tab_id}}}" in tex_text, f"Missing semantic 表~\\ref{{tab:{tab_id}}} in book.tex"

    assert "|| --- | --- ||" not in md_text, "Collapsed single-line markdown table found in book.md"
    assert "|| --- | --- ||" not in typ_text, "Unparsed collapsed markdown table found in book.typ"
    assert r"\textbar\textbar{}" not in tex_text, "Unparsed collapsed markdown table found in book.tex"

    hardcoded_prose_refs = [
        "可以在图 5",
        "可以在图5",
        "参考图5",
        "参考图 5",
        "见图2",
        "见图 2",
        "如图1",
        "如图 1",
        "如图6",
        "如图 6",
        "考虑一下图 7",
        "见表 1",
    ]
    for bad_ref in hardcoded_prose_refs:
        assert bad_ref not in typ_text, f"Hardcoded figure/table string '{bad_ref}' in book.typ (use @fig-N / @tab-N)"
        assert bad_ref not in tex_text, f"Hardcoded figure/table string '{bad_ref}' in book.tex (use \\ref{{fig:N}} / \\ref{{tab:N}})"


def test_roberts_bilingual_cjk_english_symbol_typography() -> None:
    md_text = (ROBERTS_DIR / "book.md").read_text(encoding="utf-8")
    body_text = md_text.split("# 参考文献", 1)[0]

    bad_cjk_punct = re.findall(r".{0,10}(?:[\u4e00-\u9fff][(),!?:;]|[(),!?:;][\u4e00-\u9fff]).{0,10}", body_text)
    assert not bad_cjk_punct, f"Half-width ASCII punctuation adjacent to CJK in book.md: {bad_cjk_punct[:5]}"

    non_heading_lines = [l for l in body_text.splitlines() if not l.startswith("#")]
    non_heading_body = "\n".join(non_heading_lines)
    tight_cjk_latin = re.findall(
        r".{0,10}(?:[\u4e00-\u9fff][A-Za-z0-9$]|[A-Za-z0-9$%][\u4e00-\u9fff]).{0,10}",
        non_heading_body,
    )
    assert not tight_cjk_latin, f"Missing Pangu space between CJK and English/Number/Math in book.md: {tight_cjk_latin[:5]}"

    tight_cite = re.findall(r"[A-Za-zÀ-ÿ]\(\d{4}", body_text)
    assert not tight_cite, f"Missing space before parenthetical year in English citation: {tight_cite[:5]}"

    assert "**注释**" not in body_text, "Un-normalized **注释** bold text instead of ## 注释 heading"
    welded_after_note = re.findall(r"。\s*\[\d+\][^\s\n]", body_text)
    assert not welded_after_note, f"Paragraph welded across endnote marker: {welded_after_note[:5]}"

    for bad_eng, good_eng in [
        ("General Motor)", "General Motors"),
        ("Katherine Doonik", "Katherine Doornik"),
        ("Montgomery and Wernerfeld", "Montgomery and Wernerfelt"),
        ("Montgomery and Wernerfeldt", "Montgomery and Wernerfelt"),
        ("Saioner, G.", "Saloner, G."),
    ]:
        assert bad_eng not in md_text, f"English typo '{bad_eng}' still in book.md"
        assert good_eng in md_text, f"Expected corrected English '{good_eng}' in book.md"


def test_serre_figure_cross_references_and_notation_math_mode() -> None:
    md_text = (SERRE_DIR / "combined_serre.md").read_text(encoding="utf-8")
    typ_text = (SERRE_DIR / "serre_cours_darithmetique.typ").read_text(encoding="utf-8")
    tex_text = (SERRE_DIR / "serre_cours_darithmetique.tex").read_text(encoding="utf-8")

    for fig_id in (1, 2):
        assert f"{{#fig:{fig_id}}}" in md_text, f"Missing {{#fig:{fig_id}}} in Serre markdown"
        assert f"<fig-{fig_id}>" in typ_text, f"Missing <fig-{fig_id}> in Serre Typst"
        assert f"@fig-{fig_id}" in typ_text, f"Missing @fig-{fig_id} cross-reference in Serre Typst"
        assert rf"\label{{fig:{fig_id}}}" in tex_text, f"Missing \\label{{fig:{fig_id}}} in Serre LaTeX"
        assert rf"\ref{{fig:{fig_id}}}" in tex_text, f"Missing \\ref{{fig:{fig_id}}} in Serre LaTeX"

    for bad_notation in ["**F_q**", "**Z_p**", "**U = Z_p^***", "**Q_p**", "**A\\***"]:
        assert bad_notation not in md_text, f"Un-mathified notation '{bad_notation}' in Serre Index des Notations"

    for bad_prose in ["l'arc BB'", "arcs CC' et DD'", "le demi-plan H"]:
        assert bad_prose not in md_text, f"Un-mathified symbol in Serre prose: '{bad_prose}'"


def _pandoc_ast_problems(blocks: list, problems: list[str]) -> None:
    for node in blocks:
        if isinstance(node, list):
            _pandoc_ast_problems(node, problems)
            continue
        if not isinstance(node, dict) or "t" not in node:
            continue
        kind, content = node["t"], node.get("c")
        if kind in ("RawInline", "RawBlock") and content[0] in ("tex", "latex"):
            problems.append(f"raw TeX dropped by pandoc: {content[1][:60]}")
        elif kind == "Str" and ("\\" in content or "^{" in content or "_{" in content):
            problems.append(f"LaTeX left as plain text: {content[:60]}")
        elif kind == "OrderedList":
            (_, style, delim), items = content[0], content[1]
            first_block = items[0][0] if items and items[0] else {}
            inlines = first_block.get("c", []) if first_block.get("t") in ("Para", "Plain") else []
            formula_only = bool(inlines) and inlines[0].get("t") == "Math" and all(
                i.get("t") in ("Math", "Space", "SoftBreak") or (i.get("t") == "Str" and i["c"] in ".,;:")
                for i in inlines
            )
            if style["t"] == "Decimal" and delim["t"] == "TwoParens" and formula_only:
                problems.append(f"equation number parsed as list marker: {inlines[0]['c'][1][:60]}")
        if isinstance(content, list):
            _pandoc_ast_problems(content, problems)


def test_serre_every_formula_reaches_pandoc_as_math() -> None:
    import json
    import subprocess

    ast = json.loads(
        subprocess.run(
            ["pandoc", str(SERRE_DIR / "combined_serre.md"), "-f", "markdown", "-t", "json"],
            capture_output=True, text=True, check=True,
        ).stdout
    )
    problems: list[str] = []
    _pandoc_ast_problems(ast["blocks"], problems)
    assert not problems, f"{len(problems)} formulas not parsed as math: {problems[:8]}"

    typ_text = (SERRE_DIR / "serre_cours_darithmetique.typ").read_text(encoding="utf-8")
    tex_text = (SERRE_DIR / "serre_cours_darithmetique.tex").read_text(encoding="utf-8")
    assert r"z\^{}\{12\}" not in tex_text, "Display math escaped as text in Serre LaTeX"
    assert "numbering: _ => [(44)]" in typ_text, "Equation (44) lost its right-aligned number in Typst"
    assert r"\tag{44}" in tex_text, "Equation (44) lost its \\tag in LaTeX"
    assert r"\begin{align*}" in tex_text, "Consecutive equation groups not rendered with align* in LaTeX"
    assert not re.search(r"\\\[\s*\\begin\{align\*\}", tex_text), "align* must not be nested inside \\[...\\]"
    assert "rmath[$ R_lambda R_mu $]" in typ_text, "Equations (62)-(65) not aligned with rmath grid in Typst"
    assert "[(62)]" in typ_text and "[(65)]" in typ_text, "Equations (62)-(65) missing right-aligned tags in Typst grid"


KERODON_DIR = ROOT_DIR / "output" / "kerodon"


def test_kerodon_all_deliverables_exist_and_nonempty() -> None:
    expected = {
        "chapter1.pdf": 1_000_000,
        "chapter1.typ": 150_000,
        "chapter1.tex": 150_000,
        "chapter1.epub": 1_000_000,
        "chapter1.md": 150_000,
        "book.pdf": 1_000_000,
    }
    for fname, min_bytes in expected.items():
        fpath = KERODON_DIR / fname
        assert fpath.exists(), f"Missing Kerodon deliverable: {fpath}"
        assert fpath.stat().st_size >= min_bytes, (
            f"Kerodon deliverable {fname} too small ({fpath.stat().st_size} < {min_bytes})"
        )


def test_kerodon_pdf_zero_raw_latex_leaks_and_complete_sections() -> None:
    doc = pymupdf.open(KERODON_DIR / "chapter1.pdf")
    assert 60 <= len(doc) <= 95, f"Unexpected Kerodon PDF page count: {len(doc)}"
    full_text = "\n".join(page.get_text() for page in doc)
    leaks = re.findall(r"\\[a-zA-Z]{2,}", full_text)
    assert not leaks, f"Leaked raw LaTeX macros in Kerodon PDF: {leaks[:10]}"

    typ_text = (KERODON_DIR / "chapter1.typ").read_text(encoding="utf-8")
    escaped_dollars = re.findall(r"\\\$", typ_text)
    assert not escaped_dollars, f"Escaped dollar math failure in Kerodon chapter1.typ: {len(escaped_dollars)}"

    for sec_num in ("1.1", "1.2", "1.3", "1.4", "1.5"):
        assert f"Section {sec_num}:" in full_text, f"Missing Section {sec_num} in Kerodon PDF"


@pytest.mark.slow
def test_web_exporter_domain_specific_rendering_modes(tmp_path: Path) -> None:
    from polytypst.web_exporter import export_all_web_data

    catalog = export_all_web_data(ROOT_DIR, tmp_path)
    books = {b["slug"]: b for b in catalog["books"]}
    assert set(books.keys()) == {"modern-firm", "serre-arithmetique", "kerodon-ch1"}

    roberts = books["modern-firm"]
    assert roberts["renderingMode"] == "editorial-business"
    roberts_paras = [
        blk["html"]
        for ch in roberts["chapters"]
        for blk in ch["blocks"]
        if blk["type"] == "paragraph"
    ]
    assert len(roberts_paras) > 200
    combined_roberts_html = "\n".join(roberts_paras)
    assert "$" not in combined_roberts_html, "Business web edition of Modern Firm must not use LaTeX $ math"
    assert '<var class="editorial-var">Z</var> 点内在不相互匹配' in combined_roberts_html
    assert '<var class="editorial-var">X</var> 点和 <var class="editorial-var">Y</var> 点' in combined_roberts_html
    assert '<a href="#fig-5" class="editorial-ref">图 5</a>' in combined_roberts_html

    serre = books["serre-arithmetique"]
    assert serre["renderingMode"] == "math-katex"
    serre_content = "\n".join(
        blk.get("content", "")
        for ch in serre["chapters"]
        for blk in ch["blocks"]
    )
    assert "$" in serre_content, "Serre web edition must preserve LaTeX math for KaTeX rendering"

    kerodon = books["kerodon-ch1"]
    assert kerodon["renderingMode"] == "math-katex"
    kerodon_theorems = [
        blk for ch in kerodon["chapters"] for blk in ch["blocks"] if blk["type"] == "theorem"
    ]
    assert len(kerodon_theorems) >= 200
    assert any(ch.get("tag") == "0004" for ch in kerodon["chapters"])
    assert any(blk["tag"] == "000R" for blk in kerodon_theorems)


def test_project_mise_and_uv_environment_configuration() -> None:
    import tomllib

    poly_dir = ROOT_DIR / "polytypst"
    mise_toml = poly_dir / "mise.toml"
    env_schema = poly_dir / ".env.schema"
    web_env_schema = poly_dir / "web" / ".env.schema"
    bunfig = poly_dir / "web" / "bunfig.toml"
    pyproject = poly_dir / "pyproject.toml"

    assert mise_toml.exists(), "Missing polytypst/mise.toml"
    assert env_schema.exists(), "Missing polytypst/.env.schema"
    assert web_env_schema.exists(), "Missing polytypst/web/.env.schema"
    assert bunfig.exists(), "Missing polytypst/web/bunfig.toml"
    assert pyproject.exists(), "Missing polytypst/pyproject.toml"

    mise_cfg = tomllib.loads(mise_toml.read_text(encoding="utf-8"))
    assert "_.file" not in mise_cfg.get("env", {})
    assert (poly_dir / ".python-version").read_text(encoding="utf-8").strip() == "3.12"
    assert "uv" in mise_cfg.get("tools", {})
    assert "test" in mise_cfg.get("tasks", {})
    assert "check-web" in mise_cfg.get("tasks", {})
    assert "build-web" in mise_cfg.get("tasks", {})

    bunfig_cfg = tomllib.loads(bunfig.read_text(encoding="utf-8"))
    assert bunfig_cfg.get("env", {}).get("env") is False

    schema_text = web_env_schema.read_text(encoding="utf-8")
    assert "JINA_API_KEY=" in schema_text
    assert "@sensitive" in schema_text
    assert "VITE_CONVEX_URL=" in schema_text




