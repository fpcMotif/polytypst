"""Exports the website catalog: one entry for each `[[page]]` of each `books/<key>/site.toml`.

A page names a chapter converter. The generic converters live here; `chapters = "site"` calls
`content(page, source, dest, web_base)` in the folder's own `site.py`."""

import html
import json
import re
import shutil
import subprocess
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from .book_state import transcripts as transcript_store
from .compiler.monograph import build_source
from .ocr.transcripts import TranscriptStore

SITE_TOML = "site.toml"
SITE_PY = "site.py"
ROOT_TOKEN = "@ROOT@"
DELIVERABLES = (("pdf", "pdf"), ("typ", "typst"), ("tex", "latex"), ("epub", "epub"))
FIGURE_SUFFIXES = frozenset({".svg", ".png", ".jpg", ".jpeg"})
FIGURE_FOLDERS = ("figures", "figures_color")
BESIDE_PDF = frozenset({"pdf", "epub"})
RENDERING_BADGES = {"math-katex": "KaTeX", "editorial-business": "Editorial HTML", "vertical-classic": "直排"}


@dataclass(frozen=True)
class SitePage:
    """One `[[page]]` of a `site.toml`: a book's entry on the website.

    Title, subtitle, author and language default to the book spec; a folder without `book.toml` must give them.
    `source` and `files` name the built files of a page without editions; `layout` is free data for `site.py`."""

    key: str
    folder: Path
    slug: str
    domain: str
    description: str
    editions: tuple[str, ...] = ()
    title: str = ""
    subtitle: str = ""
    author: str = ""
    language: str = ""
    rendering: str = "math-katex"
    badge: str = ""
    chapters: str = "monograph-md"
    source: str = ""
    files: str = "book"
    figure_images: str = ""
    table_images: str = ""
    legend: tuple[tuple[str, str], ...] = ()
    layout: dict[str, Any] = field(default_factory=dict)

    @property
    def toml(self) -> Path:
        return self.folder / SITE_TOML


@dataclass(frozen=True)
class SiteSource:
    """Where a page's built files are: `folder/<stem>.<ext>`; `root` is the export root that `@ROOT@` names."""

    folder: Path
    stem: str
    root: Path

    def file(self, ext: str) -> Path:
        top = self.folder / f"{self.stem}.{ext}"
        built = build_source(top, ext)
        return built if ext not in BESIDE_PDF and built.exists() else top

    def path(self, value: str) -> Path:
        from .books import expand_tokens

        return Path(expand_tokens(value.replace(ROOT_TOKEN, str(self.root))))


@dataclass
class SiteContent:
    """What a converter makes: chapters, images to copy (relative to the source folder), and,
    for a page that publishes its own files, its editions and page count."""

    chapters: list[dict[str, Any]]
    images: list[str] = field(default_factory=list)
    editions: list[dict[str, str]] | None = None
    pages: int | None = None


Converter = Callable[[SitePage, SiteSource, Path, str], SiteContent]
REQUIRED_KEYS = frozenset({"slug", "domain", "description"})
PAGE_KEYS = frozenset(f.name for f in fields(SitePage)) - {"key", "folder"}


def site_pages(folders: dict[str, Path]) -> list[SitePage]:
    """Each `[[page]]` of each `site.toml` in `folders`, in folder order; a bad key or value names its file."""
    pages: list[SitePage] = []
    for key, folder in folders.items():
        path = folder / SITE_TOML
        if not path.is_file():
            continue
        try:
            tables = tomllib.loads(path.read_text(encoding="utf-8")).get("page", [])
        except tomllib.TOMLDecodeError as error:
            raise ValueError(f"{path}: {error}") from error
        for table in tables:
            if missing := sorted(REQUIRED_KEYS - set(table)):
                raise ValueError(f"{path}: a [[page]] needs the keys {', '.join(missing)}")
            if unknown := sorted(set(table) - PAGE_KEYS):
                raise ValueError(f"{path}: unknown [[page]] key {', '.join(unknown)}; known: {', '.join(sorted(PAGE_KEYS))}")
            page = SitePage(
                key,
                folder,
                **{k: v for k, v in table.items() if k not in ("editions", "legend")},
                editions=tuple(table.get("editions", ())),
                legend=tuple((item["color"], item["label"]) for item in table.get("legend", ())),
            )
            if page.rendering not in RENDERING_BADGES:
                raise ValueError(f"{path}: rendering {page.rendering!r} is not one of {', '.join(RENDERING_BADGES)}")
            if page.chapters not in CONVERTERS and page.chapters != "site":
                raise ValueError(f"{path}: chapters {page.chapters!r} is not one of {', '.join([*CONVERTERS, 'site'])}")
            if page.chapters == "site" and not (folder / SITE_PY).is_file():
                raise ValueError(f"{path}: chapters = \"site\" needs {folder / SITE_PY}")
            pages.append(page)
    return pages


