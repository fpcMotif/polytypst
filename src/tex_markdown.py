"""TeX-compatible Markdown normalizer, figure grounder, and document stitcher."""

import re
from re import Pattern

from .vision.figure_extractor import ExtractedFigure

_OCR_NEQ_REGEX: Pattern[str] = re.compile(
    r"([a-zA-Z0-9\)])[ \t]+#[ \t]+([0-9Ooa-zA-Z])"
)
_HYPHENATION_REGEX: Pattern[str] = re.compile(r"([a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,})")
_BRACKET_RUNNING_HEADER_REGEX: Pattern[str] = re.compile(
    r"^(?:"
    r"\[?[IVXLCDM1K]+[\.,]\s*(?:§+\s*[0-9a-z:]*|Ex[a-z]*\.?)\]?(?:\s+[A-Z][A-Z\s\.,'\-]*\s*\d{0,4})?"
    r"|"
    r"(?:§?\d{1,4}\s+)?[A-Z][A-Z\s\.,'\-]{3,}\s+\[?[IVXLCDM1K]+[\.,]\s*(?:§+\s*[0-9a-z:]*|Ex[a-z]*\.?)\]?"
    r"|"
    r"[ivxlcdm]+\s+[A-Z][A-Z\s'\-]{3,}"
    r"|"
    r"[A-Z][A-Z\s'\-]{3,}\s+[ivxlcdm]+"
    r")$"
)


def _is_running_header_line(sline: str, running_headers: list[str]) -> bool:
    core = sline.strip().strip("*").strip()
    if core.startswith("#"):
        core_no_hash = core.lstrip("#").strip()
    else:
        core_no_hash = core
    if _BRACKET_RUNNING_HEADER_REGEX.match(core_no_hash):
        return True
    up = core_no_hash.upper()
    if not running_headers:
        return False
    if up in running_headers:
        return True
    stripped = re.sub(
        r"^(?:\[?[IVXLCDM1K]+[\.,]\s*(?:§+\s*[0-9a-z:]*|Ex[a-z]*\.?)\]?|\d{1,4})\s+|\s+(?:\[?[IVXLCDM1K]+[\.,]\s*(?:§+\s*[0-9a-z:]*|Ex[a-z]*\.?)\]?|\d{1,4})$",
        "",
        up,
        flags=re.IGNORECASE,
    ).strip()
    return bool(stripped and stripped in running_headers)


def _has_top_level_linebreak(s: str) -> bool:
    stripped_envs = re.sub(
        r"\\begin\{(?:array|cases|matrix|pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix)\}.*?\\end\{(?:array|cases|matrix|pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix)\}",
        "",
        s,
        flags=re.DOTALL,
    )
    if "\\\\" not in stripped_envs:
        return False
    return not bool(
        re.match(
            r"^\s*\\begin\{(?:aligned|align\*?|split|gather\*?|multline\*?)\}.*\\end\{(?:aligned|align\*?|split|gather\*?|multline\*?)\}\s*$",
            s,
            flags=re.DOTALL,
        )
    )


def _balance_braces_before_right(s: str) -> str:
    out: list[str] = []
    stack: list[int] = [0]
    i = 0
    n = len(s)
    while i < n:
        if s.startswith("\\left", i) and (i + 5 == n or not s[i + 5].isalpha()):
            stack.append(0)
            out.append("\\left")
            i += 5
            continue
        if s.startswith("\\right", i) and (i + 6 == n or not s[i + 6].isalpha()):
            inner = stack.pop() if len(stack) > 1 else 0
            if inner > 0:
                out.append("}" * inner)
            out.append("\\right")
            i += 6
            continue
        if s[i] == "\\" and i + 1 < n:
            out.append(s[i : i + 2])
            i += 2
            continue
        if s[i] == "{":
            stack[-1] += 1
            out.append("{")
        elif s[i] == "}":
            while len(stack) > 1 and stack[-1] == 0:
                _ = stack.pop()
            if stack[-1] > 0:
                stack[-1] -= 1
                out.append("}")
        else:
            out.append(s[i])
        i += 1
    rem = sum(stack)
    if rem > 0:
        joined = "".join(out)
        m_trail = re.search(r"([,\.;]+)\s*$", joined)
        if m_trail:
            return joined[: m_trail.start()] + ("}" * rem) + m_trail.group(1)
        return joined + ("}" * rem)
    return "".join(out)


