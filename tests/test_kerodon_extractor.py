import subprocess
from pathlib import Path

import pymupdf

from polytypst.books import module

KerodonCompiler = module("kerodon", "compiler").KerodonCompiler
extractor = module("kerodon", "extractor")
KerodonChapter = extractor.KerodonChapter
KerodonEnvironment = extractor.KerodonEnvironment
KerodonExtractor = extractor.KerodonExtractor
KerodonSection = extractor.KerodonSection

CHAPTER = '<title>Chapter 1 (0001): The Language&mdash;Kerodon</title><a class="sidebar-link" href="/tag/0002">1.2 <span>x</span></a>'
SECTION = (
    '<h2>1.2 Topology</h2>'
    '<article class="env-remark" id="00GZ">'
    '<a class="environment-identifier" href="/tag/00GZ">Remark <span data-tag="00GZ">1.2.2.5</span> '
    '<span class="named">(Connected Components of $\\operatorname{Sing}_{\\bullet }(X)$)</span>.</a> Let $X$ be a space.'
    '</article>'
)
TITLE = "Connected Components of $\\operatorname{Sing}_{\\bullet }(X)$"


def test_a_title_with_parentheses_inside_its_math_stays_whole(tmp_path: Path) -> None:
    (tmp_path / "tag_0001.html").write_text(CHAPTER, encoding="utf-8")
    (tmp_path / "tag_0002.html").write_text(SECTION, encoding="utf-8")

    (env,) = KerodonExtractor(tmp_path).extract_chapter(1, "0001").sections[0].intro_environments

    assert env.title == TITLE


def test_a_math_title_compiles_as_math_not_as_its_source(tmp_path: Path) -> None:
    titled = KerodonEnvironment("00GZ", "remark", "1.2.2.5", TITLE, "", "Let $X$ be a space.")
    untitled = KerodonEnvironment("00H1", "remark", "1.2.2.6", "", "", "Every space is a space.")
    section = KerodonSection("0002", "1.2", "Topology", intro_environments=[titled, untitled])
    typ = tmp_path / "chapter1.typ"
    KerodonCompiler(KerodonChapter("0001", "1", "The Language", sections=[section])).generate_typst(typ)

    _ = subprocess.run(["typst", "compile", str(typ)], check=True, capture_output=True)
    text = "".join(page.get_text() for page in pymupdf.open(typ.with_suffix(".pdf")))

    assert "Connected Components of Sing" in text
    assert "$" not in text and '"Sing"' not in text
    assert "Remark 1.2.2.6. Every space" in " ".join(text.split())
