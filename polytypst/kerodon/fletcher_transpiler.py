r"""Transpile LaTeX \xymatrix commutative diagrams into native Typst Fletcher diagrams."""

import re


def extract_balanced(s: str, open_ch: str = "{", close_ch: str = "}", start: int = 0) -> tuple[str, int]:
    """Extract content within balanced delimiters starting at or after `start`."""
    idx = s.find(open_ch, start)
    if idx == -1:
        return "", start
    depth = 0
    start_pos = idx
    for i in range(idx, len(s)):
        if s[i] == open_ch:
            depth += 1
        elif s[i] == close_ch:
            depth -= 1
            if depth == 0:
                return s[start_pos + 1 : i], i + 1
    return s[start_pos + 1 :], len(s)


def split_top_level(s: str, delim: str) -> list[str]:
    """Split string by delimiter only outside of curly braces."""
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    i = 0
    n = len(s)
    d_len = len(delim)
    while i < n:
        if s[i] == "{":
            depth += 1
            cur.append(s[i])
            i += 1
        elif s[i] == "}":
            depth = max(0, depth - 1)
            cur.append(s[i])
            i += 1
        elif depth == 0 and s[i : i + d_len] == delim:
            parts.append("".join(cur).strip())
            cur = []
            i += d_len
        else:
            cur.append(s[i])
            i += 1
    if cur:
        parts.append("".join(cur).strip())
    return parts


