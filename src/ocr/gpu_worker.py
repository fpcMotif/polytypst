"""Self-contained GPU worker: transcribe page images with any model in `ocr_models`.

Runs on a Colab VM as `python -m ocrpkg.gpu_worker` beside a copy of `ocr_models.py`, or
locally through `LocalGPUWorkerEngine`. Each page becomes `p_NNN.md`; `_stats.json`
records throughput.
"""

import argparse
import base64
import importlib
import io
import json
import logging
import multiprocessing as mp
import tarfile
import tempfile
import time
import warnings
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image

from .ocr_models import (
    DEEPSEEK_INFER_RUNTIME,
    DEFAULT_OCR_MODEL,
    JINA_RUNTIME,
    VLLM_CHAT_RUNTIME,
    OCRModel,
    ocr_model,
)

warnings.filterwarnings("ignore")
logging.getLogger("transformers_modules").setLevel(logging.ERROR)

STATS_NAME = "_stats.json"
MIN_INK_AREA = 400
VLLM_BATCH = 16

UNIVERSAL_TEX_PROMPT = (
    "Transcribe this document page into clean, high-fidelity Markdown resembling LaTeX source.\n"
    "Rules:\n"
    "1. Format all mathematical expressions, variables, and formulas in LaTeX syntax: use inline $...$ and display $$...$$.\n"
    "2. Preserve all mathematical symbols, operators, superscripts, subscripts, fractions, integrals, sums, and limits exactly.\n"
    "3. Format headings with Markdown (#, ##, ###) reflecting document structure.\n"
    "4. Bold structural environments (e.g. **Theorem 1.**, **Lemma 2.**, **Definition.**, **Proposition.**, **Proof.**, **Example.**).\n"
    "5. Label display equations with exact numbering if present (e.g. $$ f(x) = \\dots $$ (1)).\n"
    "6. Convert tables into clean Markdown or HTML tables.\n"
    "7. For diagrams and figures, transcribe any caption or figure title (e.g. FIG. 1, Figure 2, Fig. 1.1) as a standalone line and preserve natural reading order.\n"
    "8. Preserve all body text, notes, and references without omitting content."
)

Transcriber = Callable[[list[Image.Image]], list[str]]


def crop_and_measure_ink(
    img: Image.Image, padding: int = 24
) -> tuple[Image.Image, int]:
    """Remove outer white margins and return (cropped_image, dark_pixel_bbox_area)."""
    gray = img.convert("L")
    bw = gray.point(lambda p: 255 if p < 200 else 0)
    bbox = bw.getbbox()
    if not bbox:
        return img, 0
    area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    w, h = img.size
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(w, bbox[2] + padding)
    bottom = min(h, bbox[3] + padding)
    return img.crop((left, top, right, bottom)), area


def _torch() -> Any:
    return importlib.import_module("torch")


def _device() -> str:
    torch = _torch()
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        return "cuda"
    return "mps" if torch.backends.mps.is_available() else "cpu"


def _half_dtype() -> Any:
    torch = _torch()
    bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    return torch.bfloat16 if bf16 else torch.float16


def _jina_transcriber(model: OCRModel, prompt: str) -> Transcriber:
    transformers: Any = importlib.import_module("transformers")
    device = _device()
    processor = transformers.AutoProcessor.from_pretrained(
        model.hf_id, trust_remote_code=True
    )
    net = (
        transformers.AutoModelForCausalLM.from_pretrained(
            model.hf_id, torch_dtype=_half_dtype(), trust_remote_code=True
        )
        .to(device)
        .eval()
    )
    tok = getattr(processor, "tokenizer", None)
    pad_id = tok and (tok.pad_token_id or tok.eos_token_id)
    gen_kwargs: dict[str, object] = {
        "max_new_tokens": model.max_tokens,
        "do_sample": False,
    }
    if pad_id is not None:
        gen_kwargs["pad_token_id"] = pad_id

    def transcribe(images: list[Image.Image]) -> list[str]:
        texts: list[str] = []
        for img in images:
            inp = processor.prepare_ocr_inputs(img, prompt=prompt, device=device)
            with _torch().inference_mode():
                out = net.generate(**inp, **gen_kwargs)
            decoded = processor.decode_ocr(out, inp["input_ids"])
            texts.append(
                decoded[0] if isinstance(decoded, (list, tuple)) else str(decoded)
            )
        return texts

    return transcribe


