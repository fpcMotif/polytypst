"""TeX-compatible Markdown normalizer, figure grounder, and document stitcher."""

import re
from re import Pattern

from ..vision.figure_extractor import ExtractedFigure


class TeXMarkdownCleaner:
    """Universal normalizer producing pristine TeX/Typst-compatible Markdown from OCR output."""

    OCR_NEQ_REGEX: Pattern[str] = re.compile(r"([a-zA-Z0-9\)])[ \t]+#[ \t]+([0-9Ooa-zA-Z])")
    HYPHENATION_REGEX: Pattern[str] = re.compile(r"([a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,})")
    RUNNING_NUM_REGEX: Pattern[str] = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)
    BRACKET_RUNNING_HEADER_REGEX: Pattern[str] = re.compile(
        r"^(?:"
        r"\[?[IVXLCDM]+,\s*§\s*\d+[a-z]?\]?\s+[A-Z][A-Z\s\.,'\-]+\s+\d{1,4}"
        r"|"
        r"\d{1,4}\s+[A-Z][A-Z\s\.,'\-]+\s+\[?[IVXLCDM]+,\s*§\s*\d+[a-z]?\]?"
        r"|"
        r"[ivxlcdm]+\s+[A-Z][A-Z\s'\-]{3,}"
        r"|"
        r"[A-Z][A-Z\s'\-]{3,}\s+[ivxlcdm]+"
        r")$"
    )

    def __init__(self, running_headers: list[str] | None = None):
        self.running_headers: list[str] = [h.strip().upper() for h in (running_headers or []) if h.strip()]

    def _is_running_header_line(self, sline: str) -> bool:
        if self.BRACKET_RUNNING_HEADER_REGEX.match(sline):
            return True
        up = sline.upper()
        if not self.running_headers:
            return False
        if up in self.running_headers:
            return True
        stripped = re.sub(
            r"^[\d\s\[\]\(\)§\.,\-IVXLCDM]+|[\d\s\[\]\(\)§\.,\-IVXLCDM]+$",
            "",
            up,
        ).strip()
        if stripped and stripped in self.running_headers and not sline.startswith("#"):
            return True
        return False

    @staticmethod
    def _normalize_math_delimiters(text: str) -> str:
        text = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"\n\n$$\n\1\n$$\n\n", text, flags=re.DOTALL)
        text = re.sub(r"\\\(\s*(.*?)\s*\\\)", lambda m: f"${m.group(1).strip()}$", text)

        text = re.sub(
            r"^[ \t]*\(([0-9]+[a-zA-Z']*)\)[ \t]*\$\$\s*(.*?)\s*\$\$",
            lambda m: f"\n\n$$\n{m.group(2).strip()} \\tag{{{m.group(1)}}}\n$$\n\n",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        text = re.sub(
            r"\$\$\s*(.*?)\s*\$\$[ \t]*\(([0-9]+[a-zA-Z']*)\)[ \t]*$",
            lambda m: f"\n\n$$\n{m.group(1).strip()} \\tag{{{m.group(2)}}}\n$$\n\n",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )

        display_blocks: list[str] = []

        def _save_display(m: re.Match[str]) -> str:
            idx = len(display_blocks)
            body = m.group(1).strip()
            display_blocks.append(f"$$\n{body}\n$$")
            return f"\n\n@@DISPLAY_MATH_{idx}@@\n\n"

        text = re.sub(r"\$\$\s*(.*?)\s*\$\$", _save_display, text, flags=re.DOTALL)

        inline_blocks: list[str] = []

        def _save_inline(m: re.Match[str]) -> str:
            inner = m.group(1).strip()
            if not inner:
                return ""
            idx = len(inline_blocks)
            inline_blocks.append(f"${inner}$")
            return f"@@INLINE_MATH_{idx}@@"

        text = re.sub(r"(?<!\\)\$([^$\n]+?)\$", _save_inline, text)

        text = re.sub(r"([a-zA-Z0-9])(@@INLINE_MATH_\d+@@)", r"\1 \2", text)
        text = re.sub(r"(@@INLINE_MATH_\d+@@)([a-zA-Z0-9])", r"\1 \2", text)

        text = re.sub(
            r"@@INLINE_MATH_(\d+)@@",
            lambda m: inline_blocks[int(m.group(1))],
            text,
        )
        text = re.sub(
            r"@@DISPLAY_MATH_(\d+)@@",
            lambda m: display_blocks[int(m.group(1))],
            text,
        )
        return text

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
            if self._is_running_header_line(sline):
                continue

            lines.append(line)

        text = "\n".join(lines).strip()

        # 1. Standardize LaTeX delimiters: \[ \] -> $$ $$, \( \) -> $ $
        # 2. Fix OCR artifacts: # 0 -> \neq 0
        text = self.OCR_NEQ_REGEX.sub(r"\1 \\neq \2", text)

        # 3. De-hyphenate broken words across linebreaks
        text = self.HYPHENATION_REGEX.sub(r"\1\2", text)

        # 4. Normalize inline math spacing
        # Ensure space before $ if preceded by letter/number/punctuation
        # Ensure space after $ if followed by letter
        text = self._normalize_math_delimiters(text)

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
            fig_tag = f"\n\n![{fig.caption}]({fig.image_rel_path}){{#fig:{fig.figure_id}}}\n\n"
            alt_id = fig.figure_id.replace("_", ", ")

            standalone_pat = re.compile(
                rf"^[ \t\*]*(?:fig|figure|abbildung|图)\.?\s*(?:{re.escape(fig.figure_id)}|{re.escape(alt_id)})\b[^\n]*$",
                re.IGNORECASE | re.MULTILINE,
            )
            m_standalone = standalone_pat.search(modified_text)
            if m_standalone:
                line_text = m_standalone.group(0).strip().strip("*").strip()
                if len(line_text) <= 24:
                    modified_text = (
                        modified_text[: m_standalone.start()]
                        + fig_tag
                        + modified_text[m_standalone.end() :]
                    )
                else:
                    line_end = modified_text.find("\n", m_standalone.end())
                    idx = line_end if line_end != -1 else len(modified_text)
                    modified_text = modified_text[:idx] + fig_tag + modified_text[idx:]
                placed.add(fig.figure_id)
                continue

            # Search for exact or loose caption mention (e.g. "FIG. 1", "Figure 1", "Fig. 1-1")
            pattern = re.compile(
                rf"(\b(fig|figure|abbildung|图)\.?\s*(?:{re.escape(fig.figure_id)}|{re.escape(alt_id)})\b)",
                re.IGNORECASE,
            )
            match = pattern.search(modified_text)
            if match:
                # Place immediately after the line containing the caption
                para_end = modified_text.find("\n\n", match.end())
                idx = para_end if para_end != -1 else len(modified_text)
                modified_text = modified_text[:idx] + fig_tag + modified_text[idx:]
                placed.add(fig.figure_id)

        # If any figures for this page were not matched in text, append them at the end of the page
        for fig in figures:
            if fig.figure_id not in placed:
                fig_tag = f"\n\n![{fig.caption}]({fig.image_rel_path}){{#fig:{fig.figure_id}}}\n\n"
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
            if clean_p:
                cleaned_pages.append(clean_p)

        if not cleaned_pages:
            return ""

        acc = cleaned_pages[0]
        for cur in cleaned_pages[1:]:
            acc_r = acc.rstrip()
            cur_l = cur.lstrip()
            if not cur_l:
                continue
            if re.search(r"[a-zA-Z]{2,}-$", acc_r) and re.match(r"^[a-z]{2,}", cur_l):
                acc = acc_r[:-1] + cur_l
                continue
            last_line = acc_r.splitlines()[-1].strip() if acc_r else ""
            first_line = cur_l.splitlines()[0].strip()
            ends_complete = (
                last_line.endswith((".", "!", "?", ":", ";", "$$", "*", ")", "]"))
                or last_line.startswith(("#", "!["))
                or bool(re.search(r"\{#fig:[^}]+\}$", last_line))
            )
            starts_new = (
                first_line.startswith(("#", "**", "$$", "![", "* ", "- ", "†", "*"))
                or bool(re.match(r"^(?:\d+\.|\([0-9a-zA-Z']+\)|[IVXLCDM]+\.)\s", first_line))
            )
            if not ends_complete and not starts_new:
                acc = acc_r + " " + cur_l
            else:
                acc = acc_r + "\n\n" + cur_l

        full_doc = self.HYPHENATION_REGEX.sub(r"\1\2", acc)

        return full_doc
