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

from ..compiler.monograph import REPO_FONTS_DIR, MonographOutputs, compile_typst
from ..parity.source import source_pdf as resolve_source_pdf
from .spec import LONDON_TREASURY_SPEC

TEMPLATE_TYP = Path(__file__).with_name("template.typ")
TRIMS_JSON = Path(__file__).with_name("trims.json")
EPUB_CSS = Path(__file__).with_name("epub.css")
ICONS_DIR = Path(__file__).with_name("icons")
EPUB_FONTS = ("SourceSerif4-Regular", "SourceSerif4-It", "SourceSerif4-Bold", "SourceSerif4-BoldIt", "SourceSans3-Regular", "SourceSans3-Bold")
SIMPLE_ICONS_REDDIT_PATH = "M12 0C5.373 0 0 5.373 0 12c0 3.314 1.343 6.314 3.515 8.485l-2.286 2.286C.775 23.225 1.097 24 1.738 24H12c6.627 0 12-5.373 12-12S18.627 0 12 0Zm4.388 3.199c1.104 0 1.999.895 1.999 1.999 0 1.105-.895 2-1.999 2-.946 0-1.739-.657-1.947-1.539v.002c-1.147.162-2.032 1.15-2.032 2.341v.007c1.776.067 3.4.567 4.686 1.363.473-.363 1.064-.58 1.707-.58 1.547 0 2.802 1.254 2.802 2.802 0 1.117-.655 2.081-1.601 2.531-.088 3.256-3.637 5.876-7.997 5.876-4.361 0-7.905-2.617-7.998-5.87-.954-.447-1.614-1.415-1.614-2.538 0-1.548 1.255-2.802 2.803-2.802.645 0 1.239.218 1.712.585 1.275-.79 2.881-1.291 4.64-1.365v-.01c0-1.663 1.263-3.034 2.88-3.207.188-.911.993-1.595 1.959-1.595Zm-8.085 8.376c-.784 0-1.459.78-1.506 1.797-.047 1.016.64 1.429 1.426 1.429.786 0 1.371-.369 1.418-1.385.047-1.017-.553-1.841-1.338-1.841Zm7.406 0c-.786 0-1.385.824-1.338 1.841.047 1.017.634 1.385 1.418 1.385.785 0 1.473-.413 1.426-1.429-.046-1.017-.721-1.797-1.506-1.797Zm-3.703 4.013c-.974 0-1.907.048-2.77.135-.147.015-.241.168-.183.305.483 1.154 1.622 1.964 2.953 1.964 1.33 0 2.47-.81 2.953-1.964.057-.137-.037-.29-.184-.305-.863-.087-1.795-.135-2.769-.135Z"
REDDIT_ORANGE = "#ff4500"
REDDIT_DELETED = "#aaaaaa"
REDDIT_PALETTE = ("#ff4500", "#0079d3", "#46a758", "#d9a400", "#7193ff", "#e0569e", "#00a6a5", "#9a6bd6")

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


_RESOLVED_LINKS = {
    "https://apple.news/AJTR4Hew8QSama-mtyy2Xpw": "https://www.politico.com/news/2026/03/19/trump-powell-fed-chair-doj-probe-warsh-00836447",
}
_LINK_TITLES = {
    "https://www.wallstreetoasis.com/resources/skills/strategy/shareholder-value": "Shareholder Value",
    "https://www.wallstreetoasis.com/forums/why-choose-sales-and-trading-over-investment-banking": "Why choose Sales and Trading over Investment Banking?",
    "https://www.wallstreetoasis.com/faq/what-are-the-best-qa-threads-and-interviews-with-top-finance-professionals-on-wso": "What are the best Q&A threads and interviews with top finance professionals on WSO?",
    "http://www.traders-library.com": "Traders’ Library",
    "http://govttrader.blogspot.com": "Govt Trader",
}
_URL_TEXT = re.compile(r"(?:https?://|www\.)\S+")
_BARE_URL = re.compile(r"(?<![(\[<\"/\w])https?://[^\s)\]>]*[^\s)\]>.,;:!?]")


def _link_title(url: str) -> str | None:
    return _LINK_TITLES.get(url.split("#")[0].rstrip("/"))


def _title_bare_url(m: re.Match[str]) -> str:
    title = _link_title(m.group(0))
    return f"[{title}]({m.group(0)})" if title else m.group(0)


