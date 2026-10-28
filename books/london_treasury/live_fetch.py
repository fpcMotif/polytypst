# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright", "trafilatura"]
# ///
"""Replace London Treasury article caches with the article text of the live page.

Usage: uv run books/london_treasury/live_fetch.py CACHE [INDEX ...]

CACHE is the book's articles_cache folder, `articles_cache` in its output folder.

r.jina.ai misses the body of some pages. This script starts a headless Chrome,
drives it over CDP, and stores trafilatura's Markdown in articles_cache/link_NN.json.
"""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import trafilatura
from playwright.sync_api import sync_playwright

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LIVE_ARTICLES = (39,)
PORT = 9333


def fetch(cache: Path, indices: list[int]) -> None:
    profile = tempfile.mkdtemp(prefix="london-cdp-")
    chrome = subprocess.Popen(
        [CHROME, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
         "--no-first-run", "--no-default-browser-check", "about:blank"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(2.5)
        with sync_playwright() as pw:
            context = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}").contexts[0]
            for idx in indices:
                path = cache / f"link_{idx:02d}.json"
                entry = json.loads(path.read_text(encoding="utf-8"))
                page = context.new_page()
                page.goto(entry["uri"], wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3000)
                html = page.content()
                page.close()
                text = trafilatura.extract(
                    html, url=entry["uri"], output_format="markdown", include_formatting=True,
                    include_tables=True, include_links=True, include_comments=False,
                ) or ""
                if len(text) < 500:
                    sys.exit(f"{entry['uri']}: live page gave {len(text)} characters")
                entry.update(method="cdp+trafilatura", chars=len(text), text=text)
                path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"{path}: {len(text)} characters")
    finally:
        chrome.terminate()


if __name__ == "__main__":
    fetch(Path(sys.argv[1]), [int(a) for a in sys.argv[2:]] or list(LIVE_ARTICLES))
