from collections.abc import Sequence
from pathlib import Path

import httpx
import pytest
from PIL import Image, ImageDraw

from polytypst.ocr import jina
from polytypst.ocr.base import (
    OCREngine,
    OCRPage,
    normalize_ocr_markdown,
    page_number,
    pending_pages,
    transcript_path,
)
from polytypst.ocr.blank import BLANK_TRANSCRIPT, is_blank_page
from polytypst.ocr.colab_cluster import (
    ClusterStats,
    ColabOCRCluster,
    ColabOCREngine,
)
from polytypst.ocr.engines import CachedMarkdownEngine, ocr_engine
from polytypst.ocr.jina import JinaCloudOCREngine, JinaCloudUnavailable
from polytypst.pipeline import UniversalPDFPipeline


def _renders(tmp_path: Path, count: int) -> list[Path]:
    renders = tmp_path / "page_renders"
    renders.mkdir()
    pages = [renders / f"p_{n:03d}.png" for n in range(1, count + 1)]
    for p in pages:
        _page_image(PAPER, ink=INK).save(p)
    return pages


PAPER = (222, 210, 180)
INK = (40, 35, 30)


def _page_image(
    paper: tuple[int, int, int], ink: tuple[int, int, int] | None
) -> Image.Image:
    """A 400x600 sheet of `paper` that darkens toward its right edge as aged stock does,
    with ten lines of type in `ink` when given."""
    img = Image.new("RGB", (400, 600), paper)
    draw = ImageDraw.Draw(img)
    for x in range(400):
        shade = 30 * x // 400
        draw.line((x, 0, x, 599), fill=tuple(c - shade for c in paper))
    if ink is not None:
        draw = ImageDraw.Draw(img)
        for row in range(10):
            draw.rectangle((40, 60 + row * 40, 360, 72 + row * 40), fill=ink)
    return img


class CountingEngine(OCREngine):
    def __init__(self) -> None:
        self.seen: list[int] = []

    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        self.seen.append(page_number)
        return OCRPage(
            page_number,
            0,
            0,
            [],
            raw_text=f"```markdown\nPage {page_number} body text here.\n```",
        )

    def recognize_document(self, image_paths: list[Path]) -> list[OCRPage]:
        return [self.recognize_page(p, page_number(p)) for p in image_paths]


def test_normalize_unwraps_fences_lists_and_unicode() -> None:
    assert normalize_ocr_markdown(["```md\n$e$ holds\n```", "ignored"]) == "$e$ holds\n"
    assert normalize_ocr_markdown("```markdown\n# Title\n```") == "# Title\n"
    assert normalize_ocr_markdown(("é",)) == "é\n"
    assert normalize_ocr_markdown("   ") == ""


def test_transcribe_pages_resumes_and_redoes_short_transcripts(tmp_path: Path) -> None:
    pages = _renders(tmp_path, 3)
    out = tmp_path / "md"
    out.mkdir()
    _ = transcript_path(out, 1).write_text(
        "An existing transcript long enough to keep.", encoding="utf-8"
    )
    _ = transcript_path(out, 2).write_text("tiny", encoding="utf-8")
    engine = CountingEngine()
    result = engine.transcribe_pages(pages, out)
    assert engine.seen == [2, 3]
    assert [n for n, _ in result] == [1, 2, 3]
    assert result[1][1] == "Page 2 body text here.\n"


def test_pipeline_transcribes_through_an_injected_cached_engine(tmp_path: Path) -> None:
    _ = _renders(tmp_path, 3)
    cache = tmp_path / "cache"
    cache.mkdir()
    for n in (1, 2, 3):
        _ = transcript_path(cache, n).write_text(
            f"Cached transcript for page {n} of the book.", encoding="utf-8"
        )
    pipeline = UniversalPDFPipeline(
        tmp_path / "book.pdf", tmp_path, ocr_engine=CachedMarkdownEngine(cache)
    )
    result = pipeline.run_transcription(page_subset=[1, 3])
    assert result == [
        (1, "Cached transcript for page 1 of the book.\n"),
        (3, "Cached transcript for page 3 of the book.\n"),
    ]