def _unwrap_links(text: str, url: str, keep_web: bool = False) -> str:
    def label(m: re.Match[str]) -> str:
        before = text[m.start() - 1] if m.start() else ""
        after = text[m.end()] if m.end() < len(text) else ""
        lead = " " if before.isalnum() and m.group(1)[0].isalnum() else ""
        trail = " " if after.isalnum() and m.group(1)[-1].isalnum() else ""
        target = (m.group(2).split() or [""])[0]
        if keep_web and target.startswith("http"):
            target = _RESOLVED_LINKS.get(target, re.sub(r"[?&](?:cid|utm_\w+)=[^&]*$", "", target))
            return f"{lead}[{m.group(1)}]({target}){trail}"
        if _URL_TEXT.fullmatch(m.group(1)) and target.startswith("http"):
            return lead + target + trail
        return lead + m.group(1) + trail

    return re.sub(rf"\[([^\]]+)\]\(({url})\)", label, text)


def _join_drop_caps(lines: list[str]) -> list[str]:
    text = "\n".join(lines)

    def join(m: re.Match[str]) -> str:
        rest = m.group(2)
        fragment = len(rest) == 1 or len(re.findall(rf"\b{rest}\b", text)) == 1
        return m.group(1) + rest if fragment else m.group(0)

    return [re.sub(r"^([A-Z]) ([a-z]+)\b", join, l) for l in lines]


_WSO_AUTHOR = re.compile(r"^\[([^\]]+)\]\(https://www\.wallstreetoasis\.com/user/\d+\)(.*)$", re.MULTILINE)
_WSO_ROLE = re.compile(r'user-industry-and-status-key\s+"([^"]*)"')
_WSO_BADGE = re.compile(r"ranking-badges/([a-z-]+)-small\.svg")
_WSO_BOT_COMMENT = re.compile(r"^\*\*@\w+/WSO Monkey Bot\b.*?(?=^\*\*@|\Z)", re.MULTILINE | re.DOTALL)
_WSO_PROMO = re.compile(
    r"^(?:\[[^\]]*\]\(https://www\.wallstreetoasis\.com/resources/[^)]*\)\s*|\[See my WSO Blog\].*)$",
    re.MULTILINE,
)
_WSO_ANON = re.compile(
    r'^\[[A-Z&]{1,4}\]\(https://www\.wallstreetoasis\.com/page/user-industry-status "[^"]*"\)\s*\n\s*\n(.+?)\s*$',
    re.MULTILINE,
)
_WSO_ANON_MONKEY = re.compile(r"^\s*Anonymous Monkey\b.*$", re.MULTILINE)
_WSO_TAGS = re.compile(r"^(?:Keywords|Region)\n.*?^\d+ Comments$", re.MULTILINE | re.DOTALL)
_WSO_ACADEMY = re.compile(r"^(?:#+ )?\d+ WSO Academy .*?^\d+ Comments$", re.MULTILINE | re.DOTALL)
_WSO_PLAIN_TOP = re.compile(
    r"^ Forums\n .+\n[A-Z][a-z]{2} \d{1,2}, \d{4}\n(.+)\n(.+)\n[A-Za-z&]{1,4}\nSubscribe\nShare\n", re.MULTILINE
)
_WSO_PLAIN_TAIL = re.compile(r"^Reply\nQuote\nReport\nOther\n.*?(?=^\xa0$|\Z)", re.MULTILINE | re.DOTALL)
_WSO_PLAIN_HEAD = re.compile(r"^\xa0\n(.+)\n[A-Za-z&]{1,4}\n\d+[a-z]{1,2}\n(?:Best Response\n)?", re.MULTILINE)
WSO_ICONS = ("monkey", "orangutan", "gorilla", "human", "anon")
_WSO_RANK_ICON = {
    "orangutan": "orangutan",
    "neanderthal": "orangutan",
    "senior-neanderthal": "orangutan",
    "gorilla": "gorilla",
    "senior-gorilla": "gorilla",
    "king-kong": "gorilla",
    "almost-human": "human",
    "human": "human",
    "the-pro": "human",
    "the-addict": "human",
}


def _wso_icon_svg(name: str) -> str:
    return " ".join((ICONS_DIR / f"wso-{name}.svg").read_text(encoding="utf-8").split())


