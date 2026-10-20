import html
import json
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pymupdf
from bs4 import BeautifulSoup

from ..compiler.monograph import MonographOutputs, compile_typst
from .spec import LONDON_TREASURY_SPEC

TEMPLATE_TYP = Path(__file__).with_name("template.typ")
DEFAULT_SOURCE_PDF = Path("/Users/martinfan/Downloads/伦敦分行资金与交易业务阅读册.pdf")

LATIN_OBFUSCATION_WORDS = frozenset(
    {
        "voluptas",
        "dolores",
        "adipisci",
        "laudantium",
        "molestias",
        "incidunt",
        "quisquam",
        "impedit",
        "voluptatem",
        "eligendi",
        "sapiente",
        "reiciendis",
        "consequatur",
        "debitis",
        "recusandae",
        "harum",
        "ipsam",
        "beatae",
        "facilis",
        "laboriosam",
        "earum",
        "odit",
        "dolorem",
        "assumenda",
        "accusamus",
        "blanditiis",
        "praesentium",
        "voluptatum",
        "deleniti",
    }
)


@dataclass(frozen=True)
class PdfLine:
    text: str
    size: float
    y0: float
    y1: float


@dataclass(frozen=True)
class ExtractedLink:
    index: int
    src_page: int
    label: str
    en_title: str
    uri: str
    method: str
    clean_chars: int
    clean_text: str


@dataclass(frozen=True)
class ArticleEntry:
    number: int
    src_page: int
    zh_title: str
    en_title: str
    author_line: str
    date_priority_line: str
    background_line: str
    access_line: str
    uri: str
    summary_paragraphs: list[str]
    angle_paragraphs: list[str]
    questions: list[str]
    boundary_paragraphs: list[str]
    original_text: str


@dataclass(frozen=True)
class ChapterContent:
    number: int
    title: str
    intro_paragraphs: list[str]
    entries: list[ArticleEntry] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedReaderBook:
    kicker: str
    title: str
    subtitle: str
    tags: list[str]
    edition_line: str
    intro_sections: list[tuple[str, list[str]]]
    chapters: list[ChapterContent]
    back_sections: list[tuple[str, list[str], list[ExtractedLink]]]
    all_links: list[ExtractedLink]


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


def _parse_reddit_rss(xml_text: str) -> str:
    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)
    out: list[str] = []
    for idx, entry in enumerate(entries):
        title_el = entry.find("atom:title", ns)
        author_el = entry.find("atom:author/atom:name", ns)
        content_el = entry.find("atom:content", ns)
        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        author = (
            author_el.text.strip() if author_el is not None and author_el.text else ""
        )
        raw_html = content_el.text if content_el is not None and content_el.text else ""
        if not raw_html:
            continue
        soup = BeautifulSoup(html.unescape(raw_html), "html.parser")
        for a in soup.find_all("a"):
            if a.get_text(strip=True) in ("[link]", "[comments]"):
                a.decompose()
        txt = soup.get_text("\n\n", strip=True)
        txt = re.sub(r"\s*submitted by\s+/u/\S+\s*$", "", txt).strip()
        if not txt or author == "/u/AutoModerator":
            continue
        if idx == 0:
            out.append(
                f"### {title}\n\n**Author:** {author}\n\n{txt}\n\n### Q&A Discussion"
            )
        else:
            out.append(f"**{author}:**\n\n{txt}")
    return "\n\n".join(out).strip()


