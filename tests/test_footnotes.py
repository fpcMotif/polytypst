from pathlib import Path

import pymupdf

from polytypst.ahlfors.spec import AHLFORS_SPEC
from polytypst.book_state import book_state
from polytypst.bourbaki_lie.spec import BOURBAKI_LIE_SPEC
from polytypst.compiler.monograph import (
    MonographCompiler,
    RenderedMonograph,
    adhoc_spec,
    compile_typst,
    latex_footnote_header,
    markdown_footnotes,
    running_footnotes,
    typst_footnote_rules,
)
from polytypst.compiler.page_cleaner import split_page_footnotes
from polytypst.hecke.spec import HECKE_SPEC
from polytypst.kashiwara.spec import KASHIWARA_SPEC
from polytypst.klein.spec import KLEIN_SPEC
from polytypst.kodaira.spec import KODAIRA_SPEC
from polytypst.siegel_symplectic.spec import SIEGEL_SYMPLECTIC_SPEC
from polytypst.複素多様体論.spec import FUKUSO_SPEC


def note(text: str) -> str:
    return f"@@FNSTART@@{text}@@FNEND@@"


def test_superscript_notes_attach_to_their_calls():
    page = (
        "Numbers which are not algebraic are called *transcendental*. *Liouville*¹ (1851) first proved it."
        " Later *George Cantor*² showed more.\n\n"
        "¹ Liouville, Sur des classes très étendues. *Journal de Mathématiques*.\n\n"
        "² Cantor, Über eine Eigenschaft.\n"
    )
    text, _, _ = MonographCompiler(HECKE_SPEC).cleaner.clean(page, 77)
    assert "*Liouville*" + note("Liouville, Sur des classes très étendues. *Journal de Mathématiques*.") in text
    assert "*George Cantor*" + note("Cantor, Über eine Eigenschaft.") in text
    assert "¹" not in text and "²" not in text


def test_paren_notes_attach_and_a_list_in_the_body_stays():
    page = (
        "つぎにその概要を述べる$^{1)}$。\n\n1) 第一の場合.\n2) 第二の場合.\n\nしたがって $d$ コホモロジー群$^2)$ とよぶ.\n\n"
        "—\n\n1) たとえば A. Hurwitz-R. Courant: Funktionentheorie, 参照。\n\n2) 複素解析, 363 ページ参照.\n"
    )
    text, _, _ = MonographCompiler(FUKUSO_SPEC).cleaner.clean(page, 58)
    assert "述べる" + note("たとえば A. Hurwitz-R. Courant: Funktionentheorie, 参照。") + "。" in text
    assert "コホモロジー群" + note("複素解析, 363 ページ参照.") + " とよぶ" in text
    assert "1) 第一の場合." in text and "2) 第二の場合." in text
    assert "—" not in text


def test_lines_below_the_note_rule_continue_the_note():
    page = (
        "族の理論$^{1)}$ が生れた.\n\n---\n\n1) W. Fisher und H. Grauert: Lokal-triviale Familien.\n\n"
        "この論文が発表されたのは 1965 年である.\n\n225\n"
    )
    text, _, _ = MonographCompiler(FUKUSO_SPEC).cleaner.clean(page, 225)
    assert "族の理論" + note("W. Fisher und H. Grauert: Lokal-triviale Familien. この論文が発表されたのは 1965 年である.") in text
    assert "---" not in text


def test_paren_note_calls_in_other_ocr_spellings():
    page = "位相$^{(1)}$ を考える. 環¹)をなす.\n\n1) 本講座 “複素解析”, 279 ページ参照.\n\n2) 環論の初歩.\n"
    text, _, _ = MonographCompiler(FUKUSO_SPEC).cleaner.clean(page, 8)
    assert "位相" + note("本講座 “複素解析”, 279 ページ参照.") + " を考える" in text
    assert "環" + note("環論の初歩.") + "をなす" not in text
    page = "位相$^{(1)}$ を考える. 環²)をなす.\n\n1) 本講座 “複素解析”, 279 ページ参照.\n\n2) 環論の初歩.\n"
    text, _, _ = MonographCompiler(FUKUSO_SPEC).cleaner.clean(page, 8)
    assert "環" + note("環論の初歩.") + "をなす" in text


