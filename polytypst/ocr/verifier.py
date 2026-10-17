"""Cross-verification engine between Jina OCR v1 and macOS Apple Vision OCR."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import final

from .apple_vision import AppleVisionOCREngine
from .base import OCRPage


@dataclass
class PageVerificationResult:
    page_number: int
    jina_char_count: int
    apple_char_count: int
    ratio: float
    figure_captions_apple: list[str] = field(default_factory=list)
    figure_captions_jina: list[str] = field(default_factory=list)
    math_delimiter_count: int = 0
    anomalies: list[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    total_pages_verified: int
    average_length_ratio: float
    discrepant_pages: list[int]
    page_results: list[PageVerificationResult]


@final
class OCRVerifier:
    """Uses macOS Apple Vision OCR to double check, cross-validate, and audit Jina OCR v1 outputs."""

    FIG_REGEX: re.Pattern[str] = re.compile(
        r"\b(fig|figure|abbildung|图)\.?\s*([0-9]+[A-Za-z0-9\-\.]*)",
        re.IGNORECASE,
    )

    def __init__(self, languages: list[str] | None = None):
        self.apple_engine: AppleVisionOCREngine = AppleVisionOCREngine(
            languages=languages or ["en-US", "fr-FR", "zh-Hans"]
        )

    def verify_page(
        self,
        image_path: Path,
        jina_md_text: str,
        page_number: int,
    ) -> PageVerificationResult:
        """Double check a single page transcribed by Jina OCR against Apple Vision."""
        apple_page: OCRPage = self.apple_engine.recognize_page(image_path, page_number)
        apple_text = " ".join(l.text for l in apple_page.lines)

        jina_chars = len(jina_md_text.strip())
        apple_chars = len(apple_text.strip())
        ratio = (jina_chars / apple_chars) if apple_chars > 0 else 1.0

        anomalies: list[str] = []

        # 1. Length ratio check (flag if Jina output is suspiciously short or bloated)
        if ratio < 0.65:
            anomalies.append(f"Jina output significantly shorter than Apple Vision ({jina_chars} vs {apple_chars} chars)")
        elif ratio > 2.5:
            anomalies.append(f"Jina output significantly longer than Apple Vision ({jina_chars} vs {apple_chars} chars)")

        # 2. Figure caption cross-check
        apple_figs = [l.text for l in apple_page.lines if self.FIG_REGEX.search(l.text)]
        jina_figs: list[str] = []
        for line in jina_md_text.splitlines():
            if self.FIG_REGEX.search(line):
                jina_figs.append(line.strip())

        if apple_figs and not jina_figs:
            anomalies.append(f"Apple Vision detected figures {apple_figs} but Jina omitted figure labels")

        # 3. Math delimiters check (unbalanced single dollar signs)
        math_count = jina_md_text.count("$")
        double_dollars = jina_md_text.count("$$")
        single_dollars = math_count - (double_dollars * 2)
        if single_dollars % 2 != 0:
            anomalies.append(f"Unbalanced single dollar math delimiters ({single_dollars} single $ found)")

        return PageVerificationResult(
            page_number=page_number,
            jina_char_count=jina_chars,
            apple_char_count=apple_chars,
            ratio=ratio,
            figure_captions_apple=apple_figs,
            figure_captions_jina=jina_figs,
            math_delimiter_count=math_count,
            anomalies=anomalies,
        )

    def verify_document(
        self,
        image_paths: list[Path],
        jina_pages_md: list[tuple[int, str]],
    ) -> VerificationReport:
        """Run batch cross-verification across all pages."""
        img_by_pno: dict[int, Path] = {}
        for p in image_paths:
            stem = p.stem
            parts = stem.split("_")
            try:
                p_num = int(parts[-1])
                img_by_pno[p_num] = p
            except ValueError:
                pass

        results: list[PageVerificationResult] = []
        discrepant: list[int] = []

        for pno, jina_text in jina_pages_md:
            img_p = img_by_pno.get(pno)
            if not img_p:
                continue
            res = self.verify_page(img_p, jina_text, pno)
            results.append(res)
            if res.anomalies:
                discrepant.append(pno)

        avg_ratio = sum(r.ratio for r in results) / len(results) if results else 1.0

        return VerificationReport(
            total_pages_verified=len(results),
            average_length_ratio=avg_ratio,
            discrepant_pages=discrepant,
            page_results=results,
        )