def _normalize_differentials(s: str) -> str:
    protected: list[str] = []

    def _save(m: re.Match[str]) -> str:
        idx = len(protected)
        protected.append(m.group(0))
        return f"@@PROT_{idx}@@"

    s = re.sub(
        r"\\(?:text|operatorname|mathrm|mathbf|mathcal|mathit)\{[^}]*\}",
        _save,
        s,
    )
    s = re.sub(
        r"\\(d?frac)\{\s*d(\^(?:[0-9a-zA-Z]+|\{[^}]+\}))?\s*\}\{\s*d\s*",
        lambda m: f"\\{m.group(1)}{{\\mathrm{{d}}{m.group(2) or ''}}}{{\\mathrm{{d}} ",
        s,
    )
    s = re.sub(
        r"(?<![\\a-zA-Z\^_])d(\^(?:[0-9a-zA-Z]+|\{[^}]+\}))?\s*(?=\\left\s*[(\[]|[(\[](?![^()\[\]]*,))",
        lambda m: f"\\mathrm{{d}}{m.group(1) or ''}",
        s,
    )
    s = re.sub(
        r"(?<![\\a-zA-Z\^_])d(\^(?:[0-9a-zA-Z]+|\{[^}]+\}))?\s*(\\(?:alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|varsigma|tau|upsilon|phi|varphi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega)(?![a-zA-Z]))",
        lambda m: f"\\mathrm{{d}}{m.group(1) or ''} {m.group(2)}",
        s,
    )
    s = re.sub(
        r"(?<![\\a-zA-Z\^_])d(\^(?:[0-9a-zA-Z]+|\{[^}]+\}))\s*([a-zA-Z])(?![a-zA-Z])",
        r"\\mathrm{d}\1 \2",
        s,
    )
    s = re.sub(
        r"(?<![\\a-zA-Z\^_])d([xyztuvwsrabclpqXYZTUVWSRABCFPQTMI])(?![a-zA-Z])",
        r"\\mathrm{d} \1",
        s,
    )
    s = re.sub(
        r"(?<![\\a-zA-Z0-9_\^])d\s*([xyztuvwsr])(?![a-zA-Z0-9])",
        r"\\mathrm{d}\1",
        s,
    )
    s = re.sub(r"@@PROT_(\d+)@@", lambda m: protected[int(m.group(1))], s)
    return s


def normalize_html_tables(text: str) -> str:
    """Convert arbitrary HTML <table> markup into clean Markdown tables or lines."""

    def repl_table(m: re.Match[str]) -> str:
        table_html = m.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL)
        parsed_rows: list[list[str]] = []
        for r in rows:
            cells = [
                re.sub(r"<[^>]+>", "", c).strip()
                for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.DOTALL)
            ]
            cells = [c for c in cells if c]
            if cells:
                parsed_rows.append(cells)
        if not parsed_rows:
            return ""
        max_cols = max(len(r) for r in parsed_rows)
        if max_cols <= 3 and all(r[-1].isdigit() for r in parsed_rows if len(r) >= 2):
            return "\n\n" + "\n\n".join(" ".join(r) for r in parsed_rows) + "\n\n"
        header = parsed_rows[0]
        col_count = len(header)
        sep = ["---"] * col_count
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(sep) + " |",
        ]
        for row in parsed_rows[1:]:
            padded = row + [""] * (col_count - len(row))
            lines.append("| " + " | ".join(padded[:col_count]) + " |")
        return "\n\n" + "\n".join(lines) + "\n\n"

    return re.sub(r"<table>.*?</table>", repl_table, text, flags=re.DOTALL)