def test_star_notes_attach_after_punctuation_and_skip_italics():
    page = (
        "The functions from Riemann's *Nachlass* and *et al.* are known. Two curves, that have no points in common.* Therefore"
        " the cut is **Lemma 2.** proved.** Done.\n\n"
        "* This assumes the validity of the Jordan Curve Theorem.\n\n"
        "** See the figure in Fricke.\n"
    )
    text, _, _ = MonographCompiler(KODAIRA_SPEC).cleaner.clean(page, 79)
    assert "*Nachlass*" in text and "*et al.*" in text and "**Lemma 2.**" in text
    assert "in common." + note("This assumes the validity of the Jordan Curve Theorem.") + " Therefore" in text
    assert "proved." + note("See the figure in Fricke.") + " Done." in text


def test_spaced_star_call_attaches_but_math_stars_do_not():
    page = "His *Werke*. ** Upon $a * b$ return he wrote.\n\n** This was not the first time.\n"
    text, _, _ = MonographCompiler(KODAIRA_SPEC).cleaner.clean(page, 283)
    assert "*Werke*. " + note("This was not the first time.") + " Upon $a * b$" in text


def test_dagger_at_the_end_of_a_display_moves_after_it():
    page = "We have\n\n$$\nE_n = 0 \\quad \\text{for } n \\geq 0. \\dagger\n$$\n\nso on.\n\n† If $A$ and $B$ are submodules.\n"
    text, _, _ = MonographCompiler(BOURBAKI_LIE_SPEC).cleaner.clean(page, 132)
    assert text.count("$$") == 2
    assert "\\dagger" not in text
    assert "We have" + note("If $A$ and $B$ are submodules.") in text


def test_dagger_note_attaches_to_its_call():
    page = "Let $\\mathfrak{g}_i$ for $i = n, \\ldots, 1$.† Let $G_i$ be the group.\n\n† Such a sequence exists by Chapter I.\n"
    text, _, _ = MonographCompiler(BOURBAKI_LIE_SPEC).cleaner.clean(page, 370)
    assert "1$." + note("Such a sequence exists by Chapter I.") + " Let" in text


def split(page: str, spec=KLEIN_SPEC):
    return split_page_footnotes(page, spec.footnote_style, spec.folio_pattern)


def test_a_circled_mark_opening_a_line_of_display_math_is_not_a_note():
    page = "Here $a f b$ is fullwidth.\n\n$$\n①a = b ①\n$$"
    assert split_page_footnotes(page, "circled", KLEIN_SPEC.folio_pattern) == (page, [])


def test_a_list_closing_a_page_with_circled_items_that_the_body_never_calls_stays_in_the_body():
    page = (
        "主要结论如下：\n\n"
        "①自20世纪80年代后半期实施根本性税制改革以来，所得税制度的累进程度开始逐步下降。\n\n"
        "②降低所得税的累进程度削弱了所得税的收入再分配功能。\n"
    )
    assert split_page_footnotes(page, "circled", KLEIN_SPEC.folio_pattern) == (page.rstrip("\n"), [])


def test_a_circled_note_that_the_body_calls_is_cut_after_a_circled_list():
    body, notes = split_page_footnotes(
        "三种方法：①泡沫项存在检验；②单位根检验。各种情况下的可持续性均被否定。①\n\n"
        "① 感谢井堀利宏等与会人士提出的宝贵意见。\n",
        "circled",
        KLEIN_SPEC.folio_pattern,
    )
    assert body.strip() == "三种方法：①泡沫项存在检验；②单位根检验。各种情况下的可持续性均被否定。①"
    assert notes == [("①", "感谢井堀利宏等与会人士提出的宝贵意见。")]