def _wso_author(m: re.Match[str]) -> str:
    role = _WSO_ROLE.search(m.group(2))
    badge = _WSO_BADGE.search(m.group(2))
    icon = _WSO_RANK_ICON.get(badge.group(1), "monkey") if badge else "monkey"
    parts = [p for p in role.group(1).split(" - ") if p not in ("Other", "N/A", "0")] if role else []
    if any(p.startswith("No ") for p in parts):
        parts = []
    return f"**@{icon}/{m.group(1)} ({' · '.join(parts)}):**" if parts else f"**@{icon}/{m.group(1)}:**"


def _wso_plain_comments(text: str) -> str:
    parts = _WSO_PLAIN_HEAD.split(_WSO_PLAIN_TAIL.sub("", text))
    split_paras = lambda s: [p.strip() for p in re.split(r"\n\s*\n", s) if p.strip()]
    seen = set(split_paras(parts[0]))
    out = [parts[0]]
    for name, body in zip(parts[1::2], parts[2::2]):
        paras = split_paras(body)
        quote: list[str] = []
        if paras and not body.startswith("\n"):
            first = paras.pop(0)
            k = next((k for k in range(1, len(first)) if first[k:].strip() in seen), 0)
            if k:
                quote.append(first[k:].strip())
                while paras and paras[0] in seen:
                    quote.append(paras.pop(0))
            elif re.match(r"PM[A-Z]", first):
                paras.insert(0, f"*PM:* {first[2:]}")
            elif "][quote=" not in first:
                paras.insert(0, first)
        seen.update(paras)
        out.append(f"\n**@monkey/{name}:**\n\n" + "".join(f"> {q}\n\n" for q in quote) + "\n\n".join(paras) + "\n")
    return "".join(out)


def clean_wso_thread(raw_text: str, en_title: str) -> str:
    h1_pat = "^" + chr(35) + r"\s+(?!WSO)(.+)$"
    m = re.search(h1_pat, raw_text, flags=re.MULTILINE)
    start = m.start() if m else 0
    top = _WSO_PLAIN_TOP.search(raw_text)
    if top and not m:
        raw_text = raw_text[: top.start()] + f"# {top[1]}\n\n**@monkey/{top[2]}:**\n\n" + raw_text[top.end() :]
        start = top.start()
    elif not m and en_title:
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

    slice_txt = _WSO_ACADEMY.sub("", _WSO_TAGS.sub("", raw_text[start:end]))
    slice_txt = _WSO_ANON.sub(r"**@anon/\1:**", _wso_plain_comments(slice_txt))
    slice_txt = _WSO_ANON_MONKEY.sub("**@anon/Anonymous Monkey:**", slice_txt)
    slice_txt = _WSO_PROMO.sub("", _WSO_AUTHOR.sub(_wso_author, slice_txt))
    slice_txt = _WSO_BOT_COMMENT.sub("", slice_txt)
    slice_txt = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", "", slice_txt)
    slice_txt = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", slice_txt)
    slice_txt = re.sub(r"\[\]\([^)]*\)", "", slice_txt)
    slice_txt = _unwrap_links(slice_txt, r"(?:[^()]|\([^()]*\))*")

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


_BROCHURE_FOOTER = re.compile(r"[ \t]*(?:The BTRM Faculty\s+)?(?:\b\d{1,2}[ \t]*www\. ?|www\. )btrm\.org[ \t]*")
_BROCHURE_CREDIT = re.compile(r"\s*Brochure design:.*$", re.MULTILINE)
_BROCHURE_BIO = re.compile(r"([A-Z][^\s]*(?: [^\s]+){1,7}?)  (\S+ \S+.*)", re.DOTALL)


def _brochure_bio_head(p: str) -> str:
    m = _BROCHURE_BIO.match(p)
    if m and set(m[2].split()[:2]) & set(m[1].split()):
        return f"#### {m[1]}\n\n{m[2]}"
    return p