def repair_ocr_math(body: str, is_display: bool = False) -> str:
    s = body.strip()
    s = s.replace("\ufffd", "")
    s = s.replace("\\手", "\\pi")
    s = re.sub(r"A\s*\\S\s*D\s*B", "ACDB", s)
    s = (
        s.replace("\\ sin", "\\sin")
        .replace("\\ cos", "\\cos")
        .replace("\\ tan", "\\tan")
    )
    s = re.sub(
        r"\\\s+(partial|frac|int|sum|prod|lim|sqrt|infty|alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|lambda|mu|nu|xi|pi|rho|sigma|tau|phi|varphi|chi|psi|omega|Delta|Gamma|Lambda|Omega|Phi|Pi|Psi|Sigma|Theta)\b",
        r"\\\1",
        s,
    )
    s = re.sub(r"\\arc\s*\\(sin|cos|tan)", r"\\arc\1", s)
    s = re.sub(r"\\arc\s*\\cot\b", r"\\operatorname{arccot}", s)
    s = re.sub(r"\\arc\s+(sin|cos|tan)\b", r"\\arc\1", s)
    s = re.sub(r"\\arc\s+cot\b", r"\\operatorname{arccot}", s)
    s = re.sub(
        r"\\\\(?=(?:sqrt|frac|int|iint|iiint|oint|sum|prod|lim|log|ln|sin|cos|tan|cot|sec|csc|arcsin|arccos|arctan|sinh|cosh|tanh|partial|nabla|infty|alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|varphi|chi|psi|omega|Delta|Gamma|Lambda|Omega|Phi|Pi|Psi|Sigma|Theta|Upsilon|Xi|cdot|cdots|ldots|dots|quad|qquad|left|right|big|Big|bigg|Bigg|operatorname|mathrm|mathbf|mathcal|mathbb|text)\b)",
        r"\\",
        s,
    )
    s = re.sub(r'([A-Za-z0-9\)\}])"', r"\1''", s)
    s = re.sub(r"(?<!\\)\$", "", s)
    s = re.sub(
        r"(\\end\{array\}\s*\\right[\]\}\.\|],?\s*)\\end\{array\}\s*\\right[\]\}\.\|]",
        r"\1",
        s,
    )
    s = re.sub(
        r"\\left\s*\\\{\s*\\begin\{(?:array\}\{[lcr]+\}|aligned\})\s*(.*?)\s*\\end\{(?:array|aligned)\}\s*\\right\s*\.",
        r"\\begin{cases}\n\1\n\\end{cases}",
        s,
        flags=re.DOTALL,
    )
    s = re.sub(r"\\frac\{([^{}]+)\}\{\+([^{}]+)\}", r"(\1 + \2)", s)
    s = _normalize_differentials(s)
    s = re.sub(
        r"([_~^])(\\(?:mathbb|mathfrak|mathcal|mathscr|mathbf|mathsf|mathit|mathrm|boldsymbol|text|operatorname)\{[^}]+\})",
        r"\1{\2}",
        s,
    )
    s = re.sub(
        r"(\\(?:sum|prod|coprod|bigcup|bigcap|bigoplus|bigotimes)"
        r"(?:\s*[_^](?:\{(?:[^{}]|\{[^{}]*\})*\}|\\[a-zA-Z]+|\w))+)'",
        r"{\1}'",
        s,
    )
    s = s.replace("□", r"\square")
    s = s.replace("⧵", r"\setminus")
    s = s.replace("⫋", r"\subsetneq")

    if is_display:
        tag_str = ""
        m_tag = re.search(r"\\tag\{([^}]*)\}\s*$", s)
        if m_tag:
            tag_str = f" \\tag{{{m_tag.group(1)}}}"
            s = s[: m_tag.start()].strip()

        m_lead_tag = re.match(
            r"^\(([0-9]+[a-zA-Z']*)\)\s*(?:\\q?quad\s*)?(.+)$", s, flags=re.DOTALL
        )
        if m_lead_tag and not tag_str:
            tag_str = f" \\tag{{{m_lead_tag.group(1)}}}"
            s = m_lead_tag.group(2).strip()

        m_row_tag = re.search(r"\\\\\s*\(([0-9]+[a-zA-Z']*)\)\s*(?:\\q?quad\s*)?", s)
        if m_row_tag:
            if not tag_str:
                tag_str = f" \\tag{{{m_row_tag.group(1)}}}"
            s = s[: m_row_tag.start()] + "\\\\\n" + s[m_row_tag.end() :]

        if _has_top_level_linebreak(s):
            s = f"\\begin{{aligned}}\n{s}\n\\end{{aligned}}"

        if ("\\\\" in s or "\\begin{aligned}" in s or "\\begin{array}" in s) and (
            "\\left." in s or "\\right." in s
        ):
            s = re.sub(r"\\left\s*\.", "", s)
            s = re.sub(r"\\right\s*\.", "", s)
            s = re.sub(r"\\left\s*([\[\(\|])", r"\\Big\1", s)
            s = re.sub(r"\\right\s*([\]\)\|])", r"\\Big\1", s)
            s = re.sub(r"\\left\s*\\\{", r"\\Big\\{", s)
            s = re.sub(r"\\right\s*\\\}", r"\\Big\\}", s)

        n_left = len(re.findall(r"\\left(?![a-zA-Z])", s))
        n_right = len(re.findall(r"\\right(?![a-zA-Z])", s))
        if n_left != n_right:
            s = re.sub(r"\\left\s*([\[\(\|])", r"\\Big\1", s)
            s = re.sub(r"\\right\s*([\]\)\|])", r"\\Big\1", s)
            s = re.sub(r"\\left\s*\\\{", r"\\Big\\{", s)
            s = re.sub(r"\\right\s*\\\}", r"\\Big\\}", s)
            s = re.sub(r"\\left\s*\.", "", s)
            s = re.sub(r"\\right\s*\.", "", s)

        s = _balance_braces_before_right(s)
        s = re.sub(r"\n[ \t]*\n+", "\n", s.strip())
        s = s + tag_str
    else:
        n_left = len(re.findall(r"\\left(?![a-zA-Z])", s))
        n_right = len(re.findall(r"\\right(?![a-zA-Z])", s))
        if n_left != n_right:
            s = re.sub(r"\\left\s*([\[\(\|])", r"\1", s)
            s = re.sub(r"\\right\s*([\]\)\|])", r"\1", s)
            s = re.sub(r"\\left\s*\\\{", r"\\{", s)
            s = re.sub(r"\\right\s*\\\}", r"\\}", s)
            s = re.sub(r"\\left\s*\.", "", s)
            s = re.sub(r"\\right\s*\.", "", s)

        s = _balance_braces_before_right(s)
        s = re.sub(r"\s*\n\s*", " ", s.strip())

    return s


