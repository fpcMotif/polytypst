"""
Assembles the complete 8-chapter Lars Ahlfors Complex Analysis monograph (1979 McGraw-Hill style).
Two-Phase AST-compliant Typography Pipeline:
1. Strict separation of Display Equations ($$ ... $$) and Inline Math ($ ... $).
2. Automated label-gated equation numbering (Equation numbers right-aligned on display math baseline).
3. Universal LaTeX fraction, partial derivative, matrix, and Greek letter normalization.
4. Cross-page de-hyphenation.
"""

import functools
import re
import shutil
from pathlib import Path
from re import Pattern

from PIL import Image

KNOWN_MATH_WORDS = {
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "sinh",
    "cosh",
    "tanh",
    "coth",
    "arcsin",
    "arccos",
    "arctan",
    "arsinh",
    "arcosh",
    "artanh",
    "log",
    "ln",
    "lg",
    "exp",
    "det",
    "dim",
    "ker",
    "im",
    "hom",
    "Hom",
    "Set",
    "Top",
    "Cat",
    "Fun",
    "Re",
    "Im",
    "arg",
    "deg",
    "sgn",
    "mod",
    "pr",
    "gcd",
    "lcm",
    "min",
    "max",
    "sup",
    "inf",
    "lim",
    "colim",
    "plus",
    "minus",
    "times",
    "div",
    "quad",
    "wide",
    "thin",
    "med",
    "thick",
    "dots",
    "sqrt",
    "root",
    "binom",
    "sum",
    "prod",
    "product",
    "integral",
    "in",
    "notin",
    "subset",
    "supset",
    "union",
    "inter",
    "emptyset",
    "arrow",
    "bold",
    "upright",
    "italic",
    "cal",
    "frak",
    "bb",
    "mat",
    "delim",
    "cases",
    "overline",
    "underline",
    "macron",
    "hat",
    "tilde",
    "caron",
    "breve",
    "acute",
    "grave",
    "dot",
    "double",
    "circle",
    "chevron",
    "abs",
    "norm",
    "floor",
    "ceil",
    "round",
    "mid",
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "zeta",
    "eta",
    "theta",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "xi",
    "pi",
    "rho",
    "sigma",
    "tau",
    "upsilon",
    "phi",
    "chi",
    "psi",
    "omega",
    "Omega",
    "Gamma",
    "Delta",
    "Theta",
    "Lambda",
    "Xi",
    "Pi",
    "Sigma",
    "Phi",
    "Psi",
    "Upsilon",
    "RR",
    "CC",
    "ZZ",
    "NN",
    "QQ",
    "infinity",
    "partial",
    "nabla",
    "degree",
    "circ",
    "dagger",
    "ell",
    "wp",
    "dif",
    "frac",
    "op",
    "limits",
    "scripts",
    "big",
    "h",
    "c",
    "v",
    "l",
    "r",
    "approx",
    "equiv",
    "sim",
    "cong",
    "propto",
    "perp",
    "parallel",
    "slash",
}

ENGLISH_WORDS = {
    "on",
    "where",
    "with",
    "and",
    "or",
    "for",
    "as",
    "then",
    "from",
    "to",
    "is",
    "are",
    "all",
    "constant",
    "const",
    "poles",
    "even",
    "odd",
    "otherwise",
    "else",
    "some",
    "any",
    "such",
    "that",
}

MATH_OPERATOR_WORDS = {
    "Res",
    "Int",
    "Cl",
    "Bd",
    "SL",
    "GL",
    "PSL",
    "Aut",
    "End",
    "arc",
}

GREEK_WORDS = (
    "alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|"
    "pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|Omega|Gamma|Delta|Theta|Lambda|"
    "Xi|Pi|Sigma|Phi|Psi"
)
GREEK_PATTERN = (
    r"\\(alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|"
    r"xi|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|Omega|Gamma|Delta|Theta|"
    r"Lambda|Xi|Pi|Sigma|Phi|Psi)(?![a-zA-Z])"
)

UNICODE_GREEK = {
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "ζ": "zeta",
    "η": "eta",
    "θ": "theta",
    "ι": "iota",
    "κ": "kappa",
    "λ": "lambda",
    "μ": "mu",
    "ν": "nu",
    "ξ": "xi",
    "π": "pi",
    "ρ": "rho",
    "σ": "sigma",
    "τ": "tau",
    "υ": "upsilon",
    "φ": "phi",
    "χ": "chi",
    "ψ": "psi",
    "ω": "omega",
    "Γ": "Gamma",
    "Δ": "Delta",
    "Θ": "Theta",
    "Λ": "Lambda",
    "Ξ": "Xi",
    "Π": "Pi",
    "Σ": "Sigma",
    "Φ": "Phi",
    "Ψ": "Psi",
    "Ω": "Omega",
}

RUNNING_HEADER_WORDS = (
    "COMPLEX ANALYSIS|COMPLEX NUMBERS|COMPLEX FUNCTIONS|"
    "ANALYTIC FUNCTIONS AS MAPPINGS|COMPLEX INTEGRATION|"
    "SERIES AND PRODUCT DEVELOPMENTS|CONFORMAL MAPPING|"
    "ELLIPTIC FUNCTIONS|GLOBAL ANALYTIC FUNCTIONS|"
    "DIRICHLET'S PROBLEM|CONFORMAL MAPPING\\. DIRICHLET'S PROBLEM|INDEX"
)


def parse_braced(s: str, pos: int) -> tuple[str, int]:
    while pos < len(s) and s[pos].isspace():
        pos += 1
    if pos >= len(s) or s[pos] != "{":
        return "", pos
    depth = 1
    i = pos + 1
    while i < len(s) and depth > 0:
        if s[i] == "{" and (i == 0 or s[i - 1] != "\\"):
            depth += 1
        elif s[i] == "}" and (i == 0 or s[i - 1] != "\\"):
            depth -= 1
        i += 1
    return s[pos + 1 : i - 1], i


def parse_bracketed(s: str, pos: int) -> tuple[str, int]:
    while pos < len(s) and s[pos].isspace():
        pos += 1
    if pos >= len(s) or s[pos] != "[":
        return "", pos
    depth = 1
    i = pos + 1
    while i < len(s) and depth > 0:
        if s[i] == "[":
            depth += 1
        elif s[i] == "]":
            depth -= 1
        i += 1
    return s[pos + 1 : i - 1], i


UNICODE_GREEK_TABLE = str.maketrans({k: f" {v} " for k, v in UNICODE_GREEK.items()})
FRAC_MACRO_RE: Pattern[str] = re.compile(r"\\(?:d|t)?frac(?=\s*\{)")
BINOM_MACRO_RE: Pattern[str] = re.compile(r"\\binom(?=\s*\{)")
THEFRAC_RE: Pattern[str] = re.compile(r"\bthefrac(?=\{)")
BARE_FRAC_ONE_RE: Pattern[str] = re.compile(r"\\(?:d|t)?frac\s*([0-9a-zA-Z])\s*\{")
BARE_FRAC_TWO_RE: Pattern[str] = re.compile(
    r"\\(?:d|t)?frac\s*([0-9a-zA-Z])\s+([0-9a-zA-Z])"
)
SQRT_MACRO_RE: Pattern[str] = re.compile(r"\\sqrt(?=\s*[\[\{])")
SCRIPT_BRACE_RE: Pattern[str] = re.compile(r"([\^_])(?=\s*\{)")


