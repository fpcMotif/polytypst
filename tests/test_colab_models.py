import subprocess
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from polytypst.ocr import colab, engines, gpu_worker
from polytypst.ocr.colab import COLAB_GPUS, account_usage, fit_problem
from polytypst.ocr.colab_cli import sample_pages
from polytypst.ocr.engines import LocalGPUWorkerEngine, ocr_engine
from polytypst.ocr.ocr_models import JINA_RUNTIME, OCR_MODELS, ocr_model


def test_unlimited_ocr_detection_markers_are_stripped() -> None:
    raw = (
        "<|det|>title [10, 20, 300, 60]<|/det|># Chapter I\n"
        "<|det|>image [0, 0, 5, 5]<|/det|>\n"
        "<|det|>text [10, 80, 300, 200]<|/det|>Let $f$ be holomorphic."
    )
    assert (
        ocr_model("unlimited-ocr").clean(raw)
        == "# Chapter I\n\nLet $f$ be holomorphic."
    )


def test_deepseek_grounding_tags_and_end_token_are_stripped() -> None:
    raw = (
        "<|ref|>title<|/ref|><|det|>[[52, 40, 600, 90]]<|/det|>\n## 1.1 Power series\n\n"
        "<|ref|>text<|/ref|><|det|>[[52, 120, 900, 400]]<|/det|>\nA series converges.<｜end▁of▁sentence｜>"
    )
    assert (
        ocr_model("deepseek-ocr").clean(raw)
        == "## 1.1 Power series\n\nA series converges."
    )


def test_olmocr_front_matter_is_stripped() -> None:
    raw = "---\nprimary_language: en\nis_rotation_valid: True\n---\nThe text body."
    assert ocr_model("olmocr-2").clean(raw) == "The text body."


def test_book_prompt_reaches_only_models_that_follow_prompts() -> None:
    assert ocr_model("qwen3-vl-8b").prompt_for("Kodaira prompt") == "Kodaira prompt"
    assert (
        ocr_model("unlimited-ocr").prompt_for("Kodaira prompt")
        == "<image>document parsing."
    )
    with pytest.raises(ValueError, match="Unknown OCR model"):
        _ = ocr_model("telepathy")


def test_t4_has_no_bfloat16_for_deepseek_family() -> None:
    t4 = COLAB_GPUS["T4"]
    assert fit_problem(ocr_model("jina-ocr-v1"), t4) is None
    assert fit_problem(ocr_model("unlimited-ocr"), t4) is not None
    assert fit_problem(ocr_model("deepseek-ocr"), t4) is not None


def test_eight_billion_bf16_model_needs_more_than_an_l4() -> None:
    qwen = ocr_model("qwen3-vl-8b")
    assert "VRAM" in (fit_problem(qwen, COLAB_GPUS["L4"]) or "")
    assert fit_problem(qwen, COLAB_GPUS["A100"]) is None
    assert fit_problem(qwen, COLAB_GPUS["G4"]) is None


def test_copies_per_gpu_fill_vram_but_vllm_uses_one_copy() -> None:
    jina = ocr_model("jina-ocr-v1")
    assert jina.copies_per_gpu(COLAB_GPUS["T4"].vram_gb, 3) == 1
    assert jina.copies_per_gpu(COLAB_GPUS["G4"].vram_gb, 3) == 3
    assert ocr_model("olmocr-2").copies_per_gpu(COLAB_GPUS["G4"].vram_gb, 3) == 1


def test_every_model_fits_the_g4() -> None:
    assert all(fit_problem(m, COLAB_GPUS["G4"]) is None for m in OCR_MODELS.values())


def _fake_cli(stdout: str):
    def run(*args: str, stdin: str | None = None, timeout: float | None = None):
        return subprocess.CompletedProcess(["colab", *args], 0, stdout, "")

    return run


def test_account_usage_reads_balance_and_burn_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(colab.shutil, "which", lambda _name: "/usr/bin/colab")
    monkeypatch.setattr(
        colab,
        "colab_cli",
        _fake_cli(
            "Current balance: 244.65 compute units\nUsage rate: 8.90/hr\nActive assignments: 1\n"
        ),
    )
    usage = account_usage()
    assert usage is not None
    assert (usage.balance, usage.rate_per_hour, usage.active_assignments) == (
        244.65,
        8.9,
        1,
    )


def test_colab_mode_falls_back_to_local_worker_without_cli(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(colab.shutil, "which", lambda _name: None)
    engine = ocr_engine("colab", model="unlimited-ocr")
    assert isinstance(engine, LocalGPUWorkerEngine)
    assert engine.model == "unlimited-ocr"
    assert engines.OCR_MODES[0] == "colab"


def test_sample_pages_spread_across_the_book(tmp_path: Path) -> None:
    for n in range(1, 101):
        (tmp_path / f"p_{n:03d}.png").touch()
    picked = [p.name for p in sample_pages(tmp_path, 4)]
    assert picked == ["p_013.png", "p_038.png", "p_063.png", "p_088.png"]


def test_shard_worker_writes_cleaned_text_and_empty_blank_pages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inked = Image.new("RGB", (400, 400), "white")
    ImageDraw.Draw(inked).rectangle((50, 50, 350, 350), fill="black")
    inked.save(tmp_path / "p_001.png")
    Image.new("RGB", (400, 400), "white").save(tmp_path / "p_002.png")
    seen: list[str] = []

    def fake_transcriber(model, prompt):
        seen.append(prompt)
        return lambda images: [f"Text<|im_end|>{len(images)}" for _ in images]

    monkeypatch.setitem(gpu_worker.TRANSCRIBERS, JINA_RUNTIME, fake_transcriber)
    out = tmp_path / "md"
    out.mkdir()
    items = gpu_worker.page_items(tmp_path)
    done = gpu_worker._shard_worker(1, items, str(out), "book prompt", "jina-ocr-v1")
    assert done == 2
    assert seen == ["book prompt"]
    assert (out / "p_001.md").read_text(encoding="utf-8") == "Text1"
    assert (out / "p_002.md").read_text(encoding="utf-8") == ""
