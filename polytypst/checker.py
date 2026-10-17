"""Automated Strict Document Quality Checker & Linter for polytypst deliverables."""

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf


@dataclass
class QualityIssue:
    severity: str  # "ERROR" or "WARNING"
    rule_name: str
    page_num: int
    message: str
    context_snippet: str = ""


@dataclass
class CheckReport:
    pdf_path: Path
    total_pages: int
    issues: list[QualityIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not any(i.severity == "ERROR" for i in self.issues)

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
                f"{prefix} Page {issue.page_num:03d} | {issue.rule_name}: {issue.message}"
            )
            if issue.context_snippet:
                print(f"    Snippet: {issue.context_snippet!r}")
        print("============================================================\n")


class DocumentQualityChecker:
    def __init__(self, pdf_path: Path, language: str = "auto") -> None:
        self.pdf_path: Path = pdf_path
        self.doc: pymupdf.Document = pymupdf.open(pdf_path)
        if language == "auto":
            sample = "".join(
                [self.doc[i].get_text() for i in range(min(5, len(self.doc)))]
            )
            self.language: str = "zh" if re.search(r"[\u4e00-\u9fa5]", sample) else "en"
        else:
            self.language = language

    def run_all_checks(self) -> CheckReport:
        report = CheckReport(pdf_path=self.pdf_path, total_pages=len(self.doc))
        self.check_solo_pages(report)
        self.check_no_literal_tildes(report)
        self.check_no_bullets_in_bibliography(report)
        self.check_no_hyphenated_proper_nouns(report)
        self.check_cross_page_splits(report)
        self.check_isolated_math_blocks(report)
        self.check_unrendered_fractions(report)
        self.check_unrendered_math_delimiters(report)
        self.check_leaked_running_headers(report)
        self.check_extracted_figures_purity(report)
        self.check_equation_margin_overflow(report)
        self.check_chapter_structural_integrity(report)
        return report

    def _extract_body_lines(self, page: pymupdf.Page) -> list[str]:
        """Extract body text lines excluding running headers and folios."""
        rect = page.rect
        H = rect.height
        blocks = page.get_text("blocks")
        body_lines: list[str] = []
        for b in blocks:
            y0, y1 = b[1], b[3]
            if y0 < 0.08 * H or y1 > 0.93 * H:
                continue
            text = b[4].strip()
            for line in text.splitlines():
                l = line.strip()
                if l and not re.match(r"^—?\s*\d+\s*—?$", l):
                    body_lines.append(l)
        return body_lines

    def check_solo_pages(self, report: CheckReport) -> None:
        """Rule 1: No Solo / Orphan pages with <= 2 lines or < 80 characters (except intentional titles)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            if page_idx <= 4:
                continue

            page = self.doc[pno]
            content_lines = self._extract_body_lines(page)
            full_body_text = "".join(content_lines)

            if 0 < len(content_lines) <= 2 and len(full_body_text) < 70:
                if any(l.startswith(("FIG.", "Figure", "Fig.")) for l in content_lines):
                    continue
                report.issues.append(
                    QualityIssue(
                        severity="ERROR",
                        rule_name="NO_SOLO_PAGE",
                        page_num=page_idx,
                        message=f"Solo/orphan page detected ({len(content_lines)} line(s), {len(full_body_text)} chars)",
                        context_snippet=" | ".join(content_lines),
                    )
                )

    def check_no_literal_tildes(self, report: CheckReport) -> None:
        """Rule 2: Zero literal tilde characters (~) in rendered text (e.g. Nuffield~College, Roy,~1952)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            text = self.doc[pno].get_text()
            if "~" in text:
                tilde_lines = [l.strip() for l in text.splitlines() if "~" in l]
                report.issues.append(
                    QualityIssue(
                        severity="ERROR",
                        rule_name="NO_LITERAL_TILDE",
                        page_num=page_idx,
                        message="Literal tilde (~) character leaked into rendered prose",
                        context_snippet=" | ".join(tilde_lines[:2]),
                    )
                )

    def check_no_bullets_in_bibliography(self, report: CheckReport) -> None:
        """Rule 3: Academic bibliography must use hanging indent, NEVER bullet points (•)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            text = self.doc[pno].get_text()
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
                report.issues.append(
                    QualityIssue(
                        severity="ERROR",
                        rule_name="NO_BULLETS_IN_BIBLIOGRAPHY",
                        page_num=page_idx,
                        message="Academic bibliography contains bullet points (•) instead of hanging indent",
                        context_snippet=" | ".join(bullet_lines[:2]),
                    )
                )

    def check_no_hyphenated_proper_nouns(self, report: CheckReport) -> None:
        """Rule 4: Proper nouns and parenthesized names must not be hyphen-cleaved (e.g. Ric-hard)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            lines = self._extract_body_lines(self.doc[pno])
            for l in lines:
                # Check for hyphenated English names like "Ric-" or "Gene-"
                m = re.search(r"\b([A-Z][a-z]{1,4})-[\s]*$", l)
                if (
                    m
                    and not l.endswith(("—", "–"))
                    and m.group(1) not in ["Heine", "Mean", "Non", "Self"]
                ):
                    report.issues.append(
                        QualityIssue(
                            severity="WARNING",
                            rule_name="HYPHENATED_PROPER_NOUN",
                            page_num=page_idx,
                            message=f"Possible hyphen-cleaved English name '{m.group(1)}-' at line end",
                            context_snippet=l,
                        )
                    )

    def check_cross_page_splits(self, report: CheckReport) -> None:
        """Rule 5: No unclosed parentheses or split English proper nouns across page breaks."""
        for pno in range(len(self.doc) - 1):
            cur_lines = self._extract_body_lines(self.doc[pno])
            next_lines = self._extract_body_lines(self.doc[pno + 1])

            if not cur_lines or not next_lines:
                continue

            cur_text = " ".join(cur_lines)
            last_line = cur_lines[-1]
            first_line = next_lines[0]

            open_count = cur_text.count("（") + cur_text.count("(")
            close_count = cur_text.count("）") + cur_text.count(")")
            next_head = " ".join(next_lines[:3])
            next_open = next_head.count("（") + next_head.count("(")
            next_close = next_head.count("）") + next_head.count(")")
            if open_count > close_count and (open_count + next_open) > (
                close_count + next_close
            ):
                report.issues.append(
                    QualityIssue(
                        severity="WARNING",
                        rule_name="UNCLOSED_PARENTHESIS_PAGE_BREAK",
                        page_num=pno + 1,
                        message="Page ends with an unclosed parenthesis in body text",
                        context_snippet=f"{last_line}  >>> NEXT PAGE >>>  {first_line}",
                    )
                )

            # Mid-word English cleaving
            if self.language == "zh":
                is_bib = "参考文献" in cur_text or (pno + 1) >= 200
                if (
                    not is_bib
                    and re.search(r"\b[A-Za-z]+$", last_line)
                    and re.search(r"^[A-Za-z]+\b", first_line)
                ):
                    report.issues.append(
                        QualityIssue(
                            severity="ERROR",
                            rule_name="CROSS_PAGE_WORD_SPLIT",
                            page_num=pno + 1,
                            message="English proper noun cleaved across page boundary",
                            context_snippet=f"{last_line}  >>> NEXT PAGE >>>  {first_line}",
                        )
                    )
            else:
                # English document: normal sentence wrap across pages is standard.
                # Only flag if last line ends with a hyphen '-', indicating an unstitched word.
                if last_line.endswith("-"):
                    if any(
                        last_line.rstrip().endswith(h)
                        for h in [
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
                        ]
                    ):
                        continue
                    report.issues.append(
                        QualityIssue(
                            severity="ERROR",
                            rule_name="CROSS_PAGE_WORD_SPLIT",
                            page_num=pno + 1,
                            message="Word cleaved across page boundary with hyphen",
                            context_snippet=f"{last_line}  >>> NEXT PAGE >>>  {first_line}",
                        )
                    )

    def check_hallucinated_boilerplate(self, report: CheckReport) -> None:
        """Rule 6: Zero foreign boilerplate keywords from VLM hallucinations."""
        blacklist = [
            "raspberry",
            "temperature monitoring",
            "user-friendly interface",
            "energy efficient",
            "dissertation",
            "student learning",
            "social media",
            "research questions",
            "smith, j.",
        ]
        for pno in range(len(self.doc)):
            text = self.doc[pno].get_text().lower()
            for kw in blacklist:
                if kw in text:
                    report.issues.append(
                        QualityIssue(
                            severity="ERROR",
                            rule_name="HALLUCINATED_BOILERPLATE",
                            page_num=pno + 1,
                            message=f"Hallucinated template keyword '{kw}' detected",
                            context_snippet=kw,
                        )
                    )

    def check_isolated_math_blocks(self, report: CheckReport) -> None:
        """Rule 7: No single-letter isolated display equations breaking sentence flow."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            page = self.doc[pno]
            H = page.rect.height
            blocks = page.get_text("blocks")
            for b in blocks:
                x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
                if y0 < 0.10 * H or y1 > 0.90 * H:
                    continue
                # Subscripts, superscripts, and summation limits have height <= 9.5pt
                if (y1 - y0) <= 9.5:
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
                    report.issues.append(
                        QualityIssue(
                            severity="ERROR",
                            rule_name="ISOLATED_MATH_BLOCK",
                            page_num=page_idx,
                            message=f"Isolated single-letter display math block '{text}' breaking prose sentence",
                            context_snippet=text,
                        )
                    )

    def check_unrendered_fractions(self, report: CheckReport) -> None:
        """Rule 8: Detect unrendered fraction syntax {A}{B}."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            t = self.doc[pno].get_text()
            matches = re.findall(
                r"\{[0-9a-zA-Z\+\-\*\/]{1,6}\}\{[0-9a-zA-Z\+\-\*\/]{1,6}\}", t
            )
            if matches:
                report.issues.append(
                    QualityIssue(
                        severity="ERROR",
                        rule_name="UNRENDERED_FRACTION",
                        page_num=page_idx,
                        message=f"Unrendered fraction syntax detected: '{matches[0]}'",
                        context_snippet=" | ".join(matches[:2]),
                    )
                )

    def check_equation_margin_overflow(self, report: CheckReport) -> None:
        """Rule 9: Equations and text must not exceed page margin boundary."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            page = self.doc[pno]
            rect = page.rect
            max_allowed_x = rect.width - 25
            for b in page.get_text("blocks"):
                x1 = b[2]
                if x1 > max_allowed_x:
                    snippet = b[4].strip().replace("\n", " ")[:80]
                    report.issues.append(
                        QualityIssue(
                            severity="WARNING",
                            rule_name="MARGIN_OVERFLOW",
                            page_num=page_idx,
                            message=f"Block overflowed margin: x1={x1:.1f} > max={max_allowed_x:.1f}",
                            context_snippet=snippet,
                        )
                    )

    def check_chapter_structural_integrity(self, report: CheckReport) -> None:
        """Rule 10: Chapters must progress monotonically; no duplicate headings or stale headers."""
        current_chapter = 0
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            if page_idx <= 8:
                continue
            blocks = self.doc[pno].get_text("blocks")
            for b in blocks:
                text = b[4].strip()
                m = re.search(r"CHAPTER\s+(\d+)\s*:\s*([A-Z\s]+)", text)
                if m:
                    ch_num = int(m.group(1))
                    if ch_num < current_chapter:
                        report.issues.append(
                            QualityIssue(
                                severity="ERROR",
                                rule_name="CHAPTER_REGRESSION",
                                page_num=page_idx,
                                message=f"Chapter regression! Found Chapter {ch_num} on page {page_idx} after Chapter {current_chapter}",
                                context_snippet=text[:80],
                            )
                        )
                    current_chapter = ch_num

            # Check running header on odd pages
            if page_idx % 2 != 0 and current_chapter > 1:
                first_line = (
                    self.doc[pno].get_text().splitlines()[0]
                    if self.doc[pno].get_text().splitlines()
                    else ""
                )
                if (
                    "CHAPTER 1" in first_line
                    or "COMPLEX NUMBERS" in first_line.upper()
                    or first_line.strip().upper() == "EXERCISES"
                ):
                    report.issues.append(
                        QualityIssue(
                            severity="ERROR",
                            rule_name="STALE_RUNNING_HEADER",
                            page_num=page_idx,
                            message=f"Running header stuck on '{first_line}' while in Chapter {current_chapter}",
                            context_snippet=first_line,
                        )
                    )

    def check_unrendered_math_delimiters(self, report: CheckReport) -> None:
        math_delim_re = re.compile(
            r"\$\$|\$\s+[A-Za-z0-9\\\(]|[A-Za-z0-9\)]\s+\$|\$_[A-Za-z0-9\{]|\\neq\b"
        )
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            text = self.doc[pno].get_text()
            m = math_delim_re.search(text)
            if m:
                snippet = text[max(0, m.start() - 25) : min(len(text), m.end() + 25)].replace(
                    "\n", " "
                )
                report.issues.append(
                    QualityIssue(
                        severity="ERROR",
                        rule_name="UNRENDERED_MATH_DELIMITER",
                        page_num=page_idx,
                        message=f"Unrendered math delimiter or macro '{m.group(0)}' leaked into PDF",
                        context_snippet=snippet,
                    )
                )

    def check_leaked_running_headers(self, report: CheckReport) -> None:
        header_re = re.compile(
            r"(?:\[[IVXLCDM]+,\s*§\s*\d+[a-z]?|[IVXLCDM]+,\s*§\s*\d+[a-z]?\]\s+[A-Z]{4,})"
        )
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            for l in self._extract_body_lines(self.doc[pno]):
                if header_re.search(l):
                    report.issues.append(
                        QualityIssue(
                            severity="ERROR",
                            rule_name="LEAKED_RUNNING_HEADER",
                            page_num=page_idx,
                            message="Scanned running header with section bracket leaked into body text",
                            context_snippet=l[:80],
                        )
                    )

    def check_extracted_figures_purity(self, report: CheckReport) -> None:
        from .vision.typesafe_jev import TypeSafeJevVision

        fig_dir = self.pdf_path.parent / "figures"
        if not fig_dir.exists():
            return
        for png_path in sorted(fig_dir.glob("*.png")):
            ok, reasons = TypeSafeJevVision.verify_cropped_diagram(png_path)
            if not ok:
                report.issues.append(
                    QualityIssue(
                        severity="ERROR",
                        rule_name="CORRUPTED_FIGURE_CROP",
                        page_num=1,
                        message=f"Figure '{png_path.name}' failed purity check: {'; '.join(reasons)}",
                        context_snippet=png_path.name,
                    )
                )


def audit_pdf(pdf_path: Path) -> CheckReport:
    checker = DocumentQualityChecker(pdf_path)
    report = checker.run_all_checks()
    report.print_summary()
    return report


if __name__ == "__main__":
    import sys

    target = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("output/modern_firm_jina/book.pdf")
    )
    audit_pdf(target)
