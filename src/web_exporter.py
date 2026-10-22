import html
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .kerodon.compiler import KerodonCompiler
from .kerodon.diagrams import KerodonDiagramCropper
from .kerodon.extractor import KerodonExtractor
from .ocr.transcripts import TranscriptStore

HASH = chr(35)


def convert_roberts_to_business_web_blocks(book_md_path: Path) -> list[dict[str, Any]]:
    md_text = book_md_path.read_text(encoding="utf-8")
    chapters: list[dict[str, Any]] = []
    current_chapter: dict[str, Any] = {
        "slug": "frontmatter",
        "number": "导言",
        "title": "前言与致谢",
        "blocks": []
    }
    chapters.append(current_chapter)
    emitted_figs = set()
    emitted_tabs = set()

    paras = re.split(r"\n\s*\n", md_text)
    for p in paras:
        p = p.strip()
        if not p or p.startswith("%"):
            continue

        fig_m = re.search(rf"!\[([^\]]*)\]\(([^)]+)\)\{{{HASH}fig:([1-9])\}}", p)
        if fig_m:
            cap, _, fig_id_str = fig_m.groups()
            fig_id = int(fig_id_str)
            if fig_id not in emitted_figs:
                emitted_figs.add(fig_id)
                current_chapter["blocks"].append({
                    "type": "figure",
                    "id": f"fig-{fig_id}",
                    "label": f"图 {fig_id}",
                    "caption": strip_latex_for_business_web(cap.replace(f"图 {fig_id} ", "")),
                    "src": f"/assets/modern-firm/figures/fig_{fig_id}.svg"
                })
            continue

        if ": 表 1 " in p and 1 not in emitted_tabs:
            emitted_tabs.add(1)
            current_chapter["blocks"].append({
                "type": "table",
                "id": "tab-1",
                "label": "表 1",
                "caption": "1980—1986 年企业兼并",
                "headers": ["企业兼并指标", "百分比 (%)"],
                "rows": [
                    ["敌意收购努力", "14%"],
                    ["成功的敌意收购", "7%"],
                    ["在被收购后三年内经历了大规模资产剥离的公司", "44%"],
                    ["被剥离资产占收购价值的百分比", "20%"],
                    ["涉及相关业务买家的资产剥离比例", "72%"],
                ],
                "note": "资料来源：Bhagat, Shleifer, and Vishny (1990)."
            })
            continue

        if ": 表 2 " in p and 2 not in emitted_tabs:
            emitted_tabs.add(2)
            current_chapter["blocks"].append({
                "type": "table",
                "id": "tab-2",
                "label": "表 2",
                "caption": "英国石油公司的业绩",
                "headers": ["业绩指标", "1989", "1992", "1995", "1996", "1998"],
                "rows": [
                    ["重置成本利润（亿美元）", "24", "-6", "34", "42", "46"],
                    ["运营现金流（亿美元）", "62", "53", "81", "89", "90"],
                    ["平均动用资本回报率 (%)", "11.5", "—", "13.5", "16.0", "14.5"],
                    ["雇员人数（千人）", "119.6", "97.7", "56.7", "53.7", "96.6"],
                    ["产量（百万桶油当量/天）", "1.9", "1.7", "1.6", "1.7", "2.0"],
                    ["储量替代率 (%)", "85", "98", "136", "142", "174"],
                    ["勘探与开发成本（美元/桶）", "5.55", "3.85", "1.67", "1.62", "1.30"],
                    ["股价（便士）", "312", "235", "538", "698", "899"],
                ],
                "note": "资料来源：英国石油公司年报及公开财务资料。"
            })
            continue

        if p.startswith("|") or "\n|" in p:
            continue

        h_m = re.match(rf"^({HASH}{{1,3}})\s+(.+)$", p)
        if h_m and "\n" not in p:
            hashes, title = h_m.groups()
            title = strip_latex_for_business_web(title.strip())
            if len(hashes) == 1:
                slug = f"ch-{len(chapters)}"
                m_ch = re.match(r"^(第\s*[1-7]\s*章)\s*(.*)$", title)
                if m_ch:
                    ch_num, ch_title = m_ch.groups()
                else:
                    ch_num, ch_title = "专章", title
                current_chapter = {
                    "slug": slug,
                    "number": ch_num,
                    "title": ch_title or title,
                    "blocks": []
                }
                chapters.append(current_chapter)
            else:
                current_chapter["blocks"].append({
                    "type": "heading",
                    "level": min(len(hashes), 3),
                    "text": title
                })
            continue

        web_html = format_business_prose_html(p)
        current_chapter["blocks"].append({
            "type": "paragraph",
            "html": web_html,
            "text": strip_latex_for_business_web(p)
        })

    return [c for c in chapters if c["blocks"]]


def strip_latex_for_business_web(text: str) -> str:
    text = re.sub(rf"\[(图\s*[1-9]|表\s*[1-2])\]\({HASH}(?:fig|tab):[1-9]\)", r"\1", text)
    text = re.sub(r"\$([A-Za-z0-9\\_\^\{\}\s\+\-\=\(\),\.\']+)\$", lambda m: m.group(1).replace("\\", ""), text)
    return text.replace("$", "")