def _deepseek_infer_transcriber(model: OCRModel, prompt: str) -> Transcriber:
    transformers: Any = importlib.import_module("transformers")
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        model.hf_id, trust_remote_code=True
    )
    net = (
        transformers.AutoModel.from_pretrained(
            model.hf_id,
            trust_remote_code=True,
            use_safetensors=True,
            torch_dtype=_torch().bfloat16,
        )
        .eval()
        .cuda()
    )

    def transcribe(images: list[Image.Image]) -> list[str]:
        texts: list[str] = []
        for img in images:
            with tempfile.TemporaryDirectory() as tmp:
                image_file = Path(tmp) / "page.png"
                img.save(image_file)
                out = net.infer(
                    tokenizer,
                    prompt=prompt,
                    image_file=str(image_file),
                    output_path=tmp,
                    eval_mode=True,
                    **model.infer_kwargs,
                )
            texts.append(str(out or ""))
        return texts

    return transcribe


def _data_uri(img: Image.Image, max_side: int | None) -> str:
    if max_side and max(img.size) > max_side:
        img = img.copy()
        img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _vllm_chat_transcriber(model: OCRModel, prompt: str) -> Transcriber:
    vllm: Any = importlib.import_module("vllm")
    llm = vllm.LLM(
        model=model.hf_id,
        trust_remote_code=True,
        max_model_len=16384,
        limit_mm_per_prompt={"image": 1},
        gpu_memory_utilization=0.9,
    )
    params = vllm.SamplingParams(temperature=0.0, max_tokens=model.max_tokens)

    def transcribe(images: list[Image.Image]) -> list[str]:
        conversations = [
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": _data_uri(img, model.max_image_side)},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            for img in images
        ]
        outputs = llm.chat(conversations, params, use_tqdm=False)
        return [o.outputs[0].text for o in outputs]

    return transcribe


TRANSCRIBERS: dict[str, Callable[[OCRModel, str], Transcriber]] = {
    JINA_RUNTIME: _jina_transcriber,
    DEEPSEEK_INFER_RUNTIME: _deepseek_infer_transcriber,
    VLLM_CHAT_RUNTIME: _vllm_chat_transcriber,
}


def _load_page(item: tuple[int, str]) -> tuple[int, Image.Image | None]:
    p_num, path = item
    cropped, area = crop_and_measure_ink(Image.open(path).convert("RGB"))
    return p_num, cropped if area >= MIN_INK_AREA else None


def _load_batch(batch: list[tuple[int, str]]) -> list[tuple[int, Image.Image | None]]:
    return [_load_page(item) for item in batch]


def _shard_worker(
    shard_id: int,
    shard_items: list[tuple[int, str]],
    out_dir_str: str,
    prompt: str,
    model_key: str,
) -> int:
    model = ocr_model(model_key)
    out_dir = Path(out_dir_str)
    t0 = time.time()
    transcribe = TRANSCRIBERS[model.runtime](model, model.prompt_for(prompt))
    print(
        f"[Shard {shard_id}] {model.key} ready in {time.time() - t0:.1f}s for {len(shard_items)} pages.",
        flush=True,
    )
    size = VLLM_BATCH if model.batches_internally else 1
    batches = [shard_items[i : i + size] for i in range(0, len(shard_items), size)]
    completed = 0
    with ThreadPoolExecutor(max_workers=2) as pool:
        for loaded in pool.map(_load_batch, batches):
            inked = [(n, img) for n, img in loaded if img is not None]
            t_batch = time.time()
            texts = transcribe([img for _, img in inked]) if inked else []
            by_page = {
                n: model.clean(t) for (n, _), t in zip(inked, texts, strict=True)
            }
            for n, _ in loaded:
                _ = (out_dir / f"p_{n:03d}.md").write_text(
                    by_page.get(n, ""), encoding="utf-8"
                )
            completed += len(loaded)
            print(
                f"[Shard {shard_id}] Pages {loaded[0][0]:03d}-{loaded[-1][0]:03d} in {time.time() - t_batch:.1f}s",
                flush=True,
            )
    return completed