def tex_to_typst_label(s: str) -> str:
    """Convert LaTeX math fragments into clean Typst math syntax."""
    s = s.strip()
    if not s:
        return ""

    s = re.sub(r"\\raise\s*\{[^}]*\}\s*\{\s*\\square\s*\}", " square ", s)
    s = re.sub(r"raise\s*\{[^}]*\{\s*square\s*\}\s*\}", " square ", s)
    s = re.sub(r"\\(?:left|right)\b", "", s)
    s = re.sub(r"\\raise\s*\{[^}]*\}", "", s)

    # Balanced \underset
    while r"\underset" in s:
        idx = s.find(r"\underset")
        arg1, pos1 = extract_balanced(s, "{", "}", idx + 7)
        arg2, pos2 = extract_balanced(s, "{", "}", pos1)
        arg1_clean = tex_to_typst_label(arg1)
        arg2_clean = tex_to_typst_label(arg2)
        if any(w in arg2 for w in ["coprod", "amalg"]):
            repl = f" \\u{{2210}}_({arg1_clean}) "
        else:
            repl = f" {arg2_clean}_({arg1_clean}) "
        s = s[:idx] + repl + s[pos2:]

    # Balanced \underline
    while r"\underline" in s:
        idx = s.find(r"\underline")
        arg, pos = extract_balanced(s, "{", "}", idx + 10)
        s = s[:idx] + f" underline({arg.strip()}) " + s[pos:]

    # Balanced unwrappers for \operatorname, \mathrm, \mathit
    for macro in [r"\operatorname", r"\mathrm", r"\mathit"]:
        while macro in s:
            idx = s.find(macro)
            arg, pos = extract_balanced(s, "{", "}", idx + len(macro))
            s = s[:idx] + " " + arg.strip() + " " + s[pos:]

    while s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()

    s = re.sub(r"\\operatorname\s*\{\s*\{\s*\\bf\s*\\Delta\s*\}\s*\}", " bold(Delta) ", s)
    s = re.sub(r"\\operatorname\s*\{\s*\\bf\s*\\Delta\s*\}", " bold(Delta) ", s)
    s = re.sub(r"\{\s*\\bf\s*\\Delta\s*\}", " bold(Delta) ", s)
    s = s.replace(r"\mathbf{\Delta}", " bold(Delta) ")
    s = s.replace(r"\mathbf", " bold ")
    s = s.replace(r"\boldsymbol", " bold ")
    s = s.replace(r"\pmb", " bold ")
    s = s.replace(r"\bf", "")

    s = re.sub(r"\\(?:mathcal|mathscr)\s*\{?([A-Za-z])\}?", r" cal(\1) ", s)

    s = s.replace(r"Set_{\Delta }", " Set_Delta ")
    s = s.replace(r"Set_{\Delta}", " Set_Delta ")
    s = s.replace(r"Set_\Delta", " Set_Delta ")
    s = s.replace(r"\partial \Delta", " partial Delta ")
    s = s.replace(r"\partial\Delta", " partial Delta ")

    s = s.replace(r"\Delta", " Delta ")
    s = s.replace(r"\Lambda", " Lambda ")
    s = s.replace(r"\Gamma", " Gamma ")
    s = s.replace(r"\Sigma", " Sigma ")
    s = s.replace(r"\Phi", " Phi ")
    s = s.replace(r"\Pi", " Pi ")
    s = s.replace(r"\delta", " delta ")
    s = s.replace(r"\sigma", " sigma ")
    s = s.replace(r"\pi", " pi ")
    s = s.replace(r"\tau", " tau ")
    s = s.replace(r"\alpha", " alpha ")
    s = s.replace(r"\beta", " beta ")
    s = s.replace(r"\gamma", " gamma ")
    s = s.replace(r"\eta", " eta ")
    s = s.replace(r"\theta", " theta ")
    s = s.replace(r"\iota", " iota ")
    s = s.replace(r"\lambda", " lambda ")
    s = s.replace(r"\mu", " mu ")
    s = s.replace(r"\rho", " rho ")
    s = s.replace(r"\psi", " psi ")
    s = s.replace(r"\zeta", " zeta ")
    s = s.replace(r"\epsilon", " epsilon ")
    s = s.replace(r"\varphi", " phi.alt ")
    s = s.replace(r"\bullet", " bullet ")
    s = s.replace(r"\ast", " ast ")
    s = s.replace(r"\star", " star ")
    s = s.replace(r"\diamond", " diamond ")
    s = re.sub(r"\\?circ(?=[^a-zA-Z]|$)", " circle.small ", s)
    s = s.replace(r"\otimes", " ⊗ ")
    s = s.replace(r"\oplus", " ⊕ ")
    s = s.replace(r"\times", " times ")
    s = s.replace(r"\amalg", r"\u{2210}")
    s = s.replace(r"\coprod", r"\u{2210}")
    s = s.replace(r"\prod", " product ")
    s = s.replace(r"\sqcap", " inter.sq ")
    s = s.replace(r"\sqcup", " union.sq ")
    s = s.replace(r"\square", " square ")

    s = re.sub(r"\\?triangleright(?=[^a-zA-Z]|$)", " triangle.r ", s)
    s = re.sub(r"\\?triangleleft(?=[^a-zA-Z]|$)", " triangle.l ", s)
    s = s.replace(r"\triangle", " triangle ")

    s = s.replace(r"\top", " top ")
    s = s.replace(r"\vee", " or ")
    s = s.replace("hPith", "h Pith")
    s = s.replace(r"\wedge", " and ")
    s = s.replace(r"\emptyset", " nothing ")
    s = s.replace(r"\ell", " ell ")
    s = s.replace(r"\infty", " infinity ")
    s = s.replace(r"\pm", " plus.minus ")
    s = s.replace(r"\simeq", " tilde.eq ")
    s = s.replace(r"\sim", " ~ ")
    s = s.replace(r"\leq", " lt.eq ")
    s = s.replace(r"\geq", " gt.eq ")
    s = s.replace(r"\subset", " subset ")
    s = s.replace(r"\in", " in ")
    s = s.replace(r"\cap", " inter ")
    s = s.replace(r"\cup", " union ")
    s = s.replace(r"\cdots", " ... ")
    s = s.replace(r"\dots", " ... ")

    s = s.replace(r"\Downarrow", " arrow.b.double ")
    s = s.replace(r"\downarrow", " arrow.b ")
    s = s.replace(r"\Uparrow", " arrow.t.double ")
    s = s.replace(r"\uparrow", " arrow.t ")
    s = s.replace(r"\Rightarrow", " arrow.r.double ")
    s = s.replace(r"\Leftarrow", " arrow.l.double ")
    s = s.replace(r"\rightarrow", " arrow.r ")
    s = s.replace(r"\to", " arrow.r ")
    s = re.sub(r"\\?down(?=[^a-zA-Z]|$)", " arrow.b ", s)
    s = s.replace(r"\longleftarrow", " arrow.l.long ")
    s = s.replace(r"\longrightarrow", " arrow.r.long ")
    s = s.replace(r"\mapsto", " arrow.r.bar ")

    s = s.replace(r"\varinjlim", " colim ")
    s = s.replace(r"\varprojlim", " lim ")
    s = s.replace(r"\!", "")
    s = s.replace("BM", "B M")
    s = s.replace(r"\{", "{").replace(r"\}", "}")

    # Mark slice slashes
    s = re.sub(r"(?<=\()\s*/\s*", r"@@SLASH@@ ", s)
    s = re.sub(r"\s*/\s*(?=\))", r" @@SLASH@@", s)
    s = re.sub(r"(?<=_\{)\s*/\s*", r"@@SLASH@@ ", s)
    s = re.sub(r"\s*/\s*(?=\})", r" @@SLASH@@", s)
    s = re.sub(r"(?<=_)\s*/\s*", r"@@SLASH@@ ", s)

    s = re.sub(r"\^\{([^}]+)\}", r"^(\1)", s)
    s = re.sub(r"_\{([^}]+)\}", r"_(\1)", s)
    s = re.sub(r"\\(?:overline|bar)\s*\{([^}]+)\}", r'overline(\1)', s)
    s = re.sub(r"\\(?:widehat|hat)\s*\{([^}]+)\}", r'hat(\1)', s)
    s = re.sub(r"\\(?:widetilde|tilde)\s*\{([^}]+)\}", r'tilde(\1)', s)

    s = s.replace("\\", "")
    s = s.replace("@@SLASH@@", r"\/")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def format_node_label(raw: str) -> str:
    """Format raw node content as either Typst math $...$ or content block [...]."""
    raw = raw.strip()
    if not raw:
        return ""
    if r"\text" in raw or "textnormal" in raw or ("{" in raw and "}" in raw and any(w in raw.lower() for w in ["functors", "monoid", "homomorphisms", "continuous", "systems", "categories", "functions", "maps", "morphisms", "equivalences", "simplicial"])):
        s = raw.strip()
        period = ""
        if s.endswith("."):
            period = " ."
            s = s[:-1].strip()
        if s.startswith(r"\{") and s.endswith(r"\}"):
            s = s[2:-2].strip()
        elif s.startswith("{") and s.endswith("}"):
            s = s[1:-1].strip()
        m = re.match(r"\\text(?:normal)?\s*\{([\s\S]*)\}\s*$", s)
        if m:
            s = m.group(1).strip()
        else:
            s = re.sub(r"\\text(?:normal)?\s*\{", "", s)
            s = s.rstrip("}")

        parts = s.split("$")
        for i in range(len(parts)):
            if i % 2 == 1:
                parts[i] = tex_to_typst_label(parts[i])
            else:
                parts[i] = parts[i].replace("_", r"\_")
        s = "$".join(parts)
        return f"[ {{ {s} }}{period} ]"

    label = tex_to_typst_label(raw)
    return f"${label}$" if not label.startswith("$") else label


