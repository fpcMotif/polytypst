"""Self-contained GPU worker script for Jina OCR v1 inference.

Designed for Google Colab Blackwell / G4 / L4 / T4 instances or local CUDA.
Features:
1. Dynamic scanned page margin auto-cropping (strips scan borders & empty margins).
2. High-fidelity TeX-compatible Markdown prompt for any domain (math, physics, econ, etc.).
3. Pipelined CPU image pre-fetching with GPU inference.
4. Robust output streaming and archive bundling.
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


def crop_and_measure_ink(img: Image.Image, padding: int = 24) -> tuple[Image.Image, int]:
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


def auto_crop_margins(img: Image.Image, padding: int = 25) -> Image.Image:
    """Smart algorithmic crop: remove outer scanned book borders and black scanner gutters."""
    gray = img.convert("L")
    inverted = ImageOps.invert(gray)
    bbox = inverted.getbbox()
    if not bbox:
        return img
    w, h = img.size
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(w, bbox[2] + padding)
    bottom = min(h, bbox[3] + padding)
    return img.crop((left, top, right, bottom))


def _shard_worker(
    shard_id: int,
    shard_items: list[tuple[int, str]],
    out_dir_str: str,
    prompt: str,
) -> int:
    import torch  # pyright: ignore[reportMissingImports]
    from transformers import (  # pyright: ignore[reportMissingImports]
        AutoModelForCausalLM,
        AutoProcessor,
    )

    out_dir = Path(out_dir_str)
    device = (
        "cuda"
        if torch.cuda.is_available()
        else ("mps" if torch.backends.mps.is_available() else "cpu")
    )
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True

    model_id = "jinaai/jina-ocr-v1"
    t0 = time.time()
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    dtype = (
        torch.bfloat16
        if (torch.cuda.is_available() and torch.cuda.is_bf16_supported())
        else torch.float16
    )
    model = (
        AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=dtype,
            trust_remote_code=True,
        )
        .to(device)
        .eval()
    )
    print(
        f"[Shard {shard_id}] Model ready in {time.time() - t0:.2f}s for {len(shard_items)} pages.",
        flush=True,
    )

    def prefetch(item: tuple[int, str]) -> tuple[int, dict[str, object] | None]:
        p_num, p_path_str = item
        raw_img = Image.open(p_path_str).convert("RGB")
        cropped_img, area = crop_and_measure_ink(raw_img)
        if area < 400:
            return p_num, None
        inp = processor.prepare_ocr_inputs(cropped_img, prompt=prompt, device=device)
        return p_num, inp

    completed = 0
    pad_id = None
    tok = getattr(processor, "tokenizer", None)
    if tok is not None:
        pad_id = getattr(tok, "pad_token_id", None) or getattr(
            tok, "eos_token_id", None
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        for p_num, inp in executor.map(prefetch, shard_items):
            out_file = out_dir / f"p_{p_num:03d}.md"
            if inp is None:
                _ = out_file.write_text("", encoding="utf-8")
                completed += 1
                continue
            t_page = time.time()
            with torch.inference_mode():
                gen_kwargs: dict[str, object] = {
                    "max_new_tokens": 4096,
                    "do_sample": False,
                }
                if pad_id is not None:
                    gen_kwargs["pad_token_id"] = pad_id
                out = model.generate(**inp, **gen_kwargs)
            decoded = processor.decode_ocr(out, inp["input_ids"])
            text = decoded[0] if isinstance(decoded, list) else str(decoded)
            _ = out_file.write_text(text, encoding="utf-8")
            completed += 1
            dur = time.time() - t_page
            print(
                f"[Shard {shard_id}] Page {p_num:03d} transcribed in {dur:.2f}s ({len(text)} chars)",
                flush=True,
            )

    return completed


def run_worker(
    pages_dir: Path,
    out_dir: Path,
    page_list: list[int] | None = None,
    prompt: str = UNIVERSAL_TEX_PROMPT,
    num_shards: int = 1,
) -> None:
    import torch  # pyright: ignore[reportMissingImports]
    from transformers import (  # pyright: ignore[reportMissingImports]
        AutoModelForCausalLM,
        AutoProcessor,
    )

    pages_dir = Path(pages_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else device
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0
    print("=== JINA OCR V1 ACCELERATED WORKER ===", flush=True)
    print(f"Hardware: {gpu_name} ({vram_gb:.1f} GB VRAM) | Shards: {num_shards}", flush=True)

    # Target pages
    if page_list:
        target_files: list[Path] = []
        for p in page_list:
            cand = list(pages_dir.glob(f"*_{p:03d}.png")) or list(pages_dir.glob(f"*_{p}.png"))
            if cand:
                target_files.append(cand[0])
            else:
                p_direct = pages_dir / f"p_{p:03d}.png"
                if p_direct.exists():
                    target_files.append(p_direct)
    else:
        target_files = sorted(pages_dir.glob("*.png"))

    pending: list[tuple[int, str]] = []
    for p_path in target_files:
        if p_path.name.startswith("._"):
            continue
        stem = p_path.stem
        parts = stem.split("_")
        try:
            p_num = int(parts[-1])
        except ValueError:
            p_num = len(pending) + 1

        out_f = out_dir / f"p_{p_num:03d}.md"
        if not out_f.exists() or out_f.stat().st_size < 15:
            pending.append((p_num, str(p_path)))

    print(f"Pending pages for this worker: {len(pending)}", flush=True)
    if not pending:
        print("All pages already processed.", flush=True)
        _archive_output(out_dir)
        return

    actual_shards = min(max(1, num_shards), len(pending))
    if actual_shards == 1:
        t_all = time.time()
        completed = _shard_worker(1, pending, str(out_dir), prompt)
        elapsed = time.time() - t_all
        rate = completed / elapsed if elapsed > 0 else 0.0
        print(f"\nWorker finished {completed} pages in {elapsed:.2f}s ({rate:.2f} pages/s)!", flush=True)
        _archive_output(out_dir)
        return

    model_id = "jinaai/jina-ocr-v1"
    t0 = time.time()
    print("Loading Jina OCR v1 model and tokenizer...", flush=True)
    _ = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float16
    _ = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=dtype,
        trust_remote_code=True,
    )
    print(f"Model ready in {time.time() - t0:.2f}s.", flush=True)

    shards: list[list[tuple[int, str]]] = [
        pending[i::actual_shards] for i in range(actual_shards)
    ]
    t_all = time.time()
    ctx = mp.get_context("spawn")
    procs: list[mp.Process] = []
    for idx, s_items in enumerate(shards):
        proc = ctx.Process(
            target=_shard_worker,
            args=(idx + 1, s_items, str(out_dir), prompt),
        )
        proc.start()
        procs.append(proc)

    for proc in procs:
        proc.join()

    elapsed = time.time() - t_all
    completed = len(list(out_dir.glob("p_*.md")))
    rate = completed / elapsed if elapsed > 0 else 0.0
    print(f"\nWorker finished {completed} pages in {elapsed:.2f}s ({rate:.2f} pages/s)!", flush=True)
    _archive_output(out_dir)


def _archive_output(out_dir: Path) -> None:
    """Bundle all generated markdown files into an archive for rapid download."""
    tar_path = out_dir.parent / "markdown.tar.gz"
    md_files = sorted(out_dir.glob("*.md"))
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in md_files:
            tar.add(f, arcname=f.name)
    print(f"Packaged {len(md_files)} markdown files into {tar_path} ({tar_path.stat().st_size / 1024:.1f} KB)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jina OCR v1 GPU Worker")
    parser.add_argument("--pages", type=str, default="/content/pages")
    parser.add_argument("--out", type=str, default="/content/markdown")
    parser.add_argument("--page-list", type=str, default="")
    parser.add_argument("--shards", type=int, default=3)
    args, _ = parser.parse_known_args()

    pages = [int(x.strip()) for x in args.page_list.split(",") if x.strip()] if args.page_list else None
    run_worker(Path(args.pages), Path(args.out), pages, num_shards=args.shards)
