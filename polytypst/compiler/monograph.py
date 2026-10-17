"""Universal Academic Monograph Compiler for TeX-compatible Markdown, XeLaTeX, Typst, and PDF."""

import functools
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from re import Pattern

import pymupdf
from PIL import Image


@dataclass(frozen=True)
class ChapterSpec:
    number: int
    title: str
    start_page: int
    end_page: int


@dataclass(frozen=True)
class MonographSpec:
    slug: str
    title: str
    author: str
    subtitle: str = ""
    translator: str = ""
    editor: str = ""
    publisher: str = "Cambridge University Press"
    series: str = "Cambridge Studies in Advanced Mathematics"
    year: int = 2007
    preface_page: int | None = None
    chapters: list[ChapterSpec] = field(default_factory=list)
    sections: dict[str, tuple[int, str]] = field(default_factory=dict)
    problems_pages: tuple[int, int] | None = None
    references_page: int | None = None
    index_pages: tuple[int, int] | None = None
    running_headers_pattern: str = ""


@dataclass(frozen=True)
class MonographOutputs:
    markdown_path: Path
    latex_path: Path
    typst_path: Path
    pdf_path: Path
    total_pages: int


KODAIRA_SPEC = MonographSpec(
    slug="kodaira_complex_analysis",
    title="Complex Analysis",
    author="Kunihiko Kodaira",
    translator="A. Sevenster",
    editor="A. F. Beardon and T. K. Carne",
    publisher="Cambridge University Press",
    series="Cambridge Studies in Advanced Mathematics",
    year=2007,
    preface_page=10,
    chapters=[
        ChapterSpec(1, "Holomorphic functions", 12, 70),
        ChapterSpec(2, "Cauchy's Theorem", 71, 127),
        ChapterSpec(3, "Conformal mappings", 128, 163),
        ChapterSpec(4, "Analytic continuation", 164, 210),
        ChapterSpec(5, "Riemann's Mapping Theorem", 211, 257),
        ChapterSpec(6, "Riemann surfaces", 258, 329),
        ChapterSpec(7, "The structure of Riemann surfaces", 330, 386),
        ChapterSpec(8, "Analytic functions on a closed Riemann surface", 387, 404),
    ],
    sections={
        "1.1": (12, "Holomorphic functions"),
        "1.2": (26, "Power series"),
        "1.3": (35, "Integrals"),
        "1.4": (58, "Properties of holomorphic functions"),
        "2.1": (71, "Piecewise smooth curves"),
        "2.2": (85, "Cellular decomposition"),
        "2.3": (112, "Cauchy's Theorem"),
        "2.4": (124, "Differentiability and homology"),
        "3.1": (128, "Conformal mappings"),
        "3.2": (143, "The Riemann sphere"),
        "3.3": (150, "Linear fractional transformations"),
        "4.1": (164, "Analytic continuation"),
        "4.2": (171, "Analytic continuation along curves"),
        "4.3": (191, "Analytic continuation by integrals"),
        "4.4": (201, "Cauchy's Theorem (continued)"),
        "5.1": (211, "Riemann's Mapping Theorem"),
        "5.2": (225, "Correspondence of boundaries"),
        "5.3": (235, "The principle of reflection"),
        "6.1": (258, "Differential forms"),
        "6.2": (271, "Riemann surfaces"),
        "6.3": (278, "Differential forms on a Riemann surface"),
        "6.4": (305, "Dirichlet's Principle"),
        "7.1": (330, "Planar Riemann surfaces"),
        "7.2": (351, "Compact Riemann surfaces"),
        "8.1": (387, "Abelian differentials of the first kind"),
        "8.2": (390, "Abelian differentials of the second and third kind"),
        "8.3": (392, "The Riemann-Roch Theorem"),
        "8.4": (399, "Abel's Theorem"),
    },
    problems_pages=(405, 412),
    references_page=413,
    index_pages=(414, 417),
    running_headers_pattern=(
        r"Holomorphic functions|Cauchy's Theorem|Conformal mappings|"
        r"Analytic continuation|Riemann's Mapping Theorem|Riemann surfaces|"
        r"The structure of\s*Riemann surfaces|Analytic functions on a closed Riemann surface|"
        r"Piecewise smooth curves|Cellular decomposition|Differentiability and homology|"
        r"The Riemann sphere|Linear fractional transformations|"
        r"Analytic continuation along curves|Analytic continuation by integrals|"
        r"Cauchy's Theorem \(continued\)|Correspondence of boundaries|The principle of reflection|"
        r"Differential forms|Differential forms on a Riemann surface|Dirichlet's Principle|"
        r"Planar Riemann surfaces|Compact Riemann surfaces|"
        r"Abelian differentials of the first kind|Abelian differentials of the second and third kind|"
        r"The Riemann[-–—]Roch Theorem|Abel's Theorem|Power series|Integrals|"
        r"Properties of holomorphic functions|Preface|Contents|Problems|References|Index"
    ),
)


def resolve_monograph_spec(pdf_path: Path, total_pages: int) -> MonographSpec:
    name_low = pdf_path.name.lower()
    if (
        total_pages == 417
        or "kodaira" in name_low
        or "complex analysis ( etc.)" in name_low
    ):
        return KODAIRA_SPEC
    slug = re.sub(r"[^a-z0-9]+", "_", pdf_path.stem.lower()).strip("_") or "book"
    return MonographSpec(
        slug=slug,
        title=pdf_path.stem,
        author="Author",
        chapters=[ChapterSpec(1, pdf_path.stem, 1, total_pages)],
    )


