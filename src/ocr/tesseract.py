"""Tesseract 5 OCR Engine fallback for 129 languages."""

import shutil
import subprocess
from collections.abc import Iterator, Sequence

from .pages import LinePage, OCRBackendError, OcrLine, PageImage

_TESSERACT_LANGUAGES = {
    "en-US": "eng",
    "fr-FR": "fra",
    "de-DE": "deu",
    "zh-Hans": "chi_sim",
    "ja-JP": "jpn",
}
_NIX_SHELL = [
    "nix",
    "--extra-experimental-features",
    "nix-command flakes",
    "shell",
    "nixpkgs#tesseract5",
    "--command",
]


def tesseract_languages(languages: Sequence[str]) -> str:
    return "+".join(
        _TESSERACT_LANGUAGES.get(language, language) for language in languages
    )


def tsv_lines(tsv: str) -> tuple[OcrLine, ...]:
    """Group the word rows of Tesseract TSV output into lines, measured against the page row."""
    page_w = page_h = 0
    words: dict[tuple[str, ...], list[tuple[str, int, int, int, int, float]]] = {}
    for row in tsv.splitlines()[1:]:
        parts = row.split("\t")
        if len(parts) < 12:
            continue
        # level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
        level, left, top, width, height = (int(parts[i]) for i in (0, 6, 7, 8, 9))
        if level == 1:
            page_w, page_h = width, height
        elif level == 5 and parts[11].strip():
            words.setdefault(tuple(parts[1:5]), []).append(
                (
                    parts[11].strip(),
                    left,
                    top,
                    left + width,
                    top + height,
                    float(parts[10]),
                )
            )
    if not page_w or not page_h:
        return ()
    lines: list[OcrLine] = []
    for group in words.values():
        left = min(word[1] for word in group)
        top = min(word[2] for word in group)
        right = max(word[3] for word in group)
        bottom = max(word[4] for word in group)
        lines.append(
            OcrLine(
                text=" ".join(word[0] for word in group),
                x=left / page_w,
                y=1 - bottom / page_h,
                w=(right - left) / page_w,
                h=(bottom - top) / page_h,
                confidence=sum(word[5] for word in group) / len(group) / 100,
            )
        )
    return tuple(lines)


class TesseractReader:
    def __init__(self, languages: Sequence[str]):
        self.languages = tesseract_languages(languages)

    @property
    def provenance(self) -> str:
        return f"tesseract:{self.languages}"

    def read(self, pages: Sequence[PageImage]) -> Iterator[LinePage]:
        prefix = [] if shutil.which("tesseract") else _NIX_SHELL
        for page in pages:
            # Run tesseract with TSV output for bounding boxes
            cmd = [
                *prefix,
                "tesseract",
                str(page.path),
                "stdout",
                "-l",
                self.languages,
                "tsv",
            ]
            done = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if done.returncode != 0:
                raise OCRBackendError(
                    f"tesseract failed on page {page.number}: {done.stderr.strip()[-500:]}"
                )
            yield LinePage(page.number, tsv_lines(done.stdout))
