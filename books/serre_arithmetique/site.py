"""Serre, Cours d'arithmétique: French theorem callouts and KaTeX paragraphs from the combined Markdown."""

import re
from pathlib import Path
from typing import Any

from polytypst.web_exporter import SiteContent, SitePage, SiteSource

FIGURE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)\{#fig:(\d+)\}")


def content(page: SitePage, source: SiteSource, dest: Path, web_base: str) -> SiteContent:
    layout = page.layout
    md = source.folder / layout["markdown"]
    if not md.is_file():
        return SiteContent([])
    chapter_re = re.compile(layout["chapter_heading"], re.IGNORECASE)
    theorem_re = re.compile(layout["theorem"], re.DOTALL)
    current: dict[str, Any] = {"slug": "intro", "number": layout["front_number"], "title": layout["front_title"], "blocks": []}
    chapters = [current]
    emitted: set[str] = set()
    for p in re.split(r"\n\s*\n", md.read_text(encoding="utf-8")):
        p = p.strip()
        if not p or p.startswith("%"):
            continue
        if fig := FIGURE_RE.search(p):
            cap, _, n = fig.groups()
            if n not in emitted:
                emitted.add(n)
                current["blocks"].append({"type": "figure", "id": f"serre-fig-{n}", "label": f"Fig. {n}",
                                          "caption": cap, "src": f"{web_base}/figures/fig_{n}.svg"})
            continue
        if (h := re.match(r"^(#{1,3})\s+(.+)$", p)) and "\n" not in p:
            hashes, title = h.groups()
            title = title.strip()
            if len(hashes) <= 2 and chapter_re.match(title):
                current = {"slug": f"serre-ch-{len(chapters)}", "number": f"Chapitre {len(chapters)}",
                           "title": title, "blocks": []}
                chapters.append(current)
            else:
                current["blocks"].append({"type": "heading", "level": min(len(hashes), 3), "text": title})
            continue
        if thm := theorem_re.match(p):
            kind, num, body = thm.groups()
            current["blocks"].append({"type": "theorem", "kind": kind.capitalize(), "number": num.strip(),
                                      "title": "", "tag": "", "content": body.strip() or p})
        else:
            current["blocks"].append({"type": "math-paragraph", "content": p})
    return SiteContent([c for c in chapters if c["blocks"]])
