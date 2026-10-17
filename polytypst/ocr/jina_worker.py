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
    "7. For diagrams and figures, transcribe any caption or figure title (e.g. FIG. 1, Figure 2) and preserve natural reading order.\n"
    "8. Preserve all body text, notes, and references without omitting content."
)


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


def run_worker(
    pages_dir: Path,
    out_dir: Path,
    page_list: list[int] | None = None,
    prompt: str = UNIVERSAL_TEX_PROMPT,
):
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
    print("=== JINA OCR V1 ACCELERATED WORKER ===")
    print(f"Hardware: {gpu_name} ({vram_gb:.1f} GB VRAM)")

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True

    model_id = "jinaai/jina-ocr-v1"
    t0 = time.time()
    print("Loading Jina OCR v1 model and tokenizer...")
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=dtype,
        trust_remote_code=True,
    ).to(device).eval()
    print(f"Model ready in {time.time() - t0:.2f}s.")

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

    pending: list[tuple[int, Path]] = []
    for p_path in target_files:
        stem = p_path.stem
        parts = stem.split("_")
        try:
            p_num = int(parts[-1])
        except ValueError:
            p_num = len(pending) + 1

        out_f = out_dir / f"p_{p_num:03d}.md"
        if not out_f.exists() or out_f.stat().st_size < 30:
            pending.append((p_num, p_path))

    print(f"Pending pages for this worker: {len(pending)}")
    if not pending:
        print("All pages already processed.")
        _archive_output(out_dir)
        return

    def prefetch(item: tuple[int, Path]):
        p_num, p_path = item
        raw_img = Image.open(p_path).convert("RGB")
        cropped_img = auto_crop_margins(raw_img)
        inp = processor.prepare_ocr_inputs(cropped_img, prompt=prompt, device=device)
        return p_num, inp

    t_all = time.time()
    completed = 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        for p_num, inp in executor.map(prefetch, pending):
            t_page = time.time()
            with torch.inference_mode():
                pad_id = None
                tok = getattr(processor, "tokenizer", None)
                if tok is not None:
                    pad_id = getattr(tok, "pad_token_id", None) or getattr(tok, "eos_token_id", None)
                gen_kwargs = {"max_new_tokens": 4096, "do_sample": False}
                if pad_id is not None:
                    gen_kwargs["pad_token_id"] = pad_id
                out = model.generate(**inp, **gen_kwargs)
            decoded = processor.decode_ocr(out, inp["input_ids"])
            text = decoded[0] if isinstance(decoded, list) else str(decoded)

            out_file = out_dir / f"p_{p_num:03d}.md"
            out_file.write_text(text, encoding="utf-8")
            completed += 1
            dur = time.time() - t_page
            print(f"[Worker] Page {p_num:03d} transcribed in {dur:.2f}s ({len(text)} chars)")

    elapsed = time.time() - t_all
    rate = completed / elapsed if elapsed > 0 else 0
    print(f"\nWorker finished {completed} pages in {elapsed:.2f}s ({rate:.2f} pages/s)!")
    _archive_output(out_dir)


def _archive_output(out_dir: Path):
    """Bundle all generated markdown files into an archive for rapid download."""
    tar_path = out_dir.parent / "markdown.tar.gz"
    md_files = sorted(out_dir.glob("*.md"))
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in md_files:
            tar.add(f, arcname=f.name)
    print(f"Packaged {len(md_files)} markdown files into {tar_path} ({tar_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jina OCR v1 GPU Worker")
    parser.add_argument("--pages", type=str, default="/content/pages")
    parser.add_argument("--out", type=str, default="/content/markdown")
    parser.add_argument("--page-list", type=str, default="")
    args, _ = parser.parse_known_args()

    pages = [int(x.strip()) for x in args.page_list.split(",") if x.strip()] if args.page_list else None
    run_worker(Path(args.pages), Path(args.out), pages)
