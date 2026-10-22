"""Parse the reader PDF into chapters, articles and their links."""

import json
import re
from dataclasses import asdict
from pathlib import Path

import pymupdf

from .links import fetch_or_load_link
from .models import (
    ArticleEntry,
    ChapterContent,
    ExtractedLink,
    ParsedReaderBook,
    PdfLine,
)


def _join_zh_lines(lines: list[str]) -> str:
    if not lines:
        return ""
    acc = lines[0].strip()
    for nxt in lines[1:]:
        s = nxt.strip()
        if not s:
            continue
        if (
            acc
            and acc[-1].isascii()
            and acc[-1].isalnum()
            and s[0].isascii()
            and s[0].isalnum()
        ):
            acc += " " + s
        else:
            acc += s
    return acc


def _group_paragraphs(lines: list[PdfLine], gap_threshold: float = 22.0) -> list[str]:
    if not lines:
        return []
    groups: list[list[str]] = [[lines[0].text]]
    prev_y = lines[0].y0
    for ln in lines[1:]:
        if (ln.y0 - prev_y) > gap_threshold:
            groups.append([ln.text])
        else:
            groups[-1].append(ln.text)
        prev_y = ln.y0
    return [_join_zh_lines(g) for g in groups if _join_zh_lines(g)]


def _extract_page_lines(page: pymupdf.Page) -> list[PdfLine]:
    blocks = page.get_text("dict").get("blocks", [])
    out: list[PdfLine] = []
    for b in blocks:
        if b.get("type") != 0:
            continue
        for l in b.get("lines", []):
            spans = l.get("spans", [])
            txt = "".join(s.get("text", "") for s in spans).strip()
            if not txt:
                continue
            sz = max((float(s.get("size", 0.0)) for s in spans), default=0.0)
            bbox = l.get("bbox", (0.0, 0.0, 0.0, 0.0))
            if sz <= 8.5 and (bbox[1] < 35.0 or bbox[1] > 740.0):
                continue
            out.append(
                PdfLine(
                    text=txt,
                    size=round(sz, 2),
                    y0=round(float(bbox[1]), 2),
                    y1=round(float(bbox[3]), 2),
                )
            )
    return out


def _parse_article_page(
    page: pymupdf.Page, pno: int, link_idx: int, cache_dir: Path
) -> tuple[ArticleEntry, ExtractedLink]:
    lines = _extract_page_lines(page)
    zh_title = lines[0].text
    m_num = re.match(r"^(\d{2})\s+", zh_title)
    art_num = int(m_num.group(1)) if m_num else link_idx
    en_title = lines[1].text if len(lines) > 1 else ""
    author_line = lines[2].text if len(lines) > 2 else ""
    date_priority_line = lines[3].text if len(lines) > 3 else ""
    background_line = lines[4].text if len(lines) > 4 else ""
    access_line = lines[5].text if len(lines) > 5 else ""

    ext_uri = ""
    for lk in page.get_links():
        if lk.get("uri"):
            ext_uri = str(lk["uri"])
            break

    extracted = fetch_or_load_link(
        link_idx, pno, "打开英文原文", en_title, ext_uri, cache_dir
    )

    section_name = ""
    sec_lines: dict[str, list[PdfLine]] = {
        "原文讲了什么": [],
        "带着这个角度读": [],
        "轮岗时核实": [],
        "材料边界": [],
    }
    for ln in lines[6:]:
        if ln.text == "打开英文原文":
            continue
        if ln.text in sec_lines:
            section_name = ln.text
            continue
        if section_name:
            sec_lines[section_name].append(ln)

    q_items: list[str] = []
    for ln in sec_lines["轮岗时核实"]:
        if re.match(r"^[1-9]\s+", ln.text):
            q_items.append(ln.text)
        elif q_items:
            q_items[-1] = _join_zh_lines([q_items[-1], ln.text])
        else:
            q_items.append(ln.text)

    entry = ArticleEntry(
        number=art_num,
        src_page=pno,
        zh_title=zh_title,
        en_title=en_title,
        author_line=author_line,
        date_priority_line=date_priority_line,
        background_line=background_line,
        access_line=access_line,
        uri=ext_uri,
        summary_paragraphs=_group_paragraphs(sec_lines["原文讲了什么"]),
        angle_paragraphs=_group_paragraphs(sec_lines["带着这个角度读"]),
        questions=q_items,
        boundary_paragraphs=_group_paragraphs(sec_lines["材料边界"]),
        original_text=extracted.clean_text,
    )
    return entry, extracted


