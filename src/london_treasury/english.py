"""Format the English source text: inline markup, blocks and Typst escapes."""

import re
from dataclasses import dataclass

from .urls import plain_links

_CJK_FULLWIDTH = str.maketrans({"?": "？", "!": "！", ",": "，", ";": "；", ":": "："})


def escape_typst(text: str) -> str:
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


def escape_typst_str(text: str) -> str:
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
EN_TOC_ROW = re.compile(r"(.{3,60}?)\s+(\d{1,3})")
_EN_REDDIT_USER = re.compile(r"^\*{0,2}(?:/u/([\w-]+))?:\*{0,2}$")
EN_WSO_USER = re.compile(r"^\*\*@(\w+)/(.+?)(?: \((.+)\))?:\*\*$")
_EN_MARKUP_CHARS = re.compile(r"[*_#>\[\]]")
_EN_REDACTED = "This post was mass deleted and anonymized with"


def _en_inline(text: str) -> str:
    out: list[str] = []
    pos = 0
    for m in _EN_INLINE.finditer(text):
        out.append(escape_typst(text[pos : m.start()]))
        if m.group("ltext") and re.fullmatch(r"\d{1,2}", m.group("ltext")):
            out.append(f"#super[{m.group('ltext')}]")
        elif m.group("ltext"):
            label = _en_inline(m.group("ltext"))
            url = escape_typst_str(m.group("lurl"))
            out.append(f'#link("{url}")[{label}];' if url.startswith("http") else label)
        elif m.group("bold"):
            out.append(f"#strong[{_en_inline(m.group('bold'))}];")
        else:
            out.append(f"#emph[{escape_typst(m.group('istar') or m.group('iund'))}];")
        pos = m.end()
    out.append(escape_typst(text[pos:]))
    return "".join(out)


def _plain(text: str) -> str:
    return _EN_MARKUP_CHARS.sub("", plain_links(text)).strip()


def _norm_title(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _plain(text).lower())


def _is_caps_heading(line: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", line)
    return len(letters) >= 4 and letters.isupper() and len(line.split()) <= 9


@dataclass
class EnBlock:
    kind: str  # para | head | caps | user | label | bullet | numbered | quote
    text: str
    number: int = 0
    role: str | None = None
    icon: str = ""


def _en_blocks(raw_en: str, title: str) -> list[EnBlock]:
    """Turn a scraped Markdown page into typed blocks, dropping site chrome."""
    blocks: list[EnBlock] = []
    para: list[str] = []

    def flush() -> None:
        if para:
            blocks.append(EnBlock("para", " ".join(para)))
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
            blocks.append(EnBlock("head", _plain(m.group(1))))
        elif line.startswith(">"):
            flush()
            body = line.lstrip("> ").strip()
            if body:
                blocks.append(EnBlock("quote", body))
        elif m := _EN_BULLET.match(line):
            flush()
            item = m.group(1).strip()
            if h := _EN_HEADING.match(item):
                blocks.append(EnBlock("term", _plain(h.group(1))))
            else:
                blocks.append(EnBlock("bullet", item))
        elif m := _EN_NUMBERED.match(line):
            flush()
            blocks.append(EnBlock("numbered", m.group(2).strip(), int(m.group(1))))
        elif _is_caps_heading(line) and not para:
            blocks.append(EnBlock("caps", line))
        elif m := _EN_REDDIT_USER.match(line):
            flush()
            blocks.append(EnBlock("user", m.group(1) or "[deleted]"))
        elif m := EN_WSO_USER.match(line):
            flush()
            blocks.append(EnBlock("user", m.group(2), role=m.group(3) or "", icon=m.group(1)))
        elif re.fullmatch(r"\*\*[^*]+\*\*:?", line) and len(line.split()) <= 12:
            flush()
            blocks.append(EnBlock("label", line))
        else:
            para.append(line)
    flush()

    # Rejoin PDF hard wraps that were split into separate paragraphs.
    merged: list[EnBlock] = []
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
        while j < len(merged) and merged[j].kind == "para" and EN_TOC_ROW.fullmatch(merged[j].text):
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
    kept: list[EnBlock] = []
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
    result: list[EnBlock] = []
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


def _en_block_markup(blocks: list[EnBlock]) -> str:
    out: list[str] = []
    prev_kind = ""
    for b in blocks:
        if b.kind != prev_kind or b.kind not in ("bullet", "numbered"):
            out.append("")
        if b.kind == "head":
            out.append(f"#en-head[{escape_typst(b.text)}]")
        elif b.kind == "label":
            out.append(f"#en-label[{_en_inline(b.text)}]")
        elif b.kind == "quote":
            out.append(f"#en-quote[{_en_inline(b.text)}]")
        elif b.kind == "bullet":
            out.append(f"- {_en_inline(b.text)}")
        elif b.kind == "term":
            out.append(f"- #strong[{escape_typst(b.text)}]")
        elif b.kind == "toc":
            entry, page = EN_TOC_ROW.fullmatch(b.text).groups()
            out.append(f"#en-toc[{_en_inline(entry)}][{page}]")
        elif b.kind == "numbered":
            out.append(f"{b.number}. {_en_inline(b.text)}")
        else:
            out.append(_en_inline(b.text))
        prev_kind = b.kind
    return "\n".join(out).strip()


def english_groups(raw_en: str, title: str) -> list[tuple[EnBlock | None, list[EnBlock]]]:
    groups: list[tuple[EnBlock | None, list[EnBlock]]] = [(None, [])]
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


def format_english_original_typst(raw_en: str, title: str = "") -> str:
    """Render blocks; each Reddit `/u/name:` line opens a comment card until the next one."""
    out: list[str] = []
    for user, blocks in english_groups(raw_en, title):
        if user is None:
            out.append(_en_block_markup(blocks))
            continue
        args = f'"{escape_typst_str(user.text)}"'
        if user.role is not None:
            args += f', prefix: "", tag: "{escape_typst_str(user.role)}", icon: wso-icons.at("{user.icon}")'
        out.append(f"#reddit-comment({args})[\n{_en_block_markup(blocks)}\n]")
    return "\n\n".join(out)


def sanitize_markdown_for_pandoc(text: str) -> str:
    s = text.replace("$", "\\$")
    return s