KNOWN_MATH_WORDS: set[str] = {
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
    "rev",
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
    "forall",
    "exists",
    "not",
    "and",
    "or",
    "without",
}

ENGLISH_WORDS: set[str] = {
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
    "if",
    "when",
    "by",
    "of",
    "at",
    "in",
    "constant",
    "const",
    "poles",
    "pole",
    "even",
    "odd",
    "otherwise",
    "else",
    "some",
    "any",
    "such",
    "that",
    "regular",
    "holomorphic",
    "meromorphic",
    "analytic",
    "continuous",
    "compact",
    "open",
    "closed",
    "real",
    "imaginary",
    "branch",
    "cycle",
    "homologous",
    "modulo",
}

MATH_OPERATOR_WORDS: set[str] = {
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
    "ord",
    "div",
    "grad",
    "rot",
    "curl",
    "rank",
    "tr",
    "Tr",
    "Gal",
    "Pic",
    "Div",
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

UNICODE_GREEK: dict[str, str] = {
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

UNICODE_GREEK_TABLE = str.maketrans({k: f" {v} " for k, v in UNICODE_GREEK.items()})
FRAC_MACRO_RE: Pattern[str] = re.compile(r"\\(?:d|t)?frac(?=\s*\{)")
BINOM_MACRO_RE: Pattern[str] = re.compile(r"\\binom(?=\s*\{)")
THEFRAC_RE: Pattern[str] = re.compile(r"\bthefrac(?=\{)")
BARE_FRAC_ONE_RE: Pattern[str] = re.compile(r"\\(?:d|t)?frac\s*([0-9a-zA-Z])\s*\{")
BARE_FRAC_TWO_RE: Pattern[str] = re.compile(
    r"\\(?:d|t)?frac\s*([0-9a-zA-Z])\s+([0-9a-zA-Z])"
)
SQRT_MACRO_RE: Pattern[str] = re.compile(r"\\sqrt(?=\s*[\[\{])")
BARE_SQRT_RE: Pattern[str] = re.compile(r"\\sqrt\s+([0-9a-zA-Z])")
SCRIPT_BRACE_RE: Pattern[str] = re.compile(r"([\^_])(?=\s*\{)")
BARE_UNARY_ARG_RE: Pattern[str] = re.compile(
    r"(\\(?:overline|bar|underline|widetilde|tilde|widehat|hat|check|vec|ddot|dot|mathbf|boldsymbol|bm|mathcal|mathfrak|mathbb|operatorname|mathrm|textrm|textbf|textit|text|mbox))\s+(\\[a-zA-Z]+|[0-9a-zA-Z])"
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
    s = BARE_SQRT_RE.sub(r"\\sqrt{\1}", s)
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
            res.append(" sqrt ")
            pos = cur
    return "".join(res)


UNARY_MACROS: list[tuple[Pattern[str], str]] = [
    (re.compile(r"\\(?:overline|bar)(?=\s*\{)"), " overline(({0})) "),
    (re.compile(r"\\underline(?=\s*\{)"), " underline(({0})) "),
    (re.compile(r"\\(?:widetilde|tilde)(?=\s*\{)"), " tilde(({0})) "),
    (re.compile(r"\\(?:widehat|hat)(?=\s*\{)"), " hat(({0})) "),
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
    s = BARE_UNARY_ARG_RE.sub(r"\1{\2}", s)
    for pattern, fmt in UNARY_MACROS:
        while True:
            m = pattern.search(s)
            if not m:
                break
            inner, end_pos = parse_braced(s, m.end())
            inner_conv = convert_unary_macros(inner)
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
ENV_ALIGNED_RE = re.compile(
    r"\\(?:begin|end)\{(?:aligned|align|split|gather| multline)\*?\}"
)


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
        rows: list[str] = []
        for r in re.split(r"\\\\", body):
            r_clean = r.strip()
            if not r_clean:
                continue
            parts = [p.strip() for p in r_clean.split("&") if p.strip()]
            rows.append(" ".join(parts))
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
DIFF_ABS_RE = re.compile(r"(?<!\\)\|\s*(dif\s+[^|\n]+?)\s*(?<!\\)\|")


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
    code = re.sub(r"\\tag\{[^{}]*\}", "", code)
    code = convert_environments(code)
    if is_display:
        code = re.sub(r"\\\\\s*", " \\\n  ", code)
        code = re.sub(r"\s*&\s*", " ", code)
    else:
        code = re.sub(r"\\\\\s*", " ", code)
        code = re.sub(r"\s*&\s*", " ", code)

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
        .replace(r"\longleftarrow", " <-- ")
        .replace(r"\leftrightarrow", " <-> ")
        .replace(r"\Longleftrightarrow", " <==> ")
        .replace(r"\Rightarrow", " => ")
        .replace(r"\Leftarrow", " <= ")
        .replace(r"\Leftrightarrow", " <=> ")
        .replace(r"\iff", " <=> ")
        .replace(r"\implies", " => ")
        .replace(r"\to", " -> ")
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
        .replace(r"\bigoplus", " plus.circle.big ")
        .replace(r"\oplus", " plus.circle ")
        .replace(r"\otimes", " times.circle ")
        .replace(r"\iiint", " integral integral integral ")
        .replace(r"\iint", " integral integral ")
        .replace(r"\oint", " integral.cont ")
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
        .replace(r"\varnothing", " emptyset ")
        .replace(r"\wp", " ℘ ")
        .replace(r"\dagger", " dagger ")
        .replace(r"\ell", " ell ")
        .replace(r"\langle", " chevron.l ")
        .replace(r"\rangle", " chevron.r ")
        .replace(r"\forall", " forall ")
        .replace(r"\exists", " exists ")
        .replace(r"\neg", " not ")
        .replace(r"\wedge", " and ")
        .replace(r"\vee", " or ")
        .replace(r"\setminus", " without ")
        .replace(r"\backslash", " without ")
        .replace(r"\perp", " perp ")
        .replace(r"\parallel", " parallel ")
        .replace(r"\propto", " propto ")
        .replace(r"\bmod", " mod ")
    )
    code = (
        code.replace(r"\not\in", " in.not ")
        .replace(r"\not=", " != ")
        .replace(r"\not\equiv", " equiv.not ")
        .replace(r"\not\subset", " subset.not ")
    )
    code = re.sub(r"\\mid(?![a-zA-Z])", " | ", code)
    code = re.sub(r"\\in(?![a-zA-Z])", " in ", code)
    code = re.sub(r"\\ni(?![a-zA-Z])", " in.rev ", code)
    code = re.sub(r"\\notin(?![a-zA-Z])", " in.not ", code)
    code = re.sub(r"\\cap(?![a-zA-Z])", " inter ", code)
    code = re.sub(r"\\cup(?![a-zA-Z])", " union ", code)
    code = re.sub(r"\\subset(?![a-zA-Z])", " subset ", code)
    code = re.sub(r"\\supset(?![a-zA-Z])", " supset ", code)
    code = re.sub(r"\\subseteq(?![a-zA-Z])", " subset.eq ", code)
    code = re.sub(r"\\supseteq(?![a-zA-Z])", " supset.eq ", code)
    code = re.sub(r"\\subsetneq(?![a-zA-Z])", " subset.neq ", code)
    code = re.sub(r"\\supsetneq(?![a-zA-Z])", " supset.neq ", code)
    code = re.sub(r"\\sim(?![a-zA-Z])", " tilde.op ", code)
    code = re.sub(r"\\simeq(?![a-zA-Z])", " tilde.eq ", code)
    code = re.sub(r"\\cong(?![a-zA-Z])", " tilde.equiv ", code)
    code = re.sub(r"\\(?:lVert|rVert|Vert)(?![a-zA-Z])", r"\|", code)
    if r"\|" in code:
        code = re.sub(r"\\\|\s*([^|\n]+?)\s*\\\|", r" norm(\1) ", code)
        code = code.replace(r"\|", " || ")
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
        code.replace(r"\leqslant", "<=")
        .replace(r"\geqslant", ">=")
        .replace(r"\leqq", "<=")
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
        .replace(r"\vdots", " dots.v ")
        .replace(r"\ddots", " dots.down ")
        .replace(r"\pm", " plus.minus ")
        .replace(r"\mp", " minus.plus ")
    )

    code = GREEK_MACRO_RE.sub(r" \1 ", code)
    code = GREEK_ATTACH_RE.sub(r"\1\2", code)
    code = GREEK_PRIME_PAREN_RE.sub(r"\1'(", code)
    code = re.sub(r"\\\s*=", "=", code)
    code = re.sub(r"\\\s*([,\.\:\;])", r"\1", code)
    code = re.sub(r"\\([a-zA-Z]+)", r" \1 ", code)

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
        and " | " not in unquoted_check
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


def ends_complete_paragraph(text: str) -> bool:
    t = text.rstrip()
    if not t:
        return True
    last_line = t.splitlines()[-1].strip()
    if (
        last_line.startswith(("#", "=", "$$", "\\["))
        or last_line.endswith("$$")
        or re.search(r"<eq-[0-9a-zA-Z'-]+>$", last_line)
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
            "Proof",
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
    if last_line.endswith("$$") or re.search(r"<eq-[0-9a-zA-Z'-]+>$", last_line):
        return prev_r + "\n" + curr_l
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


class MonographCompiler:
    """Compiles transcribed Markdown pages and extracted figures into Markdown, LaTeX, Typst, and PDF."""

    def __init__(self, spec: MonographSpec) -> None:
        self.spec: MonographSpec = spec

    def build_typst_preamble(self) -> str:
        return f"""#set document(
  title: "{self.spec.title} — {self.spec.author}",
  author: "{self.spec.author}",
  date: auto
)

#set page(
  width: 442pt,
  height: 663pt,
  margin: (inside: 56pt, outside: 56pt, top: 56pt, bottom: 62pt),
  header: context {{
    let page-number = counter(page).get().first()
    let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
    if page-number > 4 and not on-chapter-page [
      #if calc.odd(page-number) [
        #let secs = query(heading.where(level: 2).before(here()))
        #let chaps = query(heading.where(level: 1).before(here()))
        #let title = if secs != () {{ secs.last().body }} else if chaps != () {{ chaps.last().body }} else {{ "{self.spec.title}" }}
        #grid(
          columns: (1fr, auto),
          align(left)[#text(8.5pt, font: "New Computer Modern", style: "italic")[#title]],
          align(right)[#text(9.5pt, font: "New Computer Modern")[#page-number]]
        )
      ] else [
        #let chaps = query(heading.where(level: 1).before(here()))
        #let title = if chaps != () {{ chaps.last().body }} else {{ "{self.spec.title}" }}
        #grid(
          columns: (auto, 1fr),
          align(left)[#text(9.5pt, font: "New Computer Modern")[#page-number]],
          align(right)[#text(8.5pt, font: "New Computer Modern", style: "italic")[#title]]
        )
      ]
      #v(-0.35em)
      #line(length: 100%, stroke: 0.35pt + luma(120))
    ]
  }},
  footer: none
)

#set text(
  font: "New Computer Modern",
  size: 10pt,
  lang: "en",
  hyphenate: true
)

#set par(
  leading: 0.65em,
  spacing: 0.85em,
  justify: true,
  first-line-indent: 1.5em,
  linebreaks: "optimized"
)

#show math.equation: set text(font: "New Computer Modern Math")
#set math.equation(numbering: "(1)")
#let dd = math.dif
#let dv(f, x, deg: none) = if deg == none {{ $(dif f)/(dif x)$ }} else {{ $(dif^deg f)/(dif x^deg)$ }}
#let pdv(f, x, deg: none) = if deg == none {{ $(partial f)/(partial x)$ }} else {{ $(partial^deg f)/(partial x^deg)$ }}
#show ref: it => {{
  let target = str(it.target)
  if target.starts-with("eq-") {{
    let raw = target.trim("eq-", at: start)
    let parts = raw.split("-")
    let disp = if parts.len() >= 2 {{ parts.at(-2) + "." + parts.last() }} else {{ parts.last() }}
    link(it.target)[(#disp)]
  }} else {{
    it
  }}
}}
#show math.equation.where(block: true): it => {{
  if it.numbering == none {{
    return it
  }}
  layout(size => {{
    let eq = math.equation(it.body, block: true, numbering: none)
    if not it.has("label") {{
      let m = measure(eq)
      if m.width > size.width and m.width > 0pt {{
        let factor = (size.width / m.width) * 100%
        align(center, scale(x: factor, y: factor, reflow: true, eq))
      }} else {{
        eq
      }}
    }} else {{
      let lbl = str(it.label).trim("eq-", at: start)
      let parts = lbl.split("-")
      let disp = if parts.len() >= 2 {{ parts.at(-2) + "." + parts.last() }} else {{ parts.last() }}
      let num-box = [(#disp)]
      let avail = size.width - measure(num-box).width - 12pt
      let m = measure(eq)
      let fitted = if m.width > avail and m.width > 0pt {{
        let factor = (avail / m.width) * 100%
        scale(x: factor, y: factor, reflow: true, eq)
      }} else {{
        eq
      }}
      grid(
        columns: (1fr, auto),
        column-gutter: 0.8em,
        align: (center + horizon, right + horizon),
        fitted,
        num-box
      )
    }}
  }})
}}

#show heading: set par(justify: false, first-line-indent: 0pt)

#show heading.where(level: 1): it => {{
  v(2.4em)
  align(left)[
    #text(16pt, weight: "bold", font: "New Computer Modern")[#it.body]
  ]
  v(0.6em)
  line(length: 100%, stroke: 0.6pt + black)
  v(1.4em)
}}

#show heading.where(level: 2): it => {{
  v(1.4em)
  text(12pt, weight: "bold", font: "New Computer Modern")[#it.body]
  v(0.55em)
}}

#show heading.where(level: 3): it => {{
  v(1.1em)
  text(10.5pt, weight: "bold", style: "italic", font: "New Computer Modern")[#it.body]
  v(0.35em)
}}

#show heading.where(level: 4): it => {{
  v(0.95em)
  text(10pt, weight: "bold", font: "New Computer Modern")[#smallcaps(it.body)]
  v(0.4em)
}}

#show figure.caption: it => [
  #v(0.35em)
  #text(8.5pt, font: "New Computer Modern")[#it.body]
]
"""

    def build_typst_title_page(self) -> str:
        credits = ""
        if self.spec.translator or self.spec.editor:
            parts: list[str] = []
            if self.spec.translator:
                parts.append(f"Translated by {self.spec.translator}")
            if self.spec.editor:
                parts.append(f"Edited by {self.spec.editor}")
            joined_credits = "\\ ".join(parts)
            credits = f'#v(1.6em)\n  #text(10pt, style: "italic", font: "New Computer Modern")[{joined_credits}]'
        return f"""
#align(center + horizon)[
  #text(10pt, tracking: 0.14em, font: "New Computer Modern")[#smallcaps("{self.spec.series}")]
  #v(3em)
  #text(26pt, weight: "bold", font: "New Computer Modern")[{self.spec.title.upper()}]
  #v(2.2em)
  #text(14pt, weight: "bold", font: "New Computer Modern")[#smallcaps("{self.spec.author}")]
  {credits}
  #v(5em)
  #line(length: 35%, stroke: 0.4pt + luma(140))
  #v(1.2em)
  #text(11pt, weight: "bold", tracking: 0.12em, font: "New Computer Modern")[{self.spec.publisher.upper()}]
  #v(0.4em)
  #text(8.5pt, fill: luma(90), font: "New Computer Modern")[Cambridge · New York · Melbourne · Madrid · Cape Town · Singapore]
]

#pagebreak()

#outline(title: [Contents], indent: 1.4em, depth: 2)

#pagebreak()
"""

    @staticmethod
    def make_figure_typst(
        fig_id: str, raw_caption: str, fig_dir: Path, paired: bool = False
    ) -> str:
        clean_cap = raw_caption.strip().replace("**", "")
        clean_cap = clean_margin_and_inline_math(clean_cap)
        img_path = fig_dir / f"fig_{fig_id}.png"
        if not img_path.exists():
            return f"\n\n#align(center)[#emph[{clean_cap}]]\n\n"
        with Image.open(img_path) as im:
            w_px, h_px = im.size
        if paired:
            width_pct = min(88, max(50, round(w_px / 650 * 100)))
        else:
            width_pct = min(78, max(26, round(w_px / 1350 * 100)))
            if h_px * (width_pct / 100.0) / max(w_px, 1) > 0.38:
                width_pct = max(24, round(0.38 * w_px / max(h_px, 1) * 100))
        return (
            f"#figure(\n"
            f'  image("figures/fig_{fig_id}.png", width: {width_pct}%),\n'
            f"  caption: [{clean_cap}],\n"
            f"  supplement: none\n"
            f")"
        )

    @classmethod
    def render_figure_group(cls, figs: list[tuple[str, str]], fig_dir: Path) -> str:
        if not figs:
            return ""
        valid_figs = [
            (fid, cap) for fid, cap in figs if (fig_dir / f"fig_{fid}.png").exists()
        ]
        if not valid_figs:
            return ""
        if len(valid_figs) == 2:
            f1 = cls.make_figure_typst(
                valid_figs[0][0], valid_figs[0][1], fig_dir, paired=True
            )
            f2 = cls.make_figure_typst(
                valid_figs[1][0], valid_figs[1][1], fig_dir, paired=True
            )
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
            f"\n\n#align(center)[\n  {cls.make_figure_typst(fid, cap, fig_dir)}\n]\n\n"
            for fid, cap in valid_figs
        ]
        return "".join(blocks)

    def extract_page_parts(
        self,
        md_text: str,
        pno: int,
    ) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
        raw_lines = md_text.splitlines()
        body_lines: list[str] = []
        top_figs: list[tuple[str, str]] = []
        bot_figs: list[tuple[str, str]] = []
        seen_figs_on_page: set[str] = set()
        chapter_start_pages = {c.start_page for c in self.spec.chapters}
        hdr_pat = self.spec.running_headers_pattern

        for l in raw_lines:
            lt = l.strip()
            if not lt:
                body_lines.append("")
                continue

            if re.match(r"^(?:\d{1,3}|[ivxlcdm]+)$", lt, re.IGNORECASE):
                continue

            non_empty_so_far = len([b for b in body_lines if b.strip()])
            if non_empty_so_far <= 2 and hdr_pat:
                if re.match(
                    rf"^(?:#+\s*)?(?:{hdr_pat})(?:\s+\d{{1,3}})?$",
                    lt,
                    re.IGNORECASE,
                ):
                    continue
                if re.match(rf"^\d{{1,3}}\s+(?:{hdr_pat})$", lt, re.IGNORECASE):
                    continue
                m_sec_hdr = re.match(
                    r"^(?:#+\s*)?(\d+\.\d+)\s+(.+?)(?:\s+\d{1,3})?$", lt
                )
                if m_sec_hdr:
                    sec_id = m_sec_hdr.group(1)
                    expected = self.spec.sections.get(sec_id)
                    if not expected or expected[0] != pno:
                        continue

            if pno in chapter_start_pages and non_empty_so_far <= 2:
                if re.match(r"^(?:#+\s*)?[1-9]\d?$", lt):
                    continue
                if hdr_pat and re.match(
                    rf"^(?:#+\s*)?(?:{hdr_pat})$", lt, re.IGNORECASE
                ):
                    continue

            m_fig = re.match(
                r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Fig(?:ure)?\.?\s*(\d+)[\.\-](\d+[a-z]?)\.?(?:\*\*)?\s*$",
                lt,
                re.IGNORECASE,
            )
            if m_fig:
                fid = f"{m_fig.group(1)}_{m_fig.group(2)}"
                if fid not in seen_figs_on_page:
                    seen_figs_on_page.add(fid)
                    cap = f"Fig. {m_fig.group(1)}.{m_fig.group(2)}"
                    if non_empty_so_far <= 2:
                        top_figs.append((fid, cap))
                    else:
                        bot_figs.append((fid, cap))
                continue

            m_sec = re.match(r"^(?:#+\s*|\*\*)?(\d+\.\d+)\s+([^\*\n]+?)(?:\*\*)?$", lt)
            if m_sec and m_sec.group(1) in self.spec.sections:
                sec_id = m_sec.group(1)
                start_p, canon_title = self.spec.sections[sec_id]
                if pno == start_p:
                    body_lines.append(f"## {sec_id} {canon_title}")
                    continue
                elif non_empty_so_far <= 3:
                    continue

            m_sub = re.match(
                r"^(?:#+\s*|\*\*)?([a-e])\.\s+([A-Z][A-Za-z0-9\s\-,'\(\)]{2,60}?)(?:\*\*)?\.?$",
                lt,
            )
            if m_sub and len(lt) < 72:
                body_lines.append(f"### {m_sub.group(1)}. {m_sub.group(2).strip()}")
                continue

            body_lines.append(l)

        s = "\n".join(body_lines).strip()

        s = re.sub(
            r"\\tag\{\(?(\d+)\.(\d+[a-z']?)\)?\}",
            rf"\\tag{{{pno}-\1-\2}}",
            s,
        )
        s = re.sub(
            r"\$\$(.*?)\$\$\s*\((\d+)\.(\d+[a-z']?)\)",
            rf"\n\n$$\n\1\n$$ <eq-{pno}-\2-\3>\n\n",
            s,
            flags=re.DOTALL,
        )
        s = re.sub(
            r"\\\[(.*?)\\\]\s*\((\d+)\.(\d+[a-z']?)\)",
            rf"\n\n$$\n\1\n$$ <eq-{pno}-\2-\3>\n\n",
            s,
            flags=re.DOTALL,
        )
        s = re.sub(
            r"\$\$(.*?)\\hfill\s*\((\d+)\.(\d+[a-z']?)\)\s*\$\$",
            rf"\n\n$$\n\1\n$$ <eq-{pno}-\2-\3>\n\n",
            s,
            flags=re.DOTALL,
        )
        s = re.sub(
            r"\$\$(.*?)(?:\\qquad|\\quad)\s*\((\d+)\.(\d+[a-z']?)\)\s*\$\$",
            rf"\n\n$$\n\1\n$$ <eq-{pno}-\2-\3>\n\n",
            s,
            flags=re.DOTALL,
        )
        s = re.sub(
            r"\$\$(.*?)\\tag\{([0-9a-zA-Z'-]+)\}(.*?)\$\$",
            r"\n\n$$\n\1\3\n$$ <eq-\2>\n\n",
            s,
            flags=re.DOTALL,
        )
        s = re.sub(r"\\tag\{[^{}]*\}", "", s)
        if len(re.findall(r"\$\$", s)) % 2 != 0:
            s = s.rstrip() + "$$"

        return s.strip(), top_figs, bot_figs

    @classmethod
    def stitch_chapter(
        cls,
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
                acc = cls.render_figure_group(all_top_figs, fig_dir) + text
            elif continues_prev:
                first_p, rest_p = split_first_paragraph(text)
                acc = join_cross_page_text(acc, first_p)
                if all_top_figs:
                    acc += cls.render_figure_group(all_top_figs, fig_dir)
                if rest_p:
                    acc += "\n\n" + rest_p
            else:
                if all_top_figs:
                    acc += cls.render_figure_group(all_top_figs, fig_dir)
                acc += "\n\n" + text

            if bot_figs:
                next_starts_lower = (
                    idx + 1 < len(pages_data)
                    and bool(pages_data[idx + 1][1].strip())
                    and pages_data[idx + 1][1].lstrip()[0].islower()
                )
                if ends_complete_paragraph(acc) and not next_starts_lower:
                    acc += cls.render_figure_group(bot_figs, fig_dir)
                else:
                    pending_figs.extend(bot_figs)

        if pending_figs:
            acc += cls.render_figure_group(pending_figs, fig_dir)

        return acc

    @staticmethod
    def format_typst(s: str) -> str:
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

        s = re.sub(r"^#{4,6}\s+(.*?)$", r"==== \1", s, flags=re.MULTILINE)
        s = re.sub(r"^###\s+([a-e]\.\s+.*?)$", r"=== \1", s, flags=re.MULTILINE)
        s = re.sub(r"^##\s+(\d+\.\d+\s+.*?)$", r"== \1", s, flags=re.MULTILINE)
        s = re.sub(r"^###\s+(.*?)$", r"=== \1", s, flags=re.MULTILINE)
        s = re.sub(r"^##\s+(.*?)$", r"== \1", s, flags=re.MULTILINE)
        s = re.sub(r"^#\s+(.*?)$", r"= \1", s, flags=re.MULTILINE)

        s = (
            s.replace('f"', "f''")
            .replace('w"', "w''")
            .replace('z"', "z''")
            .replace('y"', "y''")
            .replace('g"', "g''")
        )
        s = s.replace(r"\leqq", "<=").replace(r"\geqq", ">=")

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

        cleaned_lines: list[str] = []
        for line in s.splitlines():
            if line.count("$") % 2 != 0:
                line = re.sub(r"(?<!\$)\$(?!\$)", "", line, count=1)
            cleaned_lines.append(line)
        s = "\n".join(cleaned_lines)

        inline_blocks: list[str] = []
        prose_re = re.compile(
            r"differential|equations|functions|polynomial|converges|identically|"
            r"derivative|continuous|condition|sufficient|necessary|arbitrary|"
            r"original|equation|type|ordinary|point|removable|singularity|coefficients|"
            r"holomorphic|meromorphic|neighborhood|connected|compact",
            re.IGNORECASE,
        )

        def save_inline(m: re.Match[str]) -> str:
            code = m.group(1)
            if prose_re.search(code) and "\\" not in code:
                clean_w = code.replace('"', "").strip()
                return f" {clean_w} "
            idx = len(inline_blocks)
            inline_blocks.append(code)
            return f"@@INLINEMATH{idx}@@"

        s = re.sub(r"\$([^$\n]+)\$", save_inline, s)

        s = re.sub(r"(?<![=\s])#", r"\#", s)
        s = re.sub(r"^\s*#", r"\#", s, flags=re.MULTILINE)
        s = re.sub(r"<(?!eq-|fig-|sec-)", r"\< ", s)
        s = re.sub(r"^\s*/\s*", r"\/ ", s, flags=re.MULTILINE)
        s = s.replace("*/", "* /")

        s = re.sub(r"^(\s*)\*(?=\d+\.)", r"\1\\*", s, flags=re.MULTILINE)
        s = re.sub(
            r"\*\*((?:(?!\n\n|@@DISPLAYBLOCK)[^\*])+?)\*\*",
            r"#strong[\1]",
            s,
        )
        s = re.sub(
            r"(?<![\\\*])\*((?:(?!\n\n|@@DISPLAYBLOCK)[^\*])+?)\*(?!\*)",
            r"#emph[\1]",
            s,
        )
        s = re.sub(r"(?<!\\)\*", r"\\*", s)
        s = re.sub(r"(?<![a-zA-Z0-9])_(?![a-zA-Z0-9])", r"\\_", s)
        s = s.replace(r"\cdots", "...").replace(r"\ldots", "...")

        s = re.sub(r"(@@INLINEMATH\d+@@)\s+([.,;:?!\)])", r"\1\2", s)
        s = re.sub(r"(\()\s+(@@INLINEMATH\d+@@)", r"\1\2", s)

        s = re.sub(
            r"@@INLINEMATH(\d+)@@",
            lambda m: (
                f"${sanitize_math_code(inline_blocks[int(m.group(1))], is_display=False)}$"
            ),
            s,
        )

        def restore_display(m: re.Match[str]) -> str:
            body, label = display_blocks[int(m.group(1))]
            clean_body = sanitize_math_code(body, is_display=True)
            return f"\n$ {clean_body} $ {label}\n"

        s = re.sub(r"@@DISPLAYBLOCK(\d+)@@", restore_display, s)
        s = re.sub(r"@@FIGBLOCK(\d+)@@", lambda m: fig_blocks[int(m.group(1))], s)
        return s

    @staticmethod
    def format_index(md_dir: Path, start_p: int, end_p: int) -> str:
        entries: list[str] = []
        for pno in range(start_p, end_p + 1):
            p_file = md_dir / f"p_{pno:03d}.md"
            if not p_file.exists():
                continue
            for raw_line in p_file.read_text(encoding="utf-8").splitlines():
                lt = raw_line.strip()
                if not lt:
                    continue
                if re.match(r"^(?:#+\s*)?Index$", lt, re.IGNORECASE):
                    continue
                if re.match(
                    r"^\d{1,3}\s+Index$|^Index\s+\d{1,3}$|^\d{1,3}$",
                    lt,
                    re.IGNORECASE,
                ):
                    continue
                line_clean = lt.replace('"', "''").replace("#", r"\#")
                line_clean = re.sub(r"\*([^\*]+)\*", r"#emph[\1]", line_clean)
                line_clean = clean_margin_and_inline_math(line_clean)
                entries.append(line_clean)

        joined = "\n\n".join(entries)
        return (
            "\n= Index\n\n"
            "#columns(2, gutter: 1.8em)[\n"
            "  #set text(size: 9pt)\n"
            "  #set par(first-line-indent: 0pt, hanging-indent: 1.2em, leading: 0.52em, spacing: 0.48em, justify: false)\n"
            f"  {joined}\n"
            "]\n"
        )

    def build_all(self, out_dir: Path) -> MonographOutputs:
        out_dir = Path(out_dir)
        md_dir = out_dir / "markdown_pages"
        fig_dir = out_dir / "figures"

        md_sections: list[str] = [
            (
                "---\n"
                f'title: "{self.spec.title}"\n'
                f'author: "{self.spec.author}"\n'
                f'translator: "{self.spec.translator}"\n'
                f'editor: "{self.spec.editor}"\n'
                f'publisher: "{self.spec.publisher}"\n'
                f"year: {self.spec.year}\n"
                "---\n\n"
                f"# {self.spec.title}\n\n"
                f"**{self.spec.author}**  \n"
                f"**{self.spec.publisher}**\n"
            )
        ]

        typst_sections: list[str] = [
            self.build_typst_preamble(),
            self.build_typst_title_page(),
        ]

        if self.spec.preface_page is not None:
            pref_file = md_dir / f"p_{self.spec.preface_page:03d}.md"
            if pref_file.exists():
                pref_raw = pref_file.read_text(encoding="utf-8")
                pref_body, _, _ = self.extract_page_parts(
                    pref_raw, self.spec.preface_page
                )
                pref_body = re.sub(
                    r"^(?:#+\s*)?Preface\s*\n+", "", pref_body, flags=re.IGNORECASE
                ).strip()
                md_sections.append(f"\n## Preface\n\n{pref_body}\n")
                typst_sections.append(
                    "\n= Preface\n\n"
                    + self.format_typst(pref_body)
                    + "\n#pagebreak(weak: true)\n"
                )

        for chap in self.spec.chapters:
            pages_data: list[
                tuple[int, str, list[tuple[str, str]], list[tuple[str, str]]]
            ] = []
            ch_md_pages: list[str] = [f"\n# Chapter {chap.number}: {chap.title}\n"]

            for pno in range(chap.start_page, chap.end_page + 1):
                p_file = md_dir / f"p_{pno:03d}.md"
                if not p_file.exists():
                    continue
                raw_text = p_file.read_text(encoding="utf-8").strip()
                if (
                    len(raw_text) < 20
                    or "1.1.1.1.1" in raw_text
                    or "musical compositions" in raw_text
                ):
                    continue
                p_body, top_f, bot_f = self.extract_page_parts(raw_text, pno)
                pages_data.append((pno, p_body, top_f, bot_f))

                md_page = p_body
                for fid, cap in top_f:
                    if (fig_dir / f"fig_{fid}.png").exists():
                        md_page = f"![{cap}](figures/fig_{fid}.png)\n\n" + md_page
                for fid, cap in bot_f:
                    if (fig_dir / f"fig_{fid}.png").exists():
                        md_page = md_page + f"\n\n![{cap}](figures/fig_{fid}.png)"
                ch_md_pages.append(md_page)

            md_sections.append("\n\n".join(ch_md_pages))
            stitched = self.stitch_chapter(pages_data, fig_dir)
            formatted = self.format_typst(stitched)
            typst_sections.append(f"\n= {chap.number} {chap.title}\n\n" + formatted)
            typst_sections.append("\n#pagebreak(weak: true)\n")

        if self.spec.problems_pages is not None:
            prob_start, prob_end = self.spec.problems_pages
            prob_pages: list[
                tuple[int, str, list[tuple[str, str]], list[tuple[str, str]]]
            ] = []
            prob_md: list[str] = ["\n# Problems\n"]
            for pno in range(prob_start, prob_end + 1):
                p_file = md_dir / f"p_{pno:03d}.md"
                if p_file.exists():
                    raw_text = p_file.read_text(encoding="utf-8").strip()
                    p_body, top_f, bot_f = self.extract_page_parts(raw_text, pno)
                    p_body = re.sub(
                        r"^(?:#+\s*)?Problems\s*\n+", "", p_body, flags=re.IGNORECASE
                    ).strip()
                    prob_pages.append((pno, p_body, top_f, bot_f))
                    prob_md.append(p_body)
            if prob_pages:
                md_sections.append("\n\n".join(prob_md))
                stitched_prob = self.stitch_chapter(prob_pages, fig_dir)
                typst_sections.append(
                    "\n= Problems\n\n"
                    + self.format_typst(stitched_prob)
                    + "\n#pagebreak(weak: true)\n"
                )

        if self.spec.references_page is not None:
            ref_file = md_dir / f"p_{self.spec.references_page:03d}.md"
            if ref_file.exists():
                ref_raw = ref_file.read_text(encoding="utf-8").strip()
                ref_body, _, _ = self.extract_page_parts(
                    ref_raw, self.spec.references_page
                )
                ref_body = re.sub(
                    r"^(?:#+\s*)?References\s*\n+", "", ref_body, flags=re.IGNORECASE
                ).strip()
                md_sections.append(f"\n# References\n\n{ref_body}\n")
                typst_sections.append(
                    "\n= References\n\n"
                    + self.format_typst(ref_body)
                    + "\n#pagebreak(weak: true)\n"
                )

        if self.spec.index_pages is not None:
            idx_start, idx_end = self.spec.index_pages
            typst_sections.append(self.format_index(md_dir, idx_start, idx_end))

        full_md = "\n\n".join(md_sections)
        md_out = out_dir / f"{self.spec.slug}.md"
        md_book = out_dir / "book.md"
        _ = md_out.write_text(full_md, encoding="utf-8")
        if md_out != md_book:
            _ = shutil.copy2(md_out, md_book)

        full_typ = "\n".join(typst_sections)
        typ_out = out_dir / f"{self.spec.slug}.typ"
        typ_book = out_dir / "book.typ"
        _ = typ_out.write_text(full_typ, encoding="utf-8")
        if typ_out != typ_book:
            _ = shutil.copy2(typ_out, typ_book)

        tex_out = out_dir / f"{self.spec.slug}.tex"
        tex_book = out_dir / "book.tex"
        _ = subprocess.run(
            [
                "pandoc",
                str(md_out),
                "-f",
                "markdown+tex_math_dollars+raw_tex",
                "-t",
                "latex",
                "-s",
                "--top-level-division=chapter",
                "-V",
                "documentclass=book",
                "-V",
                "geometry:paperwidth=6.14in,paperheight=9.21in,margin=0.78in",
                "-o",
                str(tex_out),
            ],
            check=True,
        )
        if tex_out != tex_book:
            _ = shutil.copy2(tex_out, tex_book)

        pdf_out = out_dir / f"{self.spec.slug}.pdf"
        pdf_book = out_dir / "book.pdf"
        _ = subprocess.run(
            [
                "nix",
                "shell",
                "nixpkgs#typst",
                "--command",
                "typst",
                "compile",
                str(typ_out),
                str(pdf_out),
            ],
            check=True,
        )
        if pdf_out != pdf_book:
            _ = shutil.copy2(pdf_out, pdf_book)

        doc = pymupdf.open(str(pdf_out))
        return MonographOutputs(
            markdown_path=md_out,
            latex_path=tex_out,
            typst_path=typ_out,
            pdf_path=pdf_out,
            total_pages=len(doc),
        )