def format_business_prose_html(text: str) -> str:
    text = re.sub(rf"\[(图\s*[1-9]|表\s*[1-2])\]\({HASH}(?:fig|tab):[1-9]\)", r"\1", text)
    escaped = html.escape(text)
    escaped = re.sub(
        r"\$([A-Z](?:&#x27;|\')?)\$",
        r'<var class="editorial-var">\1</var>',
        escaped
    )
    escaped = re.sub(
        r"\$([^\$]+)\$",
        r'<var class="editorial-var">\1</var>',
        escaped
    )
    escaped = re.sub(
        r"\*\*([^*]+)\*\*",
        r"<strong>\1</strong>",
        escaped
    )
    escaped = re.sub(
        r"图\s*([1-9])(?!\d)",
        rf'<a href="{HASH}fig-\1" class="editorial-ref">图 \1</a>',
        escaped
    )
    escaped = re.sub(
        r"表\s*([1-2])(?!\d)",
        rf'<a href="{HASH}tab-\1" class="editorial-ref">表 \1</a>',
        escaped
    )
    return escaped


def convert_serre_to_math_web_blocks(serre_md_path: Path) -> list[dict[str, Any]]:
    md_text = serre_md_path.read_text(encoding="utf-8")
    chapters: list[dict[str, Any]] = []
    current_chapter: dict[str, Any] = {
        "slug": "intro",
        "number": "Avant-propos",
        "title": "Avant-propos & Première Partie",
        "blocks": []
    }
    chapters.append(current_chapter)
    emitted_figs = set()

    paras = re.split(r"\n\s*\n", md_text)
    for p in paras:
        p = p.strip()
        if not p or p.startswith("%"):
            continue

        fig_m = re.search(rf"!\[([^\]]*)\]\(([^)]+)\)\{{{HASH}fig:([1-3])\}}", p)
        if fig_m:
            cap, _, fig_id_str = fig_m.groups()
            fig_id = int(fig_id_str)
            if fig_id not in emitted_figs:
                emitted_figs.add(fig_id)
                current_chapter["blocks"].append({
                    "type": "figure",
                    "id": f"serre-fig-{fig_id}",
                    "label": f"Fig. {fig_id}",
                    "caption": cap,
                    "src": f"/assets/serre-arithmetique/figures/fig_{fig_id}.svg"
                })
            continue

        h_m = re.match(rf"^({HASH}{{1,3}})\s+(.+)$", p)
        if h_m and "\n" not in p:
            hashes, title = h_m.groups()
            title = title.strip()
            if len(hashes) <= 2 and re.match(r"^(CHAPITRE|Chapitre|PREMIÈRE PARTIE|DEUXIÈME PARTIE|APPENDICE|Appendice|Index|Bibliographie)", title, re.IGNORECASE):
                slug = f"serre-ch-{len(chapters)}"
                current_chapter = {
                    "slug": slug,
                    "number": f"Chapitre {len(chapters)}",
                    "title": title,
                    "blocks": []
                }
                chapters.append(current_chapter)
            else:
                current_chapter["blocks"].append({
                    "type": "heading",
                    "level": min(len(hashes), 3),
                    "text": title
                })
            continue

        thm_m = re.match(
            r"^(?:\*\*)?(THÉORÈME|Théorème|PROPOSITION|Proposition|LEMME|Lemme|COROLLAIRE|Corollaire|DÉFINITION|Définition|REMARQUE|Remarque|Remarques|Démonstration|Exemple|Exemples)\s*([0-9IVX\.\'\s]*)(?:\*\*)?\s*[\.\—\-\:]?\s*(.*)$",
            p,
            re.DOTALL
        )
        if thm_m:
            kind, num, body = thm_m.groups()
            current_chapter["blocks"].append({
                "type": "theorem",
                "kind": kind.capitalize(),
                "number": num.strip(),
                "title": "",
                "tag": "",
                "content": body.strip() or p
            })
        else:
            current_chapter["blocks"].append({
                "type": "math-paragraph",
                "content": p
            })

    return [c for c in chapters if c["blocks"]]


def convert_kerodon_to_math_web_blocks(kerodon_dir: Path, pdf_path: Path) -> list[dict[str, Any]]:
    from .kerodon.runner import CHAPTER_METADATA

    extractor = KerodonExtractor(kerodon_dir / "cache_web")
    cropper = KerodonDiagramCropper(pdf_path, kerodon_dir / "figures")
    chapters: list[dict[str, Any]] = []
    for ch_num, (ch_tag, start_page, end_page) in CHAPTER_METADATA.items():
        chapter = extractor.extract_chapter(ch_num, ch_tag)
        cropper.crop_chapter_diagrams(chapter, start_page=start_page, end_page=end_page)
        for sec in chapter.sections:
            blocks: list[dict[str, Any]] = []
            for env in sec.intro_environments:
                blocks.extend(_kerodon_env_to_blocks(env))
            for sub in sec.subsections:
                blocks.append({
                    "type": "heading",
                    "level": 3,
                    "text": f"§ {sub.number} {sub.title}",
                    "tag": sub.tag
                })
                for env in sub.environments:
                    blocks.extend(_kerodon_env_to_blocks(env))
            chapters.extend(_split_large_chapter({
                "slug": f"sec-{sec.number.replace('.', '-')}",
                "number": f"Chapter {ch_num} · Section {sec.number}",
                "title": sec.title,
                "tag": sec.tag,
                "blocks": blocks
            }))
    return chapters