def _join_brochure_lines(lines: list[str]) -> list[str]:
    text = _BROCHURE_CREDIT.sub("", _BROCHURE_FOOTER.sub("\n\n", "\n".join(lines)))
    words = set(re.findall(r"[a-z]+", text))
    text = re.sub(
        r"\b([A-Za-z][a-z]*)-([a-z]+)\b",
        lambda m: m[1] + m[2] if (m[1] + m[2]).lower() in words else m[0],
        text,
    )
    out: list[str] = []
    paras = (_brochure_bio_head(p.strip()) for p in re.split(r"\n\s*\n", text) if p.strip())
    for p in (q for para in paras for q in para.split("\n\n")):
        prev = out[-1] if out else ""
        plain = prev and not prev.startswith(("#", "*", "-")) and not p.startswith(("#", "*", "-", "•"))
        runs_on = plain and (
            p[0].islower() or (len(prev.split()) >= 8 and not re.search(r"[.!?:;\"”’)\]]$", prev))
        )
        if runs_on:
            out[-1] = prev + p if re.search(r"[a-z]-$", prev) else f"{prev} {p}"
        else:
            out.append(p)
    return "\n\n".join(out).splitlines()


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
    text = _unwrap_links(text, r"(?:https?://|mailto:|tel:|javascript:|/|#)(?:[^()]|\([^()]*\))*", keep_web=True)

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
        if uri.endswith(".pdf"):
            lines = _join_brochure_lines(lines)

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
        lines = _join_drop_caps(lines[start_idx:end_idx])

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


_TRIMS = json.loads(TRIMS_JSON.read_text(encoding="utf-8"))
_NESTED_LINK = re.compile(r"\[((?:[^\[\]\n]|\[[^\[\]\n]*\])*)\]\(((?:[^()\s]|\([^()\s]*\))*)(?:\s+\"[^\"]*\")?\)")


def _relink(m: re.Match[str]) -> str:
    label, target = m.group(1), m.group(2)
    if not label.strip("[]- "):
        return ""
    if target.startswith("http") and "[" not in label:
        if _URL_TEXT.fullmatch(label):
            label = _link_title(target) or label
        return f"[{label}]({target})"
    return label
_CHECKBOX = re.compile(r"(?:^|[-*+])\s*\[[ xX]\]")
_CHROME_LINE = re.compile(
    r"[*\-+•>]+(?:\s+\S)?|(?:[*\-_]\s*){3,}|[*\-+]\s+\d+|#+|\d+:\d\d"
    r"|Subscribe|Share|Tweet|Bump|Best Response|Add Comment|Read Full Bot Response|Show more|TOP OF PAGE"
    r"|Authored by: Certified .*|Previous article.*|Next article.*|More about this author|\d+ Footnotes?"
)
_SOCIAL_LINE = re.compile(
    r"(?i)join our .{0,40} on|@\w+|stay connected|video \d+"
    r"|(?:[*\-+]\s+)?(?:linkedin|youtube|twitter|facebook|instagram|ig)"
    r"|.{0,160}\bfollow us\b.{0,80}"
)
_CLICK_VIDEO = re.compile(r"\s*click\s+\[Video \d+\]\([^)]*\)\s*VIDEO")
_LOREM = frozenset(
    ["lorem", "ipsum", "dolor", "dolore", "dolorum", "dolores", "et", "ut", "id", "eos", "qui", "quia", "quae", "quis", "quo", "est", "sit", "amet", "aut", "perferendis", "aliquam", "expedita", "perspiciatis", "minus", "omnis", "quasi", "corporis", "explicabo", "rerum", "molestiae", "saepe", "exercitationem", "nulla", "optio", "pariatur", "totam", "sapiente", "sint", "nihil", "magni", "ratione", "nemo", "neque", "enim", "fugiat", "fugit", "velit", "vel", "iure", "illum", "alias", "ea", "eum", "eius", "esse", "animi", "atque", "culpa", "officia", "natus", "nobis", "odio", "porro", "quam", "quas", "ipsa", "iste", "itaque", "minima", "modi", "nam", "numquam", "vero", "voluptate", "tempora"]
) | LATIN_OBFUSCATION_WORDS


def _is_lorem(line: str) -> bool:
    words = [w.lower().strip(".,?!:;\"'()") for w in line.split()]
    return len(words) >= 5 and sum(w in _LOREM for w in words) >= 0.6 * len(words)


def _find_line(lines: list[str], anchor: list, after: int, uri: str) -> int:
    text, nth = anchor
    hits = [i for i, l in enumerate(lines) if l.strip() == text]
    if len(hits) <= nth or hits[nth] < after:
        raise ValueError(f"trim anchor {anchor!r} not found in {uri}")
    return hits[nth]


