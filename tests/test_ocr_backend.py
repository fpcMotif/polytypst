import pytest

from polytypst.ocr.backend import Backend, api_key
from polytypst.ocr.ocr_models import UNIVERSAL_TEX_PROMPT, ocr_model
from polytypst.ocr.pages import OCRBackendError


@pytest.mark.parametrize(
    ("text", "kind", "model", "options"),
    [
        (
            "gemini:gemini-3.1-pro-preview",
            "gemini",
            "gemini-3.1-pro-preview",
            {"concurrency": 4, "max_side": 2048},
        ),
        ("gemini", "gemini", "gemini-3.1-pro-preview", {}),
        ("gemini:", "gemini", "gemini-3.1-pro-preview", {}),
        (
            "gemini:?concurrency=2",
            "gemini",
            "gemini-3.1-pro-preview",
            {"concurrency": 2},
        ),
        (
            "openai:qwen2.5-vl-72b?base_url=http://gpu-box:8000/v1&key_env=",
            "openai",
            "qwen2.5-vl-72b",
            {"base_url": "http://gpu-box:8000/v1", "key_env": "", "concurrency": 8},
        ),
        ("jina", "jina", "jina-ocr-v1", {"concurrency": 1, "pace_ms": 1500}),
        ("mistral", "mistral", "mistral-ocr-latest", {"concurrency": 2}),
        ("local:deepseek-ocr?shards=2", "local", "deepseek-ocr", {"shards": 2}),
        (
            "colab",
            "colab",
            "jina-ocr-v1",
            {"gpu": "G4", "workers": 2, "shards": 3, "batch": 70},
        ),
        (
            "colab:deepseek-ocr?gpu=A100&workers=4",
            "colab",
            "deepseek-ocr",
            {"gpu": "A100", "workers": 4},
        ),
        (
            "cached:?dir=output/hecke/markdown_pages",
            "cached",
            "",
            {"dir": "output/hecke/markdown_pages"},
        ),
    ],
)
def test_parse_reads_kind_model_and_options(
    text: str, kind: str, model: str, options: dict[str, int | str]
) -> None:
    backend = Backend.parse(text)
    assert (backend.kind, backend.model) == (kind, model)
    assert {k: backend.options[k] for k in options} == options


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("telepathy:x", "Unknown OCR backend 'telepathy'"),
        ("gemini:x?colour=red", "gemini has no option 'colour'"),
        ("colab:?workers=two", "workers must be a whole number"),
        ("colab:not-a-model", "Unknown OCR model 'not-a-model'"),
        ("openai", "openai needs a model"),
        ("cached", "cached needs dir"),
    ],
)
def test_parse_rejects_bad_backends_with_the_reason(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = Backend.parse(text)


def test_str_round_trips_and_shows_only_changed_options() -> None:
    assert str(Backend.parse("gemini")) == "gemini:gemini-3.1-pro-preview"
    text = "colab:deepseek-ocr?gpu=A100&workers=4"
    assert str(Backend.parse(text)) == text
    assert Backend.parse(str(Backend.parse(text))) == Backend.parse(text)


def test_prompt_prefers_a_fixed_model_prompt_then_the_book_then_the_universal_one() -> (
    None
):
    assert Backend.parse("gemini").prompt("Book prompt.") == "Book prompt."
    assert Backend.parse("gemini").prompt(None) == UNIVERSAL_TEX_PROMPT
    assert Backend.parse("local:qwen3-vl-8b").prompt(None) == UNIVERSAL_TEX_PROMPT
    fixed = ocr_model("deepseek-ocr").fixed_prompt
    assert Backend.parse("colab:deepseek-ocr").prompt("Book prompt.") == fixed
    assert Backend.parse("mistral").prompt("Book prompt.") is None


def test_provenance_names_kind_model_and_prompt_but_not_run_options() -> None:
    plain = Backend.parse("colab:deepseek-ocr")
    busy = Backend.parse("colab:deepseek-ocr?workers=8&gpu=A100")
    assert plain.provenance("p") == busy.provenance("p")
    assert plain.provenance("p") != plain.provenance("q")
    assert plain.provenance("p").startswith("colab:deepseek-ocr#prompt=")
    assert Backend.parse("mistral").provenance(None) == "mistral:mistral-ocr-latest"


def test_api_key_names_the_missing_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(OCRBackendError, match="GEMINI_API_KEY"):
        _ = api_key("GEMINI_API_KEY")
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    assert api_key("GEMINI_API_KEY") == "k"
