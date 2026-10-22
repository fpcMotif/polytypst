import pymupdf

from polytypst.ahlfors.spec import AHLFORS_SPEC
from polytypst.bourbaki_lie.spec import BOURBAKI_LIE_SPEC
from polytypst.compiler.monograph import (
    MonographCompiler,
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
        r"\usepackage[perpage]{footmisc}"
        r"\DefineFNsymbols{original}{{\textdagger}{\textdaggerdbl}{\textsection}}\setfnsymbol{original}"
        r"\renewcommand\thefootnote{\fnsymbol{footnote}}"
    )
    assert latex_footnote_header(FUKUSO_SPEC) == r"\usepackage[perpage]{footmisc}\renewcommand\thefootnote{\arabic{footnote})}"
    assert latex_footnote_header(HECKE_SPEC) == ""
    assert latex_footnote_header(running_footnotes(HECKE_SPEC)) == r"\counterwithout{footnote}{chapter}"