def clean_wso_thread(raw_text: str, en_title: str) -> str:
    h1_pat = "^" + chr(35) + r"\s+(?!WSO)(.+)$"
    m = re.search(h1_pat, raw_text, flags=re.MULTILINE)
    start = m.start() if m else 0
    if not m and en_title:
        pos = raw_text.lower().find(en_title[:24].lower())
        if pos != -1:
            start = pos

    end = len(raw_text)
    for marker in (
        "See All Comments",
        "Unlock with",
        "Trending Content -",
        "Career Resources",
        "Similar Threads",
        "WSO Virtual Bootcamps",
        "View IB Report",
    ):
        p = raw_text.find(marker, start + 100)
        if p != -1 and p < end:
            end = p

    slice_txt = raw_text[start:end]
    slice_txt = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", "", slice_txt)
    slice_txt = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", slice_txt)
    slice_txt = re.sub(r"\[\]\([^)]*\)", "", slice_txt)
    slice_txt = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", slice_txt)

    noise_lines = {
        "*   Copy Link",
        "*   Share on Facebook",
        "*   Share on X",
        "*   Share on LinkedIn",
        "*   Share on WhatsApp",
        "*   Share via Email",
        "Copy Link",
        "Share on Facebook",
        "Share on X",
        "Share on LinkedIn",
        "Share on WhatsApp",
        "Share via Email",
        "Report",
        "Bookmark",
        "Quote",
        "Reply",
        "Follow",
        "Like",
        "Most Helpful",
        "All Replies",
        "Other",
        "[-]",
        "[-][-]",
        "AI Summary",
    }
    cleaned_lines: list[str] = []
    for line in slice_txt.splitlines():
        s = line.strip()
        if s in noise_lines:
            continue
        if re.match(
            r"^(?:IB|PE|HF|RE|CO|AM|TR|VC|OFF|ST|Rank:\s*.+|\d+\s*y|\d+y|\d+d|\d+m|\+\d+)$",
            s,
        ):
            continue
        cleaned_lines.append(line.rstrip())

    paras = [
        p.strip() for p in re.split(r"\n\s*\n", "\n".join(cleaned_lines)) if p.strip()
    ]
    final_paras: list[str] = []
    for p in paras:
        words = {w.lower().strip(".,?!:;\"'()") for w in p.split()}
        if len(words & LATIN_OBFUSCATION_WORDS) >= 2:
            continue
        if "Note: This synthesis was auto-generated" in p or "WSO Monkey Bot" in p:
            continue
        final_paras.append(p)
    return "\n\n".join(final_paras)


def clean_rotberg_transcript(raw_text: str) -> str:
    txt = re.sub(r">?\s*(?:Public Disclosure Authorized\s*)+", "", raw_text)
    txt = re.sub(r"  +", " ", txt)
    txt = re.sub(r"\s+(Q:\s+)", r"\n\n**Q:** ", txt)
    txt = re.sub(r"\s+(A:\s+)", r"\n\n**A:** ", txt)
    txt = re.sub(r"\s+(\[Laughter\])", r" *\1*", txt)
    return re.sub(r"\n{3,}", "\n\n", txt).strip()


