import json
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from conftest import COVER, COVER_INK, INK, PAPER, PageRender, sheet

from polytypst.ocr.blank import BLANK_TRANSCRIPT, is_blank_page
from polytypst.ocr.pages import PageImage, Transcript
from polytypst.ocr.transcripts import TranscriptStore, normalize_ocr_markdown


class FakeTranscriber:
    def __init__(
        self,
        provenance: str = "fake:model",
        skip: Sequence[int] = (),
        crash_after: int | None = None,
    ) -> None:
        self.provenance = provenance
        self.skip = set(skip)
        self.crash_after = crash_after
        self.seen: list[int] = []

    def transcribe(self, pages: Sequence[PageImage]) -> Iterator[Transcript]:
        for page in pages:
            self.seen.append(page.number)
            if page.number in self.skip:
                continue
            yield Transcript(
                page.number,
                f"```markdown\nPage {page.number} body from {self.provenance}.\n```",
            )
            if page.number == self.crash_after:
                raise RuntimeError("worker died")


def provenance(store_dir: Path) -> dict[str, str]:
    return json.loads((store_dir / "transcripts.json").read_text(encoding="utf-8"))[
        "pages"
    ]


def test_normalize_unwraps_fences_lists_and_unicode() -> None:
    assert normalize_ocr_markdown(["```md\n$e$ holds\n```", "ignored"]) == "$e$ holds\n"
    assert normalize_ocr_markdown("```markdown\n# Title\n```") == "# Title\n"
    assert (
        normalize_ocr_markdown("```latex\nUnclosed fence body")
        == "Unclosed fence body\n"
    )
    assert normalize_ocr_markdown(("é",)) == "é\n"
    assert normalize_ocr_markdown("   ") == ""


def test_blank_page_test_ignores_toned_paper_and_keeps_colored_covers(
    tmp_path: Path,
) -> None:
    flyleaf, text_page, cover = (tmp_path / f"{n}.png" for n in ("f", "t", "c"))
    sheet(PAPER, None).save(flyleaf)
    sheet(PAPER, INK).save(text_page)
    sheet(COVER, COVER_INK).save(cover)
    assert is_blank_page(flyleaf)
    assert not is_blank_page(text_page)
    assert not is_blank_page(cover)


def test_transcribe_writes_every_page_and_records_who_made_it(
    tmp_path: Path, page_render: PageRender
) -> None:
    pages = [page_render(n) for n in (1, 2, 3)]
    store = TranscriptStore(tmp_path / "md")
    result = store.transcribe(pages, FakeTranscriber())
    assert list(result) == [1, 2, 3]
    assert result[2] == "Page 2 body from fake:model.\n"
    assert store.text(2) == result[2]
    assert provenance(tmp_path / "md") == {
        "1": "fake:model",
        "2": "fake:model",
        "3": "fake:model",
    }


def test_transcribe_resumes_and_redoes_short_transcripts(
    tmp_path: Path, page_render: PageRender
) -> None:
    pages = [page_render(n) for n in (1, 2, 3)]
    md = tmp_path / "md"
    md.mkdir()
    (md / "p_001.md").write_text(
        "An existing transcript long enough to keep.", encoding="utf-8"
    )
    (md / "p_002.md").write_text("tiny", encoding="utf-8")
    fake = FakeTranscriber()
    result = TranscriptStore(md).transcribe(pages, fake)
    assert fake.seen == [2, 3]
    assert result[1] == "An existing transcript long enough to keep."
    assert provenance(md)["1"] == "unknown"


def test_blank_pages_get_the_marker_and_never_reach_the_transcriber(
    tmp_path: Path, page_render: PageRender
) -> None:
    pages = [page_render(1), page_render(2, blank=True), page_render(3)]
    md = tmp_path / "md"
    md.mkdir()
    (md / "p_002.md").write_text(
        "# 1. Introduction\n\n## 1.2 Invented by a model\n", encoding="utf-8"
    )
    fake = FakeTranscriber()
    result = TranscriptStore(md).transcribe(pages, fake)
    assert result[2] == BLANK_TRANSCRIPT
    assert fake.seen == [1, 3]
    assert provenance(md)["2"] == "blank"


def test_an_existing_blank_marker_is_trusted_without_rereading_the_image(
    tmp_path: Path, page_render: PageRender
) -> None:
    page = page_render(1)
    md = tmp_path / "md"
    md.mkdir()
    (md / "p_001.md").write_text(BLANK_TRANSCRIPT, encoding="utf-8")
    fake = FakeTranscriber()
    assert TranscriptStore(md).transcribe([page], fake) == {1: BLANK_TRANSCRIPT}
    assert fake.seen == []


def test_pages_from_another_backend_are_kept_and_reported(
    tmp_path: Path, page_render: PageRender, capsys: pytest.CaptureFixture[str]
) -> None:
    pages = [page_render(n) for n in (1, 2)]
    store = TranscriptStore(tmp_path / "md")
    _ = store.transcribe(pages, FakeTranscriber("old:model"))
    newer = FakeTranscriber("new:model")
    result = store.transcribe(pages, newer)
    assert newer.seen == []
    assert result[1] == "Page 1 body from old:model.\n"
    assert "2 transcripts made by old:model" in capsys.readouterr().out


def test_retranscribe_redoes_the_pages_it_is_given(
    tmp_path: Path, page_render: PageRender
) -> None:
    pages = [page_render(n) for n in (1, 2)]
    store = TranscriptStore(tmp_path / "md")
    _ = store.transcribe(pages, FakeTranscriber("old:model"))
    newer = FakeTranscriber("new:model")
    result = store.transcribe(pages[1:], newer, retranscribe=True)
    assert newer.seen == [2]
    assert result == {2: "Page 2 body from new:model.\n"}
    assert provenance(tmp_path / "md") == {"1": "old:model", "2": "new:model"}


def test_a_page_the_transcriber_skips_stays_pending(
    tmp_path: Path, page_render: PageRender, capsys: pytest.CaptureFixture[str]
) -> None:
    pages = [page_render(n) for n in (1, 2, 3)]
    store = TranscriptStore(tmp_path / "md")
    result = store.transcribe(pages, FakeTranscriber(skip=[2]))
    assert list(result) == [1, 3]
    assert "1 page still pending: 2" in capsys.readouterr().out
    retry = FakeTranscriber()
    _ = store.transcribe(pages, retry)
    assert retry.seen == [2]


def test_pages_finished_before_a_crash_are_saved(
    tmp_path: Path, page_render: PageRender
) -> None:
    pages = [page_render(n) for n in (1, 2, 3)]
    store = TranscriptStore(tmp_path / "md")
    with pytest.raises(RuntimeError, match="worker died"):
        _ = store.transcribe(pages, FakeTranscriber(crash_after=2))
    assert store.text(1) == "Page 1 body from fake:model.\n"
    assert store.text(2) == "Page 2 body from fake:model.\n"
    assert store.text(3) is None
    assert set(provenance(tmp_path / "md")) == {"1", "2"}