def parse_xymatrix_cell(cell: str, row: int, col: int) -> tuple[str, list[dict[str, object]]]:
    """Extract node label and outgoing edges from an xymatrix cell."""
    s = cell.strip()
    edges: list[dict[str, object]] = []

    s = re.sub(r"\|\\hole\b", "", s)
    s = re.sub(r"\\hole\b", "", s)

    while True:
        m = re.search(r"\\ar\b", s)
        if not m:
            break
        ar_start = m.start()
        pos = m.end()

        style = "->"
        bend = ""
        loop = ""

        while pos < len(s) and s[pos].isspace():
            pos += 1

        if pos < len(s) and s[pos] == "@":
            pos += 1
            while pos < len(s) and s[pos].isspace():
                pos += 1
            if pos < len(s) and s[pos] == "{":
                st_str, pos = extract_balanced(s, "{", "}", pos)
                if "-->" in st_str or "--" in st_str:
                    style = "-->"
                elif "hook" in st_str or "(" in st_str:
                    style = "hook'->"
                elif ">>" in st_str:
                    style = "->>"
            elif pos < len(s) and s[pos] == "/":
                end_slash = s.find("/", pos + 1)
                if end_slash != -1:
                    bend = s[pos + 1 : end_slash]
                    pos = end_slash + 1
            elif pos < len(s) and s[pos] == "(":
                end_p = s.find(")", pos + 1)
                if end_p != -1:
                    loop = s[pos + 1 : end_p]
                    pos = end_p + 1

        while pos < len(s) and s[pos].isspace():
            pos += 1

        dirs = ""
        if pos < len(s) and s[pos] == "[":
            end_brk = s.find("]", pos + 1)
            if end_brk != -1:
                dirs = s[pos + 1 : end_brk].strip()
                pos = end_brk + 1

        labels: list[tuple[str, bool]] = []
        while pos < len(s):
            while pos < len(s) and s[pos].isspace():
                pos += 1
            if pos < len(s) and s[pos] in ("^", "_", "|"):
                side_ch = s[pos]
                is_sub = (side_ch == "_")
                pos += 1
                while pos < len(s) and s[pos].isspace():
                    pos += 1
                if pos < len(s) and s[pos] == "-":
                    pos += 1
                    while pos < len(s) and s[pos].isspace():
                        pos += 1
                if pos < len(s) and s[pos] == "{":
                    lbl, pos = extract_balanced(s, "{", "}", pos)
                    labels.append((lbl, is_sub))
                else:
                    m_tok = re.match(r"[a-zA-Z0-9_\\]+", s[pos:])
                    if m_tok:
                        lbl = m_tok.group(0)
                        pos += len(lbl)
                        labels.append((lbl, is_sub))
                    else:
                        break
            else:
                break

        dx, dy = 0, 0
        for ch in dirs:
            if ch == "r":
                dx += 1
            elif ch == "l":
                dx -= 1
            elif ch == "d":
                dy += 1
            elif ch == "u":
                dy -= 1

        primary_label = ""
        primary_side = "left"
        if labels:
            primary_label = tex_to_typst_label(labels[0][0])
            primary_side = "right" if labels[0][1] else "left"

        edges.append(
            {
                "from": (col, row),
                "to": (col + dx, row + dy),
                "style": style,
                "label": primary_label,
                "label_side": primary_side,
                "bend": bend,
                "loop": loop,
            }
        )

        s = s[:ar_start] + " " + s[pos:]

    return s.strip(), edges


