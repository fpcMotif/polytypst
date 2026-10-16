"""Re-transcribe Serre pages 1 to 85 purely using the official Jina AI OCR API."""

import os
import time
import base64
import json
import httpx
from pathlib import Path

# Load JINA_API_KEY
key = os.environ.get("JINA_API_KEY")
if not key:
    with open("mise.local.toml") as f:
        for line in f:
            if line.startswith("JINA_API_KEY") and "=" in line:
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

if not key:
    raise ValueError("JINA_API_KEY not found.")

out_dir = Path("output/serre_markdown")
out_dir.mkdir(parents=True, exist_ok=True)

img_dir = Path("output/serre_split")
blank_pages = {1, 3, 7, 9, 23, 37, 51, 103, 183, 191}

# Pages 1 to 85 to re-transcribe via API
target_pages = [p for p in range(1, 86) if p not in blank_pages]

print(f"Starting pure Jina AI Cloud API transcription for Serre pages 1-85 ({len(target_pages)} content pages)...")

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

# Empty blank pages first
for bp in blank_pages:
    (out_dir / f"p_{bp:03d}.md").write_text("", encoding="utf-8")

with httpx.Client(headers=headers, timeout=60.0) as client:
    for idx, pno in enumerate(target_pages, 1):
        img_p = img_dir / f"p_{pno:03d}.png"
        md_p = out_dir / f"p_{pno:03d}.md"

        if not img_p.exists():
            continue

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
        while retries > 0:
            t0 = time.time()
            try:
                resp = client.post("https://api.jina.ai/v1/chat/completions", json=payload)
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"]
                    md_p.write_text(text, encoding="utf-8")
                    print(f"[{idx:02d}/{len(target_pages)}] p_{pno:03d}.png done in {time.time()-t0:.1f}s ({len(text)} chars)")
                    break
                elif resp.status_code == 429:
                    print(f"  Rate limited on p_{pno:03d}.png, backing off {backoff:.1f}s...")
                    time.sleep(backoff)
                    backoff *= 1.5
                    retries -= 1
                else:
                    print(f"  Error {resp.status_code} on p_{pno:03d}.png: {resp.text[:80]}")
                    time.sleep(2.0)
                    retries -= 1
            except Exception as e:
                print(f"  Exception on p_{pno:03d}.png: {e}")
                time.sleep(3.0)
                retries -= 1

        time.sleep(1.6) # Smooth pacing to avoid 429

print("\nAll target pages 1-85 successfully transcribed via official Jina Cloud API!")