def _kerodon_env_to_blocks(env) -> list[dict[str, Any]]:
    diag_idx = 0
    diagrams_out = []

    def replace_diag(m):
        nonlocal diag_idx
        img_p = None
        if diag_idx < len(env.diagrams):
            img_p = env.diagrams[diag_idx].image_path
        elif env.diagrams:
            img_p = env.diagrams[0].image_path
        diag_idx += 1
        if img_p:
            fname = Path(img_p).name
            diagrams_out.append({
                "tag": env.tag,
                "src": f"/assets/kerodon-ch1/figures/{fname}",
                "caption": f"Commutative Diagram ({env.number} · Tag {env.tag})"
            })
        return ""

    raw_body = re.sub(
        r":::COMMUTATIVE_DIAGRAM:::(.*?):::END_DIAGRAM:::",
        replace_diag,
        env.body_markdown,
        flags=re.DOTALL
    )
    cleaned_body = KerodonCompiler.clean_kerodon_tex_for_pandoc(raw_body).strip()
    cleaned_title = KerodonCompiler.clean_kerodon_tex_for_pandoc(env.title).strip() if env.title else ""

    out = [{
        "type": "theorem",
        "kind": env.env_type.capitalize(),
        "number": env.number,
        "title": cleaned_title,
        "tag": env.tag,
        "content": cleaned_body,
        "diagrams": diagrams_out
    }]
    return out


def convert_ahlfors_to_math_web_blocks(ahlfors_dir: Path) -> list[dict[str, Any]]:
    transcripts = TranscriptStore(ahlfors_dir / "markdown")
    chapters_def = [
        (1, "Complex Numbers", 1, 36),
        (2, "Complex Functions", 37, 64),
        (3, "Analytic Functions as Mappings", 65, 116),
        (4, "Complex Integration", 117, 190),
        (5, "Series and Product Developments", 191, 244),
        (6, "Conformal Mapping. Dirichlet's Problem", 245, 278),
        (7, "Elliptic Functions", 279, 298),
        (8, "Global Analytic Functions", 299, 340),
    ]
    chapters: list[dict[str, Any]] = []
    for ch_num, ch_title, start_p, end_p in chapters_def:
        blocks: list[dict[str, Any]] = []
        for pno in range(start_p, end_p + 1):
            page_text = transcripts.text(pno)
            if page_text is None:
                continue
            text = page_text.strip()
            paras = re.split(r"\n\s*\n", text)
            for p in paras:
                p = p.strip()
                if not p or p.startswith("//") or "1.1.1.1.1" in p:
                    continue
                h_m = re.match(r"^(#{1,4})\s+(.+)$", p)
                if h_m and "\n" not in p:
                    hashes, title = h_m.groups()
                    blocks.append({
                        "type": "heading",
                        "level": min(len(hashes), 3),
                        "text": title.strip()
                    })
                elif re.match(r"^(?:Theorem|Definition|Lemma|Corollary|Proposition)\s*([0-9\.]*)", p, re.IGNORECASE):
                    m = re.match(r"^(Theorem|Definition|Lemma|Corollary|Proposition)\s*([0-9\.]*)[\.\—\-\:]?\s*(.*)$", p, re.IGNORECASE | re.DOTALL)
                    if m:
                        kind, num, body = m.groups()
                        blocks.append({
                            "type": "theorem",
                            "kind": kind.capitalize(),
                            "number": num.strip(),
                            "content": body.strip() or p
                        })
                    else:
                        blocks.append({"type": "math-paragraph", "content": p})
                else:
                    blocks.append({"type": "math-paragraph", "content": p})
        chapters.append({
            "slug": f"ch-{ch_num}",
            "number": f"Chapter {ch_num}",
            "title": ch_title,
            "blocks": blocks
        })
    return chapters


def convert_goursat_to_math_web_blocks(goursat_md_path: Path) -> list[dict[str, Any]]:
    if not goursat_md_path.exists():
        return []
    text = goursat_md_path.read_text(encoding="utf-8")
    raw_chaps = re.split(r"\n(?=#+ (?:CHAPTER|Chapitre))", text)
    chapters: list[dict[str, Any]] = []
    for idx, raw in enumerate(raw_chaps):
        lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
        if not lines:
            continue
        title = lines[0].lstrip("#").strip()
        slug = f"ch-{idx}"
        number = "Preface & Introduction" if idx == 0 else f"Chapter {idx}"
        blocks: list[dict[str, Any]] = []
        paras = re.split(r"\n\s*\n", raw.strip())
        for p in paras:
            p = p.strip()
            if not p:
                continue
            h_m = re.match(r"^(#{1,4})\s+(.+)$", p)
            if h_m and "\n" not in p:
                hashes, t = h_m.groups()
                blocks.append({"type": "heading", "level": min(len(hashes), 3), "text": t.strip()})
            else:
                blocks.append({"type": "math-paragraph", "content": p})
        chapters.append({
            "slug": slug,
            "number": number,
            "title": title,
            "blocks": blocks
        })
    return chapters


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


