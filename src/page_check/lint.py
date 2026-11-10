import re
from dataclasses import replace
from pathlib import Path

from ..compiler.monograph import FOOTNOTE_RE
from ..compiler.page_cleaner import (
    PageCleaner,
    normalize_html_tables,
    split_page_footnotes,
)
from ..figure_leaks import apply_page_fixups
from . import PageCheck, prose_lines
from .results import Issue

GLUED_WORDS = re.compile(r"\b[A-Za-z]*?[a-z]{2}[A-Z][a-z]{2,}\b")
NAME_PREFIX = re.compile(r"(?:Ma?c|Mc|De|Le|La|Van|Von|O)[A-Z]")
BROKEN_TAG = re.compile(r"</\s+\w|<\s+/?t[hdr]\b|<t[hdr]\s+>")
SPACED_DECIMAL = re.compile(r"(?<![\d.])\d+ \.\d")
RUNNING_HEAD = re.compile(
    r"\d{1,3}\s+[^\n。，；《》]{1,30}|[^\n。，；《》]{1,30}\s+\d{1,3}"
)
RULE_KINDS = {
    "glued_words": "word",
    "broken_tag": "table_shape",
    "spaced_decimal": "number",
    "lone_book_mark": "mark",
    "dead_fixup": "word",
    "multiline_delete": "missing_text",
}


def hit(rule: str, line: int, text: str) -> Issue:
    return {
        "page": None,
        "line": line,
        "kind": RULE_KINDS.get(rule, "extra_text"),
        "rule": rule,
        "transcript": text,
        "scan": "",
    }


def text_blocks(markdown: str) -> list[tuple[int, str]]:
    """Each paragraph of a page with its first line number, leaving out headings such as a transcribed running head."""
    blocks, first = [], 1
    for block in re.split(r"\n\s*\n", markdown):
        if (
            block.strip()
            and not block.lstrip().startswith("#")
            and not RUNNING_HEAD.fullmatch(block.strip())
        ):
            blocks.append((first, block))
        first += block.count("\n") + 2
    return blocks


def book_marks_open(block: str) -> int:
    return block.count("《") - block.count("》")


def lint_page(markdown: str, before: str = "", after: str = "") -> list[Issue]:
    """The places on one transcript page that match an error the page check confirmed in an earlier book.
    `before` and `after` are the pages around it, for a title in 《》 that runs across the page break."""
    found = []
    for n, line in enumerate(markdown.splitlines(), 1):
        for m in BROKEN_TAG.finditer(line):
            found.append(
                hit(
                    "broken_tag", n, line[max(0, m.start() - 12) : m.end() + 12].strip()
                )
            )
    for n, line in prose_lines(markdown):
        for m in GLUED_WORDS.finditer(line):
            if not NAME_PREFIX.match(m[0]):
                found.append(hit("glued_words", n, m[0]))
        for m in SPACED_DECIMAL.finditer(line):
            found.append(
                hit("spaced_decimal", n, line[max(0, m.start() - 4) : m.end() + 2])
            )
    blocks = text_blocks(markdown)
    next_opens = book_marks_open(text_blocks(after)[0][1]) if text_blocks(after) else 0
    prev_opens = (
        book_marks_open(text_blocks(before)[-1][1]) if text_blocks(before) else 0
    )
    for k, (first, block) in enumerate(blocks):
        opened = book_marks_open(block)
        runs_on = (k == len(blocks) - 1 and opened > 0 and next_opens < 0) or (
            k == 0 and opened < 0 and prev_opens > 0
        )
        if opened and not runs_on and not block.lstrip().startswith(("|", "<table")):
            found.append(
                hit("lone_book_mark", first, block.strip().splitlines()[0][:40])
            )
    return found


def lint_typ(typ: str, title: str) -> list[Issue]:
    """Running heads, such as `120 不良债权与金融危机`, that the page cleaner left in the built book's text."""
    head = re.compile(
        rf"^\s*(?:\d{{1,3}}\s*{re.escape(title)}|{re.escape(title)}\s*\d{{1,3}})\s*$"
    )
    return [
        hit("running_head", n, line.strip())
        for n, line in enumerate(typ.splitlines(), 1)
        if head.match(line)
    ]


def is_multiline_delete(pat: str, rep: str, matched: str) -> bool:
    if rep or ("\n" not in matched.strip() and len(matched) <= 300):
        return False
    return not any(k in pat for k in (r"\A", r"\Z", "(?s)"))


def lint_fixups(
    markdown: str,
    fixups: tuple[tuple[str, str], ...],
    page_fixups: tuple[tuple[str, str], ...] = (),
    cleaned: str | None = None,
) -> list[Issue]:
    found = []
    text = markdown
    for pat, rep in fixups:
        m = re.search(pat, text, flags=re.DOTALL)
        if not m:
            found.append(hit("dead_fixup", 1, pat[:40]))
            continue
        if is_multiline_delete(pat, rep, m[0]):
            line = text[: m.start()].count("\n") + 1
            found.append(hit("multiline_delete", line, m[0].splitlines()[0][:40]))
        text = apply_page_fixups(text, ((pat, rep),))
    if not page_fixups:
        return found
    if cleaned is None:
        cleaned, _ = split_page_footnotes(
            normalize_html_tables(text), "circled", r"^\d+$"
        )
    for pat, rep in page_fixups:
        src = cleaned
        m = re.search(pat, cleaned, flags=re.DOTALL)
        if not m and not rep:
            src = text
            m = re.search(pat, text, flags=re.DOTALL)
        if not m:
            found.append(hit("dead_fixup", 1, pat[:40]))
            continue
        if is_multiline_delete(pat, rep, m[0]):
            line = src[: m.start()].count("\n") + 1
            found.append(hit("multiline_delete", line, m[0].splitlines()[0][:40]))
        cleaned = apply_page_fixups(cleaned, ((pat, rep),))
        text = apply_page_fixups(text, ((pat, rep),))
    return found


def built_typ(check: PageCheck) -> Path | None:
    typ = next(iter(check.book.editions.values())).source("typ")
    return typ if typ.exists() else None


def lint(check: PageCheck) -> list[Issue]:
    spec = check.book.spec
    cleaner = PageCleaner.for_spec(
        replace(spec, page_fixups={}, equation_numbering=None),
        asset_root=check.book.out_dir,
    )
    found: list[Issue] = []
    pages = check.pages()
    texts = []
    for page in pages:
        text = check.transcript(page)
        t_rules = spec.transcript_fixups.get(page, ())
        p_rules = spec.page_fixups.get(page, ())
        cleaned = FOOTNOTE_RE.sub("①", cleaner.clean(text, page).body) if p_rules else None
        found += [{**h, "page": page} for h in lint_fixups(text, t_rules, p_rules, cleaned)]
        texts.append(check.printed(page))
    for k, page in enumerate(pages):
        before, after = (
            texts[k - 1] if k else "",
            texts[k + 1] if k + 1 < len(texts) else "",
        )
        found += [{**h, "page": page} for h in lint_page(texts[k], before, after)]
    if typ := built_typ(check):
        found += [
            {**h, "where": str(typ)}
            for h in lint_typ(typ.read_text(encoding="utf-8"), check.title)
        ]
    return found