def site_folders() -> dict[str, Path]:
    """Every folder under `books/` with a `site.toml`, by name; a site-only folder need not hold a book."""
    from .books import BOOKS_DIR

    return {p.name: p for p in sorted(BOOKS_DIR.iterdir()) if (p / SITE_TOML).is_file()}


HTML_NESTING_TAGS = ("div", "table", "blockquote", "figure", "ul", "ol", "dl")


def _top_level_html_blocks(html_text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    for line in html_text.splitlines():
        if not line.strip() and depth == 0:
            continue
        current.append(line)
        for tag in HTML_NESTING_TAGS:
            depth += len(re.findall(rf"<{tag}[\s>]", line)) - len(re.findall(rf"</{tag}>", line))
        if depth <= 0:
            depth = 0
            blocks.append("\n".join(current))
            current = []
    if current:
        blocks.append("\n".join(current))
    return blocks


THEOREM_KINDS = (
    "Theorem", "Proposition", "Lemma", "Corollary", "Definition", "Remark", "Remarks", "Example",
    "Examples", "Exercise", "Question", "Conjecture", "Claim", "Notation", "Problem", "Scholium",
    "定理", "命题", "引理", "推论", "定义", "注",
)
THEOREM_RE = re.compile(
    rf"^\*\*({'|'.join(THEOREM_KINDS)})\s*([0-9IVX][0-9IVX.\-']*)?\.?\*\*\s*(?:\(([^)]{{1,80}})\)\s*)?(?:\*\*\s*)?(.*)$",
    re.DOTALL,
)
PLAIN_THEOREM_RE = re.compile(
    r"^(Theorem|Definition|Lemma|Corollary|Proposition)\s*([0-9\.]*)[\.\—\-\:]?\s*(.*)$", re.IGNORECASE | re.DOTALL
)
CHAPTER_HEADING_RE = re.compile(r"^Chapter\s+(\d+):\s*(.*)$")
ZH_CHAPTER_RE = re.compile(r"^(第[一二三四五六七八九十百]+章|附录\s*[IVX]+)\s*(.*)$")
EQ_LABEL_RE = re.compile(r"\$\$\s*<eq-([0-9a-z]+)-([0-9a-z]+)>")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)(?:\{[^}]*\})?")
MAX_CHAPTER_JSON = 450_000


def _md_paragraph_block(p: str, asset_base: str, images: list[str]) -> dict[str, Any]:
    img = IMAGE_RE.fullmatch(p.strip())
    if img:
        caption, path = img.groups()
        images.append(path)
        label, _, rest = caption.partition(" ") if re.match(r"^(Fig|Figure|图)\.?\s*\S+", caption) else ("", "", caption)
        if label and rest and re.match(r"^[0-9.]+$", rest.split(" ")[0]):
            label, rest = f"{label} {rest.split(' ')[0]}", " ".join(rest.split(" ")[1:])
        return {"type": "figure", "label": label, "caption": rest.strip(), "src": f"{asset_base}/{path}"}
    for _, path in IMAGE_RE.findall(p):
        images.append(path)
    p = IMAGE_RE.sub(lambda m: f"(figure: {m.group(1)})", p)
    thm = THEOREM_RE.match(p)
    if thm:
        kind, number, note, body = thm.groups()
        return {"type": "theorem", "kind": kind, "number": (number or "").rstrip("."),
                "title": note or "", "content": body.strip()}
    return {"type": "math-paragraph", "content": p}