def clean_single_link(uri: str, raw: str, en_title: str = "") -> str:
    h_prefix = chr(35) + " "
    domain = urlparse(uri).netloc.lower()
    text = raw.replace("\r\n", "\n")

    if "wallstreetoasis.com" in domain:
        return clean_wso_thread(text, en_title)

    if "documents.worldbank.org" in domain:
        return clean_rotberg_transcript(text)

    text = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[\]\([^)]*\)", "", text)
    text = re.sub(
        r"\[([^\]]+)\]\((?:https?://|mailto:|tel:|javascript:|/|#)[^)]*\)", r"\1", text
    )

    lines = [l.rstrip() for l in text.splitlines()]

    if "btrm.org" in domain:
        start_idx = 0
        if not uri.endswith(".pdf"):
            for i, l in enumerate(lines):
                if l.startswith(h_prefix):
                    start_idx = i
                    break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in ("E-MAIL: ENQUIRIES@BTRM.ORG", "Get the Brochure", "© 202")
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "treasurytoday.com" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if "Corporate View:" in l or l.startswith(h_prefix):
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "Related articles",
                    "Copyright © Treasury Today",
                    "Back to top",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "thebanktreasurynewsletter.com" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if (
                l.startswith(h_prefix)
                or "Ethan Heisler" in l
                or (en_title and en_title[:20].lower() in l.lower())
            ):
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "The Bank Treasury Newsletter is an independent",
                    "Download Chart Deck PDF",
                    "Previous Previous",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "thefullfx.com" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix):
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "Related Posts",
                    "Subscribe to our newsletter",
                    "*   The Stream",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "fi-desk.com" in domain or "marketsmedia.com" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix):
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "MORE STORIES",
                    "Copyright ©",
                    "Related Articles",
                    "Leave a Reply",
                    "FILS Europe:",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "lbma.org.uk" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix) or (
                en_title and en_title[:20].lower() in l.lower()
            ):
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "Related Articles",
                    "Sign up to receive updates",
                    "7th Floor, 62 Threadneedle Street",
                    "© 2026 LBMA",
                    "*   Good Delivery",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "efinancialcareers.com" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix) or "GUEST COMMENT:" in l:
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "Get the latest career advice",
                    "© 2026 eFinancialCareers",
                    "Related articles",
                    "Recruiters",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "toptradersunplugged.com" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix):
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "Manage consent",
                    "Read more about these purposes",
                    "Subscribe to Podcast",
                    "Leave a Review",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "iffim.org" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix) or "The Lay of the land" in l:
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "© IFFIm",
                    "Thanks for sharing!",
                    "*   Gavi, the Vaccine Alliance",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "bankofengland.co.uk" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix):
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "Bank of England Museum",
                    "Bartholomew Lane, London",
                    "©2026 Bank of England",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "globalfxc.org" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix) or "The FX Global Code" in l:
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(k in lines[i] for k in ("*   Contact", "Terms and Conditions")):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "podcasts.apple.com" in domain or "captivate.fm" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix):
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "Information",
                    "Select a country",
                    "*   United States",
                    "Listen for free",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "worldbank.org" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if l.startswith(h_prefix) or "Rotberg" in l or "What We Do" in l:
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "© 2026 World Bank Group",
                    "This site uses cookies",
                    "*   Scam Alert",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    elif "bis.org" in domain:
        start_idx = 0
        for i, l in enumerate(lines):
            if (
                l.startswith(h_prefix)
                or "Principles for Sound Liquidity" in l
                or "FX swaps and cross-currency" in l
                or "SRP98" in l
            ):
                start_idx = i
                break
        end_idx = len(lines)
        for i in range(start_idx + 3, len(lines)):
            if any(
                k in lines[i]
                for k in (
                    "Stay connected",
                    "Welcome to the new BIS website",
                    "*   Cookies notice",
                )
            ):
                end_idx = i
                break
        lines = lines[start_idx:end_idx]

    noisy_exact = {
        "Like",
        "Share",
        "Quote",
        "Reply",
        "Follow",
        "Report",
        "Bookmark",
        "Accept",
        "Decline",
        "Reject All",
        "Accept All",
        "Menu",
        "Search",
        "Sign in",
        "Log in",
        "Subscribe",
        "Read more",
        "Back to top",
        "Tweet",
    }
    filtered: list[str] = []
    for l in lines:
        s = l.strip()
        if s in noisy_exact:
            continue
        if re.match(r"^[*_\-]{3,}\s*$", s):
            continue
        if re.match(r"^(?:#+\s*)?\[Image[,:\s].*\]\s*$", s, flags=re.IGNORECASE):
            continue
        if re.match(
            r"^(?:\*\s+)?(?:Consent|Details|About|Necessary|Functional|Analytics|Performance|Advertisement)\s*$",
            s,
        ):
            continue
        if "[#IABV2" in s or "[#DSR_" in s or "[#GPC_" in s:
            continue
        filtered.append(l)

    out = "\n".join(filtered)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def fetch_or_load_link(
    idx: int, src_page: int, label: str, en_title: str, uri: str, cache_dir: Path
) -> ExtractedLink:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"link_{idx:02d}.json"
    raw_text = ""
    method = "r.jina.ai"

    if cache_file.exists():
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        raw_text = str(data.get("text", ""))
        method = str(data.get("method", "r.jina.ai"))

    if len(raw_text.strip()) < 200:
        clean_uri = uri.replace("&l=ar", "")
        with httpx.Client(follow_redirects=True, timeout=45.0) as client:
            if "reddit.com/" in clean_uri:
                time.sleep(2.0)
                rss_url = clean_uri.rstrip("/") + "/.rss?limit=100"
                resp = client.get(
                    rss_url,
                    headers={
                        "User-Agent": f"macos:polytypst.book:v1.{idx} (by /u/polytypst)"
                    },
                )
                if resp.status_code == 200 and "<feed" in resp.text:
                    raw_text = _parse_reddit_rss(resp.text)
                    method = "reddit_rss"
            if not raw_text:
                jina_url = f"https://r.jina.ai/{clean_uri}"
                resp = client.get(
                    jina_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                        "X-Return-Format": "markdown",
                    },
                )
                if resp.status_code == 200:
                    _, _, body = resp.text.partition("Markdown Content:")
                    raw_text = (body or resp.text).strip()
                    method = "r.jina.ai"

        cache_file.write_text(
            json.dumps(
                {
                    "index": idx,
                    "src_page": src_page,
                    "label": label,
                    "uri": uri,
                    "status": 200,
                    "method": method,
                    "chars": len(raw_text),
                    "text": raw_text,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    cleaned = clean_single_link(uri, raw_text, en_title)
    return ExtractedLink(
        index=idx,
        src_page=src_page,
        label=label,
        en_title=en_title,
        uri=uri,
        method=method,
        clean_chars=len(cleaned),
        clean_text=cleaned,
    )


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


_CJK_FULLWIDTH = str.maketrans({"?": "？", "!": "！", ",": "，", ";": "；", ":": "："})


def _escape_typst(text: str) -> str:
    s = re.sub(
        r"(?<=[一-鿿）」』])[?!,;:]",
        lambda m: m.group().translate(_CJK_FULLWIDTH),
        text,
    )
    s = s.replace("\\", "\\\\")
    for ch in ("#", "$", "*", "_", "[", "]", "<", ">", "@", "~", "^", "`"):
        s = s.replace(ch, "\\" + ch)
    s = re.sub(r"^(\s*)([=+\-/])", r"\1\\\2", s, flags=re.MULTILINE)
    s = re.sub(r"^(\s*\d+)\.", r"\1\\.", s, flags=re.MULTILINE)
    return s


_EN_INLINE = re.compile(
    r"\[(?P<ltext>[^\]\n]+)\]\((?P<lurl>[^)\s]+)\)"
    r"|\*\*(?P<bold>[^*\n]+?)\*\*"
    r"|(?<![\w*])\*(?P<istar>[^*\s][^*\n]*?)\*(?![\w*])"
    r"|(?<![\w\\])_(?P<iund>[^_\n]+?)_(?![\w])"
)
_EN_BULLET = re.compile(r"^\s*[*\-+•]\s+(.*)$")
_EN_NUMBERED = re.compile(r"^\s*(\d{1,3})[.)]\s+(.*)$")
_EN_HEADING = re.compile(r"^#{1,6}\s+(.*)$")
_EN_IMAGE = re.compile(r"^\**\s*!?\[?\s*image\b.*$", re.IGNORECASE)
_EN_READ_TIME = re.compile(r"^\d+\s+min(ute)?s?\s+read$", re.IGNORECASE)
_EN_SENTENCE_END = re.compile(r"[.!?:;\"”’)\]]$")
_EN_REDDIT_USER = re.compile(r"^\*{0,2}(?:/u/([\w-]+))?:\*{0,2}$")
_EN_REDACTED = "This post was mass deleted and anonymized with"


def _en_inline(text: str) -> str:
    out: list[str] = []
    pos = 0
    for m in _EN_INLINE.finditer(text):
        out.append(_escape_typst(text[pos : m.start()]))
        if m.group("ltext"):
            label = _en_inline(m.group("ltext"))
            url = m.group("lurl")
            out.append(f'#link("{url}")[{label}];' if url.startswith("http") else label)
        elif m.group("bold"):
            out.append(f"#strong[{_en_inline(m.group('bold'))}];")
        else:
            out.append(f"#emph[{_escape_typst(m.group('istar') or m.group('iund'))}];")
        pos = m.end()
    out.append(_escape_typst(text[pos:]))
    return "".join(out)


def _plain(text: str) -> str:
    return re.sub(r"[*_#>\[\]]", "", text).strip()


def _norm_title(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _plain(text).lower())


def _is_caps_heading(line: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", line)
    return len(letters) >= 4 and letters.isupper() and len(line.split()) <= 9


@dataclass
class _EnBlock:
    kind: str  # para | head | caps | user | label | bullet | numbered | quote
    text: str
    number: int = 0


def _en_blocks(raw_en: str, title: str) -> list[_EnBlock]:
    """Turn a scraped Markdown page into typed blocks, dropping site chrome."""
    blocks: list[_EnBlock] = []
    para: list[str] = []

    def flush() -> None:
        if para:
            blocks.append(_EnBlock("para", " ".join(para)))
            para.clear()

    for raw_line in raw_en.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if _EN_IMAGE.match(line) or _EN_READ_TIME.match(line):
            continue
        if m := _EN_HEADING.match(line):
            flush()
            blocks.append(_EnBlock("head", _plain(m.group(1))))
        elif line.startswith(">"):
            flush()
            body = line.lstrip("> ").strip()
            if body:
                blocks.append(_EnBlock("quote", body))
        elif m := _EN_BULLET.match(line):
            flush()
            blocks.append(_EnBlock("bullet", m.group(1).strip()))
        elif m := _EN_NUMBERED.match(line):
            flush()
            blocks.append(_EnBlock("numbered", m.group(2).strip(), int(m.group(1))))
        elif _is_caps_heading(line) and not para:
            blocks.append(_EnBlock("caps", line))
        elif m := _EN_REDDIT_USER.match(line):
            flush()
            blocks.append(_EnBlock("user", m.group(1) or "[deleted]"))
        elif re.fullmatch(r"\*\*[^*]+\*\*:?", line) and len(line.split()) <= 12:
            flush()
            blocks.append(_EnBlock("label", line))
        else:
            para.append(line)
    flush()

    # Rejoin PDF hard wraps that were split into separate paragraphs.
    merged: list[_EnBlock] = []
    for b in blocks:
        prev = merged[-1] if merged else None
        if (
            (
                prev
                and prev.kind == b.kind == "para"
                and not _EN_SENTENCE_END.search(prev.text)
                and re.match(r"[a-z(“‘\"]", b.text)
            )
            or prev
            and prev.kind == b.kind == "quote"
        ):
            prev.text = f"{prev.text} {b.text}"
        else:
            merged.append(b)

    # Site chrome sits before the first real paragraph: menus, share buttons, counters.
    first_prose = next(
        (
            i
            for i, b in enumerate(merged)
            if b.kind == "para" and len(b.text.split()) >= 18
        ),
        len(merged),
    )
    kept: list[_EnBlock] = []
    for i, b in enumerate(merged):
        words = len(_plain(b.text).split())
        if i < first_prose and (
            b.kind in ("bullet", "numbered") or (b.kind == "para" and words <= 3)
        ):
            continue
        if b.kind == "head" and _norm_title(b.text) == _norm_title(title):
            continue
        kept.append(b)

    # Navigation menus elsewhere: runs of three or more very short bullets.
    result: list[_EnBlock] = []
    i = 0
    while i < len(kept):
        j = i
        while j < len(kept) and kept[j].kind == "bullet":
            j += 1
        run = kept[i:j]
        if run and len(run) >= 3 and all(len(_plain(b.text).split()) <= 4 for b in run):
            i = j
            continue
        if run:
            result.extend(run)
            i = j
        else:
            result.append(kept[i])
            i += 1
    return result


def _en_block_markup(blocks: list[_EnBlock]) -> str:
    out: list[str] = []
    prev_kind = ""
    for b in blocks:
        if b.kind != prev_kind or b.kind not in ("bullet", "numbered"):
            out.append("")
        if b.kind == "head":
            out.append(f"#en-head[{_escape_typst(b.text)}]")
        elif b.kind == "label":
            out.append(f"#en-label[{_en_inline(b.text)}]")
        elif b.kind == "quote":
            out.append(f"#en-quote[{_en_inline(b.text)}]")
        elif b.kind == "bullet":
            out.append(f"- {_en_inline(b.text)}")
        elif b.kind == "numbered":
            out.append(f"{b.number}. {_en_inline(b.text)}")
        else:
            out.append(_en_inline(b.text))
        prev_kind = b.kind
    return "\n".join(out).strip()


def _format_english_original_typst(raw_en: str, title: str = "") -> str:
    """Render blocks; each Reddit `/u/name:` line opens a comment card until the next one."""
    out: list[str] = []
    loose: list[_EnBlock] = []
    user = ""
    comment: list[_EnBlock] = []

    def close_comment() -> None:
        if user and comment and not any(_EN_REDACTED in b.text for b in comment):
            out.append(f'#reddit-comment("{user}")[\n{_en_block_markup(comment)}\n]')
        comment.clear()

    for b in _en_blocks(raw_en, title):
        if b.kind == "user":
            if loose:
                out.append(_en_block_markup(loose))
                loose.clear()
            close_comment()
            user = b.text
        elif b.kind in ("head", "caps"):
            close_comment()
            user = ""
            loose.append(b)
        elif user:
            comment.append(b)
        else:
            loose.append(b)
    close_comment()
    if loose:
        out.append(_en_block_markup(loose))
    return "\n\n".join(out)


def _sanitize_markdown_for_pandoc(text: str) -> str:
    s = text.replace("$", "\\$")
    return s


def render_markdown(book: ParsedReaderBook) -> str:
    h1 = chr(35)
    h2 = chr(35) * 2
    h3 = chr(35) * 3
    h4 = chr(35) * 4
    lines: list[str] = [
        "---",
        f'title: "{book.title}"',
        f'subtitle: "{book.subtitle}"',
        f'author: "{LONDON_TREASURY_SPEC.author}"',
        f'publisher: "{LONDON_TREASURY_SPEC.publisher}"',
        "lang: zh-CN",
        "---",
        "",
        f"{h1} 导读与全书框架",
        "",
        f"**{book.kicker}**  ",
        f"**{book.subtitle}** · {book.edition_line}",
        "",
    ]

    for sec_title, paras in book.intro_sections:
        lines.append(f"\n{h2} {sec_title}\n")
        for p in paras:
            lines.append(f"{_sanitize_markdown_for_pandoc(p)}\n")

    for ch in book.chapters:
        lines.append(f"\n{h1} {ch.title}\n")
        for p in ch.intro_paragraphs:
            lines.append(f"{_sanitize_markdown_for_pandoc(p)}\n")

        for ent in ch.entries:
            lines.append(f"\n{h2} {ent.zh_title}\n")
            lines.append(
                f"**Original Title:** *{_sanitize_markdown_for_pandoc(ent.en_title)}*  "
            )
            lines.append(
                f"**Author / Source:** {_sanitize_markdown_for_pandoc(ent.author_line)}  "
            )
            lines.append(
                f"**Date & Priority:** {_sanitize_markdown_for_pandoc(ent.date_priority_line)}  "
            )
            lines.append(
                f"**Background:** {_sanitize_markdown_for_pandoc(ent.background_line)}  "
            )
            lines.append(
                f"**Verification:** {_sanitize_markdown_for_pandoc(ent.access_line)}  "
            )
            lines.append(f"**Source Link:** [{ent.uri}]({ent.uri})\n")

            lines.append(f"\n{h3} 原文讲了什么\n")
            for p in ent.summary_paragraphs:
                lines.append(f"{_sanitize_markdown_for_pandoc(p)}\n")

            lines.append(f"\n{h3} 带着这个角度读\n")
            for p in ent.angle_paragraphs:
                lines.append(f"{_sanitize_markdown_for_pandoc(p)}\n")

            lines.append(f"\n{h3} 轮岗时核实\n")
            for idx_q, q in enumerate(ent.questions, start=1):
                q_body = re.sub(r"^\d+\s+", "", q.strip())
                lines.append(f"{idx_q}. {_sanitize_markdown_for_pandoc(q_body)}")
            lines.append("")

            lines.append(f"\n{h3} 材料边界\n")
            for p in ent.boundary_paragraphs:
                lines.append(f"{_sanitize_markdown_for_pandoc(p)}\n")

            lines.append(f"\n{h3} 英文原文 (Original English Text)\n")
            lines.append(f"> **Source URL:** [{ent.uri}]({ent.uri})\n")
            clean_en_md = _sanitize_markdown_for_pandoc(ent.original_text)
            clean_en_md = re.sub(
                rf"^{h1}{{1,6}}\s+", f"{h4} ", clean_en_md, flags=re.MULTILINE
            )
            lines.append(f"{clean_en_md}\n")

    lines.append(f"\n{h1} 第七章 轮岗核实、词汇、现行规则与核验资料\n")
    for sec_title, paras, ref_links in book.back_sections:
        lines.append(f"\n{h2} {sec_title}\n")
        for p in paras:
            lines.append(f"{_sanitize_markdown_for_pandoc(p)}\n")
        if ref_links:
            lines.append(f"\n{h3} 提取链接与原文资料 ({len(ref_links)} 项)\n")
            for rlk in ref_links:
                lines.append(
                    f"\n{h4} [{rlk.index:02d}] {_sanitize_markdown_for_pandoc(rlk.label)}\n"
                )
                lines.append(f"**Link:** [{rlk.uri}]({rlk.uri})\n")
                clean_ref = _sanitize_markdown_for_pandoc(rlk.clean_text)
                clean_ref = re.sub(
                    rf"^{h1}{{1,6}}\s+(.+)$", r"**\1**", clean_ref, flags=re.MULTILINE
                )
                lines.append(f"{clean_ref}\n")

    return "\n".join(lines)


def _entry_heading(zh_title: str) -> str:
    """`01 主标题 副标题` → accent number, bold title, muted subtitle."""
    m = re.match(r"(\d+)\s+(\S+)(?:\s+(.+))?$", zh_title.strip())
    if not m:
        return _escape_typst(zh_title)
    num, main, sub = m.groups()
    head = f"#entry-num[{num}]{_escape_typst(main)}"
    return f"{head} #entry-sub[{_escape_typst(sub)}]" if sub else head


def render_typst(book: ParsedReaderBook) -> str:
    out: list[str] = [
        f'#set document(title: "{book.title} — {book.subtitle}", author: "{LONDON_TREASURY_SPEC.author}")',
        TEMPLATE_TYP.read_text(encoding="utf-8"),
        f"""
#page(header: none, footer: none, margin: (x: 54pt, top: 96pt, bottom: 64pt))[
  #set par(first-line-indent: 0pt, justify: false)
  #text(7.6pt, font: sans, weight: "bold", tracking: 0.18em, fill: accent)[{_escape_typst(book.kicker)}]
  #v(14pt)
  #line(length: 100%, stroke: 0.6pt + ink)
  #v(26pt)
  #text(24pt, weight: "bold")[{_escape_typst(book.title)}]
  #v(12pt)
  #text(12.5pt, fill: muted)[{_escape_typst(book.subtitle)}]
  #v(8pt)
  #text(10.5pt, style: "italic", fill: muted, lang: "en")[London Branch Treasury & Trading Reader: a practitioner's guide with 53 primary sources]
  #place(bottom + left)[
  #set text(8.4pt, font: sans, fill: ink)
  #grid(
    columns: (auto, 1fr), column-gutter: 14pt, row-gutter: 8pt,
    meta-label[范围], [{_escape_typst(book.tags[0])}],
    meta-label[材料], [{_escape_typst(book.tags[1])}],
    meta-label[体例], [{_escape_typst(book.tags[2])} · 含53篇英文原文汇编],
  )
  #v(18pt)
  #line(length: 100%, stroke: 0.4pt + rule-c)
  #v(6pt)
  #grid(columns: (1fr, auto),
    text(8pt, fill: muted)[{_escape_typst(LONDON_TREASURY_SPEC.series)}],
    text(8pt, weight: "bold")[{_escape_typst(book.edition_line)}])
  ]
]

#outline(title: text(15pt, font: sans, weight: "bold")[目录], indent: 1.2em, depth: 2)
""",
    ]

    out.append("= 导读与全书框架\n")
    for sec_title, paras in book.intro_sections:
        out.append(f"== {_escape_typst(sec_title)}\n")
        for p in paras:
            out.append(f"{_escape_typst(p)}\n")

    for ch in book.chapters:
        out.append(f"= {_escape_typst(ch.title)}\n")
        for p in ch.intro_paragraphs:
            out.append(f"{_escape_typst(p)}\n")

        for ent in ch.entries:
            out.append(f"\n#pagebreak(weak: true)\n== {_entry_heading(ent.zh_title)}\n")
            date_line, _, priority = ent.date_priority_line.partition("|")
            priority_arg = (
                f"[{_escape_typst(priority.strip())}]" if priority.strip() else "none"
            )
            out.append(
                f'#meta-card([{_escape_typst(ent.en_title)}], "{ent.uri}", '
                f"[{_escape_typst(ent.author_line)}], [{_escape_typst(date_line.strip())}], "
                f"{priority_arg}, [{_escape_typst(ent.background_line)}], "
                f"[{_escape_typst(ent.access_line)}])\n"
            )
            out.append("=== 原文讲了什么\n")
            for p in ent.summary_paragraphs:
                out.append(f"{_escape_typst(p)}\n")

            out.append("=== 带着这个角度读\n")
            for p in ent.angle_paragraphs:
                out.append(f"{_escape_typst(p)}\n")

            out.append("=== 轮岗时核实\n")
            for q in ent.questions:
                q_body = re.sub(r"^\d+\s+", "", q.strip())
                out.append(f"+ {_escape_typst(q_body)}")
            out.append("")

            out.append("=== 材料边界\n")
            for p in ent.boundary_paragraphs:
                out.append(f"{_escape_typst(p)}\n")

            out.append("=== 英文原文\n")
            formatted_en = _format_english_original_typst(
                ent.original_text, ent.en_title
            )
            out.append(
                f'#source-text([{_escape_typst(ent.en_title)}], "{ent.uri}")[\n{formatted_en}\n]\n'
            )

    out.append("= 第七章 轮岗核实、词汇、现行规则与核验资料\n")
    for sec_title, paras, ref_links in book.back_sections:
        out.append(f"== {_escape_typst(sec_title)}\n")
        if sec_title == "一次业务复原的记录页":
            out.append(f"{_escape_typst(paras[0])}\n")
            out.append(
                "#v(0.6em)\n#table(\n  columns: (135pt, 1fr),\n  stroke: 0.4pt + luma(160),\n  inset: 7pt,\n"
            )
            for row_p in paras[1:]:
                clean_row = re.sub(r"_+", "", row_p).strip()
                parts = clean_row.split(" ", 1)
                col1 = _escape_typst(parts[0])
                col2 = _escape_typst(parts[1]) if len(parts) > 1 else ""
                out.append(f"  [#strong[{col1}]], [{col2}],")
            out.append(")\n")
        else:
            for p in paras:
                out.append(f"{_escape_typst(p)}\n")

        if ref_links:
            out.append(f"=== 提取链接与原文资料（共 {len(ref_links)} 项）\n")
            for rlk in ref_links:
                title = rlk.en_title or rlk.label
                formatted_ref = _format_english_original_typst(rlk.clean_text, title)
                out.append(
                    f'#source-text([#entry-num[{rlk.index:02d}]{_escape_typst(title)}], "{rlk.uri}")'
                    f"[\n{formatted_ref}\n]\n"
                )

    return "\n".join(out)


def build_london_treasury(
    source_pdf: Path | None = None, out_dir: Path | None = None
) -> MonographOutputs:
    src = source_pdf or DEFAULT_SOURCE_PDF
    target_dir = out_dir or Path("output/london_treasury")
    target_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_reader_pdf(src, target_dir)
    md_text = render_markdown(parsed)
    typ_text = render_typst(parsed)

    slug = LONDON_TREASURY_SPEC.slug
    md_path = target_dir / f"{slug}.md"
    typ_path = target_dir / f"{slug}.typ"
    tex_path = target_dir / f"{slug}.tex"
    pdf_path = target_dir / f"{slug}.pdf"
    epub_path = target_dir / f"{slug}.epub"

    md_path.write_text(md_text, encoding="utf-8")
    typ_path.write_text(typ_text, encoding="utf-8")

    compile_typst(typ_path, pdf_path)

    subprocess.run(
        [
            "pandoc",
            str(md_path),
            "-f",
            "markdown-tex_math_dollars-raw_tex-raw_html",
            "-t",
            "latex",
            "-s",
            "--toc",
            "--top-level-division=chapter",
            "-V",
            "documentclass=ctexbook",
            "-V",
            "geometry:margin=2.4cm",
            "-o",
            str(tex_path),
        ],
        check=True,
    )

    css_path = target_dir / "epub.css"
    css_path.write_text(
        """body { font-family: "Songti SC", "PingFang SC", "Baskervville", serif; line-height: 1.68; margin: 5%; }
h1, h2, h3, h4 { font-family: "PingFang SC", "Heiti SC", sans-serif; color: #111827; margin-top: 1.4em; }
blockquote { border-left: 3px solid #64748b; padding-left: 1em; color: #334155; }
""",
        encoding="utf-8",
    )
    subprocess.run(
        [
            "pandoc",
            str(md_path),
            "-f",
            "markdown-tex_math_dollars-raw_tex-raw_html",
            "-t",
            "epub3",
            "--toc",
            "--toc-depth=2",
            "--css",
            str(css_path),
            "--metadata",
            f"title={parsed.title}",
            "--metadata",
            f"author={LONDON_TREASURY_SPEC.author}",
            "--metadata",
            "lang=zh-CN",
            "-o",
            str(epub_path),
        ],
        check=True,
    )

    for src_f, alias_name in (
        (md_path, "book.md"),
        (typ_path, "book.typ"),
        (tex_path, "book.tex"),
        (pdf_path, "book.pdf"),
        (epub_path, "book.epub"),
    ):
        shutil.copy2(src_f, target_dir / alias_name)

    with pymupdf.open(pdf_path) as built_doc:
        total_pages = len(built_doc)

    return MonographOutputs(
        markdown_path=md_path,
        latex_path=tex_path,
        typst_path=typ_path,
        pdf_path=pdf_path,
        total_pages=total_pages,
    )
