import torch, logging, warnings
warnings.filterwarnings("ignore")
logging.getLogger("transformers_modules").setLevel(logging.ERROR)

from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor

print("Testing fixed transcription on page_067.png...")
processor = AutoProcessor.from_pretrained("jinaai/jina-ocr-v1", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("jinaai/jina-ocr-v1", torch_dtype=torch.bfloat16, trust_remote_code=True).to("cuda").eval()

img = Image.open("/content/pages/page_067.png").convert("RGB")
inp = processor.prepare_ocr_inputs(img, device="cuda")
with torch.inference_mode():
    out = model.generate(**inp, max_new_tokens=4096, do_sample=False)

# FIXED: No [0] slice!
text = processor.decode_ocr(out, inp["input_ids"])
print(f"SUCCESS! Output length: {len(text)} characters!")
print("--- PREVIEW OF TRANSCRIBED MARKDOWN ---")
print(text[:600])
