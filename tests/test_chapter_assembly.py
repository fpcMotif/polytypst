from pathlib import Path

from PIL import Image

from polytypst.compiler.monograph import (
    ChapterSpec,
    MonographCompiler,
    MonographSpec,
    RenderedMonograph,
)
from polytypst.compiler.source_numbers import labels


def render_chapter(book_state_root: Path, tmp_path: Path, pages: list[str], **spec_fields: object) -> RenderedMonograph:
    """Render one chapter made of `pages`, read from a transcript store, as the build does."""
    store = book_state_root / "t" / "markdown_pages"
    store.mkdir(parents=True)
    for pno, text in enumerate(pages, 1):
        (store / f"p_{pno:03d}.md").write_text(text, encoding="utf-8")
    spec = MonographSpec(
        domain="math", slug="t", title="T", author="A", chapters=[ChapterSpec(1, "One", 1, len(pages))], **spec_fields
    )
    return MonographCompiler(spec).render(tmp_path / "t")


def test_inline_math_that_straddles_a_page_joins_into_one_formula(book_state_root: Path, tmp_path: Path) -> None:
    rendered = render_chapter(book_state_root, tmp_path, ["本文 $t = (t_1,", "$t_2)$ の続き"])
    assert "$t = (t_1, t_2)$" in rendered.markdown


def test_complete_paragraphs_on_two_pages_stay_two_paragraphs(book_state_root: Path, tmp_path: Path) -> None:
    rendered = render_chapter(book_state_root, tmp_path, ["第一段。", "第二段。"])
    assert "第一段。\n\n第二段。" in rendered.markdown


def test_a_paragraph_across_a_page_break_stays_whole_and_its_figure_follows_it_in_both_outputs(
    book_state_root: Path, tmp_path: Path
) -> None:
    figures = tmp_path / "t" / "figures"
    figures.mkdir(parents=True)
    Image.new("RGB", (40, 30), "white").save(figures / "fig_1-1.png")
    rendered = render_chapter(
        book_state_root,
        tmp_path,
        ["## 1 Setting\n\nEarlier text.\n\nThe bound holds for every $n$.", "which ends the proof.\n\n## 2 Next\n\nMore."],
        cross_references=True,
        extra_figures={1: (("1-1", "Figure 1.1"),)},
    )
    joined = "The bound holds for every $n$. which ends the proof."
    for text in (rendered.typst, rendered.latex_markdown or ""):
        assert joined in text
        assert text.index(joined) < text.index("fig_1-1.png") < text.index("Next")
    assert {"art-1", "art-2"} <= labels(rendered.typst)
    assert labels(rendered.typst) == labels(rendered.latex_markdown or "")
