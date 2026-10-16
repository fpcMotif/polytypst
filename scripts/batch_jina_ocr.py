import os
import glob
import zipfile
import time
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

# 1. Unzip pages
pages_dir = Path("/content/serre_pages")
out_dir = Path("/content/serre_md")
pages_dir.mkdir(parents=True, exist_ok=True)
out_dir.mkdir(parents=True, exist_ok=True)

zip_path = Path("/content/serre_pages.zip")
if zip_path.exists():
    print(f"Unzipping {zip_path}...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(pages_dir)
    print(f"Extracted {len(list(pages_dir.glob('*.png')))} pages.")

# 2. Load model
model_id = "jinaai/jina-ocr-v1"
print(f"Loading {model_id} on GPU...")
t0 = time.time()
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    trust_remote_code=True
).to("cuda")
print(f"Model ready in {time.time() - t0:.2f}s")

# 3. Process all pages
page_files = sorted(pages_dir.glob("p_*.png"))
total = len(page_files)
print(f"Starting batch OCR on {total} pages...")

start_time = time.time()
processed_count = 0

for idx, p_file in enumerate(page_files, 1):
    md_file = out_dir / f"{p_file.stem}.md"
    if md_file.exists() and md_file.stat().st_size > 50:
        continue

    try:
        image = Image.open(p_file).convert("RGB")
        inputs = processor.prepare_ocr_inputs(image, device="cuda")
        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=2048,
                do_sample=False
            )
        text = processor.decode_ocr(output, inputs["input_ids"])
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(text)
        processed_count += 1
    except Exception as e:
        print(f"Error on {p_file.name}: {e}")

    if idx % 10 == 0 or idx == total:
        elapsed = time.time() - start_time
        rate = elapsed / max(1, processed_count)
        rem = (total - idx) * rate
        print(f"[{idx}/{total}] Processed {processed_count} pages ({rate:.1f}s/page). Est. remaining: {rem/60:.1f} min.")

# 4. Zip results
out_zip = Path("/content/serre_markdown.zip")
with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(out_dir.glob("*.md")):
        z.write(f, arcname=f.name)

print(f"\nAll {total} pages processed! Saved to {out_zip} ({out_zip.stat().st_size / 1024:.1f} KB)")
