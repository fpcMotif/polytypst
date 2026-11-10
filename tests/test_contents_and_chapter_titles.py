from polytypst.compiler.chapter_assembly import mark_contents_lines
from polytypst.compiler.monograph import (
    ChapterSpec,
    MonographCompiler,
    MonographSpec,
)


def test_capitalized_title_after_the_chapter_line_is_dropped_on_the_chapter_start_page() -> None:
    spec = MonographSpec(
        domain="math",
        slug="t",
        title="T",
        author="A",
        chapters=[ChapterSpec(6, "The Gauss-Bonnet Theorem and Related Topics", 1, 2)],
    )
    page = "# CHAPTER 6\n\n## THE GAUSS-BONNET THEOREM AND RELATED TOPICS\n\nIn Volume II we presented Gauss' proof.\n"
    extracted, _, _ = MonographCompiler(spec).cleaner.clean(page, pno=1)
    assert "GAUSS-BONNET" not in extracted
    assert "In Volume II we presented Gauss' proof." in extracted


def test_contents_entries_join_wrapped_titles_and_keep_their_page_numbers() -> None:
    page = (
        "# Contents\n\n"
        "## CHAPTER 5. COMPLETE SURFACES OF CONSTANT CURVATURE\n\n"
        "Analysis of flat surfaces; the classical classification\n"
        "of developable surfaces . . . . . . . . 235\n"
        "Complete flat surfaces 244\n\n"
        "## INDEX . . . . . . . . 309\n"
    )
    assert mark_contents_lines(page, keep_title=False).split("\n\n") == [
        "@@CONTENTSHEAD@@CHAPTER 5. COMPLETE SURFACES OF CONSTANT CURVATURE",
        "@@CONTENTS@@Analysis of flat surfaces; the classical classification of developable surfaces@@PAGE@@235",
        "@@CONTENTS@@Complete flat surfaces@@PAGE@@244",
        "@@CONTENTS@@INDEX@@PAGE@@309",
    ]