def _paragraphs_keeping_display_math(text: str) -> list[str]:
    paras: list[str] = []
    pending = ""
    for chunk in re.split(r"\n\s*\n", text):
        pending = f"{pending}\n{chunk}" if pending else chunk
        if pending.count("$$") % 2 == 0:
            if pending.strip():
                paras.append(pending.strip())
            pending = ""
    if pending.strip():
        paras.append(pending.strip())
    return paras


def split_large_chapter(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    """The chapter, or numbered parts of it, each small enough for one JSON fetch."""
    if len(json.dumps(chapter["blocks"], ensure_ascii=False)) <= MAX_CHAPTER_JSON:
        return [chapter]
    parts: list[list[dict[str, Any]]] = [[]]
    size = 0
    for blk in chapter["blocks"]:
        blk_size = len(json.dumps(blk, ensure_ascii=False))
        if parts[-1] and size + blk_size > MAX_CHAPTER_JSON * 0.8 and (
            blk["type"] == "heading" or size + blk_size > MAX_CHAPTER_JSON
        ):
            parts.append([])
            size = 0
        parts[-1].append(blk)
        size += blk_size
    return [
        {**chapter, "slug": f"{chapter['slug']}-{i + 1}", "title": f"{chapter['title']} ({i + 1}/{len(parts)})",
         "blocks": blocks}
        for i, blocks in enumerate(parts)
    ]


def convert_monograph_md_to_math_web_blocks(md_path: Path, asset_base: str) -> tuple[list[dict[str, Any]], list[str]]:
    text = md_path.read_text(encoding="utf-8")
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)
    text = EQ_LABEL_RE.sub(lambda m: f"\\tag{{{m.group(1)}.{m.group(2)}}}$$", text)
    images: list[str] = []
    chapters: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_title_block = True
    for p in _paragraphs_keeping_display_math(text):
        if not p:
            continue
        h = re.match(r"^(#{1,4})\s+(.+)$", p)
        if h and "\n" not in p:
            hashes, title = h.groups()
            title = title.strip()
            ch = CHAPTER_HEADING_RE.match(title)
            if len(hashes) == 1 and ch:
                in_title_block = False
                num, rest = ch.groups()
                zh = ZH_CHAPTER_RE.match(rest)
                if zh:
                    number, title = zh.group(1), zh.group(2) or rest
                else:
                    number, title = ("" if re.search(r"[一-鿿]", rest) else f"Chapter {num}"), rest
                current = {"slug": f"ch-{num}", "number": number, "title": title, "blocks": []}
                chapters.append(current)
                continue
            if len(hashes) == 1:
                continue
            if current is None:
                in_title_block = False
                current = {"slug": "front", "number": "Front matter", "title": title, "blocks": []}
                chapters.append(current)
                continue
            current["blocks"].append({"type": "heading", "level": min(len(hashes), 3), "text": title})
            continue
        if current is None or in_title_block:
            continue
        current["blocks"].append(_md_paragraph_block(p, asset_base, images))
    chapters = [c for c in chapters if c["blocks"]]
    return [part for c in chapters for part in split_large_chapter(c)], images


def _monograph_md(page: SitePage, source: SiteSource, dest: Path, web_base: str) -> SiteContent:
    md = source.file("md")
    if not md.is_file():
        return SiteContent([])
    chapters, images = convert_monograph_md_to_math_web_blocks(md, web_base)
    return SiteContent(chapters, images)