def parse_reader_pdf(pdf_path: Path, out_dir: Path) -> ParsedReaderBook:
    doc = pymupdf.open(pdf_path)
    cache_dir = out_dir / "articles_cache"
    all_links: list[ExtractedLink] = []
    link_counter = 0

    p1_lines = _extract_page_lines(doc[0])
    kicker = p1_lines[0].text
    title = "".join(ln.text for ln in p1_lines[1:4])
    subtitle = p1_lines[4].text
    tags = [ln.text for ln in p1_lines[5:8]]
    edition_line = p1_lines[8].text if len(p1_lines) > 8 else "第一版 2026年10月18日"

    intro_sections: list[tuple[str, list[str]]] = []
    for pno in (2, 4, 5, 6, 7):
        plines = _extract_page_lines(doc[pno - 1])
        sec_title = plines[0].text
        paras = _group_paragraphs(plines[1:])
        intro_sections.append((sec_title, paras))

    chapter_ranges = [
        (1, 8, list(range(9, 16))),
        (2, 16, list(range(17, 26))),
        (3, 26, list(range(27, 34))),
        (4, 34, list(range(35, 41))),
        (5, 41, list(range(42, 46))),
        (6, 46, list(range(47, 49))),
    ]

    chapters: list[ChapterContent] = []
    for ch_num, intro_pno, art_pages in chapter_ranges:
        ch_lines = _extract_page_lines(doc[intro_pno - 1])
        ch_title = ch_lines[0].text
        body_lines: list[PdfLine] = []
        for ln in ch_lines[1:]:
            if ln.text == "本章选文":
                break
            body_lines.append(ln)
        intro_paras = _group_paragraphs(body_lines)
        entries: list[ArticleEntry] = []
        for ap in art_pages:
            link_counter += 1
            entry, ext_link = _parse_article_page(
                doc[ap - 1], ap, link_counter, cache_dir
            )
            entries.append(entry)
            all_links.append(ext_link)
        chapters.append(
            ChapterContent(
                number=ch_num,
                title=ch_title,
                intro_paragraphs=intro_paras,
                entries=entries,
            )
        )

    back_sections: list[tuple[str, list[str], list[ExtractedLink]]] = []
    for pno in range(49, 58):
        page = doc[pno - 1]
        plines = _extract_page_lines(page)
        sec_title = plines[0].text
        ext_links_on_page: list[ExtractedLink] = []
        link_labels: set[str] = set()
        for lk in page.get_links():
            if lk.get("uri"):
                link_counter += 1
                rect = pymupdf.Rect(lk["from"])
                lbl = page.get_textbox(rect).strip().replace("\n", " ")
                link_labels.add(lbl)
                ext_obj = fetch_or_load_link(
                    link_counter, pno, lbl, lbl, str(lk["uri"]), cache_dir
                )
                ext_links_on_page.append(ext_obj)
                all_links.append(ext_obj)
        prose_lines = [ln for ln in plines[1:] if ln.text not in link_labels]
        paras = _group_paragraphs(prose_lines)
        back_sections.append((sec_title, paras, ext_links_on_page))

    links_file = out_dir / "extracted_links.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    links_file.write_text(
        json.dumps([asdict(lk) for lk in all_links], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return ParsedReaderBook(
        kicker=kicker,
        title=title,
        subtitle=subtitle,
        tags=tags,
        edition_line=edition_line,
        intro_sections=intro_sections,
        chapters=chapters,
        back_sections=back_sections,
        all_links=all_links,
    )
