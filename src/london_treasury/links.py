"""Clean one fetched link by source, and fetch or load it from the cache."""

import html
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .models import ExtractedLink
from .trims import polish_article, trim_article
from .urls import unwrap_links
from .wso import clean_wso_thread


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


def _join_drop_caps(lines: list[str]) -> list[str]:
    text = "\n".join(lines)

    def join(m: re.Match[str]) -> str:
        rest = m.group(2)
        fragment = len(rest) == 1 or len(re.findall(rf"\b{rest}\b", text)) == 1
        return m.group(1) + rest if fragment else m.group(0)

    return [re.sub(r"^([A-Z]) ([a-z]+)\b", join, l) for l in lines]


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
    text = unwrap_links(text, r"(?:https?://|mailto:|tel:|javascript:|/|#)(?:[^()]|\([^()]*\))*", keep_web=True)

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
