import torch
from transformers import AutoModelForCausalLM, AutoProcessor
from PIL import Image
import time

model_id = "jinaai/jina-ocr-v1"
print(f"Loading {model_id} onto GPU...")
t0 = time.time()
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    trust_remote_code=True
).to("cuda")
t1 = time.time()
print(f"Model loaded in {t1 - t0:.2f}s")

image = Image.open("/content/p_010.png").convert("RGB")
inputs = processor.prepare_ocr_inputs(image, device="cuda")

t2 = time.time()
with torch.inference_mode():
    output = model.generate(
        **inputs,
        max_new_tokens=2048,
        do_sample=False,
    )
text = processor.decode_ocr(output, inputs["input_ids"])
t3 = time.time()
print(f"Inference completed in {t3 - t2:.2f}s")
print("\n=== JINA OCR V1 RESULT ===")
print(text)