def _business_md(page: SitePage, source: SiteSource, dest: Path, web_base: str) -> SiteContent:
    """Chinese prose: each `#` heading opens a chapter (第…章, else 导言), with bold, italic and links kept."""
    md = source.file("md")
    if not md.is_file():
        return SiteContent([])
    md_text = re.sub(r"\A---\n.*?\n---\n", "", md.read_text(encoding="utf-8"), flags=re.DOTALL)
    chapters: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for p in re.split(r"\n\s*\n", md_text):
        p = p.strip()
        if not p:
            continue
        h_m = re.match(r"^(#{1,4})\s+(.+)$", p)
        if h_m and "\n" not in p:
            hashes, title = h_m.groups()
            title = title.strip().replace("\\$", "$")
            if len(hashes) == 1:
                m_ch = re.match(r"^(第[一二三四五六七八九十]+章)\s*(.*)$", title)
                ch_num, ch_title = m_ch.groups() if m_ch else ("导言", title)
                current = {"slug": f"ch-{len(chapters) + 1}", "number": ch_num, "title": ch_title or title, "blocks": []}
                chapters.append(current)
            elif current is not None:
                current["blocks"].append({"type": "heading", "level": min(len(hashes), 3), "text": title})
            continue
        if current is None:
            continue
        clean_p = p.replace("\\$", "$")
        escaped = html.escape(clean_p)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", escaped)
        escaped = re.sub(
            r"\[([^\]]+)\]\((https?://[^)]+)\)",
            r'<a href="\2" target="_blank" rel="noopener noreferrer" class="editorial-ref">\1</a>',
            escaped,
        )
        current["blocks"].append({"type": "paragraph", "html": escaped.replace("\n", "<br/>"), "text": clean_p})
    return SiteContent([part for c in chapters if c["blocks"] for part in split_large_chapter(c)])


def _latex_html(page: SitePage, source: SiteSource, dest: Path, web_base: str) -> SiteContent:
    """The LaTeX master through pandoc: each `<h1>` names a part and each `<h2>` opens a chapter."""
    tex = source.file("tex")
    if not tex.is_file():
        return SiteContent([])
    html_text = subprocess.run(
        ["pandoc", str(tex), "-f", "latex", "-t", "html5", "--katex", "--wrap=none"],
        check=True, capture_output=True, text=True,
    ).stdout
    html_text = html_text.replace('src="figures/', f'src="{web_base}/figures/')
    chapters: list[dict[str, Any]] = []
    part = ""
    current: dict[str, Any] | None = None
    for blk in _top_level_html_blocks(html_text):
        h = re.fullmatch(r'<h([12])[^>]*>(.*?)</h\1>', blk.strip(), re.DOTALL)
        if h:
            level, title = h.groups()
            title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
            if level == "1":
                part = title
            current = {"slug": f"sec-{len(chapters) + 1}", "number": part if level == "2" else "",
                       "title": title, "blocks": []}
            chapters.append(current)
            continue
        if current is None or re.fullmatch(r'<div id="[^"]*">\s*</div>', blk.strip()):
            continue
        h3 = re.fullmatch(r'<h([3-6])[^>]*>(.*?)</h\1>', blk.strip(), re.DOTALL)
        if h3:
            current["blocks"].append({"type": "heading", "level": 3,
                                      "text": html.unescape(re.sub(r"<[^>]+>", "", h3.group(2))).strip()})
            continue
        current["blocks"].append({"type": "html", "html": blk})
    return SiteContent([p for c in chapters if c["blocks"] for p in split_large_chapter(c)])


def _transcript_pages(page: SitePage, source: SiteSource, dest: Path, web_base: str) -> SiteContent:
    """Each numbered chapter of the book spec, from its raw transcript pages.

    Raw, because the page cleaner's text carries compiler markers such as `@@FNSTART@@` and `<eq-…>`.
    `layout.drop_paragraphs` lists regexes for OCR debris to leave out."""
    from .books import books

    book = books()[page.key]
    spec = book.editions[page.editions[0]].spec if page.editions else book.spec
    assert spec is not None
    store = TranscriptStore(transcript_store(book.out_dir))
    drop = [re.compile(p) for p in page.layout.get("drop_paragraphs", ())]
    chapters: list[dict[str, Any]] = []
    for chapter in spec.chapters:
        if not chapter.number:
            continue
        blocks: list[dict[str, Any]] = []
        for pno in range(chapter.start_page, chapter.end_page + 1):
            if (text := store.text(pno)) is None:
                continue
            for p in re.split(r"\n\s*\n", text.strip()):
                p = p.strip()
                if not p or any(d.search(p) for d in drop):
                    continue
                if (h := re.match(r"^(#{1,4})\s+(.+)$", p)) and "\n" not in p:
                    blocks.append({"type": "heading", "level": min(len(h.group(1)), 3), "text": h.group(2).strip()})
                elif m := PLAIN_THEOREM_RE.match(p):
                    kind, num, body = m.groups()
                    blocks.append({"type": "theorem", "kind": kind.capitalize(), "number": num.strip(),
                                   "content": body.strip() or p})
                else:
                    blocks.append({"type": "math-paragraph", "content": p})
        chapters.append({"slug": f"ch-{chapter.number}", "number": f"Chapter {chapter.number}",
                         "title": chapter.title, "blocks": blocks})
    return SiteContent([c for c in chapters if c["blocks"]])


