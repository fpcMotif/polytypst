"""Automated Strict Document Quality Checker & Linter for polytypst deliverables."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict
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
    issues: List[QualityIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not any(i.severity == "ERROR" for i in self.issues)

    def print_summary(self):
        print(f"\n================ STRICT QUALITY CHECK REPORT ================")
        print(f"File: {self.pdf_path.name} ({self.total_pages} pages)")
        errors = [i for i in self.issues if i.severity == "ERROR"]
        warns = [i for i in self.issues if i.severity == "WARNING"]
        print(f"Total Issues: {len(self.issues)} ({len(errors)} Errors, {len(warns)} Warnings)")
        print("-" * 65)
        for issue in self.issues:
            prefix = "❌ [ERROR]" if issue.severity == "ERROR" else "⚠️  [WARN] "
            print(f"{prefix} Page {issue.page_num:03d} | {issue.rule_name}: {issue.message}")
            if issue.context_snippet:
                print(f"    Snippet: {repr(issue.context_snippet)}")
        print("============================================================\n")


class DocumentQualityChecker:
    def __init__(self, pdf_path: Path, language: str = "zh"):
        self.pdf_path = pdf_path
        self.doc = pymupdf.open(pdf_path)
        self.language = language

    def run_all_checks(self) -> CheckReport:
        report = CheckReport(pdf_path=self.pdf_path, total_pages=len(self.doc))
        self.check_solo_pages(report)
        self.check_no_literal_tildes(report)
        self.check_no_bullets_in_bibliography(report)
        self.check_no_hyphenated_proper_nouns(report)
        self.check_cross_page_splits(report)
        self.check_hallucinated_boilerplate(report)
        return report

    def _extract_body_lines(self, page) -> List[str]:
        """Extract body text lines excluding running headers and folios."""
        rect = page.rect
        H = rect.height
        blocks = page.get_text("blocks")
        body_lines = []
        for b in blocks:
            y0, y1 = b[1], b[3]
            if y0 < 0.10 * H or y1 > 0.90 * H:
                continue
            text = b[4].strip()
            for line in text.splitlines():
                l = line.strip()
                if l and not re.match(r"^—?\s*\d+\s*—?$", l):
                    body_lines.append(l)
        return body_lines

    def check_solo_pages(self, report: CheckReport):
        """Rule 1: No Solo / Orphan pages with <= 2 lines or < 80 characters (except intentional titles)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            if page_idx <= 4:
                continue

            page = self.doc[pno]
            content_lines = self._extract_body_lines(page)
            full_body_text = "".join(content_lines)

            # If a content page has only 1 or 2 short lines sitting alone
            if 0 < len(content_lines) <= 2 and len(full_body_text) < 70:
                report.issues.append(QualityIssue(
                    severity="ERROR",
                    rule_name="NO_SOLO_PAGE",
                    page_num=page_idx,
                    message=f"Solo/orphan page detected ({len(content_lines)} line(s), {len(full_body_text)} chars)",
                    context_snippet=" | ".join(content_lines)
                ))

    def check_no_literal_tildes(self, report: CheckReport):
        """Rule 2: Zero literal tilde characters (~) in rendered text (e.g. Nuffield~College, Roy,~1952)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            text = self.doc[pno].get_text()
            if "~" in text:
                tilde_lines = [l.strip() for l in text.splitlines() if "~" in l]
                report.issues.append(QualityIssue(
                    severity="ERROR",
                    rule_name="NO_LITERAL_TILDE",
                    page_num=page_idx,
                    message="Literal tilde (~) character leaked into rendered prose",
                    context_snippet=" | ".join(tilde_lines[:2])
                ))

    def check_no_bullets_in_bibliography(self, report: CheckReport):
        """Rule 3: Academic bibliography must use hanging indent, NEVER bullet points (•)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            # Only check pages in the actual bibliography section (pages >= 195)
            if page_idx < 195:
                continue
            text = self.doc[pno].get_text()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            bullet_lines = [l for l in lines if l.startswith(("•", "* ", "- ")) or " • " in l]
            if bullet_lines:
                report.issues.append(QualityIssue(
                    severity="ERROR",
                    rule_name="NO_BULLETS_IN_BIBLIOGRAPHY",
                    page_num=page_idx,
                    message="Academic bibliography contains bullet points (•) instead of hanging indent",
                    context_snippet=" | ".join(bullet_lines[:2])
                ))
    def check_no_hyphenated_proper_nouns(self, report: CheckReport):
        """Rule 4: Proper nouns and parenthesized names must not be hyphen-cleaved (e.g. Ric-hard)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            lines = self._extract_body_lines(self.doc[pno])
            for l in lines:
                # Check for hyphenated English names like "Ric-" or "Gene-"
                m = re.search(r"\b([A-Z][a-z]{1,4})-[\s]*$", l)
                if m and not l.endswith(("—", "–")):
                    report.issues.append(QualityIssue(
                        severity="WARNING",
                        rule_name="HYPHENATED_PROPER_NOUN",
                        page_num=page_idx,
                        message=f"Possible hyphen-cleaved English name '{m.group(1)}-' at line end",
                        context_snippet=l
                    ))

    def check_cross_page_splits(self, report: CheckReport):
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
            if open_count > close_count:
                report.issues.append(QualityIssue(
                    severity="WARNING",
                    rule_name="UNCLOSED_PARENTHESIS_PAGE_BREAK",
                    page_num=pno + 1,
                    message="Page ends with an unclosed parenthesis in body text",
                    context_snippet=f"{last_line}  >>> NEXT PAGE >>>  {first_line}"
                ))

            # Mid-word English cleaving
            is_bib = "参考文献" in cur_text or (pno + 1) >= 200
            if not is_bib and re.search(r"\b[A-Za-z]+$", last_line) and re.search(r"^[A-Za-z]+\b", first_line):
                report.issues.append(QualityIssue(
                    severity="ERROR",
                    rule_name="CROSS_PAGE_WORD_SPLIT",
                    page_num=pno + 1,
                    message="English proper noun cleaved across page boundary",
                    context_snippet=f"{last_line}  >>> NEXT PAGE >>>  {first_line}"
                ))

    def check_hallucinated_boilerplate(self, report: CheckReport):
        """Rule 6: Zero foreign boilerplate keywords from VLM hallucinations."""
        blacklist = [
            "raspberry", "temperature monitoring", "user-friendly interface",
            "energy efficient", "dissertation", "student learning",
            "social media", "research questions", "smith, j."
        ]
        for pno in range(len(self.doc)):
            text = self.doc[pno].get_text().lower()
            for kw in blacklist:
                if kw in text:
                    report.issues.append(QualityIssue(
                        severity="ERROR",
                        rule_name="HALLUCINATED_BOILERPLATE",
                        page_num=pno + 1,
                        message=f"Hallucinated template keyword '{kw}' detected",
                        context_snippet=kw
                    ))


def audit_pdf(pdf_path: Path) -> CheckReport:
    checker = DocumentQualityChecker(pdf_path)
    report = checker.run_all_checks()
    report.print_summary()
    return report


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output/modern_firm_jina/book.pdf")
    audit_pdf(target)
