import base64
import io
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from conftest import PageRender
from PIL import Image

from polytypst.ocr import http_transcriber
from polytypst.ocr.gemini import GeminiTranscriber
from polytypst.ocr.http_transcriber import encode_image
from polytypst.ocr.mistral import MistralTranscriber
from polytypst.ocr.openai_compat import OpenAICompatTranscriber
from polytypst.ocr.pages import OCRBackendError, Transcript

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http_transcriber.time, "sleep", lambda _s: None)


def client(handle: Handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handle))


def openai_reply(text: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def openai(
    handle: Handler, api_key: str | None = "k", concurrency: int = 1
) -> OpenAICompatTranscriber:
    return OpenAICompatTranscriber(
        base_url="http://gpu-box:8000/v1/",
        model="qwen2.5-vl",
        prompt="Transcribe.",
        api_key=api_key,
        provenance="openai:qwen2.5-vl",
        concurrency=concurrency,
        max_side=0,
        client=client(handle),
    )


def test_gemini_sends_prompt_and_inline_image_and_reads_candidate_parts(
    page_render: PageRender,
) -> None:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        parts = [{"text": "$x$ "}, {"text": "page"}]
        return httpx.Response(200, json={"candidates": [{"content": {"parts": parts}}]})

    page = page_render(7)
    gemini = GeminiTranscriber(
        model="gemini-3.1-pro-preview",
        prompt="Transcribe.",
        api_key="k",
        provenance="gemini:gemini-3.1-pro-preview",
        concurrency=2,
        max_side=0,
        client=client(handle),
    )
    assert list(gemini.transcribe([page])) == [Transcript(7, "$x$ page")]
    request = seen[0]
    assert request.url.path == "/v1beta/models/gemini-3.1-pro-preview:generateContent"
    assert request.headers["x-goog-api-key"] == "k"
    body = json.loads(request.content)
    text_part, image_part = body["contents"][0]["parts"]
    assert text_part == {"text": "Transcribe."}
    assert image_part["inline_data"]["mime_type"] == "image/png"
    assert base64.b64decode(image_part["inline_data"]["data"]) == page.path.read_bytes()
    assert body["generationConfig"] == {"temperature": 0}


def test_openai_compatible_posts_chat_completions_with_a_data_uri(
    page_render: PageRender,
) -> None:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return openai_reply("Body text.")

    page = page_render(3, suffix=".jpg")
    assert list(openai(handle).transcribe([page])) == [Transcript(3, "Body text.")]
    request = seen[0]
    assert str(request.url) == "http://gpu-box:8000/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer k"
    body = json.loads(request.content)
    assert body["model"] == "qwen2.5-vl"
    text_part, image_part = body["messages"][0]["content"]
    assert text_part == {"type": "text", "text": "Transcribe."}
    assert image_part["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_a_self_hosted_server_without_a_key_gets_no_auth_header(
    page_render: PageRender,
) -> None:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return openai_reply("Body text.")

    _ = list(openai(handle, api_key=None).transcribe([page_render(1)]))
    assert "Authorization" not in seen[0].headers


def test_mistral_posts_an_ocr_document_and_reads_page_markdown(
    page_render: PageRender,
) -> None:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"pages": [{"markdown": "# Heading"}]})

    mistral = MistralTranscriber(
        model="mistral-ocr-latest",
        api_key="k",
        provenance="mistral:mistral-ocr-latest",
        concurrency=1,
        max_side=0,
        client=client(handle),
    )
    assert list(mistral.transcribe([page_render(2)])) == [Transcript(2, "# Heading")]
    body = json.loads(seen[0].content)
    assert str(seen[0].url) == "https://api.mistral.ai/v1/ocr"
    assert body["model"] == "mistral-ocr-latest"
    assert body["document"]["type"] == "image_url"
    assert body["document"]["image_url"].startswith("data:image/png;base64,")


def test_a_rate_limited_page_is_retried(page_render: PageRender) -> None:
    calls: list[int] = []

    def handle(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(429) if len(calls) == 1 else openai_reply("ok")

    assert list(openai(handle).transcribe([page_render(1)])) == [Transcript(1, "ok")]
    assert len(calls) == 2


def test_a_rejected_key_stops_the_whole_backend_at_once(
    page_render: PageRender,
) -> None:
    calls: list[int] = []

    def handle(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401, text="bad key")

    with pytest.raises(OCRBackendError, match="401"):
        _ = list(openai(handle).transcribe([page_render(1), page_render(2)]))
    assert len(calls) == 1


def test_a_page_that_keeps_failing_is_left_out_and_the_rest_arrive(
    page_render: PageRender,
) -> None:
    pages = [page_render(1), page_render(2, blank=True)]
    broken = base64.b64encode(pages[1].path.read_bytes())

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503) if broken in request.content else openai_reply("ok")

    assert list(openai(handle).transcribe(pages)) == [Transcript(1, "ok")]


def test_many_failed_pages_in_a_row_stop_the_backend(page_render: PageRender) -> None:
    transcriber = openai(lambda _r: httpx.Response(503))
    pages = [page_render(n) for n in range(1, 8)]
    with pytest.raises(OCRBackendError, match="failed in a row"):
        _ = list(transcriber.transcribe(pages))


def test_concurrent_pages_all_arrive(page_render: PageRender) -> None:
    pages = [page_render(n) for n in range(1, 7)]
    got = list(openai(lambda _r: openai_reply("ok"), concurrency=3).transcribe(pages))
    assert sorted(t.number for t in got) == [1, 2, 3, 4, 5, 6]


def test_encode_image_keeps_small_files_and_downscales_large_ones(
    tmp_path: Path,
) -> None:
    small = tmp_path / "small.jpg"
    Image.new("RGB", (300, 200), "white").save(small, format="JPEG")
    kept = encode_image(small, max_side=1000)
    assert kept.mime == "image/jpeg"
    assert base64.b64decode(kept.data) == small.read_bytes()

    shrunk = encode_image(small, max_side=150)
    assert shrunk.mime == "image/jpeg"
    assert Image.open(io.BytesIO(base64.b64decode(shrunk.data))).size == (150, 100)

    tiff = tmp_path / "scan.tif"
    Image.new("L", (40, 40), 255).save(tiff)
    converted = encode_image(tiff, max_side=0)
    assert converted.mime == "image/png"
    assert Image.open(io.BytesIO(base64.b64decode(converted.data))).format == "PNG"
