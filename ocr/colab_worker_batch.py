"""Batch OCR Worker running on Google Colab A100 GPU for Lars Ahlfors Complex Analysis."""

import glob
import os
import sys
import time
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

print(f"=== COLAB A100 JINA OCR BATCH WORKER ===")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise RuntimeError("CUDA is not available on this runtime!")

print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f} GB")

# Create output directory
out_md_dir = Path("/content/markdown")
out_md_dir.mkdir(parents=True, exist_ok=True)

# Find all page images
images = sorted(glob.glob("/content/pages/page_*.png"))
# Filter out Mac dot-underscore metadata files
images = [img for img in images if not os.path.basename(img).startswith("._")]
print(f"Found {len(images)} page images to transcribe.")

# Load model
MODEL_ID = "jinaai/jina-ocr-v1"
print(f"Loading {MODEL_ID} in bfloat16 onto A100...")
t0 = time.time()
processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
model = (
    AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    .to("cuda")
    .eval()
)
print(f"Model loaded onto A100 in {time.time() - t0:.1f}s.")

# Process key pages or whole book
total_processed = 0
start_time = time.time()

for idx, img_path in enumerate(images):
    p_name = os.path.splitext(os.path.basename(img_path))[0]
    # e.g. page_017 -> p_017.md
    out_file = out_md_dir / f"p_{p_name.split('_')[-1]}.md"

    # Skip if already transcribed
    if out_file.exists() and out_file.stat().st_size > 10:
        continue

    try:
        t_page = time.time()
        with Image.open(img_path) as img:
            image_rgb = img.convert("RGB")
            inputs = processor.prepare_ocr_inputs(image_rgb, device="cuda")

        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=2048,
                do_sample=False
            )

        md_text = processor.decode_ocr(output, inputs["input_ids"])
        out_file.write_text(md_text, encoding="utf-8")
        total_processed += 1

        dt = time.time() - t_page
        if total_processed % 5 == 0 or total_processed <= 5:
            print(f"  [{idx+1:03d}/{len(images)}] {p_name} -> {out_file.name} ({len(md_text)} chars in {dt:.2f}s)")

    except Exception as e:
        print(f"  [ERROR] {img_path}: {e}")

elapsed = time.time() - start_time
print(f"\nCompleted {total_processed} pages in {elapsed:.1f}s (avg {elapsed/max(1, total_processed):.2f}s/page)!")

# Create archive
archive_path = Path("/content/ahlfors_jina_md.tar.gz")
import subprocess
subprocess.check_call(["tar", "-czf", str(archive_path), "-C", "/content", "markdown"])
print(f"Created archive: {archive_path} ({archive_path.stat().st_size / 1024:.1f} KB)")