def convert_binary_macro(s: str, pattern: Pattern[str], fmt: str) -> str:
    pos = 0
    res: list[str] = []
    while True:
        m = pattern.search(s, pos)
        if not m:
            res.append(s[pos:])
            break
        res.append(s[pos : m.start()])
        arg1, next_pos = parse_braced(s, m.end())
        arg2, end_pos = parse_braced(s, next_pos)
        c1 = convert_binary_macro(arg1, pattern, fmt)
        c2 = convert_binary_macro(arg2, pattern, fmt)
        res.append(fmt.format(c1, c2))
        pos = end_pos
    return "".join(res)


def convert_latex_fracs(s: str) -> str:
    if "frac" not in s and "binom" not in s:
        return s
    s = THEFRAC_RE.sub(r"\\frac", s)
    s = BARE_FRAC_ONE_RE.sub(r"\\frac{\1}{", s)
    s = BARE_FRAC_TWO_RE.sub(r"\\frac{\1}{\2}", s)
    s = convert_binary_macro(s, FRAC_MACRO_RE, "({0})/({1})")
    if "binom" in s:
        s = convert_binary_macro(s, BINOM_MACRO_RE, "binom({0}, {1})")
    return s


def convert_latex_sqrt(s: str) -> str:
    if "\\sqrt" not in s:
        return s
    pos = 0
    res: list[str] = []
    while True:
        m = SQRT_MACRO_RE.search(s, pos)
        if not m:
            res.append(s[pos:])
            break
        res.append(s[pos : m.start()])
        cur = m.end()
        while cur < len(s) and s[cur].isspace():
            cur += 1
        if cur < len(s) and s[cur] == "[":
            deg, cur = parse_bracketed(s, cur)
            rad, end_pos = parse_braced(s, cur)
            res.append(f" root({convert_latex_sqrt(deg)}, {convert_latex_sqrt(rad)}) ")
            pos = end_pos
        elif cur < len(s) and s[cur] == "{":
            rad, end_pos = parse_braced(s, cur)
            res.append(f" sqrt({convert_latex_sqrt(rad)}) ")
            pos = end_pos
        else:
            res.append(m.group(0))
            pos = cur
    return "".join(res)


UNARY_MACROS: list[tuple[Pattern[str], str]] = [
    (re.compile(r"\\(?:overline|bar)(?=\s*\{)"), " overline({0}) "),
    (re.compile(r"\\underline(?=\s*\{)"), " underline({0}) "),
    (re.compile(r"\\(?:widetilde|tilde)(?=\s*\{)"), " tilde({0}) "),
    (re.compile(r"\\(?:widehat|hat)(?=\s*\{)"), " hat({0}) "),
    (re.compile(r"\\check(?=\s*\{)"), " caron({0}) "),
    (re.compile(r"\\vec(?=\s*\{)"), " arrow({0}) "),
    (re.compile(r"\\ddot(?=\s*\{)"), " dot.double({0}) "),
    (re.compile(r"\\dot(?=\s*\{)"), " dot({0}) "),
    (re.compile(r"\\(?:mathbf|boldsymbol|bm)(?=\s*\{)"), " bold({0}) "),
    (re.compile(r"\\mathcal(?=\s*\{)"), " cal({0}) "),
    (re.compile(r"\\mathfrak(?=\s*\{)"), " frak({0}) "),
    (re.compile(r"\\mathbb(?=\s*\{)"), " bb({0}) "),
    (re.compile(r"\\pmod(?=\s*\{)"), " (mod {0}) "),
]

TEXT_MACROS = re.compile(
    r"\\(?:operatorname|mathrm|textrm|textbf|textit|text|mbox)(?=\s*\{)"
)


def convert_unary_macros(s: str) -> str:
    if "\\" not in s:
        return s
    s = s.replace(r"\mathrm{d}", " dif ")
    for pattern, fmt in UNARY_MACROS:
        while True:
            m = pattern.search(s)
            if not m:
                break
            inner, end_pos = parse_braced(s, m.end())
            inner_conv = convert_unary_macros(inner)
            if "," in inner_conv and not fmt.startswith(" (mod"):
                inner_conv = f"({inner_conv})"
            s = s[: m.start()] + fmt.format(inner_conv) + s[end_pos:]

    while True:
        m = TEXT_MACROS.search(s)
        if not m:
            break
        inner, end_pos = parse_braced(s, m.end())
        clean_inner = inner.replace('"', "''").strip()
        s = s[: m.start()] + f' "{clean_inner}" ' + s[end_pos:]
    return s


def convert_script_braces(s: str) -> str:
    if "{" not in s:
        return s
    pos = 0
    res: list[str] = []
    while True:
        m = SCRIPT_BRACE_RE.search(s, pos)
        if not m:
            res.append(s[pos:])
            break
        res.append(s[pos : m.start()])
        op = m.group(1)
        inner, end_pos = parse_braced(s, m.end())
        inner_conv = convert_script_braces(inner)
        res.append(f"{op}({inner_conv})")
        pos = end_pos
    return "".join(res)


ENV_VMATRIX_ARRAY_RE = re.compile(
    r"\\left\|\s*\\begin\{array\}\{[^{}]*\}(.*?)\\end\{array\}\s*\\right\|",
    re.DOTALL,
)
ENV_MATRIX_RE = re.compile(
    r"\\begin\{((?:p|b|v|V)?matrix)\}(.*?)\\end\{\1\}", re.DOTALL
)
ENV_CASES_RE = re.compile(r"\\begin\{cases\}(.*?)\\end\{cases\}", re.DOTALL)
ENV_ARRAY_RE = re.compile(r"\\begin\{array\}\{[^{}]*\}(.*?)\\end\{array\}", re.DOTALL)
ENV_ALIGNED_RE = re.compile(r"\\(?:begin|end)\{(?:aligned|align)\*?\}")


