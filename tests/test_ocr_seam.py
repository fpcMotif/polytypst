from pathlib import Path

from conftest import COVER, COVER_INK, INK, PAPER, PageRender, sheet

from polytypst.ocr.backend import Backend
from polytypst.ocr.blank import BLANK_TRANSCRIPT, is_blank_page
from polytypst.pipeline import UniversalPDFPipeline


def cached_pipeline(
    tmp_path: Path, pages: set[int] | None = None
) -> UniversalPDFPipeline:
    cache = tmp_path / "cache"
    cache.mkdir()
    for n in (1, 2, 3):
        _ = (cache / f"p_{n:03d}.md").write_text(
            f"Cached transcript for page {n} of the book.", encoding="utf-8"
        )
    backend = Backend.parse(f"cached:?dir={cache}")
    return UniversalPDFPipeline(
        tmp_path / "book.pdf", tmp_path, backend=backend, pages=pages
    )


def test_pipeline_transcribes_only_the_pages_asked_for(
    tmp_path: Path, page_render: PageRender
) -> None:
    for n in (1, 2, 3):
        _ = page_render(n)
    result = cached_pipeline(tmp_path, pages={1, 3}).run_transcription()
    assert result == {
        1: "Cached transcript for page 1 of the book.\n",
        3: "Cached transcript for page 3 of the book.\n",
    }


def test_pipeline_marks_blank_pages_instead_of_transcribing_them(
    tmp_path: Path, page_render: PageRender
) -> None:
    for n in (1, 3):
        _ = page_render(n)
    _ = page_render(2, blank=True)
    result = cached_pipeline(tmp_path).run_transcription()
    assert result[2] == BLANK_TRANSCRIPT
    assert result[3] == "Cached transcript for page 3 of the book.\n"


def test_blank_page_test_ignores_toned_paper_and_keeps_colored_covers(
    tmp_path: Path,
) -> None:
    flyleaf = tmp_path / "flyleaf.png"
    sheet(PAPER, None).save(flyleaf)
    text_page = tmp_path / "text.png"
    sheet(PAPER, INK).save(text_page)
    cover = tmp_path / "cover.png"
    sheet(COVER, COVER_INK).save(cover)
    assert is_blank_page(flyleaf)
    assert not is_blank_page(text_page)
    assert not is_blank_page(cover)
