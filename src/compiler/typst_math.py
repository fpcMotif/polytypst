"""LaTeX-to-Typst math conversion shared by every monograph build."""

import functools
import re
import subprocess
from re import Pattern

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
    "eq",
    "neq",
    "cont",
    "down",
    "t",
    "b",
    "tr",
    "br",
    "bl",
    "tl",
    "prec",
    "succ",
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
    "lr",
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
        if s[i] == "{" and s[i - 1] != "\\":
            depth += 1
        elif s[i] == "}" and s[i - 1] != "\\":
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
            rad_clean = convert_latex_sqrt(rad).strip()
            res.append(f" sqrt({rad_clean if rad_clean else 'quad'}) ")
            pos = end_pos
        else:
            res.append(" sqrt(quad) ")
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
    s = re.sub(r"(?<![\\a-zA-Z0-9_\^])d\s*([xyztuvwsr])(?![a-zA-Z0-9])", r" dif \1", s)
    s = BARE_UNARY_ARG_RE.sub(r"\1{\2}", s)
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
ENV_ALIGNED_RE = re.compile(
    r"\\(?:begin|end)\{(?:aligned|align|split|gather| multline)\*?\}"
)
MAT_CELL_LABEL_RE = re.compile(r"(^|[;,]\s*)(\\?[a-zA-Z_][a-zA-Z0-9_]*)\s*:")


def _guard_mat_cell_labels(body: str) -> str:
    return MAT_CELL_LABEL_RE.sub(r"\1(\2):", body)