def convert_environments(code: str) -> str:
    if "\\begin" not in code:
        return code
    code = ENV_VMATRIX_ARRAY_RE.sub(r"\\begin{vmatrix}\1\\end{vmatrix}", code)

    def repl_matrix(m: re.Match[str]) -> str:
        env = m.group(1)
        body = m.group(2).strip()
        delim = '"|"' if env in ("vmatrix", "Vmatrix") else '"("'
        rows = re.split(r"\\\\", body)
        out_rows: list[str] = []
        for r in rows:
            r_clean = r.strip()
            if not r_clean:
                continue
            cells = [c.strip() for c in r_clean.split("&")]
            safe_cells = [re.sub(r",\s*", ' "," ', c) for c in cells]
            out_rows.append(", ".join(safe_cells))
        return f"mat(delim: {delim}, " + "; ".join(out_rows) + ")"

    code = ENV_MATRIX_RE.sub(repl_matrix, code)

    def repl_cases(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
        return "cases(" + ", ".join(rows) + ")"

    code = ENV_CASES_RE.sub(repl_cases, code)

    def repl_array(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
        if len(rows) == 1:
            cells = [c.strip() for c in rows[0].split("&")]
            return " quad ".join(cells)
        out_rows = [", ".join(c.strip() for c in r.split("&")) for r in rows]
        return "mat(" + "; ".join(out_rows) + ")"

    code = ENV_ARRAY_RE.sub(repl_array, code)
    code = ENV_ALIGNED_RE.sub("", code)
    return code


PARTIAL_SLASH_RE = re.compile(
    r"(\\partial(?:\^[0-9]+)?(?:\s*(?:\\[a-zA-Z]+|[a-zA-Z0-9_]+))?)\s*/\s*(\\partial(?:\^[0-9]+)?\s*(?:\\bar\{[a-zA-Z]\}|\\[a-zA-Z]+|[a-zA-Z0-9_]+)(?:\^[0-9]+)?)"
)
SLASH_FN_RE = re.compile(
    r"/\s*(\\(?:sin|cos|tan|cot|sec|csc|sinh|cosh|tanh|log|ln)(?:\^[0-9]+)?\s+(?:\\frac\{[^{}]+\}\{[^{}]+\}|(?:\\(?:"
    + GREEK_WORDS
    + r")\s*)?[a-zA-Z0-9_]+(?:\s*\\(?:"
    + GREEK_WORDS
    + r"))?))"
)
SLASH_DENOM_RE = re.compile(
    r"/\s*(\d+(?:\\(?:"
    + GREEK_WORDS
    + r")|[a-zA-Z])(?:_[0-9a-zA-Z]+)?(?:\^[0-9a-zA-Z]+)?(?:\s*i\b)?)"
)
MATH_FN_RE = re.compile(
    r"\\(sin|cos|tan|cot|sec|csc|sinh|cosh|tanh|exp|ln|det|dim|ker|arg|deg|sup|inf|max|min|gcd|sgn|Re|Im)(?![a-zA-Z])"
)
GREEK_MACRO_RE = re.compile(GREEK_PATTERN)
GREEK_ATTACH_RE = re.compile(rf"\b({GREEK_WORDS})\s+(['\(_\^])")
GREEK_PRIME_PAREN_RE = re.compile(rf"\b({GREEK_WORDS})'\s+\(")
GREEK_PAIR_RE = re.compile(rf"({GREEK_WORDS})({GREEK_WORDS})")
PRE_GREEK_SPLIT_RE = re.compile(
    rf"\b(?!(?:beta|zeta|theta)(?![a-zA-Z]))([0-9a-zA-Z])({GREEK_WORDS})(?=[0-9_\^]|\b)"
)
SUB_GREEK_SPLIT_RE = re.compile(
    rf"(_[0-9a-zA-Z])(?!(?:beta|zeta|theta)(?![a-zA-Z]))({GREEK_WORDS})"
)
BARE_BRACES_RE = re.compile(r"(?<!\\)\{([^{}]*)\}")
NON_MATH_CHARS_RE = re.compile(r"[^\x00-\x7Fα-ωΑ-Ωℂℝℤℕℚ℘≤≥≠±∓×·→⇒↔⇐⇔•—–\s]")
MULTI_TOK_RE = re.compile(r"(?<![a-zA-Z0-9])[a-zA-Z0-9]{2,}(?![a-zA-Z0-9])")

DIFF_DERIV_FRAC_RE = re.compile(
    r"\(\s*(?:dif|d)(\^\([0-9a-zA-Z+\-\s]+\)|\^[0-9a-zA-Z]+)?(?:\s+([a-zA-Z0-9_']+))?\s*\)\s*/\s*\(\s*(?:dif|b|d)\s*([zxywtuvsrZ])(\^\([0-9a-zA-Z+\-\s]+\)|\^[0-9a-zA-Z]+)?\s*\)"
)
DIFF_INLINE_DERIV_RE = re.compile(
    r"\b(?:dif|d)(\^\([0-9a-zA-Z+\-\s]+\)|\^[0-9a-zA-Z]+)\s*([a-zA-Z0-9_']+)\s*/\s*(?:dif|d)\s*([zxywtuvsrZ])(\^\([0-9a-zA-Z+\-\s]+\)|\^[0-9a-zA-Z]+)"
)
DIFF_FORM_RE = re.compile(
    r"(?:thin\s+)?(?<![a-zA-Z0-9_\\])(?:dif|d)\s*(?=(?:theta|phi|rho|xi|zeta|tau|eta|omega|alpha|sigma|log|arg)\b|(?:[uavgG]_[0-9]+\b)|(?:[zxywtuvsrghFGUWZ]\b(?!\s*\^|\s*-\s*b\b))|\(u_2\s*v_1\))"
)
DIFF_ABS_RE = re.compile(r"\|\s*(dif\s+[^|\n]+?)\s*\|")


def normalize_differentials(code: str) -> str:
    if "d" not in code:
        return code

    def _repl_frac(m: re.Match[str]) -> str:
        deg1 = m.group(1) or ""
        fn = m.group(2) or ""
        var = m.group(3)
        deg2 = m.group(4) or ""
        num = f"dif{deg1} {fn}".strip()
        den = f"dif {var}{deg2}".strip()
        return f"({num})/({den})"

    code = DIFF_DERIV_FRAC_RE.sub(_repl_frac, code)
    code = DIFF_INLINE_DERIV_RE.sub(r"(dif\1 \2)/(dif \3\4)", code)
    code = DIFF_FORM_RE.sub("dif ", code)
    code = DIFF_ABS_RE.sub(r"abs(\1)", code)
    return code


@functools.lru_cache(maxsize=8192)
def sanitize_math_code(code: str, is_display: bool = False) -> str:
    code = re.sub(r"\\tag\{\d+\}", "", code)
    if code == "e^{|n|\\pi|\\tau|\\operatorname{Im}\\tau|}":
        code = "e^{-|n|\\pi \\operatorname{Im}\\tau}"

    code = convert_environments(code)
    if is_display:
        code = re.sub(r"\\\\\s*", " \\\n  ", code)
    else:
        code = re.sub(r"\\\\\s*", " ", code)

    if not code.isascii():
        code = code.translate(UNICODE_GREEK_TABLE)

    if "/" in code:
        code = PARTIAL_SLASH_RE.sub(r"(\1)/(\2)", code)
        code = SLASH_FN_RE.sub(r"/(\1)", code)
        code = SLASH_DENOM_RE.sub(r"/(\1)", code)

    code = convert_latex_fracs(code)
    code = convert_latex_sqrt(code)
    code = convert_unary_macros(code)
    code = convert_script_braces(code)

    code = (
        code.replace(r"\,", " thin ")
        .replace(r"\;", " ")
        .replace(r"\:", " ")
        .replace(r"\!", "")
        .replace(r"\ ", " ")
    )

    code = (
        code.replace(r"\times", " times ")
        .replace(r"\approx", " approx ")
        .replace(r"\equiv", " equiv ")
        .replace(r"\mapsto", " |-> ")
        .replace(r"\rightarrow", " -> ")
        .replace(r"\longrightarrow", " --> ")
        .replace(r"\leftarrow", " <- ")
        .replace(r"\leftrightarrow", " <-> ")
        .replace(r"\Rightarrow", " => ")
        .replace(r"\Leftrightarrow", " <=> ")
        .replace(r"\to", " -> ")
        .replace(r"\tilde", " tilde ")
        .replace(r"\bar", " overline ")
        .replace(r"\hat", " hat ")
        .replace(r"\varlimsup", " lim sup ")
        .replace(r"\varliminf", " lim inf ")
        .replace(r"\limsup", " lim sup ")
        .replace(r"\liminf", " lim inf ")
        .replace(r"\lim", " lim ")
        .replace(r"\log", " log ")
        .replace(r"\sum", " sum ")
        .replace(r"\prod", " product ")
        .replace(r"\bigcap", " inter.big ")
        .replace(r"\bigcup", " union.big ")
        .replace(r"\iiint", " integral integral integral ")
        .replace(r"\iint", " integral integral ")
        .replace(r"\oint", " integral ")
        .replace(r"\int", " integral ")
        .replace(r"\varepsilon", " epsilon ")
        .replace(r"\varphi", " phi ")
        .replace(r"\vartheta", " theta ")
        .replace(r"\varpi", " pi ")
        .replace(r"\varrho", " rho ")
        .replace(r"\partial", " partial ")
        .replace(r"\nabla", " nabla ")
        .replace(r"\infty", " infinity ")
        .replace(r"\emptyset", " emptyset ")
        .replace(r"\wp", " ℘ ")
        .replace(r"\dagger", " dagger ")
        .replace(r"\ell", " ell ")
        .replace(r"\langle", " chevron.l ")
        .replace(r"\rangle", " chevron.r ")
    )
    code = re.sub(r"\\mid(?![a-zA-Z])", " bar.v ", code)
    code = re.sub(r"\\in(?![a-zA-Z])", " in ", code)
    code = re.sub(r"\\notin(?![a-zA-Z])", " notin ", code)
    code = re.sub(r"\\cap(?![a-zA-Z])", " inter ", code)
    code = re.sub(r"\\cup(?![a-zA-Z])", " union ", code)
    code = re.sub(r"\\subset(?![a-zA-Z])", " subset ", code)
    code = re.sub(r"\\supset(?![a-zA-Z])", " supset ", code)
    code = re.sub(r"\\subseteq(?![a-zA-Z])", " subset.eq ", code)
    code = re.sub(r"\\supseteq(?![a-zA-Z])", " supset.eq ", code)
    code = re.sub(r"\\sim(?![a-zA-Z])", " tilde.op ", code)
    code = re.sub(r"\\simeq(?![a-zA-Z])", " tilde.eq ", code)
    code = re.sub(r"\\cong(?![a-zA-Z])", " tilde.equiv ", code)
    code = re.sub(
        r"\\left\s*\|((?:(?!\\left|\\right)[^|])+?)\\right\s*\|",
        r" abs(\1) ",
        code,
    )
    code = re.sub(
        r"\\[bB]igg?l\s*\|([^|]+?)\\[bB]igg?r\s*\|",
        r" abs(\1) ",
        code,
    )
    code = code.replace(r"\left", "").replace(r"\right", "").replace(r"\middle", "")
    code = re.sub(r"\\[bB]igg?(?:[lr])?(?![a-zA-Z])", "", code)
    code = code.replace(r"\circ", " degree ")
    code = re.sub(r"\\cdot(?![a-zA-Z])", " dot ", code)
    code = re.sub(r"\bdote\b", "dot e", code)
    code = code.replace(r"\cosec", " csc ").replace("cosec", "csc")
    code = (
        code.replace(r"\coth", " coth ")
        .replace(r"\arctan", " arctan ")
        .replace(r"\arcsin", " arcsin ")
        .replace(r"\arccos", " arccos ")
    )
    code = MATH_FN_RE.sub(r" \1 ", code)

    code = (
        code.replace(r"\leqq", "<=")
        .replace(r"\geqq", ">=")
        .replace(r"\leq", "<=")
        .replace(r"\geq", ">=")
        .replace(r"\le", "<=")
        .replace(r"\ge", ">=")
    )
    code = re.sub(r"\\ne(?:q)?(?![a-zA-Z])", "!=", code)
    code = code.replace(r"\quad", " quad ").replace(r"\qquad", " quad quad ")
    code = (
        code.replace(r"\cdots", " dots.h.c ")
        .replace(r"\ldots", " dots.h ")
        .replace(r"\dots", " dots.h ")
        .replace(r"\pm", " plus.minus ")
        .replace(r"\mp", " minus.plus ")
        .replace(r"\sqrt", " sqrt ")
    )

    code = GREEK_MACRO_RE.sub(r" \1 ", code)
    code = GREEK_ATTACH_RE.sub(r"\1\2", code)
    code = GREEK_PRIME_PAREN_RE.sub(r"\1'(", code)
    code = re.sub(r"\\\s*=", "=", code)
    code = re.sub(r"\\\s*([,\.\:\;])", r"\1", code)

    while BARE_BRACES_RE.search(code):
        code = BARE_BRACES_RE.sub(r"(\1)", code)

    code = NON_MATH_CHARS_RE.sub("", code)

    code = GREEK_PAIR_RE.sub(r"\1 \2", code)
    code = PRE_GREEK_SPLIT_RE.sub(r"\1 \2", code)
    code = SUB_GREEK_SPLIT_RE.sub(r"\1 \2", code)

    code = re.sub(r"([0-9])i([a-zA-Z])", r"\1 i \2", code)
    code = re.sub(
        r"(?<![A-Za-z])(?!(?:Re|Im|SL|GL|Cl|Bd|St)\b)([0-9a-z])([A-Z])", r"\1 \2", code
    )
    code = re.sub(
        r"(_[0-9]|_[a-zA-Z](?=[a-zA-Z]_[0-9])|_\([^\)]+\))([a-zA-Z])",
        r"\1 \2",
        code,
    )
    code = re.sub(
        r"(?<![a-zA-Z0-9])(?!(?:xi|pi|mu|nu|Re|Im|ln|in)_)([a-zA-Z0-9])([a-zA-Z]_[0-9a-zA-Z\(])",
        r"\1 \2",
        code,
    )

    code = normalize_differentials(code)

    def fix_tok(m: re.Match[str]) -> str:
        t = m.group(0)
        if t.isdigit() or t in KNOWN_MATH_WORDS:
            return t
        if t in MATH_OPERATOR_WORDS:
            return f'op("{t}")'
        if t.lower() in ENGLISH_WORDS:
            return f'"{t}"'
        m_sub = re.match(r"^([a-zA-Z])([0-9]+)$", t)
        if m_sub:
            return f"{m_sub.group(1)}_{m_sub.group(2)}"
        m_o = re.match(r"^([a-zA-Z])o$", t)
        if m_o and t.lower() not in ["to", "do", "so"]:
            return f"{m_o.group(1)}_0"
        return " ".join(list(t))

    segments = re.split(r'("[^"]*")', code)
    for idx in range(0, len(segments), 2):
        segments[idx] = MULTI_TOK_RE.sub(fix_tok, segments[idx])
    code = "".join(segments)

    unquoted_check = re.sub(r'"[^"]*"', "", code)
    if (
        "|" in unquoted_check
        and unquoted_check.count("|") % 2 == 0
        and "||" not in unquoted_check
        and "|->" not in unquoted_check
    ):
        code = re.sub(r"\|([^|\n]+?)\|", r" abs(\1) ", code)

    code = normalize_differentials(code)

    code = re.sub(r"_([a-zA-Z0-9]+)\(", r"_(\1)(", code)
    code = re.sub(r"\^([a-zA-Z0-9]+)\(", r"^(\1)(", code)
    code = re.sub(r"\s+([,\.\:\;])", r"\1", code)

    unquoted = re.sub(r'"[^"]*"', "", code)
    open_p = unquoted.count("(")
    close_p = unquoted.count(")")
    if open_p > close_p:
        code += ")" * (open_p - close_p)
    elif close_p > open_p:
        code = ("(" * (close_p - open_p)) + code
    return code.strip()


def clean_margin_and_inline_math(text: str) -> str:
    parts = text.split("$")
    for i in range(1, len(parts), 2):
        parts[i] = sanitize_math_code(parts[i], is_display=False)
    return "$".join(parts)


def make_figure_typst(
    fig_id: str, raw_caption: str, fig_dir: Path, paired: bool = False
) -> str:
    clean_cap = raw_caption.strip().replace("**", "")
    clean_cap = clean_margin_and_inline_math(clean_cap)
    rel_dir = fig_dir.name
    svg_path = fig_dir / f"fig_{fig_id}.svg"
    if svg_path.exists():
        width_pct = 82 if paired else 60
        return (
            f"#figure(\n"
            f'  image("{rel_dir}/fig_{fig_id}.svg", width: {width_pct}%),\n'
            f"  caption: [{clean_cap}]\n"
            f")"
        )
    img_path = fig_dir / f"fig_{fig_id}.png"
    width_pct = 55
    if img_path.exists():
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        if paired:
            width_pct = min(90, max(55, round(w_px / 520 * 100)))
        else:
            width_pct = min(82, max(28, round(w_px / 1050 * 100)))
            if h_px * (width_pct / 100.0) / max(w_px, 1) > 0.42:
                width_pct = max(26, round(0.42 * w_px / max(h_px, 1) * 100))
    return (
        f"#figure(\n"
        f'  image("{rel_dir}/fig_{fig_id}.png", width: {width_pct}%),\n'
        f"  caption: [{clean_cap}]\n"
        f")"
    )


def render_figure_group(figs: list[tuple[str, str]], fig_dir: Path) -> str:
    if not figs:
        return ""
    if len(figs) == 2:
        f1 = make_figure_typst(figs[0][0], figs[0][1], fig_dir, paired=True)
        f2 = make_figure_typst(figs[1][0], figs[1][1], fig_dir, paired=True)
        return (
            f"\n\n#align(center)[\n"
            f"  #grid(\n"
            f"    columns: (1fr, 1fr),\n"
            f"    column-gutter: 1.5em,\n"
            f"    align: center + bottom,\n"
            f"    [{f1}],\n"
            f"    [{f2}]\n"
            f"  )\n"
            f"]\n\n"
        )
    blocks = [
        f"\n\n#align(center)[\n  {make_figure_typst(fid, cap, fig_dir)}\n]\n\n"
        for fid, cap in figs
    ]
    return "".join(blocks)


def extract_page_parts(
    md_text: str, ch_num: int, pno: int
) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    raw_lines = md_text.splitlines()
    body_lines: list[str] = []
    footnote_lines: list[str] = []
    top_figs: list[tuple[str, str]] = []
    bot_figs: list[tuple[str, str]] = []

    for l in raw_lines:
        lt = l.strip()
        if not lt:
            body_lines.append("")
            continue
        if re.match(r"^\d{1,3}$", lt):
            continue
        if re.match(rf"^(?:{RUNNING_HEADER_WORDS})$", lt, re.IGNORECASE):
            continue
        if re.match(
            rf"^\d{{1,3}}\s+(?:{RUNNING_HEADER_WORDS})\b.*$", lt, re.IGNORECASE
        ):
            continue
        if re.match(
            rf"^(?:{RUNNING_HEADER_WORDS})\b.*?\s+\d{{1,3}}$", lt, re.IGNORECASE
        ):
            continue
        if re.match(
            r"^#\s+(?:[1-8]\b|CHAPTER|COMPLEX|ANALYTIC|SERIES|CONFORMAL|ELLIPTIC|GLOBAL|INDEX)",
            lt,
            re.IGNORECASE,
        ):
            continue
        if lt.startswith("![FIG.") or lt == "(a) (b)":
            continue
        if lt.startswith("†"):
            footnote_lines.append(lt.lstrip("†").strip())
            continue

        m_fig = re.match(r"^(?:\*\*)?FIG\.\s*(\d+)-(\d+)\.?(?:\*\*)?(.*)$", lt)
        if m_fig:
            fid = f"{m_fig.group(1)}_{m_fig.group(2)}"
            rest = m_fig.group(3).strip()
            cap = f"FIG. {m_fig.group(1)}-{m_fig.group(2)}." + (
                f" {rest}" if rest else ""
            )
            non_empty_body = len([b for b in body_lines if b.strip()])
            if non_empty_body <= 1 or pno == 298:
                top_figs.append((fid, cap))
            else:
                bot_figs.append((fid, cap))
            continue

        body_lines.append(l)

    s = "\n".join(body_lines).strip()
    if footnote_lines:
        s = re.sub(
            r"takes the form(\s*\n+\s*\$\$.*?)\s*\\dagger\s*(\$\$)",
            r"takes the form†\1\2",
            s,
            flags=re.DOTALL,
        )
        s = re.sub(r"\s*\\dagger\s*\$", "$†", s)
        for fn_text in footnote_lines:
            if "†" in s:
                s = s.replace("†", f"@@FNSTART@@{fn_text}@@FNEND@@", 1)
            else:
                s += f"@@FNSTART@@{fn_text}@@FNEND@@"
    if pno == 38:
        s = s.replace("as $x$ tends to $a$,", "as $x$ tends to $a$,*")
    if pno == 177:
        s = s.replace("if $|\\zeta| < 1$, then*", "if $|\\zeta| < 1$, then")
    if pno == 298:
        s = s.replace("Fig. 7-0", "Fig. 7-2")

    # 1. Universal equation number extraction attached to $$, \[, or standalone $
    s = re.sub(r"\\tag\{(\d+)\}", rf"\\tag{{{ch_num}-{pno}-\1}}", s)
    s = re.sub(
        r"^\s*\((\d+)\)\s*\$([^$\n]{10,})\$\s*$",
        r"(\1)\n$$\n\2\n$$",
        s,
        flags=re.MULTILINE,
    )
    s = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"$$\n\1\n$$", s, flags=re.DOTALL)

    def _replace_eq_block(m: re.Match[str]) -> str:
        pre_num = m.group(1)
        body = m.group(2).strip()
        post_num = m.group(3)
        eq_id = ""
        if pre_num:
            eq_id = f"{ch_num}-{pno}-{pre_num}"
        elif post_num:
            eq_id = f"{ch_num}-{pno}-{post_num}"
        m_start = re.match(r"^\((\d+)\)\s*(?:\\quad\s*)*", body)
        if m_start and not eq_id:
            eq_id = f"{ch_num}-{pno}-{m_start.group(1)}"
            body = body[m_start.end() :].strip()
        m_end = re.search(r"(?:\\quad|\s)+\((\d+)\)$", body)
        if m_end and not eq_id:
            eq_id = f"{ch_num}-{pno}-{m_end.group(1)}"
            body = body[: m_end.start()].strip()
        m_tag = re.search(r"\\tag\{([0-9-]+)\}", body)
        if m_tag:
            if not eq_id:
                eq_id = m_tag.group(1)
            body = (body[: m_tag.start()] + body[m_tag.end() :]).strip()
        label = f" <eq-{eq_id}>" if eq_id else ""
        return f"\n\n$$\n{body}\n$${label}\n\n"

    s = re.sub(
        r"(?:^[ \t]*\((\d+)\)[ \t]*\n*\s*)?\$\$(.*?)\$\$(?:[ \t]*\n?[ \t]*\n?[ \t]*\((\d+)\)[ \t]*(?=\n|$))?",
        _replace_eq_block,
        s,
        flags=re.MULTILINE | re.DOTALL,
    )

    if pno == 91:
        s = re.sub(r"sub-\s*\n+\s*regions", "subregions", s)

    return s.strip(), top_figs, bot_figs


def ends_complete_paragraph(text: str) -> bool:
    t = text.rstrip()
    if not t:
        return True
    last_line = t.splitlines()[-1].strip()
    if (
        last_line.startswith(("#", "=", "$$", "\\["))
        or last_line.endswith("$$")
        or re.search(r"<eq-[0-9-]+>$", last_line)
    ):
        return True
    return t.endswith(
        (".", "?", "!", ":", '."', ".'", ".)", ".*", ".*)", "]", "@@FNEND@@")
    )


def starts_new_block(text: str) -> bool:
    t = text.lstrip()
    if not t:
        return True
    first_line = t.splitlines()[0].strip()
    return first_line.startswith(
        (
            "#",
            "=",
            "$$",
            "\\[",
            "**",
            "*Proof",
            "1.",
            "2.",
            "3.",
            "4.",
            "5.",
            "(i)",
            "(ii)",
            "(a)",
            "(b)",
        )
    )


def split_first_paragraph(text: str) -> tuple[str, str]:
    parts = re.split(r"\n\s*\n", text.lstrip(), maxsplit=1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def join_cross_page_text(prev: str, curr_first: str) -> str:
    prev_r = prev.rstrip()
    curr_l = curr_first.lstrip()
    last_line = prev_r.splitlines()[-1].strip() if prev_r else ""
    if last_line.endswith("$$") or re.search(r"<eq-[0-9-]+>$", last_line):
        return prev_r + "\n" + curr_l
    # Cross-page de-hyphenation
    if prev_r.endswith("-"):
        m1 = re.search(r"\b([a-zA-Z]+)-$", prev_r)
        m2 = re.match(r"^([a-zA-Z]+)\b", curr_l)
        if m1 and m2:
            if m1.group(1).lower() in (
                "z",
                "w",
                "x",
                "y",
                "k",
                "n",
                "m",
                "p",
                "q",
                "one",
                "two",
                "non",
                "self",
                "well",
                "half",
                "single",
                "many",
            ):
                return prev_r[:-1] + "\u2011" + curr_l
            return prev_r[:-1] + curr_l
    return prev_r + " " + curr_l


def stitch_chapter_pages(
    pages_data: list[tuple[int, str, list[tuple[str, str]], list[tuple[str, str]]]],
    fig_dir: Path,
) -> str:
    acc = ""
    pending_figs: list[tuple[str, str]] = []

    for idx, (_pno, text, top_figs, bot_figs) in enumerate(pages_data):
        if not text and not top_figs and not bot_figs:
            continue

        all_top_figs = pending_figs + top_figs
        pending_figs = []
        starts_lower = bool(text.strip()) and text.lstrip()[0].islower()
        continues_prev = (
            not ends_complete_paragraph(acc) and not starts_new_block(text)
        ) or starts_lower

        if not acc:
            acc = render_figure_group(all_top_figs, fig_dir) + text
        elif continues_prev:
            first_p, rest_p = split_first_paragraph(text)
            acc = join_cross_page_text(acc, first_p)
            if all_top_figs:
                acc += render_figure_group(all_top_figs, fig_dir)
            if rest_p:
                acc += "\n\n" + rest_p
        else:
            if all_top_figs:
                acc += render_figure_group(all_top_figs, fig_dir)
            acc += "\n\n" + text

        if bot_figs:
            next_starts_lower = (
                idx + 1 < len(pages_data)
                and bool(pages_data[idx + 1][1].strip())
                and pages_data[idx + 1][1].lstrip()[0].islower()
            )
            if ends_complete_paragraph(acc) and not next_starts_lower:
                acc += render_figure_group(bot_figs, fig_dir)
            else:
                pending_figs.extend(bot_figs)

    if pending_figs:
        acc += render_figure_group(pending_figs, fig_dir)

    return acc


def format_chapter_typst(s: str) -> str:
    fig_blocks: list[str] = []

    def save_fig(m: re.Match[str]) -> str:
        idx = len(fig_blocks)
        fig_blocks.append(m.group(0))
        return f"\n\n@@FIGBLOCK{idx}@@\n\n"

    s = re.sub(
        r"#align\(center\)\[\n.*?\n\]",
        save_fig,
        s,
        flags=re.DOTALL,
    )

    s = s.replace('"', "''")

    # 2. Convert Markdown headings to Typst headings before escaping
    s = re.sub(
        r"^#{1,4}\s+(\*?)EXERCISES?\*?\s*$", r"==== \1EXERCISES", s, flags=re.MULTILINE
    )
    s = re.sub(
        r"^###\s+(\d+\.\s+(?:Compute|Prove|Find)\b.*?)$", r"\1", s, flags=re.MULTILINE
    )
    s = re.sub(r"^###\s+(Theorem\s+\d+\.)$", r"**\1**", s, flags=re.MULTILINE)
    s = re.sub(
        r"^##\s+(4\.2\.\s+Extension of .*?\.)\s+(Recall that)$",
        r"=== \1\n\n\2",
        s,
        flags=re.MULTILINE,
    )
    s = re.sub(r"^##\s+(\d+\.\d+\.\s+.*?)$", r"=== \1", s, flags=re.MULTILINE)
    s = re.sub(r"^###\s+(.*?)$", r"=== \1", s, flags=re.MULTILINE)
    s = re.sub(r"^##\s+(.*?)$", r"== \1", s, flags=re.MULTILINE)
    s = re.sub(r"^#\s+(.*?)$", r"= \1", s, flags=re.MULTILINE)

    # 3. Pre-math cleanups
    s = (
        s.replace('f"', "f''")
        .replace('w"', "w''")
        .replace('I"', "f''")
        .replace('z"', "z''")
        .replace('y"', "y''")
    )
    s = s.replace(r"\leqq", "<=").replace(r"\geqq", ">=")
    s = re.sub(
        r"(\\?partial\s+[a-zA-Z0-9_]+)\s*/\s*(\\?partial\s+[a-zA-Z0-9_]+)",
        r"(\1)/(\2)",
        s,
    )
    s = re.sub(r"(\\?partial\s+[a-zA-Z0-9_]+)\s*/\s*([a-zA-Z0-9_]+)", r"(\1)/(\2)", s)

    # 4. Extract display blocks ($$ ... $$ and \[ ... \])
    display_blocks: list[tuple[str, str]] = []

    def save_display(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        label = m.group(2) if m.group(2) else ""
        idx = len(display_blocks)
        display_blocks.append((body, label))
        return f"\n\n@@DISPLAYBLOCK{idx}@@\n\n"

    s = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"$$\n\1\n$$", s, flags=re.DOTALL)
    s = re.sub(
        r"\$\$\s*(.*?)\s*\$\$\s*(<eq-[^>]+>)?",
        save_display,
        s,
        flags=re.DOTALL,
    )

    def save_align(m: re.Match[str]) -> str:
        eq_no = m.group(1)
        body = m.group(2).strip()
        label = f"<eq-align-{eq_no}>" if eq_no else ""
        idx = len(display_blocks)
        display_blocks.append((body, label))
        return f"\n\n@@DISPLAYBLOCK{idx}@@\n\n"

    s = re.sub(
        r"(?:\((\d+)\)\s*)?\\begin\{align\*?\}(.*?)\\end\{align\*?\}",
        save_align,
        s,
        flags=re.DOTALL,
    )

    # Clean stray odd dollars
    cleaned_lines: list[str] = []
    for line in s.splitlines():
        if line.count("$") % 2 != 0:
            line = re.sub(r"(?<!\$)\$(?!\$)(?=[0-9A-Za-z_])", r"\\zeta_", line)
            line = re.sub(r"(?<!\$)\$(?!\$)", r"\\zeta ", line)
        cleaned_lines.append(line)
    s = "\n".join(cleaned_lines)

    # 5. Process inline math ($ ... $)
    inline_blocks: list[str] = []
    prose_re = re.compile(
        r"differential|equations|functions|polynomial|converges|identically|"
        r"derivative|continuous|condition|sufficient|necessary|arbitrary|"
        r"original|equation|type|ordinary|point|removable|singularity|coefficients",
        re.IGNORECASE,
    )

    def save_inline(m: re.Match[str]) -> str:
        code = m.group(1)
        if prose_re.search(code):
            clean_w = code.replace('"', "").strip()
            return f" {clean_w} "
        idx = len(inline_blocks)
        inline_blocks.append(code)
        return f"@@INLINEMATH{idx}@@"

    s = re.sub(r"\$([^$\n]+)\$", save_inline, s)

    s = re.sub(r"(?<![=\s])#", r"\#", s)
    s = re.sub(r"<(?!eq-|fig-|sec-)", r"\< ", s)
    s = re.sub(r"^\s*/\s*", r"\/ ", s, flags=re.MULTILINE)
    s = s.replace("*/", "* /")
    s = re.sub(
        r"(?<![@<])\b(?!(?:eq|fig|sec)\b)([a-zA-Z]+)-([a-zA-Z]+)",
        r"\1" + "\u2011" + r"\2",
        s,
    )
    # Fix inverted parentheses like )x >= c > 0()

    s = re.sub(r"^(\s*)\*(?=\d+\.|EXERCISES)", r"\1\\*", s, flags=re.MULTILINE)
    s = re.sub(
        r"\*\*((?:(?!\n\n|@@DISPLAYBLOCK|@@FN)[^\*])+?)\*\*",
        r"#strong[\1]",
        s,
    )
    # Standard theorem, lemma, and definition headers
    s = re.sub(r"#strong\[Theorem\s+(\d+)\.\]", r"#strong[Theorem \1.]", s)
    s = re.sub(r"#strong\[Lemma\s+(\d+)\.\]", r"#strong[Lemma \1.]", s)
    s = re.sub(r"#strong\[Definition\s+(\d+)\.\]", r"#strong[Definition \1.]", s)
    s = re.sub(
        r"(?<![\\\*])\*((?:(?!\n\n|@@DISPLAYBLOCK|@@FN)[^\*])+?)\*(?!\*)",
        r"#emph[\1]",
        s,
    )
    s = re.sub(r"(?<!\\)\*", r"\\*", s)
    s = re.sub(r"(?<![a-zA-Z0-9])_(?![a-zA-Z0-9])", r"\\_", s)
    s = s.replace(r"\cdots", "...")
    s = s.replace(r"\ldots", "...")

    s = re.sub(r"(@@INLINEMATH\d+@@)\s+([.,;:?!\)])", r"\1\2", s)
    s = re.sub(r"(\()\s+(@@INLINEMATH\d+@@)", r"\1\2", s)

    s = re.sub(
        r"@@INLINEMATH(\d+)@@",
        lambda m: (
            f"${sanitize_math_code(inline_blocks[int(m.group(1))], is_display=False)}$"
        ),
        s,
    )

    # 6. Restore display blocks with proper Typst block display syntax
    def restore_display(m: re.Match[str]) -> str:
        body, label = display_blocks[int(m.group(1))]
        clean_body = sanitize_math_code(body, is_display=True)
        return f"\n$ {clean_body} $ {label}\n"

    s = re.sub(r"@@DISPLAYBLOCK(\d+)@@", restore_display, s)
    s = re.sub(r"@@FIGBLOCK(\d+)@@", lambda m: fig_blocks[int(m.group(1))], s)
    s = re.sub(r"@@FNSTART@@(.*?)@@FNEND@@", r"#footnote[\1]", s)

    return s


def clean_markdown_page(md_text: str, ch_num: int = 1) -> str:
    """Sanitize and format markdown page for Typst."""
    body, _top_f, _bot_f = extract_page_parts(md_text, ch_num, 0)
    s = format_chapter_typst(body)
    # Prefix equation labels and refs with chapter number
    s = re.sub(r"<eq-(\d+)>", rf"<eq-{ch_num}-\1>", s)
    s = re.sub(r"@eq-(\d+)", rf"@eq-{ch_num}-\1", s)
    return s


def format_index_pages(md_dir: Path) -> str:
    entries: list[str] = []
    for pno in range(341, 348):
        p_file = md_dir / f"p_{pno:03d}.md"
        if not p_file.exists():
            continue
        for raw_line in p_file.read_text(encoding="utf-8").splitlines():
            lt = raw_line.strip()
            if not lt:
                continue
            if re.match(r"^#\s*Index$", lt, re.IGNORECASE):
                continue
            if re.match(
                r"^\d{1,3}\s+INDEX$|^INDEX\s+\d{1,3}$|^\d{1,3}$", lt, re.IGNORECASE
            ):
                continue
            is_sub = raw_line.startswith("  ") or (
                lt[0].islower() and not lt.startswith(("i.e.", "e.g."))
            )
            line_clean = lt.replace('"', "''")
            line_clean = re.sub(r"\*([^\*]+)\*", r"#emph[\1]", line_clean)
            line_clean = clean_margin_and_inline_math(line_clean)
            if is_sub:
                entries.append(f"#h(1.2em){line_clean}")
            else:
                entries.append(line_clean)

    joined = "\n\n".join(entries)
    return (
        "\n= INDEX\n\n"
        "#columns(2, gutter: 1.8em)[\n"
        "  #set text(size: 9pt)\n"
        "  #set par(first-line-indent: 0pt, hanging-indent: 1.2em, leading: 0.52em, spacing: 0.48em, justify: false)\n"
        f"  {joined}\n"
        "]\n"
    )


def assemble_ahlfors_book(out_dir: Path) -> None:
    out_dir = Path(out_dir)
    md_dir = out_dir / "markdown"
    fig_dir = out_dir / "figures"
    raw_fig_dir = out_dir / "figures_raw"
    if not raw_fig_dir.exists() and fig_dir.exists():
        raw_fig_dir.mkdir(parents=True, exist_ok=True)
        for png_path in sorted(fig_dir.glob("fig_*.png")):
            shutil.copy2(png_path, raw_fig_dir / png_path.name)

    from polytypst.ahlfors.compiler import AhlforsCompiler
    from polytypst.ahlfors.figures import generate_all_ahlfors_figures

    generate_all_ahlfors_figures(fig_dir)

    master_lines = [
        AhlforsCompiler.TYPST_PREAMBLE,
        AhlforsCompiler.TITLE_PAGE_BLOCK,
        AhlforsCompiler.TOC_BLOCK,
    ]

    # Chapter 1
    ch1_file = out_dir / "chapter1.md"
    if ch1_file.exists():
        ch1_text = ch1_file.read_text(encoding="utf-8")
        ch1_text = ch1_text.replace(
            "|z_1 / z_2| = |z_1| / |z_2|", "abs(z_1 / z_2) = abs(z_1) / abs(z_2)"
        )
        ch1_text = re.sub(r"<eq-(\d+)>", r"<eq-1-\1>", ch1_text)
        ch1_text = re.sub(r"@eq-(\d+)", r"@eq-1-\1", ch1_text)
        master_lines.append(ch1_text)
        master_lines.append("\n#pagebreak(weak: true)\n")

    # Chapters 2 through 8
    chapters_def = [
        (2, "COMPLEX FUNCTIONS", 37, 64),
        (3, "ANALYTIC FUNCTIONS AS MAPPINGS", 65, 116),
        (4, "COMPLEX INTEGRATION", 117, 190),
        (5, "SERIES AND PRODUCT DEVELOPMENTS", 191, 244),
        (6, "CONFORMAL MAPPING. DIRICHLET'S PROBLEM", 245, 278),
        (7, "ELLIPTIC FUNCTIONS", 279, 298),
        (8, "GLOBAL ANALYTIC FUNCTIONS", 299, 340),
    ]

    for ch_num, ch_title, start_p, end_p in chapters_def:
        pages_data: list[
            tuple[int, str, list[tuple[str, str]], list[tuple[str, str]]]
        ] = []
        for pno in range(start_p, end_p + 1):
            p_file = md_dir / f"p_{pno:03d}.md"
            if p_file.exists():
                text = p_file.read_text(encoding="utf-8").strip()
                if len(text) > 40 and "1.1.1.1.1" not in text:
                    p_body, top_f, bot_f = extract_page_parts(text, ch_num, pno)
                    pages_data.append((pno, p_body, top_f, bot_f))

        stitched = stitch_chapter_pages(pages_data, fig_dir)
        formatted = format_chapter_typst(stitched)
        master_lines.append(f"\n= CHAPTER {ch_num}: {ch_title}\n\n" + formatted)
        master_lines.append("\n#pagebreak(weak: true)\n")

    # Backmatter: Index (pages 341 to 347)
    master_lines.append(format_index_pages(md_dir))

    master_typ = out_dir / "ahlfors_complete.typ"
    master_pdf = out_dir / "ahlfors_complete.pdf"
    secondary_pdf = out_dir / "ahlfors.pdf"

    full_typ_content = "\n".join(master_lines)
    master_typ.write_text(full_typ_content, encoding="utf-8")
    print(
        f"Generated {master_typ} ({master_typ.stat().st_size / (1024 * 1024):.2f} MB)"
    )

    print("Compiling complete monograph with Typst...")
    AhlforsCompiler.compile_pdf(master_typ, master_pdf)
    shutil.copy2(master_pdf, secondary_pdf)

    import pymupdf

    doc = pymupdf.open(str(master_pdf))
    print("\n🏆 ABSOLUTE TRIUMPH! Compiled complete Ahlfors monograph:")
    print(f"   PDF File:    {master_pdf}")
    print(f"   Total Pages: {len(doc)} pages")
    print(f"   File Size:   {master_pdf.stat().st_size / (1024 * 1024):.2f} MB")


def assemble_illustrated_ahlfors_book(out_dir: Path) -> None:
    out_dir = Path(out_dir)
    md_dir = out_dir / "markdown"
    src_fig_dir = out_dir / "figures"
    color_fig_dir = out_dir / "figures_color"

    from polytypst.ahlfors.compiler import AhlforsCompiler
    from polytypst.ahlfors.figures import generate_colorful_ahlfors_figures

    generate_colorful_ahlfors_figures(src_fig_dir, color_fig_dir)

    master_lines = [
        AhlforsCompiler.TYPST_PREAMBLE,
        AhlforsCompiler.TITLE_PAGE_BLOCK.replace(
            "THIRD EDITION",
            "THIRD EDITION — COLORFUL ILLUSTRATED EDITION",
        ),
        AhlforsCompiler.TOC_BLOCK,
    ]

    ch1_file = out_dir / "chapter1.md"
    if ch1_file.exists():
        ch1_text = ch1_file.read_text(encoding="utf-8")
        ch1_text = ch1_text.replace(
            "|z_1 / z_2| = |z_1| / |z_2|", "abs(z_1 / z_2) = abs(z_1) / abs(z_2)"
        )
        ch1_text = ch1_text.replace('image("figures/', 'image("figures_color/')
        ch1_text = re.sub(r"<eq-(\d+)>", r"<eq-1-\1>", ch1_text)
        ch1_text = re.sub(r"@eq-(\d+)", r"@eq-1-\1", ch1_text)
        master_lines.append(ch1_text)
        master_lines.append("\n#pagebreak(weak: true)\n")

    chapters_def = [
        (2, "COMPLEX FUNCTIONS", 37, 64),
        (3, "ANALYTIC FUNCTIONS AS MAPPINGS", 65, 116),
        (4, "COMPLEX INTEGRATION", 117, 190),
        (5, "SERIES AND PRODUCT DEVELOPMENTS", 191, 244),
        (6, "CONFORMAL MAPPING. DIRICHLET'S PROBLEM", 245, 278),
        (7, "ELLIPTIC FUNCTIONS", 279, 298),
        (8, "GLOBAL ANALYTIC FUNCTIONS", 299, 340),
    ]

    bonus_figs_by_page: dict[int, list[tuple[str, str]]] = {
        55: [
            (
                "bonus_2_1",
                "FIG. 2-1. Hadamard disk of convergence $|z - z_0| < R$ and compact subdisk.",
            )
        ],
        135: [
            (
                "bonus_4_cauchy",
                "FIG. 4-2a. Cauchy integral formula contour around excavated disk $C_\\delta$.",
            )
        ],
        201: [
            (
                "bonus_5_laurent",
                "FIG. 5-1a. Laurent series annulus $r_1 < |z - a| < r_2$.",
            )
        ],
        246: [
            (
                "bonus_6_riemann",
                "FIG. 6-0a. Conformal bijection of the Riemann Mapping Theorem ($z_0 \\mapsto 0, f'(z_0) > 0$).",
            )
        ],
        281: [
            (
                "bonus_7_torus",
                "FIG. 7-1a. Quotient of the period parallelogram $(\\omega_1, \\omega_2)$ onto the complex torus $\\mathbb{C}\\text{/}\\Lambda$.",
            )
        ],
    }

    for ch_num, ch_title, start_p, end_p in chapters_def:
        pages_data: list[
            tuple[int, str, list[tuple[str, str]], list[tuple[str, str]]]
        ] = []
        for pno in range(start_p, end_p + 1):
            p_file = md_dir / f"p_{pno:03d}.md"
            if p_file.exists():
                text = p_file.read_text(encoding="utf-8").strip()
                if len(text) > 40 and "1.1.1.1.1" not in text:
                    p_body, top_f, bot_f = extract_page_parts(text, ch_num, pno)
                    if pno in bonus_figs_by_page:
                        bot_f = bot_f + bonus_figs_by_page[pno]
                    pages_data.append((pno, p_body, top_f, bot_f))

        stitched = stitch_chapter_pages(pages_data, color_fig_dir)
        formatted = format_chapter_typst(stitched)
        master_lines.append(f"\n= CHAPTER {ch_num}: {ch_title}\n\n" + formatted)
        master_lines.append("\n#pagebreak(weak: true)\n")

    master_lines.append(format_index_pages(md_dir))

    illustrated_typ = out_dir / "ahlfors_illustrated.typ"
    illustrated_pdf = out_dir / "ahlfors_illustrated.pdf"

    illustrated_typ.write_text("\n".join(master_lines), encoding="utf-8")
    AhlforsCompiler.compile_pdf(illustrated_typ, illustrated_pdf)

    import pymupdf

    doc = pymupdf.open(str(illustrated_pdf))
    print(f"   Illustrated PDF: {illustrated_pdf} ({len(doc)} pages)")


if __name__ == "__main__":
    assemble_ahlfors_book(Path("output/ahlfors"))
    assemble_illustrated_ahlfors_book(Path("output/ahlfors"))
