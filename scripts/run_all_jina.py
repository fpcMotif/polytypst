import os
import glob
import time
import zipfile
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

pages_dir = Path("/content/serre_pages")
out_dir = Path("/content/serre_md")
pages_dir.mkdir(parents=True, exist_ok=True)
out_dir.mkdir(parents=True, exist_ok=True)

zip_path = Path("/content/serre_pages.zip")
if not (pages_dir / "p_010.png").exists() and zip_path.exists():
    print("Extracting pages from zip...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(pages_dir)

model_id = "jinaai/jina-ocr-v1"
print(f"Loading {model_id} on A100 SXM4 (bfloat16)...")
t0 = time.time()
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
).to("cuda")
print(f"Model loaded in {time.time() - t0:.2f}s!")

page_files = sorted(pages_dir.glob("p_*.png"))
total = len(page_files)
print(f"Starting batch transcription for all {total} pages...")

start_total = time.time()
processed = 0

for idx, p_file in enumerate(page_files, 1):
    md_file = out_dir / f"{p_file.stem}.md"
    if md_file.exists() and md_file.stat().st_size > 30:
        continue

    t_page = time.time()
    try:
        img = Image.open(p_file).convert("RGB")
        inputs = processor.prepare_ocr_inputs(img, device="cuda")
        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=1500,
                do_sample=False
            )
        text = processor.decode_ocr(output, inputs["input_ids"])
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(text)
        processed += 1
        elapsed_p = time.time() - t_page
        print(f"[{idx:03d}/{total}] {p_file.name}: {elapsed_p:.1f}s ({len(text)} chars)")
    except Exception as e:
        print(f"[{idx:03d}/{total}] Error on {p_file.name}: {e}")

    # Intermediate zip every 25 pages
    if idx % 25 == 0 or idx == total:
        out_zip = Path("/content/serre_markdown.zip")
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out_dir.glob("*.md")):
                z.write(f, arcname=f.name)
        print(f"--> Checkpoint saved to {out_zip} ({len(list(out_dir.glob('*.md')))} pages completed)")

print(f"\nAll done! Total time: {time.time() - start_total:.1f}s.")