def test_star_notes_with_no_space_after_the_mark_are_cut():
    body, notes = split(
        "Body text.\n\n*The conditions described in this paragraph hold only for the 18th century.\n\n"
        "** Leipzig 1894-1904. We shall abbreviate this work as *Enz.* (Translator's note)\n"
    )
    assert body.strip() == "Body text."
    assert notes == [
        ("*", "The conditions described in this paragraph hold only for the 18th century."),
        ("**", "Leipzig 1894-1904. We shall abbreviate this work as *Enz.* (Translator's note)"),
    ]


def test_escaped_star_note_below_the_rule_is_cut():
    body, notes = split("Body text.\n\n---\n\n\\* Later published in a supplementary volume.\n")
    assert body.strip() == "Body text."
    assert notes == [("*", "Later published in a supplementary volume.")]


def test_star_that_opens_an_italic_title_below_the_rule_stays_in_the_note():
    _, notes = split("Body text.\n\n---\n\n*Memorial*, see the note on p. 96.\n\n*Note by the editors.* Cf. *Werke* p. 68.\n")
    assert notes == [("*", "*Memorial*, see the note on p. 96."), ("*", "*Note by the editors.* Cf. *Werke* p. 68.")]


def test_note_in_mid_page_is_cut_with_the_lines_that_continue_it():
    body, notes = split(
        "10. Show that $u$ is an isomorphism.\n\n† When $g$ is not graded, we do not know whether the condition\n\n"
        '"$H^2(g, M) = 0$ for every module"\n\nimplies that $g$ is free.\n',
        BOURBAKI_LIE_SPEC,
    )
    assert body.strip() == "10. Show that $u$ is an isomorphism."
    assert notes == [("†", 'When $g$ is not graded, we do not know whether the condition "$H^2(g, M) = 0$ for every module" implies that $g$ is free.')]


def test_note_above_the_last_body_paragraph_is_cut_and_the_paragraph_stays():
    body, notes = split(
        "the functions extend.\n\n† Lie had already stated without proof a result of this type.\n\n"
        "The result of F. Schur was to lead Hilbert in 1900 to ask.\n",
        BOURBAKI_LIE_SPEC,
    )
    assert " ".join(body.split()) == "the functions extend. The result of F. Schur was to lead Hilbert in 1900 to ask."
    assert notes == [("†", "Lie had already stated without proof a result of this type.")]


def test_section_mark_note_is_cut_and_attaches_to_its_call():
    page = (
        "Lie wrote it in collaboration with F. Engel§; it is the object of [3 f], §5) here.\n\n"
        "‡ Today they are called Lie pseudo-groups.\n\n§ From 1886 to 1898, Lie occupied the chair at Leipzig.\n\n"
        "† The analogous notion for permutation groups.\n"
    )
    _, notes = split(page, BOURBAKI_LIE_SPEC)
    assert [k for k, _ in notes] == ["‡", "§", "†"]
    text, _, _ = MonographCompiler(BOURBAKI_LIE_SPEC).cleaner.clean(page, 435)
    assert "F. Engel" + note("From 1886 to 1898, Lie occupied the chair at Leipzig.") + "; it is" in text
    assert "§5)" in text


def test_note_ending_in_a_colon_takes_the_list_below_it():
    body, notes = split(
        "Gauss's works were edited.\n\n*The Goettingen observatory was completed only in 1816.\n\n"
        "**The contents of the volumes are:\n\n1. *Disquisitiones Arithmeticae*\n2. Higher Arithmetic\n"
    )
    assert body.strip() == "Gauss's works were edited."
    assert notes == [
        ("*", "The Goettingen observatory was completed only in 1816."),
        ("**", "The contents of the volumes are: 1. *Disquisitiones Arithmeticae* 2. Higher Arithmetic"),
    ]


def test_italic_at_the_start_of_a_body_line_is_not_a_note():
    page = "*Der barycentrische Calcul* of 1827 is a true mine.\n\n**Lemma 2.** It holds.\n\nMore text.\n"
    assert split(page) == (page.rstrip("\n"), [])


def test_a_semicolon_after_a_note_stays_in_the_text():
    typst = MonographCompiler(HECKE_SPEC).format_typst("une catégorie" + note("Nous considérons.") + "; pour deux objets")
    assert "#footnote[Nous considérons.]\\; pour" in typst


