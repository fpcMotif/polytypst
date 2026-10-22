from polytypst.compiler.monograph import ChapterSpec, MonographSpec
from polytypst.compiler.page_cleaner import CleanPage, PageCleaner

SPEC = MonographSpec(
    slug="probe",
    title="Probe",
    author="A",
    chapters=[ChapterSpec(1, "Holomorphic functions", 1, 40)],
    sections={"1.2": (5, "Power series")},
)


def test_a_section_heading_is_placed_once_and_its_running_head_is_dropped_later():
    cleaner = PageCleaner.for_spec(SPEC)
    first = cleaner.clean("## 1.2 Power Series\n\nEvery power series converges in a disc.", 5)
    later = cleaner.clean("1.2 Power series 7\n\nThe radius is given by Hadamard.", 7)
    assert first.body == "## 1.2 Power series\n\nEvery power series converges in a disc."
    assert later.body == "The radius is given by Hadamard."


def test_a_new_cleaner_has_placed_no_headings():
    _ = PageCleaner.for_spec(SPEC).clean("## 1.2 Power Series\n\nText.", 5)
    fresh = PageCleaner.for_spec(SPEC).clean("## 1.2 Power Series\n\nText.", 5)
    assert fresh.body.startswith("## 1.2 Power series")


def test_folios_watermarks_and_captions_leave_the_body():
    page = "12\n\nClibPDF - www.fastio.com\n\nThe map is shown below.\n\nFig. 1.3\n\nIt is conformal.\n\nSo is its inverse.\n\nFig. 1.4"
    assert PageCleaner.for_spec(SPEC).clean(page, 12) == CleanPage(
        "The map is shown below.\n\nIt is conformal.\n\nSo is its inverse.",
        [("1_3", "Fig. 1.3")],
        [("1_4", "Fig. 1.4")],
    )
