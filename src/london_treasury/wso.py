"""Clean Wall Street Oasis threads: authors, ranks, promos and bot comments."""

import re

from .urls import unwrap_links

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
    slice_txt = unwrap_links(slice_txt, r"(?:[^()]|\([^()]*\))*")

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