def convert_environments(code: str) -> str:
    if "begin" not in code:
        return code
    code = re.sub(r"\\\s+(begin|end)\b", r"\\\1", code)
    code = ENV_VMATRIX_ARRAY_RE.sub(r"\\begin{vmatrix}\1\\end{vmatrix}", code)
    code = re.sub(r"\\left\s*\(\s*\\begin\{array\}\{[^}]*\}", r"\\begin{pmatrix}", code)
    code = re.sub(r"\\end\{array\}\s*\\right\s*\)", r"\\end{pmatrix}", code)
    code = re.sub(r"\\begin\{array\}\{[^}]*\}", r"\\begin{matrix}", code)
    code = re.sub(r"\\end\{array\}", r"\\end{matrix}", code)

    def repl_matrix(m: re.Match[str]) -> str:
        env = m.group(1)
        body = m.group(2).strip()
        delim = (
            '"|"'
            if env in ("vmatrix", "Vmatrix")
            else ('"["' if env == "bmatrix" else '"("')
        )
        rows = re.split(r"\\\\", body)
        out_rows: list[str] = []
        for r in rows:
            r_clean = re.sub(r"&\.\s*", "& ", r.strip())
            if not r_clean:
                continue
            cells = [c.strip() for c in r_clean.split("&")]
            safe_cells = [re.sub(r",\s*", ' "," ', c) for c in cells]
            out_rows.append(", ".join(safe_cells))
        cells = _guard_mat_cell_labels("; ".join(out_rows))
        return f"mat(delim: {delim}, {cells})"

    code = ENV_MATRIX_RE.sub(repl_matrix, code)

    def repl_cases(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        rows: list[str] = []
        for r in re.split(r"\\\\", body):
            r_clean = r.strip()
            if not r_clean:
                continue
            parts = [
                p.strip().rstrip(",").strip() for p in r_clean.split("&") if p.strip()
            ]
            rows.append(" quad ".join(parts))
        return "cases(" + ", ".join(rows) + ")"

    code = ENV_CASES_RE.sub(repl_cases, code)

    def repl_array(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
        if len(rows) == 1:
            cells = [c.strip() for c in rows[0].split("&")]
            return " quad ".join(cells)
        out_rows = [", ".join(c.strip() for c in r.split("&")) for r in rows]
        return "mat(" + _guard_mat_cell_labels("; ".join(out_rows)) + ")"

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


def _is_variable_product(m: re.Match[str]) -> bool:
    """A two-letter word like `if` or `by` that is applied or follows an operator is a product."""
    if len(m.group(0)) != 2:
        return False
    before = m.string[: m.start()].rstrip()
    after = m.string[m.end() :]
    return after.startswith("(") or before.endswith(("+", "-", "=", "(", "^", "_"))


LEFT_RIGHT_ABS_RE = re.compile(r"\\left\s*\|((?:(?!\\left|\\right)[^|])+?)\\right\s*\|")
BIG_ABS_RE = re.compile(r"\\[bB]igg?l\s*\|([^|]+?)\\[bB]igg?r\s*\|")


def _abs_call(m: re.Match[str]) -> str:
    inner = m.group(1).strip()
    return f" lr(| {inner} |) " if "," in inner else f" abs({inner}) "


@functools.lru_cache(maxsize=8192)
def sanitize_math_code(code: str, is_display: bool = False) -> str:
    code = re.sub(r"\\tag\{[^{}]*\}", "", code)
    code = re.sub(r"\\[\u4e00-\u9fff]", "", code)
    code = re.sub(r"\(\s*\\(?=[\s\)\]])\s*", "(", code)
    code = re.sub(r"\s*\\\s*\)", ")", code)
    code = convert_environments(code)
    if is_display:
        multi_row = bool(re.search(r"\\\\", code))
        code = re.sub(r"\\\\\s*", " \\\n  ", code)
        if multi_row:
            code = re.sub(r"[ \t]*&[ \t]*", " &", code)
        else:
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
        .replace(r"\uparrow", " arrow.t ")
        .replace(r"\downarrow", " arrow.b ")
        .replace(r"\updownarrow", " arrow.t.b ")
        .replace(r"\Uparrow", " arrow.t.double ")
        .replace(r"\Downarrow", " arrow.b.double ")
        .replace(r"\nearrow", " arrow.tr ")
        .replace(r"\searrow", " arrow.br ")
        .replace(r"\swarrow", " arrow.bl ")
        .replace(r"\nwarrow", " arrow.tl ")
        .replace(r"\colon", ": ")
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
    code = re.sub(r"\\prec(?![a-zA-Z])", " prec ", code)
    code = re.sub(r"\\succ(?![a-zA-Z])", " succ ", code)
    code = re.sub(r"\\preceq(?![a-zA-Z])", " prec.eq ", code)
    code = re.sub(r"\\succeq(?![a-zA-Z])", " succ.eq ", code)
    code = re.sub(r"\\sim(?![a-zA-Z])", " tilde.op ", code)
    code = re.sub(r"\\simeq(?![a-zA-Z])", " tilde.eq ", code)
    code = re.sub(r"\\cong(?![a-zA-Z])", " tilde.equiv ", code)
    code = re.sub(r"\\(?:lVert|rVert|Vert)(?![a-zA-Z])", r"\|", code)
    if r"\|" in code:
        code = re.sub(
            r"\\\|\s*([^|\n]+?)\s*\\\|",
            lambda m: (
                f" lr(|| {m.group(1)} ||) "
                if "," in m.group(1)
                else f" norm({m.group(1)}) "
            ),
            code,
        )
        code = code.replace(r"\|", " || ")
    code = LEFT_RIGHT_ABS_RE.sub(_abs_call, code)
    code = BIG_ABS_RE.sub(_abs_call, code)
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
        if t.lower() in ENGLISH_WORDS and not _is_variable_product(m):
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
        seg = MULTI_TOK_RE.sub(fix_tok, segments[idx])
        if (
            "|" in seg
            and seg.count("|") % 2 == 0
            and "||" not in seg
            and " | " not in seg
        ):
            seg = re.sub(
                r"\|([^|\n]+?)\|",
                lambda m: (
                    f" lr(| {m.group(1)} |) "
                    if "," in m.group(1)
                    else f" abs({m.group(1)}) "
                ),
                seg,
            )
        segments[idx] = seg
    code = "".join(segments)

    code = normalize_differentials(code)

    code = re.sub(r"_([a-zA-Z0-9]+)\(", r"_(\1)(", code)
    code = re.sub(r"\^([a-zA-Z0-9]+)\(", r"^(\1)(", code)
    code = re.sub(r"(_(?:\([^\)]+\)|[a-zA-Z0-9]+))('+)", r"\2\1", code)
    code = re.sub(
        r"([a-zA-Z0-9_']+\([^\(\)]+\))\s*/\s*([a-zA-Z0-9_']+\([^\(\)]+\))",
        r"\1 \/ \2",
        code,
    )
    code = re.sub(r"\bsqrt\(\s*\)", "sqrt(quad)", code)
    code = re.sub(r"\s+([,\.\:\;])", r"\1", code)

    unquoted = re.sub(r'"[^"]*"', "", code)
    open_p = unquoted.count("(")
    close_p = unquoted.count(")")
    if open_p > close_p:
        code += ")" * (open_p - close_p)
    elif close_p > open_p:
        code = ("(" * (close_p - open_p)) + code
    return code.strip()


PANDOC_SEPARATOR = "PTSEPARATOR"
PANDOC_SPLIT_RE = re.compile(rf"\n\s*{PANDOC_SEPARATOR}\s*\n")
TOP_LEVEL_ENV_RE = re.compile(
    r"^\s*\\begin\{([a-zA-Z*]+)\}.*\\end\{\1\}\s*$", re.DOTALL
)
OPERATOR_STRING_RE = re.compile(r'(?<![\w(])"([A-Za-z]{2,})"')
UPRIGHT_LETTERS_RE = re.compile(r"upright\(((?:[A-Za-z] )+[A-Za-z])\)")
ESCAPED_BAR_RE = re.compile(r"\\\|")
ESCAPED_DELIM_RE = re.compile(r"\\([()\[\]])")
LATEX_MACRO_REWRITES: tuple[tuple[Pattern[str], str], ...] = (
    (re.compile(r"\\tag\*?\{[^{}]*\}"), ""),
    (re.compile(r"\\(?:nonumber|notag|displaystyle|textstyle)(?![a-zA-Z])"), ""),
    (re.compile(r"\\varprojlim"), r"\\underset{\\longleftarrow}{\\lim}"),
    (re.compile(r"\\varinjlim"), r"\\underset{\\longrightarrow}{\\lim}"),
    (re.compile(r"\\leqq(?![a-zA-Z])"), r"\\leq"),
    (re.compile(r"\\geqq(?![a-zA-Z])"), r"\\geq"),
    (re.compile(r"\\setminus(?![a-zA-Z])"), r"\\backslash"),
    (re.compile(r"\\longrightarrow(?![a-zA-Z])"), "⟶"),
    (re.compile(r"\\longleftarrow(?![a-zA-Z])"), "⟵"),
    (re.compile(r"\\longleftrightarrow(?![a-zA-Z])"), "⟷"),
    (re.compile(r"\\longmapsto(?![a-zA-Z])"), "⟼"),
    (re.compile(r"\\Longrightarrow(?![a-zA-Z])"), "⟹"),
    (re.compile(r"\\Longleftarrow(?![a-zA-Z])"), "⟸"),
    (re.compile(r"\\Longleftrightarrow(?![a-zA-Z])"), "⟺"),
    (re.compile(r"\\\s+(begin|end)\b"), r"\\\1"),
    (re.compile(r"\\\s+Right\b"), r"\\right"),
    (re.compile(r"\\\s+Left\b"), r"\\left"),
    (
        re.compile(
            rf"\\ +(?=(?:var)?(?:{GREEK_WORDS}|equiv|cong|approx|sim|to|mapsto|in|notin|subset|supset|cup|cap|times|cdot|le|ge|leq|geq|neq|pm|mp|mid|left|right|Big|big)(?![a-zA-Z]))"
        ),
        "\\\\",
    ),
    (re.compile(r"[\"“”]"), r"\\text{”}"),
    (re.compile(r"(?<=[(\[|])\s*\\ \s*"), ""),
    (re.compile(r"\s*\\ \s*(?=[)\]|])"), ""),
)
_PANDOC_CACHE: dict[tuple[str, bool], str] = {}


def _balance_left_right(row: str) -> str:
    """Close a `\\left` or open a `\\right` that the OCR split onto another row."""
    lefts = len(re.findall(r"\\left(?![a-zA-Z])", row))
    rights = len(re.findall(r"\\right(?![a-zA-Z])", row))
    if lefts > rights:
        return row + r" \right." * (lefts - rights)
    if rights > lefts:
        return r"\left. " * (rights - lefts) + row
    return row


def _fix_single_col_cases(m: re.Match[str]) -> str:
    body = m.group(1)
    if "&" in body:
        return m.group(0)
    rows = [f"{r.strip()} &" for r in re.split(r"\\\\", body) if r.strip()]
    return r"\begin{cases} " + r" \\ ".join(rows) + r" \end{cases}"


def _unescape_balanced_delims_line(line: str) -> str:
    matches = list(ESCAPED_DELIM_RE.finditer(line))
    if not matches:
        return line
    stack: list[tuple[str, int]] = []
    unescape_indices: set[int] = set()
    pairs = {")": "(", "]": "["}
    for idx, m in enumerate(matches):
        ch = m.group(1)
        if ch in ("(", "["):
            stack.append((ch, idx))
        elif stack and stack[-1][0] == pairs[ch]:
            _, open_idx = stack.pop()
            unescape_indices.add(open_idx)
            unescape_indices.add(idx)
        else:
            stack.clear()
    if not unescape_indices:
        return line
    out: list[str] = []
    pos = 0
    for idx, m in enumerate(matches):
        out.append(line[pos : m.start()])
        out.append(m.group(1) if idx in unescape_indices else m.group(0))
        pos = m.end()
    out.append(line[pos:])
    return "".join(out)


def prepare_latex_math(code: str, is_display: bool) -> str:
    """Normalize OCR LaTeX so that Pandoc's TeX math reader accepts it."""
    code = code.strip()
    for pattern, repl in LATEX_MACRO_REWRITES:
        code = pattern.sub(repl, code)
    code = ENV_CASES_RE.sub(_fix_single_col_cases, code)
    code = re.sub(r"\n\s*\n", "\n", code).strip()
    if not is_display:
        if r"\begin{" not in code:
            return re.sub(r"\\\\(?:\[[^\]]*\])?", r" \\quad ", code)
        return code
    if r"\\" not in code or TOP_LEVEL_ENV_RE.match(code):
        return _balance_left_right(code)
    rows = [
        _balance_left_right(r.strip()) for r in re.split(r"\\\\", code) if r.strip()
    ]
    env = "aligned" if any("&" in r for r in rows) else "gathered"
    return rf"\begin{{{env}}}" + r" \\ ".join(rows) + rf"\end{{{env}}}"


def _is_balanced(text: str) -> bool:
    depth = {"{": 0, "(": 0}
    closer = {"}": "{", ")": "("}
    for ch in text:
        if ch in depth:
            depth[ch] += 1
        elif ch in closer:
            depth[closer[ch]] -= 1
            if depth[closer[ch]] < 0:
                return False
    return all(d == 0 for d in depth.values())


def _pair_escaped_bars(body: str) -> str:
    bars = [m.start() for m in ESCAPED_BAR_RE.finditer(body)]
    out: list[str] = []
    cursor = 0
    k = 0
    while k + 1 < len(bars):
        a, b = bars[k], bars[k + 1]
        inner = body[a + 2 : b]
        closes_ok = body[b + 2 : b + 3] not in ("_", "^")
        opens_ok = body[a + 2 : a + 3] not in ("_", "^")
        if (
            opens_ok
            and closes_ok
            and inner.strip()
            and len(inner) <= 62
            and "\n" not in inner
            and _is_balanced(inner)
        ):
            out.append(body[cursor:a])
            out.append(f"abs({inner.strip()})")
            cursor = b + 2
            k += 2
        else:
            k += 1
    out.append(body[cursor:])
    return "".join(out)


def polish_pandoc_math(body: str) -> str:
    """Prefer Typst operator and symbol spellings over Pandoc's literal choices."""
    body = re.sub(r"#hide\[\s*=", r"#hide[\\=", body)
    body = OPERATOR_STRING_RE.sub(r'op("\1")', body)
    body = UPRIGHT_LETTERS_RE.sub(
        lambda m: f'op("{m.group(1).replace(" ", "")}")', body
    )
    body = re.sub(r'upright\("\s+([^"]+?)\s+"\)', r'med upright("\1") med', body)
    body = re.sub(r'upright\("\s+([^"]+?)"\)', r'med upright("\1")', body)
    body = re.sub(r'upright\("([^"]+?)\s+"\)', r'upright("\1") med', body)
    body = re.sub(r"(?<!\\);(?=\s*\))", r"\\;", body)
    unsubscripted_bars = len(re.findall(r"\\\|(?![_^])", body))
    if unsubscripted_bars % 2 == 0 and unsubscripted_bars > 0:
        body = _pair_escaped_bars(body)
    body = re.sub(r"\bsqrt\(\s*\)", "sqrt(med)", body)
    body = re.sub(r"\bangle\.([lr])\b", r"chevron.\1", body)
    body = re.sub(r"\bsect(?![A-Za-z0-9])", "inter", body)
    body = re.sub(r"\bdiff(?![A-Za-z0-9])", "partial", body)
    body = re.sub(r"\bxor\.big(?![A-Za-z0-9])", "plus.o.big", body)
    body = re.sub(r"\bxor(?![A-Za-z0-9.])", "plus.o", body)
    body = re.sub(r"\b(plus|minus|times|dot|div)\.circle\b", r"\1.o", body)
    body = re.sub(
        r"\b(arrow\.(?:r|l|l\.r)(?:\.double)?)(?:\.long)?([\^_])",
        r"limits(\1.long)\2",
        body,
    )
    return "\n".join(_unescape_balanced_delims_line(line) for line in body.splitlines())


def _run_pandoc_math(items: list[tuple[str, bool]]) -> list[str | None]:
    parts: list[str] = []
    for code, is_display in items:
        prepared = prepare_latex_math(code, is_display)
        parts.append(f"$${prepared}$$" if is_display else f"${prepared}$")
    source = f"\n\n{PANDOC_SEPARATOR}\n\n".join(parts)
    try:
        res = subprocess.run(
            ["pandoc", "-f", "markdown", "-t", "typst", "--wrap=none"],
            input=source,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return [None] * len(items)
    chunks = PANDOC_SPLIT_RE.split("\n" + res.stdout.strip() + "\n")
    chunks = [c.strip() for c in chunks]
    if len(chunks) != len(items):
        return [None] * len(items)
    out: list[str | None] = []
    for chunk in chunks:
        if len(chunk) >= 2 and chunk.startswith("$") and chunk.endswith("$"):
            out.append(polish_pandoc_math(chunk[1:-1].strip()))
        else:
            out.append(None)
    return out


def convert_math_batch(items: list[tuple[str, bool]]) -> list[str]:
    """Convert (LaTeX, is_display) snippets to Typst math bodies in one Pandoc run.

    A snippet that Pandoc rejects falls back to the regex sanitizer.
    """
    todo = list(dict.fromkeys(k for k in items if k not in _PANDOC_CACHE))
    if todo:
        for key, converted in zip(todo, _run_pandoc_math(todo), strict=True):
            if converted is None:
                converted = sanitize_math_code(key[0], is_display=key[1])
                converted = converted.replace("plus.circle", "plus.o")
                if converted.count('"') % 2:
                    converted = converted.replace('"', "")
            _PANDOC_CACHE[key] = converted
    return [_PANDOC_CACHE[k] for k in items]


def clean_margin_and_inline_math(text: str) -> str:
    parts = text.split("$")
    odd = list(range(1, len(parts), 2))
    converted = convert_math_batch([(parts[i], False) for i in odd])
    for i, body in zip(odd, converted, strict=True):
        parts[i] = body
    return "$".join(parts)