CONVERTERS: dict[str, Converter] = {
    "monograph-md": _monograph_md,
    "business-md": _business_md,
    "latex-html": _latex_html,
    "transcript-pages": _transcript_pages,
}


def _pdf_page_count(pdf: Path) -> int:
    import pymupdf

    with pymupdf.open(pdf) as doc:
        return doc.page_count


def _copy_edition_files(rebuilt_pdf: Path, dest: Path, name: str, web_base: str) -> dict[str, str]:
    files: dict[str, str] = {}
    built = SiteSource(rebuilt_pdf.parent, rebuilt_pdf.stem, rebuilt_pdf.parent)
    for ext, key in DELIVERABLES:
        src = built.file(ext)
        if src.exists():
            shutil.copy2(src, dest / f"{name}.{ext}")
            files[key] = f"{web_base}/{name}.{ext}"
    return files


def _copy_book_files(source: SiteSource, dest: Path, web_base: str) -> dict[str, str]:
    """Copy `<stem>.<ext>` as `book.<ext>`, and the figure folders; return the deliverables."""
    files: dict[str, str] = {}
    for ext, key in (*DELIVERABLES, ("md", "")):
        if (cand := source.file(ext)).exists():
            shutil.copy2(cand, dest / f"book.{ext}")
            if key:
                files[key] = f"{web_base}/book.{ext}"
    for name in FIGURE_FOLDERS:
        for fig in sorted((source.folder / name).glob("*")) if (source.folder / name).is_dir() else ():
            if fig.suffix.lower() in FIGURE_SUFFIXES:
                (dest / "figures").mkdir(parents=True, exist_ok=True)
                shutil.copy2(fig, dest / "figures" / fig.name)
    return files


IMG_SRC_RE = re.compile(r'<img[^>]*\ssrc="([^"]+)"')


def _images(chapters: list[dict[str, Any]]) -> set[str]:
    """The distinct images the chapters show: figure blocks, theorem diagrams, and images inside Markdown content or HTML."""
    srcs: set[str] = set()
    for c in chapters:
        for b in c["blocks"]:
            if b["type"] == "figure":
                srcs.add(b["src"])
            srcs |= {d["src"] for d in b.get("diagrams", ())}
            srcs |= {m.group(2) for m in IMAGE_RE.finditer(b.get("content", ""))}
            srcs |= set(IMG_SRC_RE.findall(b.get("html", "")))
    return srcs


def _counts(page: SitePage, chapters: list[dict[str, Any]]) -> tuple[int, int]:
    """Figures and tables: images that match `figure_images` (all images when unset) and those that match
    `table_images`, plus table blocks and HTML tables."""
    images = _images(chapters)
    tables = {s for s in images if page.table_images and re.search(page.table_images, s)}
    figures = {s for s in images - tables if not page.figure_images or re.search(page.figure_images, s)}
    table_blocks = sum(
        1
        for c in chapters
        for b in c["blocks"]
        if b["type"] == "table" or (b["type"] == "html" and "<table" in b["html"])
    )
    return len(figures), len(tables) + table_blocks


