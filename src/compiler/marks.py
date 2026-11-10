"""The semantic markers that chapter text carries from the page cleaner and chapter assembly to the writers.

A producer writes a marker with a constructor here, and each writer turns every marker into its own dialect:
`to_typst` into preamble calls and page rules, `to_markdown` into plain Markdown. Transcripts and page fixups
may also hold `@@PAGEBREAK@@` and `@@FNSTART@@...@@FNEND@@`, so the spellings are part of the input dialect.
Notes stay as markers through both writers, because the Typst, Markdown and LaTeX note writers each run at
their own point (`FOOTNOTE_RE`)."""

import re

FOOTNOTE_RE = re.compile(r"@@FNSTART@@(.*?)@@FNEND@@", re.DOTALL)
PAGE_BREAK = "@@PAGEBREAK@@"
NO_INDENT = "@@NOINDENT@@"
JUSTIFY_END = "@@JUSTIFYEND@@"
LINE_BREAK = "@@BR@@"
HYPHEN_BREAK = "@@HY@@"
ABSTRACT_END = "@@ENDABSTRACT@@"


def footnote(body: str) -> str:
    return f"@@FNSTART@@{body}@@FNEND@@"


def landscape(columns: int) -> str:
    """Start an n-column landscape page; 0 turns the page back to portrait."""
    return f"@@FLIPPED{columns}@@"


def subtitle(text: str) -> str:
    return f"@@SUBTITLE@@ {text}"


def byline(names: str) -> str:
    return f"@@BYLINE@@ {names}"


def abstract(note: str, blocks: list[str]) -> list[str]:
    return [f"@@ABSTRACT@@{note}", *blocks, ABSTRACT_END]


def contents_line(title: str, page: int | str) -> str:
    return f"@@CONTENTS@@{title}@@PAGE@@{page}"


def contents_head(title: str) -> str:
    return f"@@CONTENTSHEAD@@{title}"


def source_page(pno: int) -> str:
    return f"@@SRCPAGE{pno}@@"


def page_top(pno: int) -> str:
    return f"@@SRCTOP{pno}@@"


def page_end(pno: int) -> str:
    return f"@@SRCEND{pno}@@"


def to_typst(s: str, *, paginate: bool) -> str:
    """Typst for every marker but notes. Run it after `layout_tables`, which reads the page-break and landscape markers
    and writes the `#set text` sizes that a landscape run shrinks."""
    if paginate:
        s = re.sub(
            r"(?:#h\([^)]*\);)?@@SRCPAGE(\d+)@@",
            r"#src-page(\1)\n#set text(size: fit-size(\1))\n"
            r"#set par(leading: fit-leading(\1, 0), spacing: fit-leading(\1, 0))",
            s,
        )
        s = re.sub(r"@@SRCTOP(\d+)@@", r"#src-top(\1);", s)
        s = re.sub(r"@@SRCEND(\d+)@@", r"#src-end(\1);", s)
        s = s.replace(JUSTIFY_END, "#linebreak(justify: true)")
        s = s.replace(LINE_BREAK, "#linebreak(justify: true);")
        s = s.replace(HYPHEN_BREAK, "-#linebreak(justify: true);")
        s = re.sub(r"(?:#h\([^)]*\);)?@@NOINDENT@@\s*", "#src-cont;", s)
        s = s.replace(PAGE_BREAK, "\n#pagebreak()\n")
    else:
        s = re.sub(r"[ \t]*\n*@@PAGEBREAK@@\n*[ \t]*", "\n\n", s)
    s = re.sub(
        r"@@FLIPPED([2-9])@@.*?(?=@@FLIPPED)",
        lambda m: re.sub(
            r"#set text\(size: ([\d.]+)pt\)", lambda t: f"#set text(size: {float(t.group(1)) * 0.8:.2f}pt)", m.group(0)
        ),
        s,
        flags=re.DOTALL,
    )
    s = re.sub(
        r"@@FLIPPED(\d+)@@",
        lambda m: f"\n#set page(flipped: true, columns: {m.group(1)})\n#set table(inset: (x: 4pt, y: 1.6pt))\n"
        if m.group(1) != "0"
        else "\n#set page(flipped: false, columns: 1)\n#set table(inset: 5pt)\n",
        s,
    )
    s = re.sub(r"^@@SUBTITLE@@ (.*)$", r"#chapter-subtitle[\1]", s, flags=re.MULTILINE)
    s = re.sub(r"^@@BYLINE@@ (.*)$", r"#chapter-byline[\1]", s, flags=re.MULTILINE)
    s = re.sub(r"@@CONTENTS@@(.*?)@@PAGE@@(\d+)", r'#contents-line("\2")[\1]', s)
    s = re.sub(r"@@CONTENTSHEAD@@(.*?)$", r"#contents-head[\1]", s, flags=re.MULTILINE)
    s = re.sub(r"^@@ABSTRACT@@(.*)$", r"#chapter-abstract(note: [\1])[", s, flags=re.MULTILINE)
    return re.sub(r"^@@ENDABSTRACT@@$", "]", s, flags=re.MULTILINE)


def to_markdown(body: str) -> str:
    """Plain Markdown for every marker but notes: drop landscape and page-break markers, keep the opening's text."""
    body = re.sub(r"[ \t]*\n*@@PAGEBREAK@@\n*[ \t]*", "\n\n", body)
    body = re.sub(r"@@CONTENTS@@(.*?)@@PAGE@@(\d+)", r"\1 \2", body)
    body = re.sub(r"@@CONTENTSHEAD@@", "", body)
    body = re.sub(r"\n*@@FLIPPED\d+@@\n*", "\n\n", body)
    body = re.sub(r"(?m)^@@SUBTITLE@@ (.+)$", r"*\1*", body)
    body = re.sub(r"(?m)^@@BYLINE@@ ", "", body)
    body = re.sub(r"(?m)^@@ABSTRACT@@", "", body)
    return re.sub(r"\n*@@ENDABSTRACT@@\n*", "\n\n", body)
