import html
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List

from .compiler.roberts_jina_typst import RobertsJinaTypstCompiler
from .compiler.french_math_typst import FrenchMathTypstCompiler
from .kerodon.compiler import KerodonCompiler
from .kerodon.extractor import KerodonExtractor
from .kerodon.diagrams import KerodonDiagramCropper

HASH = chr(35)


def convert_roberts_to_business_web_blocks(book_md_path: Path) -> List[Dict[str, Any]]:
    md_text = book_md_path.read_text(encoding="utf-8")
    chapters: List[Dict[str, Any]] = []
    current_chapter: Dict[str, Any] = {
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


def convert_serre_to_math_web_blocks(serre_md_path: Path) -> List[Dict[str, Any]]:
    md_text = serre_md_path.read_text(encoding="utf-8")
    chapters: List[Dict[str, Any]] = []
    current_chapter: Dict[str, Any] = {
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


def convert_kerodon_to_math_web_blocks(kerodon_dir: Path, pdf_path: Path) -> List[Dict[str, Any]]:
    extractor = KerodonExtractor(kerodon_dir / "cache_web")
    chapter = extractor.extract_chapter_1()
    cropper = KerodonDiagramCropper(pdf_path, kerodon_dir / "figures")
    cropper.crop_chapter_diagrams(chapter, start_page=18, end_page=145)

    chapters: List[Dict[str, Any]] = []
    for sec in chapter.sections:
        blocks: List[Dict[str, Any]] = []
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
        chapters.append({
            "slug": f"sec-{sec.number.replace('.', '-')}",
            "number": f"Section {sec.number}",
            "title": sec.title,
            "tag": sec.tag,
            "blocks": blocks
        })
    return chapters


def _kerodon_env_to_blocks(env) -> List[Dict[str, Any]]:
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


def convert_ahlfors_to_math_web_blocks(ahlfors_dir: Path) -> List[Dict[str, Any]]:
    md_dir = ahlfors_dir / "markdown"
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
    chapters: List[Dict[str, Any]] = []
    for ch_num, ch_title, start_p, end_p in chapters_def:
        blocks: List[Dict[str, Any]] = []
        for pno in range(start_p, end_p + 1):
            p_file = md_dir / f"p_{pno:03d}.md"
            if not p_file.exists():
                continue
            text = p_file.read_text(encoding="utf-8").strip()
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


def convert_goursat_to_math_web_blocks(goursat_md_path: Path) -> List[Dict[str, Any]]:
    if not goursat_md_path.exists():
        return []
    text = goursat_md_path.read_text(encoding="utf-8")
    raw_chaps = re.split(r"\n(?=#+ (?:CHAPTER|Chapitre))", text)
    chapters: List[Dict[str, Any]] = []
    for idx, raw in enumerate(raw_chaps):
        lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
        if not lines:
            continue
        title = lines[0].lstrip("#").strip()
        slug = f"ch-{idx}"
        number = "Preface & Introduction" if idx == 0 else f"Chapter {idx}"
        blocks: List[Dict[str, Any]] = []
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


def convert_taocp_to_math_web_blocks(taocp_typ_path: Path) -> List[Dict[str, Any]]:
    if not taocp_typ_path.exists():
        return []
    text = taocp_typ_path.read_text(encoding="utf-8")
    raw_chaps = re.split(r"\n(?=={1,2}\s+(?:\*?5\.\d|\*?6\.\d|Chapter Five|Chapter Six|Preface|About|Notes|Answers|Appendix|Table|Index))", text)
    chapters: List[Dict[str, Any]] = []
    idx = 0
    for raw in raw_chaps:
        raw = raw.strip()
        if not raw.startswith("="):
            continue
        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        title = lines[0].lstrip("=").strip()
        blocks: List[Dict[str, Any]] = []
        paras = re.split(r"\n\s*\n", raw)
        for p in paras:
            p = p.strip()
            if not p:
                continue
            h_m = re.match(r"^(=+)\s+(.+)$", p)
            if h_m and "\n" not in p:
                eqs, t = h_m.groups()
                blocks.append({"type": "heading", "level": min(len(eqs), 3), "text": t.strip()})
            else:
                blocks.append({"type": "math-paragraph", "content": p})

        max_chunk = 600
        if len(blocks) <= max_chunk:
            idx += 1
            chapters.append({
                "slug": f"sec-{idx}",
                "number": f"Section {idx}",
                "title": title,
                "blocks": blocks
            })
        else:
            for part_i in range(0, len(blocks), max_chunk):
                idx += 1
                sub_blocks = blocks[part_i:part_i + max_chunk]
                part_num = (part_i // max_chunk) + 1
                chapters.append({
                    "slug": f"sec-{idx}",
                    "number": f"Section {idx}",
                    "title": f"{title} (Part {part_num})",
                    "blocks": sub_blocks
                })
    return chapters

def export_all_web_data(root_dir: Path, web_public_dir: Path) -> Dict[str, Any]:
    assets_dir = web_public_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    existing_books_map = {}
    cat_file = web_public_dir / "data" / "catalog.json"
    if cat_file.exists():
        try:
            old_data = json.loads(cat_file.read_text(encoding="utf-8"))
            for b in old_data.get("books", []):
                existing_books_map[b["slug"]] = b
        except Exception:
            pass

    roberts_out_dir = root_dir / "output" / "modern_firm"
    serre_out_dir = root_dir / "output" / "serre_arithmetique"
    kerodon_out_dir = root_dir / "output" / "kerodon"
    ahlfors_out_dir = root_dir / "output" / "ahlfors"
    goursat_out_dir = root_dir / "output" / "goursat_colab"
    taocp_out_dir = root_dir / "output" / "taocp"
    kerodon_pdf = root_dir / "kerodon.pdf"

    sync_configs = [
        ("modern-firm", roberts_out_dir, "book"),
        ("serre-arithmetique", serre_out_dir, "serre_cours_darithmetique"),
        ("kerodon-ch1", kerodon_out_dir, "chapter1"),
        ("ahlfors", ahlfors_out_dir, "ahlfors_complete"),
        ("goursat-analyse", goursat_out_dir, "book"),
        ("taocp-vol3", taocp_out_dir, "taocp_vol3"),
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

    books_payload: List[Dict[str, Any]] = []

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
            "title": "Kerodon — Chapter 1: The Language of ∞-Categories",
            "subtitle": "An Online Resource for Homotopy-Coherent Mathematics",
            "author": "Jacob Lurie",
            "language": "en-US",
            "domain": "Higher Category Theory & Homotopy Theory",
            "renderingMode": "math-katex",
            "renderingBadge": "KaTeX Engine + Kerodon Tag Permalinks + 300-DPI Commutative Diagrams",
            "description": "Jacob Lurie 高阶范畴论巨著第一章。涵盖单纯集、基本群胚、拟范畴、同伦范畴与神经函子，包含 237 个结构化数学环境、精确 Tag 永久链接与 60 幅 300-DPI 交换图。",
            "stats": {"pages": 74, "figures": 60, "tables": 0, "chapters": len(kerodon_chapters)},
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

    if (taocp_out_dir / "taocp_vol3.typ").exists():
        taocp_chapters = convert_taocp_to_math_web_blocks(taocp_out_dir / "taocp_vol3.typ")
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

    catalog_data = {"books": books_payload}
    data_dir = web_public_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "catalog.json").write_text(
        json.dumps(catalog_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return catalog_data
