"""High-Throughput Multi-Shard G4 Blackwell Worker for Jina OCR v1 (Kodaira Complex Analysis).

Runs on Google Colab G4 (NVIDIA RTX PRO 6000 Blackwell 95GB VRAM):
1. Pre-warms HuggingFace cache once for jinaai/jina-ocr-v1.
2. Spawns N parallel GPU worker processes per G4 node (default 3 processes = ~20GB / 95GB VRAM)
   to saturate Blackwell Tensor Cores and memory bandwidth.
3. Uses content-aware margin auto-cropping and blank-page guard.
4. Produces faithful LaTeX-compatible Markdown for every page and bundles /content/markdown.tar.gz.
"""

import argparse
import logging
import multiprocessing as mp
import tarfile
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageOps

warnings.filterwarnings("ignore")
logging.getLogger("transformers_modules").setLevel(logging.ERROR)

KODAIRA_TEX_PROMPT = (
    "Transcribe this page from Kunihiko Kodaira's Complex Analysis textbook into clean, "
    "faithful TeX-compatible Markdown.\n"
    "Rules:\n"
    "1. Format all mathematical expressions in exact LaTeX syntax: inline $...$ and display $$...$$.\n"
    "2. Preserve all Greek letters, barred conjugates (\\bar{z}), integrals (\\int_\\gamma), "
    "sums, fractions, subscripts, superscripts, and homology/cohomology notation exactly.\n"
    "3. Format chapter, section, and subsection headings with Markdown (#, ##, ###).\n"
    "4. Bold theorem, lemma, definition, corollary, proposition, and remark headers "
    "(e.g. **Theorem 1.1.**, **Definition 1.5.**, **Lemma 2.3.**) and italicize *Proof.*\n"
    "5. Preserve exact equation numbers on display equations (e.g. $$ |zw|^2 = |z|^2 |w|^2 $$ (1.1)).\n"
    "6. When a figure caption appears (e.g. Fig. 1.1), output a standalone line `Fig. X.Y` at its exact position.\n"
    "7. Do not omit any prose, proofs, or exercises."
)


def auto_crop_margins(img: Image.Image, padding: int = 24) -> tuple[Image.Image, int]:
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


def shard_worker(
    shard_id: int,
    shard_items: list[tuple[int, str]],
    out_dir_str: str,
) -> int:
    import torch  # pyright: ignore[reportMissingImports]
    from transformers import (  # pyright: ignore[reportMissingImports]
        AutoModelForCausalLM,
        AutoProcessor,
    )

    out_dir = Path(out_dir_str)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True

    model_id = "jinaai/jina-ocr-v1"
    t0 = time.time()
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    model = (
        AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        )
        .to(device)
        .eval()
    )
    print(
        f"[Shard {shard_id}] Model loaded in {time.time() - t0:.2f}s for {len(shard_items)} pages.",
        flush=True,
    )

    def prefetch(item: tuple[int, str]):
        p_num, p_path_str = item
        raw_img = Image.open(p_path_str).convert("RGB")
        cropped_img, area = auto_crop_margins(raw_img)
        if area < 400:
            return p_num, None
        inp = processor.prepare_ocr_inputs(
            cropped_img, prompt=KODAIRA_TEX_PROMPT, device=device
        )
        return p_num, inp

    completed = 0
    pad_id = None
    tok = getattr(processor, "tokenizer", None)
    if tok is not None:
        pad_id = getattr(tok, "pad_token_id", None) or getattr(
            tok, "eos_token_id", None
        )

    with ThreadPoolExecutor(max_workers=2) as ex:
        for p_num, inp in ex.map(prefetch, shard_items):
            out_file = out_dir / f"p_{p_num:03d}.md"
            if inp is None:
                out_file.write_text("", encoding="utf-8")
                completed += 1
                continue
            t_page = time.time()
            with torch.inference_mode():
                gen_kwargs = {"max_new_tokens": 4096, "do_sample": False}
                if pad_id is not None:
                    gen_kwargs["pad_token_id"] = pad_id
                out = model.generate(**inp, **gen_kwargs)
            decoded = processor.decode_ocr(out, inp["input_ids"])
            text = decoded[0] if isinstance(decoded, list) else str(decoded)
            out_file.write_text(text, encoding="utf-8")
            completed += 1
            dur = time.time() - t_page
            print(
                f"[Shard {shard_id}] p_{p_num:03d} done in {dur:.2f}s ({len(text)} chars)",
                flush=True,
            )

    return completed


def run_node(pages_dir: Path, out_dir: Path, num_shards: int = 3) -> None:
    import torch  # pyright: ignore[reportMissingImports]
    from transformers import (  # pyright: ignore[reportMissingImports]
        AutoModelForCausalLM,
        AutoProcessor,
    )

    pages_dir = Path(pages_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    gpu_name = (
        torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    )
    vram_gb = (
        torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if torch.cuda.is_available()
        else 0.0
    )
    print(
        f"=== DUAL-G4 BLACKWELL MULTI-SHARD NODE ({gpu_name}, {vram_gb:.1f} GB VRAM, {num_shards} shards) ===",
        flush=True,
    )

    # Pre-warm HuggingFace cache in main process before spawning shards
    model_id = "jinaai/jina-ocr-v1"
    t_warm = time.time()
    _ = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    _ = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch.bfloat16, trust_remote_code=True
    )
    print(f"Pre-warmed HF model cache in {time.time() - t_warm:.2f}s.", flush=True)

    target_files = sorted(pages_dir.glob("*.png"))
    pending: list[tuple[int, str]] = []
    for p_path in target_files:
        if p_path.name.startswith("._"):
            continue
        stem = p_path.stem
        try:
            p_num = int(stem.split("_")[-1])
        except ValueError:
            continue
        out_f = out_dir / f"p_{p_num:03d}.md"
        if not out_f.exists() or out_f.stat().st_size < 15:
            pending.append((p_num, str(p_path)))

    print(f"Total pending pages on this G4 node: {len(pending)}", flush=True)
    if not pending:
        _bundle_archive(out_dir)
        return

    actual_shards = min(num_shards, len(pending))
    shards: list[list[tuple[int, str]]] = [
        pending[i::actual_shards] for i in range(actual_shards)
    ]

    t_start = time.time()
    ctx = mp.get_context("spawn")
    procs: list[mp.Process] = []
    for idx, s_items in enumerate(shards):
        p = ctx.Process(
            target=shard_worker, args=(idx + 1, s_items, str(out_dir))
        )
        p.start()
        procs.append(p)

    for p in procs:
        p.join()

    elapsed = time.time() - t_start
    done_files = list(out_dir.glob("p_*.md"))
    print(
        f"Node completed {len(done_files)} pages in {elapsed:.2f}s ({len(done_files) / max(elapsed, 0.1):.2f} pages/s)!",
        flush=True,
    )
    _bundle_archive(out_dir)


def _bundle_archive(out_dir: Path) -> None:
    tar_path = out_dir.parent / "markdown.tar.gz"
    md_files = sorted(out_dir.glob("p_*.md"))
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in md_files:
            tar.add(f, arcname=f.name)
    print(
        f"Packaged {len(md_files)} markdown files into {tar_path} ({tar_path.stat().st_size / 1024:.1f} KB)",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=str, default="/content/pages")
    parser.add_argument("--out", type=str, default="/content/markdown")
    parser.add_argument("--shards", type=int, default=3)
    args, _ = parser.parse_known_args()
    run_node(Path(args.pages), Path(args.out), num_shards=args.shards)
