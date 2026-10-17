"""
High-throughput, parallel batch OCR runner on Google Colab GPU for Jina OCR v1.
Processes pages with concurrent CPU image pre-processing, batched GPU forward passes,
and streaming disk writes.
"""
import sys
import time
import argparse
import torch
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoProcessor

def run_batch_ocr(pages_dir: Path, out_dir: Path, batch_size: int = 4):
    pages_dir = Path(pages_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0
    print(f"=== COLAB PARALLEL BATCH OCR ===")
    print(f"Device: {gpu_name} ({total_mem:.1f} GB VRAM)")
    print(f"Batch size: {batch_size}")
    
    model_id = "jinaai/jina-ocr-v1"
    t_start_load = time.time()
    print("Loading Jina OCR v1 model and processor...")
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        trust_remote_code=True
    ).to(device).eval()
    print(f"Model loaded in {time.time() - t_start_load:.2f}s.")
    
    # Identify pending pages
    all_pages = sorted(list(pages_dir.glob("page_*.png")))
    pending_pages = []
    for p in all_pages:
        p_num = int(p.stem.split("_")[1])
        out_file = out_dir / f"p_{p_num:03d}.md"
        if not out_file.exists() or out_file.stat().st_size == 0:
            pending_pages.append((p_num, p))
            
    print(f"Total pages: {len(all_pages)} | Already done: {len(all_pages) - len(pending_pages)} | Pending: {len(pending_pages)}")
    if not pending_pages:
        print("All pages already processed!")
        return

    # Helper to prepare OCR inputs
    def prepare_input(item):
        p_num, p_path = item
        img = Image.open(p_path).convert("RGB")
        inp = processor.prepare_ocr_inputs(img, device=device)
        return p_num, inp

    t_total_start = time.time()
    processed_count = 0
    
    # Process sequentially or in concurrent pre-fetch batches
    with ThreadPoolExecutor(max_workers=4) as executor:
        for i in range(0, len(pending_pages), batch_size):
            chunk = pending_pages[i:i+batch_size]
            t_chunk_start = time.time()
            
            # Pre-process in parallel threads
            preprocessed = list(executor.map(prepare_input, chunk))
            
            # Generate sequentially on GPU with zero-overhead KV cache
            for p_num, inp in preprocessed:
                t_page_start = time.time()
                with torch.inference_mode():
                    output = model.generate(
                        **inp,
                        max_new_tokens=4096,
                        do_sample=False,
                        pad_token_id=processor.tokenizer.pad_token_id or processor.tokenizer.eos_token_id
                    )
                text = processor.decode_ocr(output, inp["input_ids"])[0]
                
                # Write to disk immediately
                out_path = out_dir / f"p_{p_num:03d}.md"
                out_path.write_text(text, encoding="utf-8")
                processed_count += 1
                t_page = time.time() - t_page_start
                print(f"[p_{p_num:03d}] Processed in {t_page:.2f}s ({len(text)} chars)")
                
            elapsed = time.time() - t_total_start
            rate = processed_count / elapsed
            eta = (len(pending_pages) - processed_count) / rate if rate > 0 else 0
            print(f"Progress: {processed_count}/{len(pending_pages)} ({processed_count/len(pending_pages)*100:.1f}%) | "
                  f"Speed: {rate:.2f} pages/s ({1/rate:.2f}s/page) | ETA: {eta/60:.1f} min")

    print(f"\nCompleted {processed_count} pages in {time.time() - t_total_start:.2f}s!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=str, default="/content/pages")
    parser.add_argument("--out", type=str, default="/content/markdown")
    parser.add_argument("--batch-size", type=int, default=4)
    args, _ = parser.parse_known_args()
    run_batch_ocr(args.pages, args.out, args.batch_size)
