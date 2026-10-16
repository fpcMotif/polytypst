"""Transcribe remaining pages using official Jina AI OCR API with rate-limiting and auto-resume."""

import os
import time
import base64
import httpx
from pathlib import Path

# Load JINA_API_KEY from mise.local.toml or environment
key = os.environ.get("JINA_API_KEY")
if not key:
    with open("mise.local.toml") as f:
        for line in f:
            if line.startswith("JINA_API_KEY") and "=" in line:
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

if not key:
    raise ValueError("JINA_API_KEY not found in mise.local.toml or environment.")

out_dir = Path("output/serre_markdown")
out_dir.mkdir(parents=True, exist_ok=True)

img_dir = Path("output/serre_split")
all_imgs = sorted(img_dir.glob("p_*.png"))

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

print(f"Jina AI API Runner: Checking {len(all_imgs)} pages...")

to_process = []
for img_p in all_imgs:
    md_p = out_dir / f"{img_p.stem}.md"
    if not md_p.exists() or md_p.stat().st_size < 30:
        to_process.append(img_p)

print(f"Found {len(to_process)} pages needing transcription.")

with httpx.Client(headers=headers, timeout=60.0) as client:
    for idx, img_p in enumerate(to_process, 1):
        md_p = out_dir / f"{img_p.stem}.md"

        with open(img_p, "rb") as fp:
            b64 = base64.b64encode(fp.read()).decode("ascii")

        payload = {
            "model": "jina-ocr-v1",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe this document into clean Markdown format with LaTeX math."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]
            }]
        }

        retries = 5
        backoff = 2.0
        success = False

        while retries > 0:
            t0 = time.time()
            try:
                resp = client.post("https://api.jina.ai/v1/chat/completions", json=payload)
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"]
                    with open(md_p, "w", encoding="utf-8") as out_fp:
                        out_fp.write(text)
                    print(f"[{idx:03d}/{len(to_process)}] {img_p.name} done in {time.time()-t0:.1f}s ({len(text)} chars)")
                    success = True
                    break
                elif resp.status_code == 429:
                    print(f"  Rate limited on {img_p.name}, waiting {backoff:.1f}s...")
                    time.sleep(backoff)
                    backoff *= 1.5
                    retries -= 1
                else:
                    print(f"  Error {resp.status_code} on {img_p.name}: {resp.text[:100]}")
                    time.sleep(2.0)
                    retries -= 1
            except Exception as e:
                print(f"  Exception on {img_p.name}: {e}")
                time.sleep(3.0)
                retries -= 1

        # Gentle throttle between requests
        time.sleep(1.5)

print("\nAll missing pages transcribed via Jina AI API!")
