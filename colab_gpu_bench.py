import time
import torch
from pathlib import Path
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor

print(f"Device: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")

model_id = "jinaai/jina-ocr-v1"
t0 = time.time()
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
    trust_remote_code=True
).to("cuda").eval()
t_load = time.time() - t0
print(f"Model load time: {t_load:.2f}s")

# Test pages
test_imgs = list(Path("/content/pages").glob("*.png"))[:4]
print(f"Benchmarking with {len(test_imgs)} pages...")

# Sequential benchmark
t_seq_start = time.time()
for img_path in test_imgs:
    image = Image.open(img_path).convert("RGB")
    messages = [{"role": "user", "content": [
        {"type": "text", "text": "Transcribe this document to Markdown with exact LaTeX formulas."},
        {"type": "image_url", "image_url": {"url": f"file://{img_path}"}}
    ]}]
    inputs = processor.prepare_ocr_inputs(image, device="cuda")
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=4096, do_sample=False)
    text = processor.decode_ocr(output, inputs["input_ids"])[0]
t_seq = time.time() - t_seq_start
print(f"Sequential 4 pages: {t_seq:.2f}s ({t_seq/len(test_imgs):.2f}s/page, {len(test_imgs)/t_seq:.2f} pages/s)")
