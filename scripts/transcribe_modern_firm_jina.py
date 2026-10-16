"""Batch transcription for John Roberts' The Modern Firm using Jina OCR API with automatic fallback."""

import os
import sys
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
    raise ValueError("JINA_API_KEY not found in mise.local.toml.")

out_dir = Path("output/modern_firm_jina/markdown")
out_dir.mkdir(parents=True, exist_ok=True)

img_dir = Path("page_renders")
all_imgs = sorted(img_dir.glob("p_*.png"))

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

print(f"Starting Jina OCR API transcription for {len(all_imgs)} pages of John Roberts' The Modern Firm...")

to_process = []
for p in all_imgs:
    md_p = out_dir / f"{p.stem}.md"
    if not md_p.exists() or md_p.stat().st_size < 30:
        to_process.append(p)

print(f"Pages to transcribe: {len(to_process)} / {len(all_imgs)}")

consecutive_failures = 0
MAX_FAILURES_BEFORE_COLAB = 5

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
                    {"type": "text", "text": "Transcribe this Chinese academic book page into clean Markdown format with natural reading order and LaTeX math."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]
            }]
        }

        retries = 4
        backoff = 2.0
        success = False

        while retries > 0:
            t0 = time.time()
            try:
                resp = client.post("https://api.jina.ai/v1/chat/completions", json=payload)
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"]
                    md_p.write_text(text, encoding="utf-8")
                    dur = time.time() - t0
                    print(f"[{idx:03d}/{len(to_process)}] {img_p.name} done in {dur:.1f}s ({len(text)} chars)")
                    success = True
                    consecutive_failures = 0
                    break
                elif resp.status_code == 429:
                    print(f"  [Rate limited on {img_p.name}] Backing off {backoff:.1f}s...")
                    time.sleep(backoff)
                    backoff *= 1.5
                    retries -= 1
                else:
                    print(f"  [HTTP {resp.status_code} on {img_p.name}]: {resp.text[:80]}")
                    time.sleep(2.0)
                    retries -= 1
            except Exception as e:
                print(f"  [Exception on {img_p.name}]: {e}")
                time.sleep(3.0)
                retries -= 1

        if not success:
            consecutive_failures += 1
            print(f"Failed to transcribe {img_p.name} after retries.")
            if consecutive_failures >= MAX_FAILURES_BEFORE_COLAB:
                print(f"CRITICAL: {consecutive_failures} consecutive API failures. Triggering Colab fallback...")
                sys.exit(42)

        # Smooth pacing between calls
        time.sleep(1.2)

print("\nAll pages successfully transcribed via Jina AI Cloud API!")