def xymatrix_to_fletcher(latex: str, tag: str = "") -> str:
    r"""Translate XY-pic \xymatrix LaTeX string into Typst Fletcher code."""
    content = latex.strip()
    idx = content.find("{")
    if idx != -1 and "xymatrix" in content[:idx]:
        content = content[idx + 1 :]
    content = content.rstrip("}").strip()

    rows = split_top_level(content, r"\\")
    nodes: list[tuple[tuple[int, int], str]] = []
    edges: list[dict[str, object]] = []

    for r_idx, r in enumerate(rows):
        cells = split_top_level(r, "&")
        for c_idx, cell in enumerate(cells):
            raw_node, cell_edges = parse_xymatrix_cell(cell, r_idx, c_idx)
            formatted_node = format_node_label(raw_node)
            if formatted_node:
                nodes.append(((c_idx, r_idx), formatted_node))
            edges.extend(cell_edges)

    lines = [
        '#import "@preview/fletcher:0.5.8": diagram, node, edge',
        "",
        '#let Hom = math.op("Hom")',
        '#let Set = math.op("Set")',
        '#let Cat = math.op("Cat")',
        '#let Mon = math.op("Mon")',
        '#let Fun = math.op("Fun")',
        '#let Path = math.op("Path")',
        '#let Edge = math.op("Edge")',
        '#let Vert = math.op("Vert")',
        '#let Sing = math.op("Sing")',
        '#let sk = math.op("sk")',
        '#let cosk = math.op("cosk")',
        '#let Spine = math.op("Spine")',
        '#let Ob = math.op("Ob")',
        '#let Obj = math.op("Obj")',
        '#let Lin = math.op("Lin")',
        '#let Op = math.op("Op")',
        '#let Ker = math.op("Ker")',
        '#let Coker = math.op("Coker")',
        '#let Im = math.op("Im")',
        '#let Map = math.op("Map")',
        '#let Sub = math.op("Sub")',
        '#let Pith = math.op("Pith")',
        '#let h = math.op("h")',
        '#let rev = math.op("rev")',
        '#let id = math.op("id")',
        '#let Id = math.op("Id")',
        '#let hc = math.op("hc")',
        '#let holim = math.op("holim")',
        '#let colim = math.op("colim")',
        '#let Isom = math.op("Isom")',
        '#let QCat = math.op("QCat")',
        '#let AW = math.op("AW")',
        '#let ev = math.op("ev")',
        '#let Kan = math.op("Kan")',
        '#let MonCat = math.op("MonCat")',
        '#let lax = math.op("lax")',
        '#let sTr = math.op("sTr")',
        '#let hTr = math.op("hTr")',
        '#let hEq = math.op("hEq")',
        '#let init = math.op("init")',
        '#let FG = math.op("FG")',
        '#let Rf = math.op("Rf")',
        '#let UF = math.op("UF")',
        '#let Top = math.op("Top")',
        '#let UG = math.op("UG")',
        '#let nd = "nd"',
        '#let th = "th"',
        "",
        "#diagram(",
        "  spacing: (52.32pt, 53.92pt),",
        "  node-inset: 3pt,",
    ]

    for pos, formatted_node in nodes:
        lines.append(f"  node({pos}, {formatted_node}),")

    edge_counts: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}
    for e in edges:
        from_p = e["from"]
        to_p = e["to"]
        if isinstance(from_p, tuple) and isinstance(to_p, tuple):
            k = (from_p, to_p)
            edge_counts[k] = edge_counts.get(k, 0) + 1

    seen_edges: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}
    for e in edges:
        from_p = e["from"]
        to_p = e["to"]
        if isinstance(from_p, tuple) and isinstance(to_p, tuple):
            k = (from_p, to_p)
            total = edge_counts.get(k, 1)
            idx = seen_edges.get(k, 0)
            seen_edges[k] = idx + 1

            args = [f'{e["from"]}', f'{e["to"]}', f'"{e["style"]}"']
            if e["label"]:
                args.append(f'${e["label"]}$')
                args.append(f'label-side: {e["label_side"]}')

            if total > 1:
                shift_pt = -4 + idx * 8
                args.append(f"shift: {shift_pt}pt")

            if e["bend"]:
                deg = "25deg" if "2pc" in str(e["bend"]) or "1.5pc" in str(e["bend"]) else "18deg"
                args.append(f"bend: {deg}")

            lines.append(f"  edge({', '.join(args)}),")

    lines.append(")")
    return "\n".join(lines)
