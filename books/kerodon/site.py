"""Kerodon on the website: one chapter per section, each result a theorem block with its tag and cropped diagrams."""

import re
from pathlib import Path
from typing import Any

from polytypst.web_exporter import (
    SiteContent,
    SitePage,
    SiteSource,
    split_large_chapter,
)

from .compiler import KerodonCompiler
from .diagrams import KerodonDiagramCropper
from .extractor import KerodonEnvironment, KerodonExtractor
from .runner import CHAPTER_METADATA

DIAGRAM_RE = re.compile(r":::COMMUTATIVE_DIAGRAM:::(.*?):::END_DIAGRAM:::", re.DOTALL)


def _env_block(env: KerodonEnvironment, web_base: str) -> dict[str, Any]:
    diagrams: list[dict[str, str]] = []
    seen = 0

    def take(_: re.Match[str]) -> str:
        nonlocal seen
        found = env.diagrams[seen] if seen < len(env.diagrams) else (env.diagrams[0] if env.diagrams else None)
        seen += 1
        if found is not None and found.image_path:
            diagrams.append({
                "tag": env.tag,
                "src": f"{web_base}/figures/{Path(found.image_path).name}",
                "caption": f"Commutative Diagram ({env.number} · Tag {env.tag})",
            })
        return ""

    body = DIAGRAM_RE.sub(take, env.body_markdown)
    clean = KerodonCompiler.clean_kerodon_tex_for_pandoc
    return {
        "type": "theorem",
        "kind": env.env_type.capitalize(),
        "number": env.number,
        "title": clean(env.title).strip() if env.title else "",
        "tag": env.tag,
        "content": clean(body).strip(),
        "diagrams": diagrams,
    }


def content(page: SitePage, source: SiteSource, dest: Path, web_base: str) -> SiteContent:
    cache = source.folder / page.layout["web_cache"]
    pdf = source.path(page.layout["pdf"])
    if not (cache.exists() and pdf.exists()):
        return SiteContent([])
    extractor = KerodonExtractor(cache)
    cropper = KerodonDiagramCropper(pdf, source.folder / "figures")
    chapters: list[dict[str, Any]] = []
    for number, (tag, first, last) in CHAPTER_METADATA.items():
        chapter = extractor.extract_chapter(number, tag)
        cropper.crop_chapter_diagrams(chapter, start_page=first, end_page=last)
        for sec in chapter.sections:
            blocks = [_env_block(env, web_base) for env in sec.intro_environments]
            for sub in sec.subsections:
                blocks.append({"type": "heading", "level": 3, "text": f"§ {sub.number} {sub.title}", "tag": sub.tag})
                blocks.extend(_env_block(env, web_base) for env in sub.environments)
            chapters.extend(split_large_chapter({
                "slug": f"sec-{sec.number.replace('.', '-')}",
                "number": f"Chapter {number} · Section {sec.number}",
                "title": sec.title,
                "tag": sec.tag,
                "blocks": blocks,
            }))
    return SiteContent(chapters)
