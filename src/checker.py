"""Automated Strict Document Quality Checker & Linter for polytypst deliverables."""

import re
import unicodedata
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from itertools import pairwise
from pathlib import Path
from typing import Literal

import pymupdf

from .compiler.monograph import MonographSpec

Severity = Literal["ERROR", "WARNING"]
TEXT_TIER = 1
LAYOUT_TIER = 2
STRUCTURE_TIER = 3
ALL_TIERS = frozenset({TEXT_TIER, LAYOUT_TIER, STRUCTURE_TIER})


@dataclass
class QualityIssue:
    severity: str  # "ERROR" or "WARNING"
    rule_name: str
    page_num: int
    message: str
    context_snippet: str = ""
    tier: int = TEXT_TIER


@dataclass
class CheckReport:
    pdf_path: Path
    total_pages: int
    issues: list[QualityIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not any(i.severity == "ERROR" for i in self.issues)

    def rules(self) -> set[str]:
        return {i.rule_name for i in self.issues}

    def print_summary(self) -> None:
        print("\n================ STRICT QUALITY CHECK REPORT ================")
        print(f"File: {self.pdf_path.name} ({self.total_pages} pages)")
        errors = [i for i in self.issues if i.severity == "ERROR"]
        warns = [i for i in self.issues if i.severity == "WARNING"]
        print(
            f"Total Issues: {len(self.issues)} ({len(errors)} Errors, {len(warns)} Warnings)"
        )
        print("-" * 65)
        for issue in self.issues:
            prefix = "❌ [ERROR]" if issue.severity == "ERROR" else "⚠️  [WARN] "
            print(
                f"{prefix} Page {issue.page_num:03d} | T{issue.tier} {issue.rule_name}: {issue.message}"
            )
            if issue.context_snippet:
                print(f"    Snippet: {issue.context_snippet!r}")
        if len(self.issues) == 0:
            print("Result: PASSED")
        else:
            print("Result: FAILED")
        print("============================================================\n")


@dataclass(frozen=True)
class AuditSpec:
    """What the audit knows about one book: its chapter headings and exempt pages."""

    front_matter_pages: int = 4
    figure_pages: frozenset[int] = frozenset()
    chapter_heading_regex: str = r"CHAPTER\s+(?P<number>\d+)\s*:"
    chapter_titles: dict[int, str] = field(default_factory=dict)
    bibliography_from_page: int | None = None
    language: str = "auto"
    book_headers: tuple[str, ...] = ()
    footnote_numbering: str = ""
    footnote_marks: tuple[str, ...] = ()
    footnote_reset: str = "page"

    def footnote_label(self, n: int) -> str:
        if n <= len(self.footnote_marks):
            return self.footnote_marks[n - 1]
        return str(n) if self.footnote_marks else self.footnote_numbering.replace("1", str(n))

    @classmethod
    def from_monograph(cls, spec: MonographSpec) -> "AuditSpec":
        heading = re.escape(spec.chapter_label or spec.chapter_heading)
        heading = heading.replace(re.escape("{number}"), r"(?P<number>\d+)")
        titles = "|".join(re.escape(ch.title) for ch in spec.chapters) or ".+"
        heading = heading.replace(re.escape("{title}"), f"(?:{titles})")
        return cls(
            chapter_heading_regex=rf"^{heading}$",
            chapter_titles={ch.number: ch.title for ch in spec.chapters},
            figure_pages=spec.figure_pages,
            book_headers=tuple(filter(None, (spec.author, spec.title))),
            footnote_numbering=spec.footnote_numbering if spec.footnote_style else "",
            footnote_marks=spec.footnote_marks,
            footnote_reset=spec.footnote_reset,
        )


def _letters(text: str) -> str:
    return "".join(c for c in text.casefold() if c.isalpha())


def _snippet(text: str, start: int, end: int, pad: int = 20) -> str:
    return text[max(0, start - pad) : min(len(text), end + pad)].replace("\n", " ")


_MATH_DELIMITER_RE = re.compile(
    r"\$\$|\$\s+[A-Za-z0-9\\\(]|[A-Za-z0-9\)]\s+\$|\$_[A-Za-z0-9\{]|\\neq\b"
)
_LATEX_KEYWORDS = (
    "\\begin{",
    "\\end{",
    "\\frac{",
    "\\operatorname{",
    "\\left",
    "\\right",
    "\\quad",
    "\\cdots",
    "<<<",
    ">>>",
    "mat(delim",
    "overline(",
    "underline(",
)
_LEAKED_MATH_WORDS = (
    "overline",
    "underline",
    "begin",
    "end",
    "cases",
    "mat",
    "delim",
    "sqrt",
    "root",
    "binom",
    "cal",
    "frak",
    "pmod",
    "bmod",
    "zin",
    "cosec",
    "operatorname",
    "mathrm",
    "mathbf",
    "mathcal",
    "mathfrak",
    "mathbb",
    "where",
    "with",
    "for",
    "and",
    "const",
    "poles",
    "even",
    "odd",
    "otherwise",
)
_ITALIC_RUN_RE = re.compile(r"[\U0001D434-\U0001D6A5]{3,}")
_SPACED_WORDS = (
    (r"\bi\s+n\s+f\s+i\s+n\s+i\s+t\s+y\b", "Mangled 'infinity'"),
    (r"\bp\s+a\s+r\s+t\s+i\s+a\s+l\b", "Mangled 'partial'"),
    (r"\bl\s+e\s+f\s+t\b", "Mangled 'left'"),
    (r"\br\s+i\s+g\s+h\s+t\b", "Mangled 'right'"),
    (r"\bc\s+i\s+r\s+c\b", "Mangled 'circ'"),
    (r"\bd\s+o\s+t\s+s\b", "Mangled 'dots'"),
)
_MASHED_TOKENS = (
    r"\bdote\b",
    r"\bcosecz\b",
    r"\bzin\b",
    r"\bbmod\b",
    r",d[zxyrtuvs]\b",
    r"\(\d+\([a-zA-Z\s]+\)\d+\)",
)
_NOTE_MARK_RE = re.compile(r"^(?:\d{1,3}\)?|\*{1,3}|[†‡§¶]{1,2})$")
_NOTE_MARK_START_RE = re.compile(r"^(\d{1,3}\)?|\*{1,3}|[†‡§¶]{1,2})(?=[^\s\d.,])")
_FOLIO_RE = re.compile(r"^—?\s*\d+\s*—?$")
_NAME_HYPHEN_RE = re.compile(r"\b([A-Z][a-z]{1,4})-[\s]*$")
_TRAILING_WORD_RE = re.compile(r"\b[A-Za-z]+$")
_LEADING_WORD_RE = re.compile(r"^[A-Za-z]+\b")
_BOILERPLATE = (
    "raspberry",
    "temperature monitoring",
    "user-friendly interface",
    "energy efficient",
    "dissertation",
    "student learning",
    "social media",
    "research questions",
    "smith, j.",
    "problem statement",
    "literature review",
    "existing solutions",
    "data preprocessing",
    "model training",
)
_HYPHEN_PREFIXES = (
    "z-",
    "w-",
    "𝑧-",
    "𝑤-",
    "right-",
    "well-",
    "self-",
    "semi-",
    "quasi-",
    "non-",
    "single-",
)


class DocumentQualityChecker:
    def __init__(self, pdf_path: Path, spec: AuditSpec | None = None) -> None:
        self.pdf_path: Path = Path(pdf_path)
        self.spec: AuditSpec = spec or AuditSpec()
        self.doc: pymupdf.Document = pymupdf.open(self.pdf_path)
        self._texts: list[str] = [page.get_text() for page in self.doc]
        if self.spec.language == "auto":
            sample = "".join(self._texts[:5])
            if re.search(r"[\u3040-\u30ff]", sample):
                self.language: str = "ja"
            elif re.search(r"[一-龥]", sample):
                self.language = "zh"
            else:
                self.language = "en"
        else:
            self.language = self.spec.language

    def _checks(self) -> dict[int, tuple[Callable[[CheckReport], None], ...]]:
        return {
            TEXT_TIER: (
                self.check_no_literal_tildes,
                self.check_no_bullets_in_bibliography,
                self.check_hallucinated_boilerplate,
                self.check_unrendered_fractions,
                self.check_unrendered_math_delimiters,
                self.check_raw_latex_macros,
                self.check_unconverted_markdown_headings,
                self.check_spaced_words,
                self.check_mangled_math_tokens,
                self.check_inverted_partial_derivatives,
                self.check_mangled_dots,
                self.check_leaked_running_headers,
                self.check_footnotes_left_in_body,
            ),
            LAYOUT_TIER: (
                self.check_solo_pages,
                self.check_no_hyphenated_proper_nouns,
                self.check_cross_page_splits,
                self.check_isolated_math_blocks,
                self.check_orphaned_equation_numbers,
                self.check_equation_margin_overflow,
                self.check_shrunken_display_math,
                self.check_visual_line_height_spikes,
                self.check_footnote_mark_sequence,
            ),
            STRUCTURE_TIER: (
                self.check_chapter_structural_integrity,
                self.check_extracted_figures_purity,
            ),
        }

    def run_all_checks(self, tiers: frozenset[int] = ALL_TIERS) -> CheckReport:
        report = CheckReport(pdf_path=self.pdf_path, total_pages=len(self.doc))
        for tier, checks in self._checks().items():
            if tier not in tiers:
                continue
            start = len(report.issues)
            for check in checks:
                check(report)
            for issue in report.issues[start:]:
                issue.tier = tier
        return report

    def _issue(
        self,
        report: CheckReport,
        severity: Severity,
        rule: str,
        page_num: int,
        message: str,
        snippet: str = "",
    ) -> None:
        report.issues.append(QualityIssue(severity, rule, page_num, message, snippet))

    def _extract_body_lines(self, page: pymupdf.Page) -> list[str]:
        """Extract body text lines excluding running headers and folios."""
        H = page.rect.height
        body_lines: list[str] = []
        for b in page.get_text("blocks"):
            y0, y1 = b[1], b[3]
            if y0 < 0.08 * H or y1 > 0.93 * H:
                continue
            for line in b[4].strip().splitlines():
                l = line.strip()
                if l and not _FOLIO_RE.match(l):
                    body_lines.append(l)
        return body_lines

    def check_solo_pages(self, report: CheckReport) -> None:
        """Rule 1: No Solo / Orphan pages with <= 2 lines or < 80 characters (except intentional titles)."""
        for pno in range(self.spec.front_matter_pages, len(self.doc)):
            content_lines = self._extract_body_lines(self.doc[pno])
            full_body_text = "".join(content_lines)
            if 0 < len(content_lines) <= 2 and len(full_body_text) < 70:
                if any(l.startswith(("FIG.", "Figure", "Fig.")) for l in content_lines):
                    continue
                self._issue(
                    report,
                    "ERROR",
                    "NO_SOLO_PAGE",
                    pno + 1,
                    f"Solo/orphan page detected ({len(content_lines)} line(s), {len(full_body_text)} chars)",
                    " | ".join(content_lines),
                )

    def check_no_literal_tildes(self, report: CheckReport) -> None:
        """Rule 2: Zero literal tilde characters (~) in rendered text (e.g. Nuffield~College, Roy,~1952)."""
        for pno, text in enumerate(self._texts):
            if "~" in text:
                tilde_lines = [l.strip() for l in text.splitlines() if "~" in l]
                self._issue(
                    report,
                    "ERROR",
                    "NO_LITERAL_TILDE",
                    pno + 1,
                    "Literal tilde (~) character leaked into rendered prose",
                    " | ".join(tilde_lines[:2]),
                )

    def check_no_bullets_in_bibliography(self, report: CheckReport) -> None:
        """Rule 3: Academic bibliography must use hanging indent, NEVER bullet points (•)."""
        for pno, text in enumerate(self._texts):
            is_bib = any(
                k in text.lower()
                for k in ["bibliography", "references", "参考文献", "bibliographie"]
            )
            if not is_bib:
                continue
            # Only flag if the page is an actual bibliography list
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            bullet_lines = [
                l
                for l in lines
                if (
                    l.startswith(("* ", "- ", "• "))
                    and any(yr in l for yr in ["(19", "(20", "19", "20"])
                )
            ]
            if bullet_lines:
                self._issue(
                    report,
                    "ERROR",
                    "NO_BULLETS_IN_BIBLIOGRAPHY",
                    pno + 1,
                    "Academic bibliography contains bullet points (•) instead of hanging indent",
                    " | ".join(bullet_lines[:2]),
                )

    def check_no_hyphenated_proper_nouns(self, report: CheckReport) -> None:
        """Rule 4: Proper nouns and parenthesized names must not be hyphen-cleaved (e.g. Ric-hard)."""
        for pno in range(len(self.doc)):
            for l in self._extract_body_lines(self.doc[pno]):
                # Check for hyphenated English names like "Ric-" or "Gene-"
                m = _NAME_HYPHEN_RE.search(l)
                if (
                    m
                    and not l.endswith(("—", "–"))
                    and m.group(1) not in ["Heine", "Mean", "Non", "Self"]
                ):
                    self._issue(
                        report,
                        "WARNING",
                        "HYPHENATED_PROPER_NOUN",
                        pno + 1,
                        f"Possible hyphen-cleaved English name '{m.group(1)}-' at line end",
                        l,
                    )

    def check_cross_page_splits(self, report: CheckReport) -> None:
        """Rule 5: No unclosed parentheses or split English proper nouns across page breaks."""
        bib_from = self.spec.bibliography_from_page
        body_lines = [self._extract_body_lines(page) for page in self.doc]
        for pno, (cur_lines, next_lines) in enumerate(pairwise(body_lines)):
            if not cur_lines or not next_lines:
                continue

            cur_text = " ".join(cur_lines)
            last_line = cur_lines[-1]
            first_line = next_lines[0]
            boundary = f"{last_line}  >>> NEXT PAGE >>>  {first_line}"

            open_count = cur_text.count("（") + cur_text.count("(")
            close_count = cur_text.count("）") + cur_text.count(")")
            next_head = " ".join(next_lines[:3])
            next_open = next_head.count("（") + next_head.count("(")
            next_close = next_head.count("）") + next_head.count(")")
            if open_count > close_count and (open_count + next_open) > (
                close_count + next_close
            ):
                self._issue(
                    report,
                    "WARNING",
                    "UNCLOSED_PARENTHESIS_PAGE_BREAK",
                    pno + 1,
                    "Page ends with an unclosed parenthesis in body text",
                    boundary,
                )

            # Mid-word English cleaving
            if self.language == "zh":
                is_bib = "参考文献" in cur_text or (
                    bib_from is not None and pno + 1 >= bib_from
                )
                if (
                    not is_bib
                    and _TRAILING_WORD_RE.search(last_line)
                    and _LEADING_WORD_RE.search(first_line)
                ):
                    self._issue(
                        report,
                        "ERROR",
                        "CROSS_PAGE_WORD_SPLIT",
                        pno + 1,
                        "English proper noun cleaved across page boundary",
                        boundary,
                    )
            # English document: normal sentence wrap across pages is standard.
            # Only flag if last line ends with a hyphen '-', indicating an unstitched word.
            elif last_line.endswith("-") and not last_line.rstrip().endswith(
                _HYPHEN_PREFIXES
            ):
                self._issue(
                    report,
                    "ERROR",
                    "CROSS_PAGE_WORD_SPLIT",
                    pno + 1,
                    "Word cleaved across page boundary with hyphen",
                    boundary,
                )

    def check_hallucinated_boilerplate(self, report: CheckReport) -> None:
        """Rule 6: Zero foreign boilerplate keywords from VLM hallucinations."""
        for pno, text in enumerate(self._texts):
            lowered = text.lower()
            found = [kw for kw in _BOILERPLATE if kw in lowered]
            if len(found) < 2:
                continue
            for kw in found:
                self._issue(
                    report,
                    "ERROR",
                    "HALLUCINATED_BOILERPLATE",
                    pno + 1,
                    f"Hallucinated template keyword '{kw}' detected",
                    kw,
                )

    def check_isolated_math_blocks(self, report: CheckReport) -> None:
        """Rule 7: No single-letter isolated display equations breaking sentence flow."""
        for pno in range(len(self.doc)):
            if pno + 1 in self.spec.figure_pages:
                continue
            page = self.doc[pno]
            H = page.rect.height
            blocks = page.get_text("blocks")
            for b in blocks:
                x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
                if y0 < 0.10 * H or y1 > 0.90 * H:
                    continue
                # Subscripts, superscripts, and summation limits have height <= 9.5pt
                if (y1 - y0) <= 0.0135 * H:
                    continue
                # Ignore figure pages where axis labels (x, y, a, b) reside in diagrams
                if len(text) == 1 and text.isalpha():
                    # Ignore if it is part of a fraction (has a neighbor numerator/denominator within 22pt vertically)
                    is_fraction = any(
                        other != b
                        and (abs(other[1] - y1) < 22 or abs(other[3] - y0) < 22)
                        and (other[0] <= x1 + 10 and other[2] >= x0 - 10)
                        for other in blocks
                    )
                    if is_fraction:
                        continue
                    self._issue(
                        report,
                        "ERROR",
                        "ISOLATED_MATH_BLOCK",
                        pno + 1,
                        f"Isolated single-letter display math block '{text}' breaking prose sentence",
                        text,
                    )

    def check_unrendered_fractions(self, report: CheckReport) -> None:
        """Rule 8: Detect unrendered fraction syntax {A}{B}."""
        for pno, t in enumerate(self._texts):
            matches = re.findall(
                r"\{[0-9a-zA-Z\+\-\*\/]{1,6}\}\{[0-9a-zA-Z\+\-\*\/]{1,6}\}", t
            )
            if matches:
                self._issue(
                    report,
                    "ERROR",
                    "UNRENDERED_FRACTION",
                    pno + 1,
                    f"Unrendered fraction syntax detected: '{matches[0]}'",
                    " | ".join(matches[:2]),
                )

    def check_equation_margin_overflow(self, report: CheckReport) -> None:
        """Rule 9: Equations and text must not exceed page margin boundary."""
        for pno in range(len(self.doc)):
            page = self.doc[pno]
            max_allowed_x = page.rect.width * 0.96
            for b in page.get_text("blocks"):
                x1 = b[2]
                if x1 > max_allowed_x:
                    self._issue(
                        report,
                        "WARNING",
                        "MARGIN_OVERFLOW",
                        pno + 1,
                        f"Block overflowed margin: x1={x1:.1f} > max={max_allowed_x:.1f}",
                        b[4].strip().replace("\n", " ")[:80],
                    )

    def check_chapter_structural_integrity(self, report: CheckReport) -> None:
        """Rule 10: Chapters must progress monotonically; no duplicate headings or stale headers."""
        heading_re = re.compile(self.spec.chapter_heading_regex, re.MULTILINE)
        titles = self.spec.chapter_titles
        current_chapter = 0
        for pno in range(self.spec.front_matter_pages, len(self.doc)):
            page_idx = pno + 1
            for b in self.doc[pno].get_text("blocks"):
                text = b[4].strip()
                m = heading_re.search(text)
                if not m or "number" not in heading_re.groupindex:
                    # A spec whose heading carries no number, such as 第1章 正則関数.
                    continue
                ch_num = int(m.group("number"))
                if ch_num < current_chapter:
                    self._issue(
                        report,
                        "ERROR",
                        "CHAPTER_REGRESSION",
                        page_idx,
                        f"Chapter regression! Found Chapter {ch_num} on page {page_idx} after Chapter {current_chapter}",
                        text[:80],
                    )
                current_chapter = ch_num

            # Check running header on odd pages
            lines = self._texts[pno].splitlines()
            first_line = lines[0].strip() if lines else ""
            earlier = [titles[n] for n in titles if n < current_chapter]
            if (
                page_idx % 2 != 0
                and first_line
                and any(first_line.upper() == t.upper() for t in earlier)
            ):
                self._issue(
                    report,
                    "ERROR",
                    "STALE_RUNNING_HEADER",
                    page_idx,
                    f"Running header stuck on '{first_line}' while in Chapter {current_chapter}",
                    first_line,
                )

    def check_unrendered_math_delimiters(self, report: CheckReport) -> None:
        for pno, text in enumerate(self._texts):
            m = _MATH_DELIMITER_RE.search(text)
            if m:
                self._issue(
                    report,
                    "ERROR",
                    "UNRENDERED_MATH_DELIMITER",
                    pno + 1,
                    f"Unrendered math delimiter or macro '{m.group(0)}' leaked into PDF",
                    _snippet(text, m.start(), m.end(), pad=25),
                )

    def check_leaked_running_headers(self, report: CheckReport) -> None:
        header_re = re.compile(
            r"(?:\[[IVXLCDM]+,\s*§\s*\d+[a-z]?|[IVXLCDM]+,\s*§\s*\d+[a-z]?\]\s+[A-Z]{4,})"
        )
        book_headers = {_letters(h) for h in self.spec.book_headers}
        # A scan sets its running header in capitals, which prose never does for its own author.
        caps_headers = [" ".join(h.upper().split()) for h in self.spec.book_headers]
        for pno in range(len(self.doc)):
            for l in self._extract_body_lines(self.doc[pno]):
                if pno >= self.spec.front_matter_pages and (
                    _letters(l) in book_headers
                    or any(h in " ".join(l.split()) for h in caps_headers)
                ):
                    self._issue(
                        report,
                        "ERROR",
                        "LEAKED_RUNNING_HEADER",
                        pno + 1,
                        "Scanned running header with the book's author or title leaked into body text",
                        l[:80],
                    )
                elif header_re.search(l):
                    self._issue(
                        report,
                        "ERROR",
                        "LEAKED_RUNNING_HEADER",
                        pno + 1,
                        "Scanned running header with section bracket leaked into body text",
                        l[:80],
                    )

    def check_extracted_figures_purity(self, report: CheckReport) -> None:
        from .ocr.lines import DEFAULT_OCR_LANGUAGES, line_reader
        from .vision.typesafe_jev import TypeSafeJevVision

        fig_dir = self.pdf_path.parent / "figures"
        if not fig_dir.exists():
            return
        reader = line_reader(DEFAULT_OCR_LANGUAGES)
        for png_path in sorted(fig_dir.glob("fig_*.png")):
            ok, reasons = TypeSafeJevVision.verify_cropped_diagram(png_path, reader)
            if not ok:
                self._issue(
                    report,
                    "ERROR",
                    "CORRUPTED_FIGURE_CROP",
                    1,
                    f"Figure '{png_path.name}' failed purity check: {'; '.join(reasons)}",
                    png_path.name,
                )

    def check_spaced_words(self, report: CheckReport) -> None:
        """Rule 1: No letter-spaced words like 'i n f i n i t y', 'p a r t i a l', 'l e f t'."""
        for pno, raw in enumerate(self._texts):
            text = unicodedata.normalize("NFKC", raw)
            for pat, name in _SPACED_WORDS:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    self._issue(
                        report,
                        "ERROR",
                        "SPACED_MATH_TOKEN",
                        pno + 1,
                        f"{name} detected on canvas",
                        _snippet(text, m.start(), m.end()),
                    )

    def check_unconverted_markdown_headings(self, report: CheckReport) -> None:
        """Rule 2: No raw markdown heading hashes (###, ##) in rendered text."""
        for pno, text in enumerate(self._texts):
            for line in text.splitlines():
                l = line.strip()
                if re.match(
                    r"^(?:\\#|#){1,6}\s+(?:\d+(?:\.\d+)*\.?\s+)?[^\W\d_]{2,}", l
                ):
                    self._issue(
                        report,
                        "ERROR",
                        "RAW_MARKDOWN_HEADING",
                        pno + 1,
                        "Raw markdown heading hashes leaking into rendered body",
                        l[:80],
                    )

    def check_raw_latex_macros(self, report: CheckReport) -> None:
        r"""Rule 3: No unrendered raw LaTeX macros (\begin, \frac, \operatorname)."""
        for pno, raw_text in enumerate(self._texts):
            norm_text = unicodedata.normalize("NFKC", raw_text)
            for kw in _LATEX_KEYWORDS:
                if kw in norm_text:
                    self._issue(
                        report,
                        "ERROR",
                        "UNRENDERED_LATEX_MACRO",
                        pno + 1,
                        f"Raw unrendered LaTeX macro '{kw}' present in rendered canvas",
                        kw,
                    )
            for m in _ITALIC_RUN_RE.finditer(raw_text):
                word = unicodedata.normalize("NFKC", m.group(0))
                if any(bad in word.lower() for bad in _LEAKED_MATH_WORDS):
                    self._issue(
                        report,
                        "ERROR",
                        "UNRENDERED_MATH_ITALIC_WORD",
                        pno + 1,
                        f"Multi-letter Mathematical Italic token '{word}' leaked inside math mode",
                        _snippet(raw_text, m.start(), m.end(), pad=15),
                    )

    def check_mangled_math_tokens(self, report: CheckReport) -> None:
        """Rule 4: Detect mashed tokens like 'dote', 'cosecz'."""
        for pno, raw in enumerate(self._texts):
            text = unicodedata.normalize("NFKC", raw)
            for pat in _MASHED_TOKENS:
                m = re.search(pat, text)
                if m:
                    self._issue(
                        report,
                        "ERROR",
                        "MANGLED_MATH_TOKEN",
                        pno + 1,
                        f"Mangled concatenated token '{m.group(0)}' detected",
                        _snippet(text, m.start(), m.end()),
                    )

    def check_orphaned_equation_numbers(self, report: CheckReport) -> None:
        """Taste Rule 6: Equation numbers (N) must not sit alone on orphaned lines."""
        for pno in range(self.spec.front_matter_pages, len(self.doc)):
            page_idx = pno + 1
            page = self.doc[pno]
            blocks = page.get_text("blocks")
            for b in blocks:
                t = b[4].strip()
                if not re.match(r"^\(\d+\)$", t):
                    continue
                has_adjacent_formula = any(
                    o != b
                    and (
                        abs((o[1] + o[3]) / 2 - (b[1] + b[3]) / 2) < 26
                        or (o[1] - 8 <= (b[1] + b[3]) / 2 <= o[3] + 8)
                    )
                    for o in blocks
                )
                if not has_adjacent_formula:
                    self._issue(
                        report,
                        "ERROR",
                        "ORPHANED_EQUATION_NUMBER",
                        page_idx,
                        f"Equation number '{t}' sitting stranded on an empty line above/below formula",
                        t,
                    )

            number_zone = page.rect.width * 0.6
            spans: list[tuple[tuple[float, float, float, float], str]] = []
            for blk in page.get_text("dict").get("blocks", []):
                if blk.get("type") != 0:
                    continue
                for line in blk.get("lines", []):
                    for sp in line.get("spans", []):
                        st = str(sp.get("text", "")).strip()
                        if st:
                            x0, y0, x1, y1 = sp.get("bbox", (0.0, 0.0, 0.0, 0.0))
                            spans.append(
                                ((float(x0), float(y0), float(x1), float(y1)), st)
                            )
            for i, (b1, t1) in enumerate(spans):
                if not (
                    re.match(r"^\(\d+(?:\.\d+[a-z']?)?\)$", t1)
                    and t1 != "(0)"
                    and b1[2] > number_zone
                ):
                    continue
                cy1 = (b1[1] + b1[3]) / 2.0
                for j, (b2, t2) in enumerate(spans):
                    cy2 = (b2[1] + b2[3]) / 2.0
                    if (
                        i != j
                        and abs(cy1 - cy2) < 6.0
                        and b2[2] > b1[0] + 1.0
                        and b2[0] < b1[2] - 1.0
                    ):
                        self._issue(
                            report,
                            "ERROR",
                            "EQUATION_NUMBER_COLLISION",
                            page_idx,
                            f"Equation number {t1} collides horizontally with '{t2}'",
                            f"{t2} <-> {t1}",
                        )

    def check_inverted_partial_derivatives(self, report: CheckReport) -> None:
        r"""Taste Rule 7: Partial derivatives must have correct denominator grouping (no \partial U / \partial x)."""
        for pno, t in enumerate(self._texts):
            m = re.search(
                r"(?:𝜕|partial)\s*[A-Za-z0-9_]+\s*\n\s*(?:𝜕|partial)\s*\n\s*[xyz]", t
            )
            if m:
                self._issue(
                    report,
                    "ERROR",
                    "INVERTED_PARTIAL_DERIVATIVE",
                    pno + 1,
                    "Inverted partial derivative fraction detected (denominator parsed as operator)",
                    _snippet(t, m.start(), m.end(), pad=10),
                )

    def check_mangled_dots(self, report: CheckReport) -> None:
        """Taste Rule 8: Ellipsis must be rendered as clean dots, never '⋅𝑠' or 'cdot s'."""
        for pno, t in enumerate(self._texts):
            m = re.search(r"(?:⋅\s*𝑠|dot\s+s)", t)
            if m:
                self._issue(
                    report,
                    "ERROR",
                    "MANGLED_ELLIPSIS_DOTS",
                    pno + 1,
                    "Mangled ellipsis '⋅𝑠' (corrupted from \\cdots) detected",
                    _snippet(t, m.start(), m.end(), pad=15),
                )

    @cached_property
    def _page_dicts(self) -> list[dict]:
        return [page.get_text("dict") for page in self.doc]

    @cached_property
    def _body_size(self) -> float | None:
        sizes: Counter[float] = Counter()
        for d in self._page_dicts:
            for b in d["blocks"]:
                for ln in b.get("lines", []):
                    for s in ln["spans"]:
                        sizes[round(s["size"], 1)] += len(s["text"].strip())
        return sizes.most_common(1)[0][0] if sizes else None

    def _footnote_entries(self, pno: int) -> list[str]:
        """Marks of the note entries below the page's note rule, read from the first line of each note-size block.

        A mark is a small span of its own, or a superscript glyph merged into the note text ("1First")."""
        body = self._body_size
        page = self.doc[pno]
        blocks = [b for b in self._page_dicts[pno]["blocks"] if b.get("lines")]
        body_tops = [
            b["bbox"][1] for b in blocks
            if any(s["size"] >= 0.95 * body and s["text"].strip() for s in b["lines"][0]["spans"])
            and not _FOLIO_RE.match("".join(s["text"] for s in b["lines"][0]["spans"]).strip())
        ]
        rules = [
            d["rect"].y0
            for d in page.get_drawings()
            if d["rect"].height < 2 and 0.15 * page.rect.width < d["rect"].width < 0.5 * page.rect.width
            and d["rect"].y0 > 0.3 * page.rect.height
            and not any(top > d["rect"].y0 for top in body_tops)
        ]
        if not rules:
            return []
        marks = []
        for b in blocks:
            lines = b["lines"]
            if lines[0]["bbox"][1] < max(rules):
                continue
            spans = [s for s in lines[0]["spans"] if s["text"].strip()]
            text_spans = [s for s in spans if s["size"] > 0.7 * body]
            if not text_spans or not all(s["size"] < 0.95 * body for s in text_spans):
                continue
            if len(spans) > 1 and spans[0]["size"] < 0.75 * spans[1]["size"]:
                mark = spans[0]["text"].strip()
            else:
                m = _NOTE_MARK_START_RE.match("".join(s["text"] for s in spans).strip())
                mark = m.group(1) if m else ""
            if _NOTE_MARK_RE.match(mark):
                marks.append(mark)
        return marks

    def check_footnote_mark_sequence(self, report: CheckReport) -> None:
        """Note marks on each page follow the scan's numbering: restart per page, per chapter, or run on."""
        if not self.spec.footnote_numbering or self._body_size is None:
            return
        numbers = {self.spec.footnote_label(n): n for n in range(200, 0, -1)}
        last = 0
        for pno in range(len(self.doc)):
            marks = self._footnote_entries(pno)
            if not marks:
                continue
            found = [numbers.get(m, 0) for m in marks]
            starts = {"page": {1}, "chapter": {1, last + 1}, "book": {last + 1}}[self.spec.footnote_reset]
            if not any(found == list(range(s, s + len(found))) for s in starts):
                expected = " ".join(self.spec.footnote_label(n) for n in range(min(starts), min(starts) + len(found)))
                self._issue(
                    report, "ERROR", "FOOTNOTE_MARK_SEQUENCE", pno + 1,
                    f"Note marks {' '.join(marks)} where the scan's numbering gives {expected}",
                )
            last = found[-1]

    def check_footnotes_left_in_body(self, report: CheckReport) -> None:
        """A body-size paragraph that opens with a note mark ("*The …", "¹ Liouville …") is a note the splitter missed."""
        if not self.spec.footnote_numbering or self._body_size is None:
            return
        marks = [*map(re.escape, sorted(self.spec.footnote_marks, key=len, reverse=True)), "[¹²³⁴⁵⁶⁷⁸⁹⁰]+"]
        opener = re.compile(rf"^(?:{'|'.join(marks)})\s*\w+(?:\s+\S+){{3}}")
        for pno, d in enumerate(self._page_dicts):
            block_starts = [
                (b["bbox"][3], "".join(s["text"] for s in b["lines"][0]["spans"]).strip())
                for b in d["blocks"]
                if b.get("lines") and b["lines"][0]["spans"]
                and b["lines"][0]["spans"][0]["size"] >= 0.95 * self._body_size
            ]
            for _, text in block_starts:
                if opener.match(text):
                    self._issue(
                        report, "WARNING", "FOOTNOTE_LEFT_IN_BODY", pno + 1,
                        "A note line sits in the body text instead of the page's notes", text[:80],
                    )

    def check_shrunken_display_math(self, report: CheckReport) -> None:
        """A math line whose largest glyph is far below body size was scaled down to fit the measure."""
        body = self._body_size
        if body is None:
            return
        pages = self._page_dicts
        floor = 0.6 * body
        script_sizes = (0.7 * body, 0.5 * body)
        for pno, d in enumerate(pages):
            if pno + 1 in self.spec.figure_pages:
                continue
            lines = [
                [s for s in ln["spans"] if s["text"].strip()]
                for b in d["blocks"]
                for ln in b.get("lines", [])
            ]
            full_size = [pymupdf.Rect(s["bbox"]) for spans in lines for s in spans if s["size"] >= floor]
            figures = [r for r in self.doc[pno].cluster_drawings() if r.width >= 40 and r.height >= 40]

            def beside_full_size(spans: list[dict], full_size: list[pymupdf.Rect]) -> bool:
                box = pymupdf.Rect(spans[0]["bbox"])
                for s in spans[1:]:
                    box |= s["bbox"]
                box = box + (-floor, -floor, floor, floor)
                return any(box.intersects(r) for r in full_size)

            shrunk = [
                spans
                for spans in lines
                if len("".join(s["text"] for s in spans).strip()) >= 3
                and all("Math" in s["font"] for s in spans)
                and max(s["size"] for s in spans) < floor
                and not any(abs(max(s["size"] for s in spans) - size) < 0.1 for size in script_sizes)
                and not beside_full_size(spans, full_size)
                and not any(pymupdf.Rect(spans[0]["bbox"]) in r for r in figures)
            ]
            if shrunk:
                size = max(s["size"] for s in shrunk[0])
                self._issue(
                    report,
                    "WARNING",
                    "SHRUNKEN_DISPLAY_MATH",
                    pno + 1,
                    f"Math set at {size:.1f}pt, below {floor:.1f}pt",
                    "".join(s["text"] for s in shrunk[0]).strip()[:80],
                )

    def check_visual_line_height_spikes(self, report: CheckReport) -> None:
        """Taste Rule 9: Body text lines must not exceed 2.2x font leading (detects crammed inline multiline formulas)."""
        for pno in range(self.spec.front_matter_pages, len(self.doc)):
            page = self.doc[pno]
            for b in page.get_text("blocks"):
                lines = b[4].splitlines()
                if len(lines) >= 3:
                    avg_h = (b[3] - b[1]) / len(lines)
                    if avg_h > 24.0:
                        self._issue(
                            report,
                            "WARNING",
                            "CRAMPED_INLINE_DISPLAY_MATH",
                            pno + 1,
                            f"Paragraph line height ({avg_h:.1f}pt) severely distorted by crammed multiline formula",
                            lines[0][:80],
                        )


def audit_pdf(
    pdf_path: Path,
    spec: AuditSpec | MonographSpec | None = None,
    tiers: frozenset[int] = ALL_TIERS,
) -> CheckReport:
    if spec is None:
        import pymupdf

        from .books import find_known_book

        with pymupdf.open(str(pdf_path)) as doc:
            spec = find_known_book(pdf_path, len(doc))
    if isinstance(spec, MonographSpec):
        spec = AuditSpec.from_monograph(spec)
    report = DocumentQualityChecker(pdf_path, spec).run_all_checks(tiers)
    report.print_summary()
    return report


if __name__ == "__main__":
    import sys

    from .books import book_specs

    target = Path(sys.argv[1])
    book = book_specs().get(sys.argv[2]) if len(sys.argv) > 2 else None
    _ = audit_pdf(target, book)