def test_blank_page_test_ignores_toned_paper_and_keeps_colored_covers(
    tmp_path: Path,
) -> None:
    flyleaf = tmp_path / "flyleaf.png"
    _page_image(PAPER, ink=None).save(flyleaf)
    text_page = tmp_path / "text.png"
    _page_image(PAPER, ink=INK).save(text_page)
    cover = tmp_path / "cover.png"
    _page_image((40, 82, 112), ink=(140, 120, 30)).save(cover)
    assert is_blank_page(flyleaf)
    assert not is_blank_page(text_page)
    assert not is_blank_page(cover)


def test_pipeline_marks_blank_pages_and_never_sends_them_to_ocr(
    tmp_path: Path,
) -> None:
    pages = _renders(tmp_path, 3)
    _page_image(PAPER, ink=None).save(pages[1])
    engine = CountingEngine()
    pipeline = UniversalPDFPipeline(tmp_path / "book.pdf", tmp_path, ocr_engine=engine)
    pipeline.markdown_dir.mkdir()
    _ = transcript_path(pipeline.markdown_dir, 2).write_text(
        "# 1. Introduction\n\n## 1.2 Problem Statement\n", encoding="utf-8"
    )
    result = dict(pipeline.run_transcription())
    assert result[2] == BLANK_TRANSCRIPT
    assert engine.seen == [1, 3]
    assert pending_pages([pages[1]], pipeline.markdown_dir) == []


def test_ocr_engine_factory_rejects_unknown_modes(tmp_path: Path) -> None:
    assert isinstance(ocr_engine("cached", cache_dir=tmp_path), CachedMarkdownEngine)
    with pytest.raises(ValueError):
        _ = ocr_engine("cached")
    with pytest.raises(ValueError):
        _ = ocr_engine("telepathy")


def _jina_engine(handler: httpx.MockTransport, failures: int = 5) -> JinaCloudOCREngine:
    return JinaCloudOCREngine(
        api_key="test-key",
        retries=3,
        pacing_sec=0.0,
        max_consecutive_failures=failures,
        client=httpx.Client(transport=handler),
    )


def test_jina_cloud_backs_off_on_rate_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jina.time, "sleep", lambda _s: None)
    calls: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        assert request.headers["Authorization"] == "Bearer test-key"
        if len(calls) == 1:
            return httpx.Response(429)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "```markdown\n$z^2$ page\n```"}}]
            },
        )

    pages = _renders(tmp_path, 1)
    result = _jina_engine(httpx.MockTransport(handle)).transcribe_pages(
        pages, tmp_path / "md"
    )
    assert len(calls) == 2
    assert result == [(1, "$z^2$ page\n")]


def test_jina_cloud_gives_up_after_consecutive_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jina.time, "sleep", lambda _s: None)
    engine = _jina_engine(
        httpx.MockTransport(lambda _r: httpx.Response(503)), failures=2
    )
    pages = _renders(tmp_path, 3)
    with pytest.raises(JinaCloudUnavailable):
        _ = engine.transcribe_pages(pages, tmp_path / "md")
    assert not transcript_path(tmp_path / "md", 1).read_text(encoding="utf-8")


class FakeCluster(ColabOCRCluster):
    def __init__(self) -> None:
        super().__init__()
        self.batches: list[list[int]] = []

    def run_cluster(
        self,
        pages_dir: Path,
        out_dir: Path,
        pages: Sequence[Path] | None = None,
    ) -> ClusterStats:
        batch = [page_number(p) for p in pages or []]
        self.batches.append(batch)
        for n in batch:
            _ = transcript_path(out_dir, n).write_text(
                f"```\nColab transcript of page {n}.\n```", encoding="utf-8"
            )
        return ClusterStats(len(batch), len(batch), 0.0, 0.0, 1)


def test_colab_adapter_runs_pending_pages_in_batches(tmp_path: Path) -> None:
    pages = _renders(tmp_path, 5)
    out = tmp_path / "md"
    out.mkdir()
    _ = transcript_path(out, 2).write_text(
        "Page two already transcribed earlier.", encoding="utf-8"
    )
    cluster = FakeCluster()
    result = ColabOCREngine(cluster, batch_size=2).transcribe_pages(pages, out)
    assert cluster.batches == [[1, 3], [4, 5]]
    assert dict(result)[4] == "Colab transcript of page 4.\n"