def export_page(page: SitePage, root_dir: Path, assets_dir: Path) -> dict[str, Any] | None:
    """The catalog entry for one page, with its files copied into `assets_dir/<slug>`; None when nothing is built."""
    from .books import book_folders, books, module

    book = books()[page.key] if page.key in book_folders() else None
    spec = None
    if book is not None:
        spec = book.editions[page.editions[0]].spec if page.editions else book.spec
    if page.editions:
        assert book is not None, f"{page.toml}: editions need a book.toml"
        rebuilt = root_dir / book.editions[page.editions[0]].rebuilt
        source = SiteSource(rebuilt.parent, rebuilt.stem, root_dir)
    elif page.source or book is not None:
        folder = SiteSource(Path(), "", root_dir).path(page.source) if page.source else book.out_dir
        source = SiteSource(folder, page.files, root_dir)
    else:
        raise ValueError(f"{page.toml}: page {page.slug} needs editions or a source folder")

    dest = assets_dir / page.slug
    web_base = f"/assets/{page.slug}"
    dest.mkdir(parents=True, exist_ok=True)
    convert = module(page.key, "site").content if page.chapters == "site" else CONVERTERS[page.chapters]
    content = convert(page, source, dest, web_base)
    if not content.chapters:
        return None

    for rel in content.images:
        if (src := source.folder / rel).is_file():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / rel)
    editions = content.editions
    if editions is None and page.editions:
        editions = []
        for name in page.editions:
            ed = book.editions[name]
            files = _copy_edition_files(root_dir / ed.rebuilt, dest, name, web_base)
            if "pdf" in files:
                editions.append({"name": name, "label": ed.summary or name, **files})
    if editions is not None:
        deliverables = editions[0]
        pdf = dest / Path(editions[0]["pdf"]).name
    else:
        deliverables = _copy_book_files(source, dest, web_base)
        pdf = dest / "book.pdf"
    pages = content.pages if content.pages is not None else (_pdf_page_count(pdf) if pdf.is_file() else 0)
    figures, tables = _counts(page, content.chapters)

    def meta(name: str, default: str) -> str:
        if value := getattr(page, name) or default:
            return value
        raise ValueError(f"{page.toml}: page {page.slug} needs {name}, since {page.key} has no book spec")

    entry: dict[str, Any] = {
        "slug": page.slug,
        "title": meta("title", spec.title if spec else ""),
        "subtitle": meta("subtitle", (spec.subtitle or f"{spec.publisher}, {spec.year}") if spec else ""),
        "author": meta("author", spec.author if spec else ""),
        "language": meta("language", ("zh-CN" if spec.lang == "zh" else "en-US") if spec else ""),
        "domain": page.domain,
        "renderingMode": page.rendering,
        "renderingBadge": page.badge or RENDERING_BADGES[page.rendering],
        "description": page.description,
        "stats": {"pages": pages, "figures": figures, "tables": tables, "chapters": len(content.chapters)},
        "deliverables": {k: deliverables.get(k, "") for _, k in DELIVERABLES},
    }
    if editions is not None:
        entry["editions"] = editions
    if page.legend:
        entry["legend"] = [{"color": c, "label": label} for c, label in page.legend]
    entry["chapters"] = content.chapters
    return entry


def export_all_web_data(root_dir: Path, web_public_dir: Path) -> dict[str, Any]:
    """Write `data/catalog.json` and the assets for every site page; a page with no build keeps its last entry."""
    assets_dir = web_public_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    cat_file = web_public_dir / "data" / "catalog.json"
    previous: dict[str, dict[str, Any]] = {}
    if cat_file.exists():
        try:
            previous = {b["slug"]: b for b in json.loads(cat_file.read_text(encoding="utf-8")).get("books", [])}
        except (OSError, ValueError, KeyError):
            previous = {}

    books_payload: list[dict[str, Any]] = []
    for page in site_pages(site_folders()):
        entry = export_page(page, root_dir, assets_dir) or previous.get(page.slug)
        if entry is not None:
            books_payload.append(entry)

    catalog_data = {"books": books_payload}
    cat_file.parent.mkdir(parents=True, exist_ok=True)
    cat_file.write_text(json.dumps(catalog_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return catalog_data
