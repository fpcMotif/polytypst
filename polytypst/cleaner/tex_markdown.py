"""TeX-compatible Markdown normalizer, figure grounder, and document stitcher."""

import re
from re import Pattern

from ..vision.figure_extractor import ExtractedFigure


class TeXMarkdownCleaner:
    """Universal normalizer producing pristine TeX/Typst-compatible Markdown from OCR output."""

    OCR_NEQ_REGEX: Pattern[str] = re.compile(r"([a-zA-Z0-9\)])\s*[#\*]\s*([0-9Ooa-zA-Z])")
    HYPHENATION_REGEX: Pattern[str] = re.compile(r"([a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,})")
    RUNNING_NUM_REGEX: Pattern[str] = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)

    def __init__(self, running_headers: list[str] | None = None):
        self.running_headers: list[str] = [h.strip().upper() for h in (running_headers or []) if h.strip()]

    def clean_page(
        self,
        raw_md: str,
        page_num: int = 1,
        page_figures: list[ExtractedFigure] | None = None,
    ) -> str:
        """Sanitize a single OCR transcribed page and ground its figures."""
        _ = page_num
        lines: list[str] = []
        for line in raw_md.splitlines():
            sline = line.strip()
            if not sline:
                lines.append("")
                continue

            # Strip standalone page number lines
            if re.match(r"^\d{1,4}$", sline):
                continue

            # Strip running book/chapter headers
            if self.running_headers and sline.upper() in self.running_headers:
                continue

            lines.append(line)

        text = "\n".join(lines).strip()

        # 1. Standardize LaTeX delimiters: \[ \] -> $$ $$, \( \) -> $ $
        text = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"\n\n$$ \1 $$\n\n", text, flags=re.DOTALL)
        text = re.sub(r"\\\(\s*(.*?)\s*\\\)", r"$ \1 $", text)

        # 2. Fix OCR artifacts: # 0 -> \neq 0
        text = self.OCR_NEQ_REGEX.sub(r"\1 \\neq \2", text)

        # 3. De-hyphenate broken words across linebreaks
        text = self.HYPHENATION_REGEX.sub(r"\1\2", text)

        # 4. Normalize inline math spacing
        # Ensure space before $ if preceded by letter/number/punctuation
        text = re.sub(r"([a-zA-Z0-9,\.\:\;])(?<!\$)\$(?!\$)", r"\1 $", text)
        # Ensure space after $ if followed by letter
        text = re.sub(r"(?<!\$)\$(?!\$)([a-zA-Z0-9])", r"$ \1", text)

        # 5. Ground and inject figures for this page
        if page_figures:
            text = self.inject_figures(text, page_figures)

        return text.strip()

    @staticmethod
    def inject_figures(
        page_text: str,
        figures: list[ExtractedFigure],
    ) -> str:
        """Inject figure markdown images into the text near their captions."""
        modified_text = page_text
        placed: set[str] = set()

        for fig in figures:
            fig_tag = f"\n\n![{fig.caption}]({fig.image_rel_path})\n\n"

            # Search for exact or loose caption mention (e.g. "FIG. 1", "Figure 1", "Fig. 1-1")
            pattern = re.compile(
                rf"(\b(fig|figure|abbildung|图)\.?\s*{re.escape(fig.figure_id)}\b)",
                re.IGNORECASE,
            )
            match = pattern.search(modified_text)
            if match:
                # Place immediately after the line containing the caption
                line_end = modified_text.find("\n", match.end())
                idx = line_end if line_end != -1 else len(modified_text)
                modified_text = modified_text[:idx] + fig_tag + modified_text[idx:]
                placed.add(fig.figure_id)

        # If any figures for this page were not matched in text, append them at the end of the page
        for fig in figures:
            if fig.figure_id not in placed:
                fig_tag = f"\n\n![{fig.caption}]({fig.image_rel_path})\n\n"
                modified_text = modified_text + fig_tag

        return modified_text

    def stitch_document(
        self,
        pages_md: list[tuple[int, str]],
        figures: list[ExtractedFigure] | None = None,
    ) -> str:
        """Assemble all cleaned pages into a unified, continuous document."""
        fig_by_page: dict[int, list[ExtractedFigure]] = {}
        if figures:
            for f in figures:
                fig_by_page.setdefault(f.source_page, []).append(f)

        cleaned_pages: list[str] = []
        for pno, raw_text in pages_md:
            p_figs = fig_by_page.get(pno, [])
            clean_p = self.clean_page(raw_text, pno, p_figs)
            cleaned_pages.append(clean_p)

        full_doc = "\n\n".join(cleaned_pages)
        full_doc = self.HYPHENATION_REGEX.sub(r"\1\2", full_doc)

        return full_doc