def _normalize_math_delimiters(text: str) -> str:
    text = re.sub(r"<td>([^<\n]*?)</th>", r"<td>\1</td>", text)
    text = re.sub(r"<th>([^<\n]*?)</td>", r"<th>\1</th>", text)
    text = re.sub(r"</tr>\s*</tr>", "</tr>", text)
    text = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"\n\n$$\n\1\n$$\n\n", text, flags=re.DOTALL)
    text = re.sub(r"\\\(\s*(.*?)\s*\\\)", lambda m: f"${m.group(1).strip()}$", text)

    text = re.sub(
        r"\$\$\s*\(([0-9]+[a-zA-Z']*)\)\s*\$\$\s*\$\$\s*((?:(?!\$\$).)+?)\s*\$\$",
        lambda m: f"\n\n$$\n{m.group(2).strip()} \\tag{{{m.group(1)}}}\n$$\n\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"^[ \t]*\(([0-9]+[a-zA-Z']*)\)\s*\$\$\s*((?:(?!\$\$).)+?)\s*\$\$",
        lambda m: f"\n\n$$\n{m.group(2).strip()} \\tag{{{m.group(1)}}}\n$$\n\n",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    text = re.sub(
        r"\$\$\s*((?:(?!\$\$).)+?)\s*\$\$(?:[ \t]*\n)*[ \t]*\(([0-9]+[a-zA-Z']*)\)[ \t]*$",
        lambda m: f"\n\n$$\n{m.group(1).strip()} \\tag{{{m.group(2)}}}\n$$\n\n",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    text = re.sub(
        r"\$\$\s*\(([0-9]+[a-zA-Z']*)\)\s*(?:\\q?quad\s*)+((?:(?!\$\$).)+?)\s*\$\$",
        lambda m: f"\n\n$$\n{m.group(2).strip()} \\tag{{{m.group(1)}}}\n$$\n\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"^[ \t]*\(([0-9]+[a-zA-Z']*)\)[ \t]*\${1,2}\s*(\\left\s*\\\{\s*\\begin\{array\}.*?\\end\{array\}\s*\\right\s*\.)\s*\${1,2}([,\.;]?)[ \t]*$",
        lambda m: (
            f"\n\n$$\n{m.group(2).strip()}{m.group(3)} \\tag{{{m.group(1)}}}\n$$\n\n"
        ),
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    text = re.sub(
        r"^[ \t]*\(([0-9]+[a-zA-Z']*)\)[ \t]*\${1,2}([^$\n]+?)\${1,2}([,\.;]?)[ \t]*$",
        lambda m: (
            f"\n\n$$\n{m.group(2).strip()}{m.group(3)} \\tag{{{m.group(1)}}}\n$$\n\n"
        ),
        text,
        flags=re.MULTILINE,
    )

    display_blocks: list[str] = []

    def _save_display(m: re.Match[str]) -> str:
        raw_inner = m.group(1).strip()
        if raw_inner.lower().startswith("where $") and "\\" not in raw_inner:
            return f"\n\n{raw_inner}\n\n"
        idx = len(display_blocks)
        body = repair_ocr_math(raw_inner, is_display=True)
        display_blocks.append(f"$$\n{body}\n$$")
        return f"\n\n@@DISPLAY_MATH_{idx}@@\n\n"

    text = re.sub(r"\$\$\s*(.*?)\s*\$\$", _save_display, text, flags=re.DOTALL)

    inline_blocks: list[str] = []

    def _save_inline(m: re.Match[str]) -> str:
        inner = repair_ocr_math(m.group(1), is_display=False)
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


def _clean_page(
    raw_md: str,
    running_headers: list[str],
    page_figures: list[ExtractedFigure],
) -> str:
    """Sanitize a single OCR transcribed page and ground its figures."""
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
        if _is_running_header_line(sline, running_headers):
            continue

        lines.append(line)

    text = "\n".join(lines).strip()

    # 1. Standardize LaTeX delimiters: \[ \] -> $$ $$, \( \) -> $ $
    # 2. Fix OCR artifacts: # 0 -> \neq 0
    text = _OCR_NEQ_REGEX.sub(r"\1 \\neq \2", text)

    # 3. De-hyphenate broken words across linebreaks
    text = _HYPHENATION_REGEX.sub(r"\1\2", text)

    # 4. Normalize inline math spacing
    # Ensure space before $ if preceded by letter/number/punctuation
    # Ensure space after $ if followed by letter
    text = _normalize_math_delimiters(text)

    # 5. Ground and inject figures for this page
    if page_figures:
        text = _inject_figures(text, page_figures)

    return text.strip()


def _inject_figures(
    page_text: str,
    figures: list[ExtractedFigure],
) -> str:
    """Inject figure markdown images into the text near their captions."""
    modified_text = page_text
    placed: set[str] = set()

    for fig in figures:
        fig_tag = (
            f"\n\n![{fig.caption}]({fig.image_rel_path}){{#fig:{fig.figure_id}}}\n\n"
        )
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
    pages_md: list[tuple[int, str]],
    figures: list[ExtractedFigure] | None = None,
    running_headers: list[str] | None = None,
) -> str:
    """Assemble all cleaned pages into a unified, continuous document."""
    header_keys = [h.strip().upper() for h in (running_headers or []) if h.strip()]
    fig_by_page: dict[int, list[ExtractedFigure]] = {}
    if figures:
        for f in figures:
            fig_by_page.setdefault(f.source_page, []).append(f)

    cleaned_pages: list[str] = []
    for pno, raw_text in pages_md:
        p_figs = fig_by_page.get(pno, [])
        clean_p = _clean_page(raw_text, header_keys, p_figs)
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
        starts_new = first_line.startswith(
            ("#", "**", "$$", "![", "* ", "- ", "†", "*")
        ) or bool(re.match(r"^(?:\d+\.|\([0-9a-zA-Z']+\)|[IVXLCDM]+\.)\s", first_line))
        if not ends_complete and not starts_new:
            acc = acc_r + " " + cur_l
        else:
            acc = acc_r + "\n\n" + cur_l

    full_doc = _HYPHENATION_REGEX.sub(r"\1\2", acc)

    return full_doc
