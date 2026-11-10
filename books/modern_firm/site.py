"""Roberts, The Modern Firm: editorial web prose with `$X$` points as variables and 图/表 links as anchors."""

import html
import re
from pathlib import Path
from typing import Any

from polytypst.web_exporter import SiteContent, SitePage, SiteSource

REF_RE = re.compile(r"\[(图\s*\d+|表\s*\d+)\]\(#(?:fig|tab):\d+\)")
FIGURE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)\{#fig:(\d+)\}")
CHAPTER_RE = re.compile(r"^(第\s*\d+\s*章)\s*(.*)$")


def plain_text(text: str) -> str:
    text = REF_RE.sub(r"\1", text)
    text = re.sub(r"\$([A-Za-z0-9\\_\^\{\}\s\+\-\=\(\),\.\']+)\$", lambda m: m.group(1).replace("\\", ""), text)
    return text.replace("$", "")


def prose_html(text: str) -> str:
    escaped = html.escape(REF_RE.sub(r"\1", text))
    escaped = re.sub(r"\$([A-Z](?:&#x27;|\')?)\$", r'<var class="editorial-var">\1</var>', escaped)
    escaped = re.sub(r"\$([^\$]+)\$", r'<var class="editorial-var">\1</var>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"图\s*(\d+)(?!\d)", r'<a href="#fig-\1" class="editorial-ref">图 \1</a>', escaped)
    return re.sub(r"表\s*(\d+)(?!\d)", r'<a href="#tab-\1" class="editorial-ref">表 \1</a>', escaped)


def content(page: SitePage, source: SiteSource, dest: Path, web_base: str) -> SiteContent:
    md = source.file("md")
    if not md.is_file():
        return SiteContent([])
    layout = page.layout
    tables = {t["marker"]: t for t in layout["tables"]}
    current: dict[str, Any] = {
        "slug": "frontmatter", "number": layout["front_number"], "title": layout["front_title"], "blocks": []
    }
    chapters = [current]
    emitted: set[str] = set()
    for p in re.split(r"\n\s*\n", md.read_text(encoding="utf-8")):
        p = p.strip()
        if not p or p.startswith("%"):
            continue
        if fig := FIGURE_RE.search(p):
            cap, _, n = fig.groups()
            if f"fig-{n}" not in emitted:
                emitted.add(f"fig-{n}")
                current["blocks"].append({
                    "type": "figure", "id": f"fig-{n}", "label": f"图 {n}",
                    "caption": plain_text(cap.replace(f"图 {n} ", "")), "src": f"{web_base}/figures/fig_{n}.svg",
                })
            continue
        table = next((t for marker, t in tables.items() if marker in p), None)
        if table is not None and table["id"] not in emitted:
            emitted.add(table["id"])
            current["blocks"].append({"type": "table", **{k: v for k, v in table.items() if k != "marker"}})
            continue
        if p.startswith("|") or "\n|" in p:
            continue
        if (h := re.match(r"^(#{1,3})\s+(.+)$", p)) and "\n" not in p:
            hashes, title = h.groups()
            title = plain_text(title.strip())
            if len(hashes) == 1:
                number, rest = (m.groups() if (m := CHAPTER_RE.match(title)) else (layout["chapter_number"], title))
                current = {"slug": f"ch-{len(chapters)}", "number": number, "title": rest or title, "blocks": []}
                chapters.append(current)
            else:
                current["blocks"].append({"type": "heading", "level": min(len(hashes), 3), "text": title})
            continue
        current["blocks"].append({"type": "paragraph", "html": prose_html(p), "text": plain_text(p)})
    return SiteContent([c for c in chapters if c["blocks"]])