def test_markdown_output_uses_pandoc_inline_notes():
    assert markdown_footnotes("common." + note("This *assumes* it.") + " So") == "common.^[This *assumes* it.] So"


THREE_PAGES = (
    "= One\nA#footnote[one] B#footnote[two]\n#pagebreak()\nC#footnote[three]\n"
    "= Two\nD#footnote[four]\n#pagebreak()\nE#footnote[five]\n"
)


def page_words(spec, tmp_path):
    typ = tmp_path / "notes.typ"
    typ.write_text("#set page(width: 220pt, height: 220pt)\n" + typst_footnote_rules(spec) + THREE_PAGES, encoding="utf-8")
    compile_typst(typ, tmp_path / "notes.pdf")
    return [[w for w in page.get_text().split() if w[0] in "ABCDE"] for page in pymupdf.open(tmp_path / "notes.pdf")]


def test_paren_marks_restart_on_each_page(tmp_path):
    assert page_words(FUKUSO_SPEC, tmp_path) == [["A1)", "B2)"], ["C1)", "D2)"], ["E1)"]]


def test_star_marks_grow_and_restart_on_each_page(tmp_path):
    assert page_words(KLEIN_SPEC, tmp_path) == [["A*", "B**"], ["C*", "D**"], ["E*"]]


def test_dagger_marks_restart_on_each_page(tmp_path):
    assert page_words(BOURBAKI_LIE_SPEC, tmp_path) == [["A†", "B‡"], ["C†", "D‡"], ["E†"]]


def test_hecke_numbers_restart_at_each_chapter(tmp_path):
    assert page_words(HECKE_SPEC, tmp_path) == [["A1", "B2"], ["C3", "D1"], ["E2"]]


def test_running_option_numbers_through_the_book(tmp_path):
    assert page_words(running_footnotes(FUKUSO_SPEC), tmp_path) == [["A1", "B2"], ["C3", "D4"], ["E5"]]


def test_note_entry_stays_on_the_page_of_its_call(tmp_path):
    paragraph = MonographCompiler(KLEIN_SPEC).format_typst(
        "Noether (born in 1844, at Erlangen since 1875" + note("Died 1922.") + ") will occupy us extensively"
        " when we deal with the modern theory of algebraic varieties. He is one of Clebsch's students."
    )
    apart = []
    for words in range(225, 255, 3):
        typ = tmp_path / "q.typ"
        typ.write_text(
            "#set page(width: 300pt, height: 300pt)\n#set text(10pt)\n#set par(justify: true)\n"
            + typst_footnote_rules(KLEIN_SPEC) + f"#lorem({words})\n\n{paragraph}\n\n#lorem(60)\n",
            encoding="utf-8",
        )
        compile_typst(typ, tmp_path / "q.pdf")
        pages = [p.get_text() for p in pymupdf.open(tmp_path / "q.pdf")]
        call = next(i for i, t in enumerate(pages) if "1875*" in t)
        entry = next(i for i, t in enumerate(pages) if "*Died 1922." in t)
        if call != entry:
            apart.append(words)
    assert apart == []


LOREM_40 = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore"
    " magnam aliquam quaerat voluptatem. Ut enim aeque doleamus animo, cum corpore dolemus, fieri tamen permagna"
    " accessio potest, si aliquod aeternum et infinitum impendere."
)


def test_note_entry_stays_on_the_page_of_a_call_near_the_end_of_its_paragraph(tmp_path):
    paragraph = MonographCompiler(KLEIN_SPEC).format_typst(
        f"{LOREM_40} Noether at Erlangen since 1875" + note("Died 1922.") + " will occupy us."
    )
    apart = []
    for words in (*range(196, 208, 2), *range(322, 332, 2)):
        typ = tmp_path / "w.typ"
        typ.write_text(
            "#set page(width: 300pt, height: 300pt)\n#set text(10pt)\n#set par(justify: true)\n"
            + typst_footnote_rules(KLEIN_SPEC)
            + f"#lorem({words})\n\n{paragraph}\n\n#lorem(60)\n",
            encoding="utf-8",
        )
        compile_typst(typ, tmp_path / "w.pdf")
        pages = [p.get_text() for p in pymupdf.open(tmp_path / "w.pdf")]
        call = next(i for i, t in enumerate(pages) if "1875*" in t)
        entry = next(i for i, t in enumerate(pages) if "*Died 1922." in t)
        if call != entry:
            apart.append(words)
    assert apart == []


