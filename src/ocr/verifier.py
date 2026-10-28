"""Cross-verification between model transcripts and macOS Apple Vision OCR."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import final

from .apple_vision import AppleVisionReader
from .lines import LineStore, source_ocr_dir
from .pages import LineReader, PageImage
from .transcripts import TranscriptStore


@dataclass
class PageVerificationResult:
    page_number: int
    transcript_char_count: int
    apple_char_count: int
    ratio: float
    figure_captions_apple: list[str] = field(default_factory=list)
    figure_captions_transcript: list[str] = field(default_factory=list)
    math_delimiter_count: int = 0
    anomalies: list[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    total_pages_verified: int
    average_length_ratio: float
    discrepant_pages: list[int]
    page_results: list[PageVerificationResult]


def _page_num(path: Path) -> int:
    m = re.search(r"\d+", path.stem)
    return int(m.group(0)) if m else 0


@final
class OCRVerifier:
    """Uses macOS Apple Vision OCR to double check, cross-validate, and audit OCR transcriptions."""

    FIG_REGEX: re.Pattern[str] = re.compile(
        r"\b(fig|figure|abbildung|图)\.?\s*([0-9]+[A-Za-z0-9\-\.]*)",
        re.IGNORECASE,
    )

    def __init__(
        self, languages: Sequence[str] | None = None, reader: LineReader | None = None
    ) -> None:
        self.languages: tuple[str, ...] = tuple(languages or ["en-US", "fr-FR", "zh-Hans"])
        self.reader: LineReader = reader or AppleVisionReader(self.languages)
    def verify_pages(
        self,
        renders_dir: Path,
        transcripts_dir: Path,
        line_cache: Path | None = None,
    ) -> VerificationReport:
        renders = sorted(
            [p for p in renders_dir.glob("p_*.*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")],
            key=_page_num,
        )
        if not renders:
            print("No rendered page images found to verify.")
            return VerificationReport(0, 1.0, [], [])

        page_images: list[PageImage] = []
        md_by_pno: dict[int, str] = {}
        store = TranscriptStore(transcripts_dir)
        for r in renders:
            m = re.search(r"\d+", r.stem)
            if not m:
                continue
            pno = int(m.group(0))
            page_images.append(PageImage(pno, r))
            if (text := store.text(pno)) is not None:
                md_by_pno[pno] = text
            elif (cand := transcripts_dir / f"p_{pno}.md").exists():
                md_by_pno[pno] = cand.read_text(encoding="utf-8")

        results: list[PageVerificationResult] = []
        discrepant: list[int] = []
        cache_dir = line_cache or source_ocr_dir(renders_dir.parent)
        lines_by_page = LineStore(cache_dir).read(page_images, self.reader)

        for pno, page_lines in sorted(lines_by_page.items()):
            apple_text = " ".join(l.text for l in page_lines)
            md_text = md_by_pno.get(pno, "")

            md_chars = len(md_text.strip())
            apple_chars = len(apple_text.strip())
            ratio = (md_chars / apple_chars) if apple_chars > 0 else 1.0

            anomalies: list[str] = []

            # 1. Length ratio check
            if apple_chars > 50 and ratio < 0.60:
                anomalies.append(
                    f"Transcript significantly shorter than Apple Vision ({md_chars} vs {apple_chars} chars, ratio {ratio:.2f})"
                )
            elif apple_chars > 50 and ratio > 2.8:
                anomalies.append(
                    f"Transcript significantly longer than Apple Vision ({md_chars} vs {apple_chars} chars, ratio {ratio:.2f})"
                )

            # 2. Figure caption check
            apple_figs = [l.text for l in page_lines if self.FIG_REGEX.search(l.text)]
            md_figs = [l.strip() for l in md_text.splitlines() if self.FIG_REGEX.search(l)]
            if apple_figs and not md_figs:
                anomalies.append(f"Apple Vision detected figures {apple_figs} but transcript omitted figure labels")

            # 3. Math delimiters check
            math_count = md_text.count("$")
            double_dollars = md_text.count("$$")
            single_dollars = math_count - (double_dollars * 2)
            if single_dollars % 2 != 0:
                anomalies.append(f"Unbalanced single dollar math delimiters ({single_dollars} single $ found)")

            res = PageVerificationResult(
                page_number=pno,
                transcript_char_count=md_chars,
                apple_char_count=apple_chars,
                ratio=ratio,
                figure_captions_apple=apple_figs,
                figure_captions_transcript=md_figs,
                math_delimiter_count=math_count,
                anomalies=anomalies,
            )
            results.append(res)
            if anomalies:
                discrepant.append(pno)

        avg_ratio = sum(r.ratio for r in results) / len(results) if results else 1.0
        print(f"Verified {len(results)} pages. Discrepancies found on {len(discrepant)} pages.")
        for p in results:
            if p.anomalies:
                print(f"  [Page {p.page_number}] {'; '.join(p.anomalies)}")

        return VerificationReport(
            total_pages_verified=len(results),
            average_length_ratio=avg_ratio,
            discrepant_pages=discrepant,
            page_results=results,
        )


def verify_transcripts(
    renders_dir: Path,
    transcripts_dir: Path,
    languages: Sequence[str] | None = None,
) -> VerificationReport:
    verifier = OCRVerifier(languages=languages)
    return verifier.verify_pages(renders_dir, transcripts_dir)
