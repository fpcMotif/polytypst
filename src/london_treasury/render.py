"""Render the parsed reader to Markdown, EPUB Markdown and Typst."""

import re
import shutil
from pathlib import Path

from .english import (
    _EN_TOC_ROW,
    _EN_WSO_USER,
    _EnBlock,
    _english_groups,
    _escape_typst,
    _escape_typst_str,
    _format_english_original_typst,
    _sanitize_markdown_for_pandoc,
)
from .models import ArticleEntry, ParsedReaderBook
from .spec import LONDON_TREASURY_SPEC

TEMPLATE_TYP = Path(__file__).with_name("template.typ")


ICONS_DIR = Path(__file__).with_name("icons")


SIMPLE_ICONS_REDDIT_PATH = "M12 0C5.373 0 0 5.373 0 12c0 3.314 1.343 6.314 3.515 8.485l-2.286 2.286C.775 23.225 1.097 24 1.738 24H12c6.627 0 12-5.373 12-12S18.627 0 12 0Zm4.388 3.199c1.104 0 1.999.895 1.999 1.999 0 1.105-.895 2-1.999 2-.946 0-1.739-.657-1.947-1.539v.002c-1.147.162-2.032 1.15-2.032 2.341v.007c1.776.067 3.4.567 4.686 1.363.473-.363 1.064-.58 1.707-.58 1.547 0 2.802 1.254 2.802 2.802 0 1.117-.655 2.081-1.601 2.531-.088 3.256-3.637 5.876-7.997 5.876-4.361 0-7.905-2.617-7.998-5.87-.954-.447-1.614-1.415-1.614-2.538 0-1.548 1.255-2.802 2.803-2.802.645 0 1.239.218 1.712.585 1.275-.79 2.881-1.291 4.64-1.365v-.01c0-1.663 1.263-3.034 2.88-3.207.188-.911.993-1.595 1.959-1.595Zm-8.085 8.376c-.784 0-1.459.78-1.506 1.797-.047 1.016.64 1.429 1.426 1.429.786 0 1.371-.369 1.418-1.385.047-1.017-.553-1.841-1.338-1.841Zm7.406 0c-.786 0-1.385.824-1.338 1.841.047 1.017.634 1.385 1.418 1.385.785 0 1.473-.413 1.426-1.429-.046-1.017-.721-1.797-1.506-1.797Zm-3.703 4.013c-.974 0-1.907.048-2.77.135-.147.015-.241.168-.183.305.483 1.154 1.622 1.964 2.953 1.964 1.33 0 2.47-.81 2.953-1.964.057-.137-.037-.29-.184-.305-.863-.087-1.795-.135-2.769-.135Z"


REDDIT_ORANGE = "#ff4500"


REDDIT_DELETED = "#aaaaaa"


REDDIT_PALETTE = ("#ff4500", "#0079d3", "#46a758", "#d9a400", "#7193ff", "#e0569e", "#00a6a5", "#9a6bd6")


WSO_ICONS = ("monkey", "orangutan", "gorilla", "human", "anon")


def _wso_icon_svg(name: str) -> str:
    return " ".join((ICONS_DIR / f"wso-{name}.svg").read_text(encoding="utf-8").split())


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
