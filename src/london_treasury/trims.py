"""Per-article trims from trims.json and the final polish of fetched text."""

import json
import re
from pathlib import Path

from .urls import _BARE_URL, _URL_TEXT, _link_title, _plain_links, _title_bare_url
from .wso import LATIN_OBFUSCATION_WORDS

TRIMS_JSON = Path(__file__).with_name("trims.json")


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
