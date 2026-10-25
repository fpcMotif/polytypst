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


@pytest.mark.parametrize(
    ("ocr", "typesettable"),
    [
        ("Step 1\ufe0f\u20e3 then 2\ufe0f\u20e3.", "Step 1 then 2."),
        ("Take $1\u20e3 + x$ here.", "Take $1 + x$ here."),
        ("Tag #\ufe0f\u20e3 and *\ufe0f\u20e3 in $#\u20e3 a *\u20e3 b$.", "Tag \\# and \\* in $\\# a * b$."),
        ("Results 🎉 hold for $n$ 🚀.", "Results hold for $n$."),
        ("A 👨\u200d👩\u200d👧 family.", "A family."),
        ("Made in 🇫🇷 with 👍🏽 care.", "Made in with care."),
        ("Flag 🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f end.", "Flag end."),
        ("Odd \ufe0f selector, tone \U0001f3fd alone.", "Odd selector, tone alone."),
        ("Love \u2764\ufe0f and \u263a\ufe0f done, \u2716\ufe0f times, \u2264\ufe0e text.", "Love and done, \u00d7 times, \u2264 text."),
        ("$a\u200b+b$ and text\u200bjoined\u2060.", "$a+b$ and textjoined."),
        ("Left\u200f right\u202e reversed\u2066 x\u2069.", "Left right reversed x."),
        ("\ufeffBefore\x00null\x07bell\x1bescape after.", "Beforenullbellescape after."),
        ("Glyph \ue000 from \U000f0001 a font.", "Glyph from a font."),
        ("Soft\u00adhyphen.", "Softhyphen."),
        ("$ｆ（ｘ）＝ｘ＋１$ is fullwidth math.", "$f(x)=x+1$ is fullwidth math."),
        ("$$\nｆ\u3000＝\u3000ｇ\n$$", "$$\nf = g\n$$"),
        ("Items ⑵, ⒊, ⒜ and ❹, ➊, ⓫, ⓵, ⓿.", "Items (2), 3., (a) and ④, ①, ⑪, ①, ⓪."),
        ("$\u0301x$ starts on a mark.", "$x$ starts on a mark."),
        ("Literal \\ud83d\\ude00 and \\ud83d alone.", "Literal and alone."),
        ("Entity &#x1F600; and &#128512; here.", "Entity and here."),
    ],
)
def test_the_store_reads_ocr_markdown_as_typesettable_text(
    tmp_path: Path, ocr: str, typesettable: str
) -> None:
    store = TranscriptStore(tmp_path)
    _ = (tmp_path / "p_001.md").write_text(ocr, encoding="utf-8")
    assert store.text(1) == typesettable


@pytest.mark.parametrize(
    "kept",
    [
        "定理 1.1. 正則関数 $f$ は $D$ で連続である．（証明）",
        "هذه جملة عربية مع $x^2$ رياضيات.",
        "Ünïcödé café, naïve, «guillemets», “curly”, 1 000 m, 10°C, © 1950.",
        "$𝒪_X \\otimes 𝔪$ and $a − b × c ≤ d → e$ and $\\alpha ∈ ℝ$.",
        "Tabs\tand\nnewlines\n\nstay.",
        "估算①，见 ⑳ 与 ⓪，Ⓐ 和 ⓩ.\n\n① Romer (2006)，p. 178.",
        "The breve \\u{a} and \\upsilon and \\underline{x} are LaTeX.",
        "Costs &amp; benefits, &lt;x&gt;.",
    ],
)
def test_the_store_keeps_text_that_the_book_fonts_draw(tmp_path: Path, kept: str) -> None:
    store = TranscriptStore(tmp_path)
    _ = (tmp_path / "p_001.md").write_text(kept, encoding="utf-8")
    assert store.text(1) == kept
