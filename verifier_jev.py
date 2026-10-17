"""
TypeSafe Jev Semantic & Layout Verifier for Mathematical Document Pipelines.
Audits compiled Typst and PDF deliverables for semantic integrity, typography,
unrendered LaTeX, and layout regressions.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf


@dataclass
class JevViolation:
    page_num: int
    rule: str
    severity: str  # "ERROR", "WARNING"
    snippet: str
    message: str


@dataclass
class JevReport:
    pdf_path: Path
    total_pages: int
    violations: list[JevViolation] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not any(v.severity == "ERROR" for v in self.violations)

    def print_report(self) -> None:
        print("\n================ JEV SEMANTIC & LAYOUT REPORT ================")
        print(f"Target: {self.pdf_path.name} ({self.total_pages} pages)")
        errors = [v for v in self.violations if v.severity == "ERROR"]
        warns = [v for v in self.violations if v.severity == "WARNING"]
        print(
            f"Status: {'PASSED (Clean)' if not errors else 'FAILED'} | {len(errors)} Errors, {len(warns)} Warnings"
        )
        print("-" * 65)
        for v in self.violations:
            prefix = "❌ [ERROR]" if v.severity == "ERROR" else "⚠️  [WARN] "
            print(f"{prefix} Page {v.page_num:03d} | {v.rule}: {v.message}")
            if v.snippet:
                print(f"    Context: {v.snippet[:120]!r}")
        print("============================================================\n")


class JevSemanticVerifier:
    def __init__(self, pdf_path: Path) -> None:
        self.pdf_path: Path = Path(pdf_path)
        self.doc: pymupdf.Document = pymupdf.open(self.pdf_path)

    def audit(self) -> JevReport:
        report = JevReport(pdf_path=self.pdf_path, total_pages=len(self.doc))
        self.check_spaced_words(report)
        self.check_unconverted_markdown_headings(report)
        self.check_raw_latex_macros(report)
        self.check_unrendered_math_delimiters(report)
        self.check_mangled_math_tokens(report)
        self.check_isolated_display_letters(report)
        self.check_orphaned_equation_numbers(report)
        self.check_inverted_partial_derivatives(report)
        self.check_mangled_dots(report)
        self.check_visual_line_height_spikes(report)
        self.check_figure_crops_with_jev(report)
        return report

    def check_spaced_words(self, report: JevReport) -> None:
        """Rule 1: No letter-spaced words like 'i n f i n i t y', 'p a r t i a l', 'l e f t'."""
        bad_patterns = [
            (r"\bi\s+n\s+f\s+i\s+n\s+i\s+t\s+y\b", "Mangled 'infinity'"),
            (r"\bp\s+a\s+r\s+t\s+i\s+a\s+l\b", "Mangled 'partial'"),
            (r"\bl\s+e\s+f\s+t\b", "Mangled 'left'"),
            (r"\br\s+i\s+g\s+h\s+t\b", "Mangled 'right'"),
            (r"\bc\s+i\s+r\s+c\b", "Mangled 'circ'"),
            (r"\bd\s+o\s+t\s+s\b", "Mangled 'dots'"),
        ]
        for pno in range(len(self.doc)):
            text = unicodedata.normalize("NFKC", self.doc[pno].get_text())
            for pat, name in bad_patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    report.violations.append(
                        JevViolation(
                            page_num=pno + 1,
                            rule="SPACED_MATH_TOKEN",
                            severity="ERROR",
                            snippet=text[
                                max(0, m.start() - 20) : min(len(text), m.end() + 20)
                            ],
                            message=f"{name} detected on canvas",
                        )
                    )

    def check_unconverted_markdown_headings(self, report: JevReport) -> None:
        """Rule 2: No raw markdown heading hashes (###, ##) in rendered text."""
        for pno in range(len(self.doc)):
            text = self.doc[pno].get_text()
            for line in text.splitlines():
                l = line.strip()
                if l.startswith(("#", "\\#", "###", "##")):
                    report.violations.append(
                        JevViolation(
                            page_num=pno + 1,
                            rule="RAW_MARKDOWN_HEADING",
                            severity="ERROR",
                            snippet=l[:80],
                            message="Raw markdown heading hashes leaking into rendered body",
                        )
                    )

    def check_raw_latex_macros(self, report: JevReport) -> None:
        r"""Rule 3: No unrendered raw LaTeX macros (\begin, \frac, \operatorname)."""
        latex_kws = [
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
        ]
        leaked_math_words = (
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
        italic_run_re = re.compile(r"[\U0001D434-\U0001D6A5]{3,}")
        for pno in range(len(self.doc)):
            raw_text = self.doc[pno].get_text()
            norm_text = unicodedata.normalize("NFKC", raw_text)
            for kw in latex_kws:
                if kw in norm_text:
                    report.violations.append(
                        JevViolation(
                            page_num=pno + 1,
                            rule="UNRENDERED_LATEX_MACRO",
                            severity="ERROR",
                            snippet=kw,
                            message=f"Raw unrendered LaTeX macro '{kw}' present in rendered canvas",
                        )
                    )
            for m in italic_run_re.finditer(raw_text):
                word = unicodedata.normalize("NFKC", m.group(0))
                w_low = word.lower()
                if any(bad in w_low for bad in leaked_math_words):
                    report.violations.append(
                        JevViolation(
                            page_num=pno + 1,
                            rule="UNRENDERED_MATH_ITALIC_WORD",
                            severity="ERROR",
                            snippet=raw_text[
                                max(0, m.start() - 15) : min(
                                    len(raw_text), m.end() + 15
                                )
                            ].replace("\n", " "),
                            message=f"Multi-letter Mathematical Italic token '{word}' leaked inside math mode",
                        )
                    )

    def check_mangled_math_tokens(self, report: JevReport) -> None:
        """Rule 4: Detect mashed tokens like 'dote', 'cosecz'."""
        bad_mashed = [
            r"\bdote\b",
            r"\bcosecz\b",
            r"\bzin\b",
            r"\bbmod\b",
            r",d[zxyrtuvs]\b",
            r"\(\d+\([a-zA-Z\s]+\)\d+\)",
        ]
        for pno in range(len(self.doc)):
            text = unicodedata.normalize("NFKC", self.doc[pno].get_text())
            for pat in bad_mashed:
                m = re.search(pat, text)
                if m:
                    report.violations.append(
                        JevViolation(
                            page_num=pno + 1,
                            rule="MANGLED_MATH_TOKEN",
                            severity="ERROR",
                            snippet=text[
                                max(0, m.start() - 20) : min(len(text), m.end() + 20)
                            ],
                            message=f"Mangled concatenated token '{m.group(0)}' detected",
                        )
                    )

    def check_isolated_display_letters(self, report: JevReport) -> None:
        """Rule 5: No isolated single-letter display math blocks breaking sentences."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            if page_idx in [8, 9, 10, 11, 12, 13]:  # Figure diagram pages
                continue
            blocks = self.doc[pno].get_text("blocks")
            for b in blocks:
                text = b[4].strip()
                if len(text) == 1 and text.isalpha() and (b[3] - b[1]) > 10:
                    # Check if it has a nearby vertical fraction partner
                    is_frac = any(
                        o != b
                        and abs(o[1] - b[3]) < 22
                        and (o[0] <= b[2] + 10 and o[2] >= b[0] - 10)
                        for o in blocks
                    )
                    if not is_frac:
                        report.violations.append(
                            JevViolation(
                                page_num=page_idx,
                                rule="ISOLATED_DISPLAY_LETTER",
                                severity="ERROR",
                                snippet=text,
                                message=f"Single letter '{text}' isolated as display block",
                            )
                        )

    def check_orphaned_equation_numbers(self, report: JevReport) -> None:
        """Taste Rule 6: Equation numbers (N) must not sit alone on orphaned lines."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            if page_idx <= 8:  # Skip TOC
                continue
            blocks = self.doc[pno].get_text("blocks")
            for b in blocks:
                t = b[4].strip()
                # Check if block is solely an equation number like "(56)" or "(34)"
                if re.match(r"^\(\d+\)$", t):
                    # Check if there is a display equation on the same vertical level
                    has_adjacent_formula = any(
                        o != b
                        and (
                            abs((o[1] + o[3]) / 2 - (b[1] + b[3]) / 2) < 26
                            or (o[1] - 8 <= (b[1] + b[3]) / 2 <= o[3] + 8)
                        )
                        for o in blocks
                    )
                    if not has_adjacent_formula:
                        report.violations.append(
                            JevViolation(
                                page_num=page_idx,
                                rule="ORPHANED_EQUATION_NUMBER",
                                severity="ERROR",
                                snippet=t,
                                message=f"Equation number '{t}' sitting stranded on an empty line above/below formula",
                            )
                        )

            d = self.doc[pno].get_text("dict")
            spans: list[tuple[tuple[float, float, float, float], str]] = []
            for blk in d.get("blocks", []):
                if blk.get("type") != 0:
                    continue
                for line in blk.get("lines", []):
                    for sp in line.get("spans", []):
                        st = str(sp.get("text", "")).strip()
                        if st:
                            bbox = sp.get("bbox", (0.0, 0.0, 0.0, 0.0))
                            spans.append(
                                (
                                    (
                                        float(bbox[0]),
                                        float(bbox[1]),
                                        float(bbox[2]),
                                        float(bbox[3]),
                                    ),
                                    st,
                                )
                            )
            for i, (b1, t1) in enumerate(spans):
                if (
                    re.match(r"^\(\d+(?:\.\d+[a-z']?)?\)$", t1)
                    and t1 != "(0)"
                    and b1[2] > 382
                ):
                    cy1 = (b1[1] + b1[3]) / 2.0
                    for j, (b2, t2) in enumerate(spans):
                        cy2 = (b2[1] + b2[3]) / 2.0
                        if (
                            i != j
                            and abs(cy1 - cy2) < 6.0
                            and b2[2] > b1[0] + 1.0
                            and b2[0] < b1[2] - 1.0
                        ):
                            report.violations.append(
                                JevViolation(
                                    page_num=page_idx,
                                    rule="EQUATION_NUMBER_COLLISION",
                                    severity="ERROR",
                                    snippet=f"{t2} <-> {t1}",
                                    message=f"Equation number {t1} collides horizontally with '{t2}'",
                                )
                            )

    def check_inverted_partial_derivatives(self, report: JevReport) -> None:
        r"""Taste Rule 7: Partial derivatives must have correct denominator grouping (no \partial U / \partial x)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            t = self.doc[pno].get_text()
            # Check for inverted pattern: partial followed by fraction line then variable
            m = re.search(
                r"(?:𝜕|partial)\s*[A-Za-z0-9_]+\s*\n\s*(?:𝜕|partial)\s*\n\s*[xyz]", t
            )
            if m:
                report.violations.append(
                    JevViolation(
                        page_num=page_idx,
                        rule="INVERTED_PARTIAL_DERIVATIVE",
                        severity="ERROR",
                        snippet=t[
                            max(0, m.start() - 10) : min(len(t), m.end() + 10)
                        ].replace("\n", " "),
                        message="Inverted partial derivative fraction detected (denominator parsed as operator)",
                    )
                )

    def check_mangled_dots(self, report: JevReport) -> None:
        """Taste Rule 8: Ellipsis must be rendered as clean dots, never '⋅𝑠' or 'cdot s'."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            t = self.doc[pno].get_text()
            if "⋅𝑠" in t or "⋅ 𝑠" in t or "dot s" in t:
                m = re.search(r"(?:⋅\s*𝑠|dot\s+s)", t)
                if m:
                    report.violations.append(
                        JevViolation(
                            page_num=page_idx,
                            rule="MANGLED_ELLIPSIS_DOTS",
                            severity="ERROR",
                            snippet=t[
                                max(0, m.start() - 15) : min(len(t), m.end() + 15)
                            ].replace("\n", " "),
                            message="Mangled ellipsis '⋅𝑠' (corrupted from \\cdots) detected",
                        )
                    )

    def check_visual_line_height_spikes(self, report: JevReport) -> None:
        """Taste Rule 9: Body text lines must not exceed 2.2x font leading (detects crammed inline multiline formulas)."""
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            page = self.doc[pno]
            for b in page.get_text("blocks"):
                # Ignore display equation blocks (usually 1-3 lines centered)
                if (
                    b[0] > 100
                    and b[2] < page.rect.width - 100
                    and len(b[4].splitlines()) <= 2
                ):
                    continue
                # Check for individual lines within paragraphs that have excessive height > 24pt
                lines = b[4].splitlines()
                if len(lines) >= 3:
                    avg_h = (b[3] - b[1]) / len(lines)
                    if avg_h > 24.0:
                        report.violations.append(
                            JevViolation(
                                page_num=page_idx,
                                rule="CRAMPED_INLINE_DISPLAY_MATH",
                                severity="WARNING",
                                snippet=lines[0][:80],
                                message=f"Paragraph line height ({avg_h:.1f}pt) severely distorted by crammed multiline formula",
                            )
                        )

    def check_unrendered_math_delimiters(self, report: JevReport) -> None:
        delim_re = re.compile(
            r"\$\$|\$\s+[A-Za-z0-9\\\(]|[A-Za-z0-9\)]\s+\$|\$_[A-Za-z0-9\{]|\\neq\b"
        )
        for pno in range(len(self.doc)):
            page_idx = pno + 1
            text = self.doc[pno].get_text()
            m = delim_re.search(text)
            if m:
                snippet = text[
                    max(0, m.start() - 25) : min(len(text), m.end() + 25)
                ].replace("\n", " ")
                report.violations.append(
                    JevViolation(
                        page_num=page_idx,
                        rule="UNRENDERED_MATH_DELIMITER",
                        severity="ERROR",
                        snippet=snippet,
                        message=f"Literal math delimiter or macro '{m.group(0)}' leaked into rendered PDF",
                    )
                )

    def check_figure_crops_with_jev(self, report: JevReport) -> None:
        from polytypst.vision.typesafe_jev import TypeSafeJevVision

        fig_dir = self.pdf_path.parent / "figures"
        if not fig_dir.exists():
            return
        for png_path in sorted(fig_dir.glob("*.png")):
            ok, reasons = TypeSafeJevVision.verify_cropped_diagram(png_path)
            if not ok:
                report.violations.append(
                    JevViolation(
                        page_num=1,
                        rule="CORRUPTED_FIGURE_CROP",
                        severity="ERROR",
                        snippet=png_path.name,
                        message=f"Figure '{png_path.name}' failed purity verification: {'; '.join(reasons)}",
                    )
                )


def audit_jev(pdf_path: Path) -> JevReport:
    verifier = JevSemanticVerifier(pdf_path)
    report = verifier.audit()
    report.print_report()
    return report


if __name__ == "__main__":
    import sys

    p = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("output/ahlfors/ahlfors_complete.pdf")
    )
    audit_jev(p)
