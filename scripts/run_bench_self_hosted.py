import os
import time
import zipfile
import json
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

pages_dir = Path("/content/bench_pages")
out_dir = Path("/content/bench_self_hosted")
pages_dir.mkdir(parents=True, exist_ok=True)
out_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile("/content/bench_10.zip", "r") as z:
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

bench_pages = [10, 24, 38, 55, 75, 95, 115, 135, 155, 175]
results = {}

# Warmup
warmup_img = Image.open(pages_dir / "p_010.png").convert("RGB")
w_in = processor.prepare_ocr_inputs(warmup_img, device="cuda")
with torch.inference_mode():
    _ = model.generate(**w_in, max_new_tokens=64, do_sample=False)
print("GPU warmup complete.")

print("=== Running Benchmark: Self-Hosted on A100 GPU ===")

for pno in bench_pages:
    img_p = pages_dir / f"p_{pno:03d}.png"
    img = Image.open(img_p).convert("RGB")
    inputs = processor.prepare_ocr_inputs(img, device="cuda")

    t_start = time.time()
    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=False
        )
    text = processor.decode_ocr(output, inputs["input_ids"])
    lat = time.time() - t_start

    (out_dir / f"p_{pno:03d}.md").write_text(text, encoding="utf-8")
    results[pno] = {
        "status": "success",
        "latency_sec": round(lat, 2),
        "char_count": len(text)
    }
    print(f"Page {pno:03d}: {lat:.2f}s | {len(text)} chars")

with open(out_dir / "bench_self_hosted_meta.json", "w") as fp:
    json.dump(results, fp, indent=2)

# Zip output
with zipfile.ZipFile("/content/bench_self_hosted.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(out_dir.glob("*.*")):
        z.write(f, arcname=f.name)

print("Self-hosted A100 benchmark complete.")