def convert_taocp_to_math_web_blocks(taocp_tex_path: Path) -> list[dict[str, Any]]:
    if not taocp_tex_path.exists():
        return []
    html_text = subprocess.run(
        ["pandoc", str(taocp_tex_path), "-f", "latex", "-t", "html5", "--katex", "--wrap=none"],
        check=True, capture_output=True, text=True,
    ).stdout
    html_text = html_text.replace('src="figures/', 'src="/assets/taocp-vol3/figures/')
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
    chapters = [c for c in chapters if c["blocks"]]
    return [p for c in chapters for p in _split_large_chapter(c)]

THEOREM_KINDS = (
    "Theorem", "Proposition", "Lemma", "Corollary", "Definition", "Remark", "Remarks", "Example",
    "Examples", "Exercise", "Question", "Conjecture", "Claim", "Notation", "Problem", "Scholium",
    "定理", "命题", "引理", "推论", "定义", "注",
)
THEOREM_RE = re.compile(
    rf"^\*\*({'|'.join(THEOREM_KINDS)})\s*([0-9IVX][0-9IVX.\-']*)?\.?\*\*\s*(?:\(([^)]{{1,80}})\)\s*)?(?:\*\*\s*)?(.*)$",
    re.DOTALL,
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


def _split_large_chapter(chapter: dict[str, Any]) -> list[dict[str, Any]]:
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
    return [part for c in chapters for part in _split_large_chapter(c)], images


def _pdf_page_count(pdf: Path) -> int:
    import pymupdf

    with pymupdf.open(pdf) as doc:
        return doc.page_count


def _copy_edition_files(rebuilt_pdf: Path, dest: Path, name: str, web_base: str) -> dict[str, str]:
    files: dict[str, str] = {}
    for ext, key in (("pdf", "pdf"), ("typ", "typst"), ("tex", "latex"), ("epub", "epub")):
        src = rebuilt_pdf.with_suffix(f".{ext}")
        if src.exists():
            shutil.copy2(src, dest / f"{name}.{ext}")
            files[key] = f"{web_base}/{name}.{ext}"
    return files


REGISTRY_WEB_BOOKS: tuple[tuple[str, str, tuple[str, ...], str, str], ...] = (
    ("bourbaki", "bourbaki-commutative-algebra", ("modern", "vintage", "facsimile"), "Commutative Algebra & Homological Methods",
     "Bourbaki's Commutative Algebra, Chapters 1–7: flat modules, localization, filtrations and completions, primary decomposition, integers, valuations and divisors. Three print editions: a reflowed modern monograph, the 1970 vintage edition broken line for line like the scan, and a word-placed facsimile."),
    ("bourbaki_lie", "bourbaki-lie", ("monograph",), "Lie Theory",
     "Bourbaki's Lie Groups and Lie Algebras, Chapters 1–3: Lie algebras, free Lie algebras and the Campbell–Hausdorff formula, and Lie groups."),
    ("fermat", "fermat-dream", ("vol1",), "Number Theory",
     "Number Theory 1: Fermat's Dream. Elementary number theory, rational points on elliptic curves, conics and p-adic numbers, the zeta function, and algebraic number theory."),
    ("fermat", "class-field-theory", ("vol2",), "Number Theory",
     "Number Theory 2: Introduction to Class Field Theory. Zeta functions, the local and global class field theory, and their applications."),
    ("kashiwara", "kashiwara-algebraic-analysis", ("monograph",), "Algebraic Analysis & Microlocal Theory",
     "Foundations of Algebraic Analysis: hyperfunctions, microfunctions, and the theory of pseudo-differential operators and holonomic systems."),
    ("klein", "klein-19th-century", ("en",), "History of Mathematics",
     "Felix Klein's lectures on the development of mathematics in the 19th century."),
    ("klein", "klein-19th-century-zh", ("zh",), "数学史",
     "克莱因《数学在19世纪的发展》第二卷中文版：线性不变量理论、狭义相对论、二次微分形式与解析点变换群，以及埃尔朗根纲领与黎曼的三篇附录。"),
    ("kodaira", "kodaira-complex-analysis", ("monograph",), "Complex Function Theory & Riemann Surfaces",
     "Kodaira's Complex Analysis: holomorphic functions, Cauchy's theorem, conformal mappings, analytic continuation, Riemann's mapping theorem, and Riemann surfaces up to Riemann–Roch and Abel's theorem."),
)


def export_registry_books(root_dir: Path, assets_dir: Path) -> list[dict[str, Any]]:
    from .books import books

    registry = books()
    out: list[dict[str, Any]] = []
    for key, slug, edition_names, domain, description in REGISTRY_WEB_BOOKS:
        book = registry[key]
        primary = book.editions[edition_names[0]]
        spec = primary.spec
        assert spec is not None
        md_path = root_dir / primary.rebuilt.with_suffix(".md")
        if not md_path.exists():
            continue
        dest = assets_dir / slug
        dest.mkdir(parents=True, exist_ok=True)
        web_base = f"/assets/{slug}"
        chapters, images = convert_monograph_md_to_math_web_blocks(md_path, web_base)
        for rel in set(images):
            src = md_path.parent / rel
            if src.exists():
                (dest / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest / rel)
        editions = []
        for name in edition_names:
            ed = book.editions[name]
            files = _copy_edition_files(root_dir / ed.rebuilt, dest, name, web_base)
            if "pdf" in files:
                editions.append({"name": name, "label": ed.summary or name, **files})
        first = editions[0]
        pdf_pages = _pdf_page_count(root_dir / primary.rebuilt)
        out.append({
            "slug": slug,
            "title": spec.title,
            "subtitle": spec.subtitle or f"{spec.publisher}, {spec.year}",
            "author": spec.author,
            "language": "zh-CN" if spec.lang == "zh" else "en-US",
            "domain": domain,
            "renderingMode": "math-katex",
            "renderingBadge": "KaTeX",
            "description": description,
            "stats": {"pages": pdf_pages, "figures": len(set(images)), "tables": 0, "chapters": len(chapters)},
            "deliverables": {
                "pdf": first["pdf"],
                "typst": first.get("typst", ""),
                "latex": first.get("latex", ""),
                "epub": first.get("epub", ""),
            },
            "editions": editions,
            "chapters": chapters,
        })
    return out


SHITOUJI_LEGEND: tuple[tuple[str, str], ...] = (
    ("E73E29", "甲戌本硃批"),
    ("A70236", "庚辰本硃批"),
    ("0E56A7", "庚辰本墨批 · 己卯本墨夾批"),
    ("EC008C", "蒙府本之批"),
    ("A46C35", "戚序本之批 · 有正補文"),
    ("008080", "甲戌本墨眉批 · 列藏本"),
    ("800080", "甲辰本"),
    ("581600", "楊藏本"),
    ("FAA624", "舒序本補文"),
)


def export_shitouji(root_dir: Path, assets_dir: Path) -> list[dict[str, Any]]:
    from .shitouji_vertical import extract_chapters

    src_dir = root_dir / "shitouji"
    volumes = sorted((src_dir / "typst").glob("volume_0*.pdf"))
    if not volumes:
        return []
    slug = "shitouji"
    dest = assets_dir / slug
    dest.mkdir(parents=True, exist_ok=True)
    web_base = f"/assets/{slug}"
    editions = []
    pages = 0
    for n, pdf in enumerate(volumes, start=1):
        name = pdf.stem
        files: dict[str, str] = {}
        for src, key in ((pdf, "pdf"), (pdf.with_suffix(".typ"), "typst"), (src_dir / "latex" / f"{name}.tex", "latex")):
            if src.exists():
                shutil.copy2(src, dest / src.name)
                files[key] = f"{web_base}/{src.name}"
        pages += _pdf_page_count(pdf)
        editions.append({"name": name, "label": f"第{'一二三四五六七八'[n - 1]}冊", **files})
    chapters = extract_chapters()
    first = editions[0]
    return [{
        "slug": slug,
        "title": "脂硯齋重評石頭記",
        "subtitle": "四校訖自用本 · 直排彙校",
        "author": "曹雪芹 著 · 脂硯齋 評",
        "language": "zh-Hant",
        "domain": "中國古典小說",
        "renderingMode": "vertical-classic",
        "renderingBadge": "直排",
        "description": "《石頭記》八十回彙校本。正文直排，夾批雙行小字，側批與眉批依原色區分各本批語。",
        "stats": {"pages": pages, "figures": 0, "tables": 0, "chapters": len(chapters)},
        "deliverables": {
            "pdf": first["pdf"],
            "typst": first.get("typst", ""),
            "latex": first.get("latex", ""),
            "epub": "",
        },
        "editions": editions,
        "legend": [{"color": c, "label": label} for c, label in SHITOUJI_LEGEND],
        "chapters": chapters,
    }]


def _first_existing(*paths: Path) -> Path:
    return next((p for p in paths if p.exists()), paths[0])


def convert_london_treasury_to_business_web_blocks(book_md_path: Path) -> list[dict[str, Any]]:
    md_text = book_md_path.read_text(encoding="utf-8")
    md_text = re.sub(r"\A---\n.*?\n---\n", "", md_text, flags=re.DOTALL)
    chapters: list[dict[str, Any]] = []
    current_chapter: dict[str, Any] | None = None

    for p in re.split(r"\n\s*\n", md_text):
        p = p.strip()
        if not p:
            continue
        h_m = re.match(rf"^({HASH}{{1,4}})\s+(.+)$", p)
        if h_m and "\n" not in p:
            hashes, title = h_m.groups()
            title = title.strip().replace("\\$", "$")
            if len(hashes) == 1:
                m_ch = re.match(r"^(第[一二三四五六七八九十]+章)\s*(.*)$", title)
                if m_ch:
                    ch_num, ch_title = m_ch.groups()
                else:
                    ch_num, ch_title = "导言", title
                current_chapter = {
                    "slug": f"ch-{len(chapters) + 1}",
                    "number": ch_num,
                    "title": ch_title or title,
                    "blocks": [],
                }
                chapters.append(current_chapter)
            elif current_chapter is not None:
                current_chapter["blocks"].append({
                    "type": "heading",
                    "level": min(len(hashes), 3),
                    "text": title,
                })
            continue
        if current_chapter is None:
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
        escaped = escaped.replace("\n", "<br/>")
        current_chapter["blocks"].append({
            "type": "paragraph",
            "html": escaped,
            "text": clean_p,
        })

    chapters = [c for c in chapters if c["blocks"]]
    return [part for c in chapters for part in _split_large_chapter(c)]


def export_all_web_data(root_dir: Path, web_public_dir: Path) -> dict[str, Any]:
    assets_dir = web_public_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    existing_books_map = {}
    cat_file = web_public_dir / "data" / "catalog.json"
    if cat_file.exists():
        try:
            old_data = json.loads(cat_file.read_text(encoding="utf-8"))
            for b in old_data.get("books", []):
                existing_books_map[b["slug"]] = b
        except (OSError, ValueError, KeyError):
            existing_books_map = {}

    roberts_out_dir = _first_existing(root_dir / "output" / "modern_firm", root_dir.parent / "output" / "modern_firm")
    serre_out_dir = _first_existing(
        root_dir / "output" / "serre_arithmetique", root_dir.parent / "output" / "serre_arithmetique"
    )
    kerodon_out_dir = root_dir / "output" / "kerodon"
    ahlfors_out_dir = root_dir / "output" / "ahlfors"
    goursat_out_dir = root_dir / "output" / "goursat_colab"
    taocp_out_dir = root_dir / "output" / "taocp"
    london_treasury_out_dir = root_dir / "output" / "london_treasury"
    kerodon_pdf = root_dir / "kerodon.pdf"

    sync_configs = [
        ("modern-firm", roberts_out_dir, "book"),
        ("serre-arithmetique", serre_out_dir, "serre_cours_darithmetique"),
        ("kerodon-ch1", kerodon_out_dir, "kerodon_complete"),
        ("ahlfors", ahlfors_out_dir, "ahlfors_complete"),
        ("goursat-analyse", goursat_out_dir, "book"),
        ("taocp-vol3", taocp_out_dir, "taocp_vol3"),
        ("london-treasury", london_treasury_out_dir, "london_branch_treasury_and_trading_reader"),
    ]

    for slug, src_dir, base_prefix in sync_configs:
        dest = assets_dir / slug
        dest_figs = dest / "figures"
        dest_figs.mkdir(parents=True, exist_ok=True)
        if src_dir.exists():
            for ext in ("pdf", "typ", "tex", "epub", "md"):
                cand = src_dir / f"{base_prefix}.{ext}"
                if not cand.exists():
                    cand = src_dir / f"book.{ext}"
                if cand.exists():
                    shutil.copy2(cand, dest / f"book.{ext}")
            src_figs = src_dir / "figures"
            if src_figs.exists():
                for fig_f in src_figs.iterdir():
                    if fig_f.suffix.lower() in (".svg", ".png", ".jpg", ".jpeg"):
                        shutil.copy2(fig_f, dest_figs / fig_f.name)
            src_figs_color = src_dir / "figures_color"
            if src_figs_color.exists():
                for fig_f in src_figs_color.iterdir():
                    if fig_f.suffix.lower() in (".svg", ".png"):
                        shutil.copy2(fig_f, dest_figs / fig_f.name)

    books_payload: list[dict[str, Any]] = []

    if "modern-firm" in existing_books_map and not (roberts_out_dir / "book.md").exists():
        books_payload.append(existing_books_map["modern-firm"])
    elif (roberts_out_dir / "book.md").exists():
        roberts_chapters = convert_roberts_to_business_web_blocks(roberts_out_dir / "book.md")
        books_payload.append({
            "slug": "modern-firm",
            "title": "现代企业：基于绩效与增长的组织设计",
            "subtitle": "The Modern Firm: Organizational Design for Performance and Growth",
            "author": "John Roberts (约翰·罗伯茨)",
            "language": "zh-CN",
            "domain": "Organizational Economics & Executive Strategy",
            "renderingMode": "editorial-business",
            "renderingBadge": "Editorial HTML Typography (Non-LaTeX Web Prose + Vector SVG Diagrams)",
            "description": "斯坦福商学院经典战略组织著作。网页端采用纯正商业社论排版（不使用繁琐的 MathJax/LaTeX 公式渲染，将分析点 X、Y、Z 与图 1—图 9、表 1—表 2 转化为原生交互式锚点与高清矢量图），本地 PDF/Typst/LaTeX 则保持严谨出版级数学排版。",
            "stats": {"pages": 252, "figures": 9, "tables": 2, "chapters": len(roberts_chapters)},
            "deliverables": {
                "pdf": "/assets/modern-firm/book.pdf",
                "typst": "/assets/modern-firm/book.typ",
                "latex": "/assets/modern-firm/book.tex",
                "epub": "/assets/modern-firm/book.epub"
            },
            "chapters": roberts_chapters
        })

    if "serre-arithmetique" in existing_books_map and not (serre_out_dir / "combined_serre.md").exists():
        books_payload.append(existing_books_map["serre-arithmetique"])
    elif (serre_out_dir / "combined_serre.md").exists():
        serre_chapters = convert_serre_to_math_web_blocks(serre_out_dir / "combined_serre.md")
        books_payload.append({
            "slug": "serre-arithmetique",
            "title": "Cours d'arithmétique",
            "subtitle": "Presses Universitaires de France — Collection « Le Mathématicien »",
            "author": "Jean-Pierre Serre",
            "language": "fr-FR",
            "domain": "Algebraic Number Theory & Modular Forms",
            "renderingMode": "math-katex",
            "renderingBadge": "KaTeX / MathJax Engine + Semantic French Theorem Callouts",
            "description": "塞尔经典法文数论名著。完整收录第一部分（二次型、p-进域、Hasse-Minkowski 定理）与第二部分（Dirichlet 算术级数定理、模形式与 Hecke 算子），网页端搭载 KaTeX 实时公式渲染与高清复平面基本域矢量图。",
            "stats": {"pages": 173, "figures": 3, "tables": 0, "chapters": len(serre_chapters)},
            "deliverables": {
                "pdf": "/assets/serre-arithmetique/book.pdf",
                "typst": "/assets/serre-arithmetique/book.typ",
                "latex": "/assets/serre-arithmetique/book.tex",
                "epub": "/assets/serre-arithmetique/book.epub"
            },
            "chapters": serre_chapters
        })

    if "kerodon-ch1" in existing_books_map and not (kerodon_out_dir / "cache_web").exists():
        books_payload.append(existing_books_map["kerodon-ch1"])
    elif (kerodon_out_dir / "cache_web").exists() and kerodon_pdf.exists():
        kerodon_chapters = convert_kerodon_to_math_web_blocks(kerodon_out_dir, kerodon_pdf)
        books_payload.append({
            "slug": "kerodon-ch1",
            "title": "Kerodon — Chapters 1–10: The Complete Resource for Homotopy-Coherent Mathematics",
            "subtitle": "An Online Resource for Homotopy-Coherent Mathematics (Complete 10 Chapters)",
            "author": "Jacob Lurie",
            "language": "en-US",
            "domain": "Higher Category Theory & Homotopy Theory",
            "renderingMode": "math-katex",
            "renderingBadge": "KaTeX Engine + Kerodon Tag Permalinks + 300-DPI Commutative Diagrams + Complete 10 Chapters",
            "description": "Jacob Lurie 高阶范畴论完整十卷巨著（Kerodon 全十卷）。收录第 1 章至第 10 章全部 57 个标准节，涵盖单纯集、∞-范畴、Kan 复形、同伦论、Cartesian 纤维化、伴随函子、极限与余极限、米田嵌入、大 ∞-范畴以及正合性与动画，包含数千个定理与精确定位 Tag 永久链接。",
            "stats": {"pages": 889, "figures": 60, "tables": 0, "chapters": len(kerodon_chapters)},
            "deliverables": {
                "pdf": "/assets/kerodon-ch1/book.pdf",
                "typst": "/assets/kerodon-ch1/book.typ",
                "latex": "/assets/kerodon-ch1/book.tex",
                "epub": "/assets/kerodon-ch1/book.epub"
            },
            "chapters": kerodon_chapters
        })

    if ahlfors_out_dir.exists():
        ahlfors_chapters = convert_ahlfors_to_math_web_blocks(ahlfors_out_dir)
        if ahlfors_chapters:
            books_payload.append({
                "slug": "ahlfors",
                "title": "Complex Analysis (Third Edition)",
                "subtitle": "An Introduction to the Theory of Analytic Functions of One Complex Variable",
                "author": "Lars V. Ahlfors",
                "language": "en-US",
                "domain": "Complex Function Theory & Riemann Surfaces",
                "renderingMode": "math-katex",
                "renderingBadge": "1979 McGraw-Hill Standard + KaTeX Engine + Pen-and-Ink Figures",
                "description": "哈佛大学阿尔福斯经典复分析教程（第三版）。完整收录 8 章全本，涵盖代数复数、复函数、解析映射、复积分、级数展开、共形映射与狄利克雷问题、椭圆函数以及全局解析函数，附带 50 幅高精度出版级矢量与黑白插图。",
                "stats": {"pages": 340, "figures": 50, "tables": 0, "chapters": len(ahlfors_chapters)},
                "deliverables": {
                    "pdf": "/assets/ahlfors/book.pdf",
                    "typst": "/assets/ahlfors/book.typ",
                    "latex": "/assets/ahlfors/book.tex",
                    "epub": "/assets/ahlfors/book.epub"
                },
                "chapters": ahlfors_chapters
            })

    if (goursat_out_dir / "book.md").exists():
        goursat_chapters = convert_goursat_to_math_web_blocks(goursat_out_dir / "book.md")
        if goursat_chapters:
            books_payload.append({
                "slug": "goursat-analyse",
                "title": "A Course in Mathematical Analysis, Volume I",
                "subtitle": "Derivatives and Differentials, Definite Integrals, Expansion in Series, Applications to Geometry",
                "author": "Édouard Goursat (Trans. E. R. Hedrick)",
                "language": "en-US",
                "domain": "Classical Mathematical Analysis & Differential Geometry",
                "renderingMode": "math-katex",
                "renderingBadge": "Dover/Hedrick Edition + KaTeX Modern Notation + Restored Figures",
                "description": "法国巴黎大学古萨经典数学分析教程第一卷。涵盖实变函数微分与偏导数、隐函数、定积分、级数展开与几何应用，全书 646 页完整数字化重构与 KaTeX 数学排版。",
                "stats": {"pages": 646, "figures": 52, "tables": 0, "chapters": len(goursat_chapters)},
                "deliverables": {
                    "pdf": "/assets/goursat-analyse/book.pdf",
                    "typst": "/assets/goursat-analyse/book.typ",
                    "latex": "/assets/goursat-analyse/book.tex",
                    "epub": "/assets/goursat-analyse/book.epub"
                },
                "chapters": goursat_chapters
            })

    if (taocp_out_dir / "taocp_vol3.tex").exists():
        taocp_chapters = convert_taocp_to_math_web_blocks(taocp_out_dir / "taocp_vol3.tex")
        if taocp_chapters:
            books_payload.append({
                "slug": "taocp-vol3",
                "title": "The Art of Computer Programming, Vol. 3: Sorting and Searching",
                "subtitle": "Second Edition — Authentic Computer Modern & Knuthian Typography",
                "author": "Donald E. Knuth",
                "language": "en-US",
                "domain": "Algorithms, Data Structures & Combinatorial Computing",
                "renderingMode": "math-katex",
                "renderingBadge": "Knuth CM Typeface + 300-DPI Matched Diagrams + Complete Exercises",
                "description": "高德纳计算机程序设计艺术第三卷：排序与查找。包含第 5 章（内部排序、外部排序、最优排序）与第 6 章（顺序查找、树查找、散列法），并收录全部习题精析与数学常数附录，共 768 页完整出版级重现。",
                "stats": {"pages": 768, "figures": 230, "tables": 12, "chapters": len(taocp_chapters)},
                "deliverables": {
                    "pdf": "/assets/taocp-vol3/book.pdf",
                    "typst": "/assets/taocp-vol3/book.typ",
                    "latex": "/assets/taocp-vol3/book.tex",
                    "epub": "/assets/taocp-vol3/book.epub"
                },
                "chapters": taocp_chapters
            })

    if (london_treasury_out_dir / "book.md").exists():
        lt_chapters = convert_london_treasury_to_business_web_blocks(london_treasury_out_dir / "book.md")
        lt_pages = (
            _pdf_page_count(london_treasury_out_dir / "book.pdf")
            if (london_treasury_out_dir / "book.pdf").exists()
            else 430
        )
        if lt_chapters:
            books_payload.append({
                "slug": "london-treasury",
                "title": "伦敦分行资金与交易业务阅读册",
                "subtitle": "从业者经验导读与轮岗问题（含 53 篇英文原始文献与监管规则全文）",
                "author": "伦敦分行资金与交易业务编写组",
                "language": "zh-CN",
                "domain": "Treasury, ALM, Foreign Exchange, Fixed Income & Precious Metals",
                "renderingMode": "editorial-business",
                "renderingBadge": "Editorial Bilingual Reader + 53 Extracted Primary Sources (r.jina.ai)",
                "description": "面向银行伦敦分行交易与资金条线（外币货币市场、现券、外汇远期与掉期、贵金属、资产负债管理 ALM）的赴任导读与轮岗核实手册。完整提取并精排原书全部 53 条外部链接（35 篇从业者深度材料、4 部现行市场准则与监管规则、3 档核心播客及 11 项核验资料）的英文原文。",
                "stats": {"pages": lt_pages, "figures": 0, "tables": 1, "chapters": len(lt_chapters)},
                "deliverables": {
                    "pdf": "/assets/london-treasury/book.pdf",
                    "typst": "/assets/london-treasury/book.typ",
                    "latex": "/assets/london-treasury/book.tex",
                    "epub": "/assets/london-treasury/book.epub",
                },
                "chapters": lt_chapters,
            })

    books_payload.extend(export_registry_books(root_dir, assets_dir))
    books_payload.extend(export_shitouji(root_dir, assets_dir))

    catalog_data = {"books": books_payload}
    data_dir = web_public_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "catalog.json").write_text(
        json.dumps(catalog_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return catalog_data