def page_items(
    pages_dir: Path, page_list: Sequence[int] | None = None
) -> list[tuple[int, str]]:
    """(page number, path) for each `*_NNN.png` render, limited to `page_list` when given."""
    items: list[tuple[int, str]] = []
    for path in sorted(pages_dir.glob("*.png")):
        if path.name.startswith("._"):
            continue
        try:
            n = int(path.stem.split("_")[-1])
        except ValueError:
            continue
        if page_list is None or n in page_list:
            items.append((n, str(path)))
    return items


def _gpu_summary() -> tuple[str, float]:
    torch = _torch()
    if not torch.cuda.is_available():
        return _device(), 0.0
    props = torch.cuda.get_device_properties(0)
    return props.name, props.total_memory / 2**30


def _is_pending(out_dir: Path, n: int) -> bool:
    out = out_dir / f"p_{n:03d}.md"
    return not out.exists() or out.stat().st_size < 15


def run_worker(
    pages_dir: Path,
    out_dir: Path,
    page_list: Sequence[int] | None = None,
    prompt: str = UNIVERSAL_TEX_PROMPT,
    num_shards: int = 1,
    model_key: str = DEFAULT_OCR_MODEL,
) -> None:
    model = ocr_model(model_key)
    out_dir.mkdir(parents=True, exist_ok=True)
    gpu_name, vram_gb = _gpu_summary()
    pending = [
        (n, p) for n, p in page_items(pages_dir, page_list) if _is_pending(out_dir, n)
    ]
    shards = min(
        model.copies_per_gpu(vram_gb, num_shards) if vram_gb else 1,
        max(1, len(pending)),
    )
    print(
        f"=== OCR WORKER: {model.key} on {gpu_name} ({vram_gb:.1f} GB) | "
        f"{shards} shard(s) | {len(pending)} pending pages ===",
        flush=True,
    )
    t0 = time.time()
    if pending:
        hub: Any = importlib.import_module("huggingface_hub")
        _ = hub.snapshot_download(model.hf_id)
    t_download = time.time() - t0
    if pending and shards == 1:
        _ = _shard_worker(1, pending, str(out_dir), prompt, model.key)
    elif pending:
        ctx = mp.get_context("spawn")
        procs = [
            ctx.Process(
                target=_shard_worker,
                args=(i + 1, pending[i::shards], str(out_dir), prompt, model.key),
            )
            for i in range(shards)
        ]
        for proc in procs:
            proc.start()
        for proc in procs:
            proc.join()
    t_transcribe = time.time() - t0 - t_download
    stats = {
        "model": model.key,
        "gpu": gpu_name,
        "vram_gb": round(vram_gb, 1),
        "shards": shards,
        "pages": len(pending),
        "download_sec": round(t_download, 1),
        "transcribe_sec": round(t_transcribe, 1),
        "pages_per_sec": round(len(pending) / t_transcribe, 3) if t_transcribe else 0.0,
    }
    _ = (out_dir / STATS_NAME).write_text(json.dumps(stats) + "\n", encoding="utf-8")
    print(f"Worker stats: {stats}", flush=True)
    _archive_output(out_dir)


def _archive_output(out_dir: Path) -> None:
    """Bundle the transcripts and stats into one archive for a single download."""
    tar_path = out_dir.parent / "markdown.tar.gz"
    files = [
        f for f in [*sorted(out_dir.glob("*.md")), out_dir / STATS_NAME] if f.exists()
    ]
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in files:
            tar.add(f, arcname=f.name)
    print(f"Packaged {len(files)} files into {tar_path}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Self-hosted OCR GPU worker")
    _ = parser.add_argument("--pages", type=str, default="/content/pages")
    _ = parser.add_argument("--out", type=str, default="/content/markdown")
    _ = parser.add_argument("--page-list", type=str, default="")
    _ = parser.add_argument("--shards", type=int, default=3)
    _ = parser.add_argument("--prompt-file", type=str, default="")
    _ = parser.add_argument("--model", type=str, default=DEFAULT_OCR_MODEL)
    args, _ = parser.parse_known_args()
    run_worker(
        Path(args.pages),
        Path(args.out),
        [int(x) for x in args.page_list.split(",") if x.strip()] or None,
        prompt=(
            Path(args.prompt_file).read_text(encoding="utf-8")
            if args.prompt_file
            else UNIVERSAL_TEX_PROMPT
        ),
        num_shards=args.shards,
        model_key=args.model,
    )