def trim_article(uri: str, text: str) -> str:
    trim = _TRIMS.get(uri)
    if not trim:
        return text
    lines = text.splitlines()
    start = _find_line(lines, trim["start"], 0, uri)
    end = _find_line(lines, trim["end"], start, uri)
    keep = [True] * len(lines)
    for first, last in trim.get("drop", []):
        a = _find_line(lines, first, start, uri)
        b = _find_line(lines, last, a, uri)
        keep[a : b + 1] = [False] * (b + 1 - a)
    return "\n".join(l for i, l in enumerate(lines[: end + 1]) if i >= start and keep[i])


def polish_article(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines():
        line = _BARE_URL.sub(_title_bare_url, _CLICK_VIDEO.sub("", _NESTED_LINK.sub(_relink, line)))
        s = _plain_links(line).strip()
        if (
            (_CHECKBOX.search(s) and len(s.split()) <= 12)
            or _CHROME_LINE.fullmatch(s)
            or _SOCIAL_LINE.fullmatch(s.strip("*_ "))
            or _is_lorem(s)
        ):
            continue
        out.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


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

    cleaned = polish_article(trim_article(uri, clean_single_link(uri, raw_text, en_title)))
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


def _escape_typst_str(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


_EN_INLINE = re.compile(
    r"\[(?P<ltext>[^\]\n]+)\]\((?P<lurl>(?:[^()\s]|\([^()\s]*\))+)\)"
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
_EN_DANGLING = re.compile(r"(?:,|\b(?:the|of|and|with|a|an|to|in|for|on|by|or|from|that))$")
_EN_TOC_ROW = re.compile(r"(.{3,60}?)\s+(\d{1,3})")
_EN_REDDIT_USER = re.compile(r"^\*{0,2}(?:/u/([\w-]+))?:\*{0,2}$")
_EN_WSO_USER = re.compile(r"^\*\*@(\w+)/(.+?)(?: \((.+)\))?:\*\*$")
_EN_REDACTED = "This post was mass deleted and anonymized with"


def _en_inline(text: str) -> str:
    out: list[str] = []
    pos = 0
    for m in _EN_INLINE.finditer(text):
        out.append(_escape_typst(text[pos : m.start()]))
        if m.group("ltext") and re.fullmatch(r"\d{1,2}", m.group("ltext")):
            out.append(f"#super[{m.group('ltext')}]")
        elif m.group("ltext"):
            label = _en_inline(m.group("ltext"))
            url = _escape_typst_str(m.group("lurl"))
            out.append(f'#link("{url}")[{label}];' if url.startswith("http") else label)
        elif m.group("bold"):
            out.append(f"#strong[{_en_inline(m.group('bold'))}];")
        else:
            out.append(f"#emph[{_escape_typst(m.group('istar') or m.group('iund'))}];")
        pos = m.end()
    out.append(_escape_typst(text[pos:]))
    return "".join(out)


def _plain_links(text: str) -> str:
    return re.sub(r"\[([^\]]*)\]\((?:[^()]|\([^()]*\))*\)", r"\1", text)


def _plain(text: str) -> str:
    return re.sub(r"[*_#>\[\]]", "", _plain_links(text)).strip()


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
    role: str | None = None
    icon: str = ""


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
            item = m.group(1).strip()
            if h := _EN_HEADING.match(item):
                blocks.append(_EnBlock("term", _plain(h.group(1))))
            else:
                blocks.append(_EnBlock("bullet", item))
        elif m := _EN_NUMBERED.match(line):
            flush()
            blocks.append(_EnBlock("numbered", m.group(2).strip(), int(m.group(1))))
        elif _is_caps_heading(line) and not para:
            blocks.append(_EnBlock("caps", line))
        elif m := _EN_REDDIT_USER.match(line):
            flush()
            blocks.append(_EnBlock("user", m.group(1) or "[deleted]"))
        elif m := _EN_WSO_USER.match(line):
            flush()
            blocks.append(_EnBlock("user", m.group(2), role=m.group(3) or "", icon=m.group(1)))
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
        if prev and prev.kind == "term" and b.kind == "para":
            prev.kind, prev.text = "bullet", f"**{prev.text}** {b.text}"
        elif prev and prev.kind == "head" and b.kind == "para" and re.fullmatch(r"\d+(?:\.\d+)+", prev.text):
            prev.kind, prev.text = "para", f"**{prev.text}** {b.text}"
        elif (
            prev
            and prev.kind in ("bullet", "numbered")
            and b.kind == "para"
            and not _EN_SENTENCE_END.search(prev.text)
            and re.match(r"[a-z]", b.text)
        ) or (
            prev
            and prev.kind == b.kind == "head"
            and not _EN_SENTENCE_END.search(prev.text)
            and re.match(r"[a-z]", b.text)
        ) or (prev and prev.kind == b.kind == "para" and _EN_DANGLING.search(prev.text)) or (
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

    i = 0
    while i < len(merged):
        j = i
        while j < len(merged) and merged[j].kind == "para" and _EN_TOC_ROW.fullmatch(merged[j].text):
            j += 1
        if j - i >= 4:
            for b in merged[i:j]:
                b.kind = "toc"
        i = max(j, i + 1)

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
        elif b.kind == "term":
            out.append(f"- #strong[{_escape_typst(b.text)}]")
        elif b.kind == "toc":
            entry, page = _EN_TOC_ROW.fullmatch(b.text).groups()
            out.append(f"#en-toc[{_en_inline(entry)}][{page}]")
        elif b.kind == "numbered":
            out.append(f"{b.number}. {_en_inline(b.text)}")
        else:
            out.append(_en_inline(b.text))
        prev_kind = b.kind
    return "\n".join(out).strip()


def _english_groups(raw_en: str, title: str) -> list[tuple[_EnBlock | None, list[_EnBlock]]]:
    groups: list[tuple[_EnBlock | None, list[_EnBlock]]] = [(None, [])]
    for b in _en_blocks(raw_en, title):
        if b.kind == "user":
            groups.append((b, []))
            continue
        if b.kind in ("head", "caps") and groups[-1][0]:
            groups.append((None, []))
        groups[-1][1].append(b)
    return [
        (user, blocks)
        for user, blocks in groups
        if blocks and not (user and any(_EN_REDACTED in b.text for b in blocks))
    ]


def _format_english_original_typst(raw_en: str, title: str = "") -> str:
    """Render blocks; each Reddit `/u/name:` line opens a comment card until the next one."""
    out: list[str] = []
    for user, blocks in _english_groups(raw_en, title):
        if user is None:
            out.append(_en_block_markup(blocks))
            continue
        args = f'"{_escape_typst_str(user.text)}"'
        if user.role is not None:
            args += f', prefix: "", tag: "{_escape_typst_str(user.role)}", icon: wso-icons.at("{user.icon}")'
        out.append(f"#reddit-comment({args})[\n{_en_block_markup(blocks)}\n]")
    return "\n\n".join(out)


def _sanitize_markdown_for_pandoc(text: str) -> str:
    s = text.replace("$", "\\$")
    return s


def _md_reading_sections(ent: ArticleEntry) -> list[str]:
    lines: list[str] = []
    for heading, paras in (("原文讲了什么", ent.summary_paragraphs), ("带着这个角度读", ent.angle_paragraphs)):
        lines.append(f"\n### {heading}\n")
        lines.extend(f"{_sanitize_markdown_for_pandoc(p)}\n" for p in paras)
    lines.append("\n### 轮岗时核实\n")
    for idx_q, q in enumerate(ent.questions, start=1):
        q_body = re.sub(r"^\d+\s+", "", q.strip())
        lines.append(f"{idx_q}. {_sanitize_markdown_for_pandoc(q_body)}")
    lines.append("")
    lines.append("\n### 材料边界\n")
    lines.extend(f"{_sanitize_markdown_for_pandoc(p)}\n" for p in ent.boundary_paragraphs)
    return lines


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
            lines.append(f"**Source Link:** [{ent.en_title}]({ent.uri})\n")
            lines.extend(_md_reading_sections(ent))
            lines.append(f"\n{h3} 英文原文 (Original English Text)\n")
            lines.append(f"> **Source:** [{ent.en_title}]({ent.uri})\n")
            clean_en_md = _sanitize_markdown_for_pandoc(ent.original_text)
            clean_en_md = re.sub(
                _EN_WSO_USER.pattern,
                lambda m: f"**{m[2]}**" + (f" · *{m[3]}*" if m[3] else ""),
                clean_en_md,
                flags=re.MULTILINE,
            )
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
                lines.append(f"**Link:** [{rlk.en_title or rlk.label}]({rlk.uri})\n")
                clean_ref = _sanitize_markdown_for_pandoc(rlk.clean_text)
                clean_ref = re.sub(
                    rf"^{h1}{{1,6}}\s+(.+)$", r"**\1**", clean_ref, flags=re.MULTILINE
                )
                lines.append(f"{clean_ref}\n")

    return "\n".join(lines)


_EN_FOOTREF = re.compile(r"\[(\d{1,2})\]\((https?://[^)\s]+)\)")


def _md_literal(text: str) -> str:
    return re.sub(r"([\\\[\]*_`])", r"\\\1", text)


def _avatar_hue(name: str) -> int:
    h = 7
    for c in name:
        h = (h * 31 + ord(c)) % 9973
    return h % len(REDDIT_PALETTE)


def _reddit_svg(fill: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{fill}" d="{SIMPLE_ICONS_REDDIT_PATH}"/></svg>'


def _write_epub_assets(asset_dir: Path) -> None:
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "reddit-logo.svg").write_text(_reddit_svg(REDDIT_ORANGE), encoding="utf-8")
    (asset_dir / "reddit-grey.svg").write_text(_reddit_svg(REDDIT_DELETED), encoding="utf-8")
    for i, color in enumerate(REDDIT_PALETTE):
        (asset_dir / f"reddit-{i}.svg").write_text(_reddit_svg(color), encoding="utf-8")
    for name in WSO_ICONS:
        shutil.copy2(ICONS_DIR / f"wso-{name}.svg", asset_dir)


def _en_blocks_md(blocks: list[_EnBlock]) -> str:
    out: list[str] = []
    list_kinds = {"bullet", "term"}
    prev = ""
    for b in blocks:
        text = _EN_FOOTREF.sub(r"^[\1](\2)^", b.text)
        if b.kind == "head":
            line = f"#### {text}"
        elif b.kind == "caps":
            line = f"[{text}]{{.en-caps}}"
        elif b.kind == "quote":
            line = f"> {text}"
        elif b.kind == "bullet":
            line = f"- {text}"
        elif b.kind == "term":
            line = f"- **{text}**"
        elif b.kind == "toc":
            entry, page = _EN_TOC_ROW.fullmatch(b.text).groups()
            line = f"[{entry}]{{.toc-entry}} [{page}]{{.toc-page}}"
        elif b.kind == "numbered":
            line = f"{b.number}. {text}"
        else:
            line = text
        tight = {b.kind, prev} <= list_kinds or b.kind == prev == "numbered"
        out.append(("\n" if tight else "\n\n") + line)
        prev = b.kind
    return "".join(out).strip()


def _epub_comment(user: _EnBlock, blocks: list[_EnBlock]) -> str:
    deleted = user.text.startswith("[")
    hue = "grey" if deleted else str(_avatar_hue(user.text))
    if user.role is None:
        avatar = f"![](reddit-{hue}.svg){{.avatar}}"
        name = user.text if deleted else f"u/{user.text}"
    else:
        avatar = f"![](wso-{user.icon}.svg){{.avatar .wso .tint-{hue}}}"
        name = user.text
    role = f" [{_md_literal(user.role)}]{{.role}}" if user.role else ""
    head = f"{avatar} [{_md_literal(name)}]{{.handle}}{role}"
    return f":::: comment\n::: comment-head\n{head}\n:::\n\n{_en_blocks_md(blocks)}\n::::"


def _reddit_logo_md(uri: str) -> str:
    return "![](reddit-logo.svg){.logo} " if "reddit.com" in uri else ""


def _epub_source_text(title: str, uri: str, raw_en: str, num: str = "") -> str:
    prefix = f"[{num}]{{.entry-num}} " if num else ""
    parts = [f"::: source-title\n{prefix}{_reddit_logo_md(uri)}[{_md_literal(title)}]({uri})\n:::"]
    for user, blocks in _english_groups(raw_en, title):
        parts.append(_en_blocks_md(blocks) if user is None else _epub_comment(user, blocks))
    return '::::: {.source-text lang="en"}\n' + "\n\n".join(parts) + "\n:::::\n"


def _epub_meta_card(ent: ArticleEntry) -> str:
    date_line, _, priority = ent.date_priority_line.partition("|")
    badge = f" [{priority.strip()}]{{.priority}}" if priority.strip() else ""
    title = f"[{_reddit_logo_md(ent.uri)}[{_md_literal(ent.en_title)}]({ent.uri})]{{.meta-title}}{badge}"
    rows = (
        ("作者", ent.author_line),
        ("日期", date_line.strip()),
        ("出处", ent.background_line),
        ("获取", ent.access_line),
    )
    body = "\n\n".join(f"[{k}]{{.meta-label}} {_sanitize_markdown_for_pandoc(v)}" for k, v in rows)
    return f"::: meta-card\n{title}\n\n{body}\n:::\n"


def _epub_entry_heading(zh_title: str) -> str:
    m = re.match(r"(\d+)\s+(\S+)(?:\s+(.+))?$", zh_title.strip())
    if not m:
        return zh_title
    num, main, sub = m.groups()
    return f"[{num}]{{.entry-num}} {main}" + (f" [{sub}]{{.entry-sub}}" if sub else "")


def render_epub_markdown(book: ParsedReaderBook) -> str:
    lines: list[str] = [
        "---",
        f'title: "{book.title}"',
        f'subtitle: "{book.subtitle}"',
        f'author: "{LONDON_TREASURY_SPEC.author}"',
        f'publisher: "{LONDON_TREASURY_SPEC.publisher}"',
        "lang: zh-CN",
        "---",
        "",
        "# 导读与全书框架",
        "",
        f"[{book.kicker}]{{.kicker}}",
        "",
        f"**{book.subtitle}** · {book.edition_line}",
        "",
    ]
    for sec_title, paras in book.intro_sections:
        lines.append(f"\n## {sec_title}\n")
        lines.extend(f"{_sanitize_markdown_for_pandoc(p)}\n" for p in paras)

    for ch in book.chapters:
        lines.append(f"\n# {ch.title}\n")
        lines.extend(f"{_sanitize_markdown_for_pandoc(p)}\n" for p in ch.intro_paragraphs)
        for ent in ch.entries:
            lines.append(f"\n## {_epub_entry_heading(ent.zh_title)}\n")
            lines.append(_epub_meta_card(ent))
            lines.extend(_md_reading_sections(ent))
            lines.append("\n### 英文原文\n")
            lines.append(_epub_source_text(ent.en_title, ent.uri, ent.original_text))

    lines.append("\n# 第七章 轮岗核实、词汇、现行规则与核验资料\n")
    for sec_title, paras, ref_links in book.back_sections:
        lines.append(f"\n## {sec_title}\n")
        if sec_title == "一次业务复原的记录页":
            lines.append(f"{_sanitize_markdown_for_pandoc(paras[0])}\n")
            rows = []
            for row_p in paras[1:]:
                key, _, val = re.sub(r"_+", "", row_p).strip().partition(" ")
                rows.append(f"[{_md_literal(key)}]{{.record-key}} {_sanitize_markdown_for_pandoc(val)}")
            lines.append("::: record\n" + "\n\n".join(rows) + "\n:::\n")
        else:
            lines.extend(f"{_sanitize_markdown_for_pandoc(p)}\n" for p in paras)
        if ref_links:
            lines.append(f"\n### 提取链接与原文资料（共 {len(ref_links)} 项）\n")
            for rlk in ref_links:
                lines.append(
                    _epub_source_text(rlk.en_title or rlk.label, rlk.uri, rlk.clean_text, f"{rlk.index:02d}")
                )
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
        f'#let reddit-path = "{SIMPLE_ICONS_REDDIT_PATH}"',
        "#let reddit-palette = (" + ", ".join(f'rgb("{c}")' for c in REDDIT_PALETTE) + ")",
        "#let wso-icons = ("
        + ", ".join(f'{name}: "{_escape_typst_str(_wso_icon_svg(name))}"' for name in WSO_ICONS)
        + ")",
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
    src = resolve_source_pdf(LONDON_TREASURY_SPEC, source_pdf)
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

    asset_dir = target_dir / "epub_assets"
    _write_epub_assets(asset_dir)
    subprocess.run(
        [
            "pandoc",
            "-f",
            "markdown-tex_math_dollars-raw_tex-raw_html",
            "-t",
            "epub3",
            "--toc",
            "--toc-depth=2",
            "--css",
            str(EPUB_CSS),
            "--resource-path",
            str(asset_dir),
            *(f"--epub-embed-font={REPO_FONTS_DIR / f'{name}.otf'}" for name in EPUB_FONTS),
            "--metadata",
            f"title={parsed.title}",
            "--metadata",
            f"author={LONDON_TREASURY_SPEC.author}",
            "--metadata",
            "lang=zh-CN",
            "-o",
            str(epub_path),
        ],
        input=render_epub_markdown(parsed),
        text=True,
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