def test_a_paragraph_without_notes_never_leaves_one_line_on_the_next_page(tmp_path):
    alone = []
    for words in range(200, 300, 3):
        typ = tmp_path / "o.typ"
        typ.write_text(
            "#set page(width: 300pt, height: 300pt)\n#set text(10pt)\n#set par(justify: true)\n"
            + typst_footnote_rules(HECKE_SPEC) + f"#lorem({words})\n",
            encoding="utf-8",
        )
        compile_typst(typ, tmp_path / "o.pdf")
        pages = pymupdf.open(tmp_path / "o.pdf")
        lines = [ln for b in pages[-1].get_text("dict")["blocks"] for ln in b.get("lines", [])]
        if len(pages) > 1 and len(lines) == 1:
            alone.append(words)
    assert alone == []


def test_chinese_note_mark_never_starts_a_line(tmp_path):
    spec = adhoc_spec(Path("Probe.pdf"), 1, lang="zh")
    leading = []
    for chars in range(10, 40):
        typ = tmp_path / "m.typ"
        typ.write_text(
            '#set page(width: 200pt, height: 200pt)\n#set text(font: ("Songti SC", "New Computer Modern"), lang: "zh")\n'
            "#set par(justify: true)\n"
            + typst_footnote_rules(spec)
            + "经" * chars + "济#footnote[注。]。考察以下两个时期中三个时间点。\n",
            encoding="utf-8",
        )
        compile_typst(typ, tmp_path / "m.pdf")
        page = pymupdf.open(tmp_path / "m.pdf")[0]
        lines = ["".join(s["text"] for s in ln["spans"]) for b in page.get_text("dict")["blocks"] for ln in b.get("lines", [])]
        if any(ln.startswith("1") or ln.startswith("①") for ln in lines if "注" not in ln):
            leading.append(chars)
    assert leading == []


def test_each_book_keeps_the_marks_of_its_scan():
    marks = {
        spec.slug: (spec.footnote_marks, spec.footnote_numbering, spec.footnote_reset)
        for spec in (HECKE_SPEC, KASHIWARA_SPEC, FUKUSO_SPEC, BOURBAKI_LIE_SPEC, AHLFORS_SPEC, KODAIRA_SPEC, KLEIN_SPEC, SIEGEL_SYMPLECTIC_SPEC)
    }
    assert marks == {
        HECKE_SPEC.slug: ((), "1", "chapter"),
        KASHIWARA_SPEC.slug: ((), "1", "book"),
        FUKUSO_SPEC.slug: ((), "1)", "page"),
        BOURBAKI_LIE_SPEC.slug: (("†", "‡", "§"), "1", "page"),
        AHLFORS_SPEC.slug: (("†", "‡"), "1", "page"),
        KODAIRA_SPEC.slug: (("*", "**", "***"), "1", "page"),
        KLEIN_SPEC.slug: (("*", "**", "***"), "1", "page"),
        SIEGEL_SYMPLECTIC_SPEC.slug: (("*", "**", "***"), "1", "page"),
    }


def test_latex_header_follows_footmisc():
    assert latex_footnote_header(BOURBAKI_LIE_SPEC) == (
        r"\usepackage{footmisc}\usepackage{zref-perpage}\zmakeperpage{footnote}"
        r"\DefineFNsymbols{original}{{\textdagger}{\textdaggerdbl}{\textsection}}\setfnsymbol{original}"
        r"\renewcommand\thefootnote{\fnsymbol{footnote}}"
    )
    assert latex_footnote_header(FUKUSO_SPEC) == (
        r"\usepackage{footmisc}\usepackage{zref-perpage}\zmakeperpage{footnote}\renewcommand\thefootnote{\arabic{footnote})}"
    )
    assert latex_footnote_header(HECKE_SPEC) == ""
    assert latex_footnote_header(running_footnotes(HECKE_SPEC)) == r"\counterwithout{footnote}{chapter}"


def rendered_book(tmp_path: Path, *pages: str, lang: str = "zh") -> tuple[MonographCompiler, RenderedMonograph]:
    spec = adhoc_spec(Path("Probe.pdf"), len(pages), lang=lang)
    md_dir = book_state(tmp_path) / spec.markdown_dir
    md_dir.mkdir(parents=True)
    for pno, page in enumerate(pages, start=1):
        _ = (md_dir / f"p_{pno:03d}.md").write_text(page, encoding="utf-8")
    compiler = MonographCompiler(spec)
    return compiler, compiler.render(tmp_path)


def test_hand_numbered_circled_notes_become_auto_numbered_footnotes(tmp_path):
    compiler, rendered = rendered_book(
        tmp_path,
        "潜在 GDP 可以从数据中估算①，结果却大不相同②。\n\n① Romer (2006)，p. 178.\n② 根据日本经济企划厅（1999）制定。",
    )
    assert compiler.spec.footnote_style == "circled"
    assert rendered.markdown.count("^[") == 2
    assert rendered.typst.count("#footnote[") == 2
    assert "估算①" not in rendered.typst and "② 根据" not in rendered.typst
    assert 'numbering: "①"' in rendered.typst
    assert r"\textcircled" in latex_footnote_header(compiler.spec)


def test_chinese_note_marks_are_drawn_in_the_text_and_the_note_area(tmp_path):
    _, rendered = rendered_book(
        tmp_path,
        "潜在 GDP 可以从数据中估算①，结果却大不相同②。\n\n① Romer (2006)，p. 178.\n② 根据日本经济企划厅（1999）制定。",
    )
    typ = tmp_path / "zh.typ"
    _ = typ.write_text(rendered.typst, encoding="utf-8")
    compile_typst(typ, tmp_path / "zh.pdf")
    page = pymupdf.open(tmp_path / "zh.pdf")[-1]
    marks = page.search_for("①") + page.search_for("②")
    assert len(marks) == 4
    for rect in marks:
        pix = page.get_pixmap(clip=rect, dpi=300, colorspace=pymupdf.csGRAY)
        assert min(pix.samples) < 128, f"mark at {rect} has no ink"


def test_circled_numbers_that_are_not_notes_are_drawn_as_circles(tmp_path):
    compiler, rendered = rendered_book(tmp_path, "Two steps: ① sort the list, then Ⓑ merge it.", lang="en")
    assert compiler.spec.footnote_style == ""
    assert "① sort" in rendered.markdown
    typ = tmp_path / "circled.typ"
    _ = typ.write_text(rendered.typst, encoding="utf-8")
    compile_typst(typ, tmp_path / "circled.pdf")
    page = pymupdf.open(tmp_path / "circled.pdf")[-1]
    text = page.get_text()
    assert "sort" in text and "①" not in text and "Ⓑ" not in text
    assert len(page.get_drawings()) >= 2


def test_a_note_on_a_heading_prints_its_mark_on_the_heading_line(tmp_path):
    _, rendered = rendered_book(
        tmp_path,
        "## 4 本文的研究分析①\n\n基于以上现有研究，本节进行实证检验。\n\n① 关于本节实证分析，在此致谢。",
    )
    typ = tmp_path / "heading.typ"
    _ = typ.write_text(rendered.typst, encoding="utf-8")
    compile_typst(typ, tmp_path / "heading.pdf")
    doc = pymupdf.open(tmp_path / "heading.pdf")
    lines = [line.strip() for line in doc[-1].get_text().splitlines() if line.strip()]
    heading = next(i for i, line in enumerate(lines) if "本文的研究分析" in line)
    assert lines[heading].endswith("本文的研究分析①")
    assert lines[heading + 1].startswith("基于以上")
    assert all("致谢" not in title for _, title, _ in doc.get_toc())
