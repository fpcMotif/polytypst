import re

CELL_STYLE_TAGS = {"b": "strong", "i": "emph"}
CELL_SPAN_RE = re.compile(r'<span data-colspan="(\d+)">(.*)</span>')


def _merge_cell_spans(row: list[str]) -> list[tuple[str, int]]:
    """Fold each span-marked cell and the cells it covers into one (text, colspan) cell."""
    cells: list[tuple[str, int]] = []
    idx = 0
    while idx < len(row):
        m = CELL_SPAN_RE.fullmatch(row[idx])
        span = min(int(m.group(1)), len(row) - idx) if m else 1
        cells.append((m.group(2) if m else row[idx], span))
        idx += span
    return cells


TYPST_MATH_SPAN = re.compile(r"((?<!\\)\$.*?(?<!\\)\$)")


def _escape_table_cell_text(cell: str) -> str:
    parts = TYPST_MATH_SPAN.split(cell)
    for idx in range(0, len(parts), 2):
        part = re.sub(r"<(?!eq-|fig-|sec-)", r"\<", parts[idx])
        part = re.sub(r"(?<![@\\])@(?=[\w])(?!@)", r"\@", part)
        part = re.sub(r"(?<!\\)\[", r"\[", part)
        part = re.sub(r"(?<!\\)\]", r"\]", part)
        part = re.sub(r"(?<!\\)\*", r"\*", part)
        parts[idx] = re.sub(r"(?<!\\)_", r"\_", part)
    return "".join(parts)


THREE_LINE_MIN_WEIGHT = 3
THREE_LINE_MAX_WEIGHT = 30


def _display_width(cell: str) -> int:
    return sum(2 if ord(ch) >= 0x2E80 else 1 for ch in cell)


TABLE_NUMBER = re.compile(r"([−\-+]?[\d,]*\d)(\.\d+)?(%?)")
NUMERIC_COLUMN_SHARE = 0.7
STUB_AUTO_MAX_WIDTH = 12
FIGURE_SPACE, POINT_SPACE = " ", " "


def _decimal_pads(column: list[str]) -> dict[str, str] | None:
    """Each number of a numeric column, padded with figure spaces so that the decimal points line up when the
    cells are centred. None when the column is mostly text."""
    filled = [c for c in column if c and c not in ("—", "-", "–", "…")]
    numbers = [m for c in filled if (m := TABLE_NUMBER.fullmatch(c))]
    if len(numbers) < 2 or len(numbers) < NUMERIC_COLUMN_SHARE * len(filled):
        return None
    whole = max(len(m[1]) for m in numbers)
    tail = max(len(m[2] or "") + len(m[3]) for m in numbers)
    pads = {}
    for m in numbers:
        fraction = (m[2] or "") + m[3]
        right = (POINT_SPACE + FIGURE_SPACE * (tail - 1) if not fraction and tail else FIGURE_SPACE * (tail - len(fraction)))
        pads[m[0]] = FIGURE_SPACE * (whole - len(m[1])) + m[0] + right
    return pads


TEXT_TABLE_MIN_COLUMNS = 4
TEXT_TABLE_MIN_CELL_WIDTH = 30
TEXT_TABLE_MAX_NATURAL_WIDTH = 110
TABLE_CAPTION_BLOCK = r"#v\(0\.6em\)\n#block\(sticky: true, width: 100%\)\[#align\(center\)\[#strong\[[^\n]*\]\]\]\n#v\(0\.2em\)"
TABLE_RUN = re.compile(
    rf"^(?:{TABLE_CAPTION_BLOCK}\n+)?(?:#block\(sticky: true\)\[[^\n]*\]\n+)?@@TABLEBLOCK\d+@@"
    rf"(?:\n+(?:(?:@@PAGEBREAK@@ *)?(?:#block\(sticky: true\)\[[^\n]*\]|续表)\n+)?@@TABLEBLOCK\d+@@)*"
    r"(?:\n+(?:注|资料来源|（注|\(注)[^\n]*)*\n*",
    re.MULTILINE,
)


def _is_prose_column(column: list[str]) -> bool:
    cells = [_display_width(re.sub(r"<[^>]+>", "", c)) for c in column if c.strip()]
    return bool(cells) and sum(cells) / len(cells) >= TEXT_TABLE_MIN_CELL_WIDTH


def _is_text_table(table: str) -> bool:
    """A table of four or more columns whose cells hold sentences, which a portrait page squeezes into narrow columns."""
    rows = [[c.strip() for c in line.strip().split("|")[1:-1]] for line in table.splitlines() if line.strip().startswith("|")]
    rows = [r for r in rows if not all(set(c) <= set(" -:—–") for c in r)]
    if not rows or len(rows[0]) < TEXT_TABLE_MIN_COLUMNS or len(rows) < 2:
        return False
    widths = [[_display_width(re.sub(r"<[^>]+>", "", c)) for c in r] for r in rows[1:]]
    cells = [w for r in widths for w in r[1:] if w]
    natural = sum(max((r[c] for r in widths if c < len(r)), default=0) for c in range(len(rows[0])))
    phrase_columns = sum(
        1
        for c in range(1, len(rows[0]))
        if sum(bool(re.search(r"[一-鿿]{4}", r[c])) for r in rows[1:] if c < len(r)) * 2 > len(rows) - 1
    )
    return bool(cells) and (
        sum(cells) / len(cells) >= TEXT_TABLE_MIN_CELL_WIDTH
        or (natural > TEXT_TABLE_MAX_NATURAL_WIDTH and phrase_columns >= 2)
    )


def _rotate_text_tables(text: str, table_blocks: list[str]) -> str:
    """Set each run of caption, text tables, continuation label and note on its own landscape page."""

    def rotate(m: re.Match[str]) -> str:
        tables = [table_blocks[int(n)] for n in re.findall(r"@@TABLEBLOCK(\d+)@@", m[0])]
        if not any(_is_text_table(t) for t in tables):
            return m[0]
        run = re.sub(r"(?m)^(?:@@PAGEBREAK@@ *)?续表$", "#block(sticky: true)[续表]", m[0]).strip()
        return f"#page(flipped: true)[\n#set table.cell(breakable: false)\n{run}\n]\n\n"

    return TABLE_RUN.sub(rotate, text)


PANEL = r"(?:#block\(sticky: true\)\[[^\n]*\]\n+)?@@TABLEBLOCK\d+@@"
NOTE_LINES = re.compile(r"^((?:注|资料来源)[:：][^\n]*)((?:\n[^\n]+)+)", re.MULTILINE)


def _panel_grid(section: str, columns: int) -> str | None:
    """Set the `columns` adjacent panel tables of a multi-column scan page side by side in one grid, so that no
    panel breaks across page columns, and put each of the notes below on its own line. None when the page holds
    other than `columns` adjacent panels."""
    run = re.search(rf"{PANEL}(?:\n+{PANEL})*", section)
    panels = re.findall(PANEL, run[0]) if run else []
    if len(panels) != columns or len(re.findall(r"@@TABLEBLOCK\d+@@", section)) != columns:
        return None
    head = section[: run.start()]
    unit = re.search(r"\n*^(单位[:：][^\n]*)\n*$", head, re.MULTILINE)
    if unit and all(p.startswith("#block") for p in panels):
        head = head[: unit.start()] + "\n\n"
        panels = [re.sub(r"\]\n", rf"#h(1fr){unit[1]}]\n", p, count=1) for p in panels]
    grid = (
        f"#set table(inset: (x: 3pt, y: 1pt))\n#grid(columns: (1fr,) * {columns}, column-gutter: 1.5em,\n"
        + "".join(f"[{p}],\n" for p in panels)
        + ")"
    )
    rest = NOTE_LINES.sub(
        lambda m: "#block(above: 0.8em)[#set text(size: 8.5pt)\n#set par(first-line-indent: 0pt, leading: 0.55em)\n"
        + m[1] + m[2].replace("\n", "\\\n") + "]",
        section[run.end() :],
    )
    return head + grid + rest


TABLE_LABEL_MAX_WIDTH = 24
SHORT_COLUMN_MAX_WIDTH = 8


def _is_table_label(line: str) -> bool:
    """A short line right before a table, such as a panel label or a unit, which belongs on the table's page."""
    text = line.strip()
    return (
        0 < _display_width(text) <= TABLE_LABEL_MAX_WIDTH
        and not re.search(r"[。，；]|@@", text)
        and not text.startswith(("#", "|", "]", ")", "=", "- ", "+ ", "/ "))
    )


def _column_weights(header: list[list[str]], body: list[list[str]], ncols: int, short_auto: bool = False) -> str:
    """Column widths in proportion to each column's widest body cell, with room for its header on two lines.
    A short stub column takes `auto`, so that its labels stay on one line; with `short_auto`, so does every
    column of short cells, which the long prose columns of the table would otherwise squeeze."""
    def width(cell: str) -> int:
        return _display_width(re.sub(r"<[^>]+>", "", cell))

    weights = []
    for c in range(ncols):
        widest = max((width(r[c]) for r in body), default=0)
        head = max((-(-width(r[c]) // 2) for r in header), default=0)
        weights.append(min(THREE_LINE_MAX_WEIGHT, max(THREE_LINE_MIN_WEIGHT, widest, head)))
    stub = "auto" if max((width(r[0]) for r in body), default=0) <= STUB_AUTO_MAX_WIDTH else f"{weights[0]}fr"
    rest = ["auto" if short_auto and w <= SHORT_COLUMN_MAX_WIDTH else f"{w}fr" for w in weights[1:]]
    return "(" + ", ".join([stub, *rest]) + ")"


CONTINUED_TABLE_HEAD_RE = re.compile(r"^(?:@@PAGEBREAK@@\s*)?(?:#+\s*)?续表[^\n]*")
CONTINUED_TABLE_PAIR_RE = re.compile(
    r"((?:^[ \t]*\|[^\n]+\|[ \t]*\n)+)"
    r"(?:[ \t]*\n)+(?:@@PAGEBREAK@@\s*)?(?:#+\s*)?续表[^\n]*\n(?:[ \t]*\n)*"
    r"((?:^[ \t]*\|[^\n]+\|[ \t]*\n?)+)",
    re.MULTILINE,
)


def continued_table_split(text: str) -> tuple[str, str] | None:
    """For a page that opens with a 续表, the continued table with its notes and the text after it. None when
    the page opens with anything else."""
    if not CONTINUED_TABLE_HEAD_RE.match(text.lstrip()):
        return None
    stripped = text.lstrip()
    m = re.search(
        r"^(?:@@PAGEBREAK@@\s*)?(?:#+\s*)?续表[^\n]*(?:\n[ \t]*)*(?:\n[ \t]*\|[^\n]+\|[ \t]*)+"
        r"(?:\n+(?:注|资料来源|（注|\(注|（资料来源|\(资料来源)[^\n]*(?:\n(?![ \t]*\n)[^\n]+)*)*",
        stripped,
        re.MULTILINE,
    )
    if not m:
        return text, ""
    return stripped[: m.end()].rstrip(), stripped[m.end() :].lstrip()


def _parse_pipe_rows(block: str) -> tuple[list[list[str]], str]:
    rows: list[list[str]] = []
    sep = ""
    for raw in block.strip().splitlines():
        line = raw.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        if not sep and rows and all(c in " |-:—–" for c in line):
            sep = line
            continue
        rows.append([c.strip() for c in line.split("|")[1:-1]])
    return rows, sep


def _norm_header_cell(cell: str) -> str:
    s = re.sub(r"<br\s*/?>", "", cell)
    s = re.sub(r"[\s*_$^²{}（）()—–\-\u2060.,·:：]", "", s)
    return s


def _is_data_like_cell(cell: str) -> bool:
    s = cell.strip()
    return bool(re.match(r"^(?:\d{4}\s*[年.\-—–/]|[-−+]?\d+(?:\.\d+)?%?$|（[1-9]\）|\([1-9]\))", s))


def _header_rows_match(r1: list[str], r2: list[str]) -> bool:
    n1 = [_norm_header_cell(c) for c in r1]
    n2 = [_norm_header_cell(c) for c in r2]
    if n1 == n2:
        return True
    if _is_data_like_cell(r1[0]) or _is_data_like_cell(r2[0]):
        return False
    non_empty1 = [c for c in n1 if c]
    non_empty2 = [c for c in n2 if c]
    if non_empty1 and set(non_empty1) == set(non_empty2):
        return True
    matches = sum(1 for a, b in zip(n1, n2) if a and (a == b or a in b or b in a))
    needed = max(1, (max(len(non_empty1), len(non_empty2)) + 1) // 2)
    return matches >= needed and matches >= 2


def _repeated_header_count(rows1: list[list[str]], rows2: list[list[str]]) -> int:
    max_k = min(4, len(rows1), len(rows2))
    k = 0
    while k < max_k and _header_rows_match(rows1[k], rows2[k]):
        k += 1
    if k > 0:
        return k
    for sub_k in (3, 2):
        if len(rows2) >= sub_k and len(rows1) > sub_k:
            for start in range(1, len(rows1) - sub_k + 1):
                window = [[_norm_header_cell(c) for c in r] for r in rows1[start : start + sub_k]]
                if all(_header_rows_match(a, b) for a, b in zip(window, rows2[:sub_k])):
                    return sub_k
    return 0


def merge_continued_tables(text: str) -> str:
    def _merge_pair(m: re.Match[str]) -> str:
        t1, t2 = m.group(1), m.group(2)
        rows1, sep1 = _parse_pipe_rows(t1)
        rows2, _ = _parse_pipe_rows(t2)
        if not rows1 or not rows2 or not sep1:
            return f"{t1.rstrip()}\n\n{t2.lstrip()}"
        ncols1 = max(len(r) for r in rows1)
        ncols2 = max(len(r) for r in rows2)
        if ncols1 != ncols2:
            return f"{t1.rstrip()}\n\n{t2.lstrip()}"
        for r in rows1:
            r.extend([""] * (ncols1 - len(r)))
        for r in rows2:
            r.extend([""] * (ncols2 - len(r)))
        drop = _repeated_header_count(rows1, rows2)
        merged_rows = rows1 + rows2[drop:]
        lines = [
            "| " + " | ".join(merged_rows[0]) + " |",
            sep1,
            *("| " + " | ".join(r) + " |" for r in merged_rows[1:]),
        ]
        trailing = "\n" if t2.endswith("\n") else ""
        return "\n".join(lines) + trailing

    prev = None
    while prev != text:
        prev = text
        text = CONTINUED_TABLE_PAIR_RE.sub(_merge_pair, text)
    return text


def _format_pipe_tables(text: str, three_line: bool = False, merge_continued: bool = False) -> str:
    """Typst tables for the Markdown pipe tables in `text`. A `three_line` table (三线表) fills the text width,
    weights each narrow table's columns by their widest cell, and rules only its top, header and bottom."""
    if merge_continued:
        text = merge_continued_tables(text)
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and line.endswith("|") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith("|") and next_line.endswith("|") and all(c in " |-:—–" for c in next_line):
                table_lines = [line]
                i += 2
                while i < len(lines):
                    curr = lines[i].strip()
                    if curr.startswith("|") and curr.endswith("|"):
                        table_lines.append(curr)
                        i += 1
                    else:
                        break

                parsed_rows: list[list[str]] = []
                for tl in table_lines:
                    cells = [c.strip() for c in tl.split("|")[1:-1]]
                    parsed_rows.append(cells)

                if parsed_rows:
                    ncols = max(len(r) for r in parsed_rows)
                    for r in parsed_rows:
                        r.extend([""] * (ncols - len(r)))
                    nrows = len(parsed_rows)
                    first_row = parsed_rows[0]
                    two_level = nrows > 2 and any(
                        first_row[c].strip() and not first_row[c + 1].strip() for c in range(1, ncols - 1)
                    ) and any(not c.strip() for c in parsed_rows[1]) and any(c.strip() for c in parsed_rows[1])
                    header_rows = 2 if two_level else 1
                    body_rows = parsed_rows[header_rows:]
                    pads = [_decimal_pads([r[c].strip() for r in body_rows]) for c in range(ncols)]
                    items: list[str] = []
                    row_starts: list[int] = []
                    for r_idx, r in enumerate(parsed_rows):
                        row_starts.append(len(items))
                        merged = _merge_cell_spans(r)
                        first = r[0].strip()
                        if first and all(not c.strip() for c in r[1:]) and first.startswith(("#strong", "**", "一、", "二、", "三、", "四、", "A ", "B ", "A面板", "B面板", "A 面板", "B 面板")):
                            title_text = re.sub(r"^\*\*(.*?)\*\*$", r"\1", first)
                            title_text = re.sub(r"^#strong\[(.*?)\]$", r"\1", title_text)
                            items.append(f"table.cell(colspan: {ncols}, fill: luma(245))[#strong[{title_text}]]")
                        elif r_idx < 2 and any(not c.strip() for c, _ in merged) and any(c.strip() for c in r):
                            col_idx = 0
                            while col_idx < len(r):
                                c = r[col_idx]
                                c_clean = _escape_table_cell_text(c.replace("<br>", "\\ ").replace("<br/>", "\\ "))
                                span = 1
                                if c.strip():
                                    while col_idx + span < len(r) and not r[col_idx + span].strip():
                                        span += 1
                                    if span > 1:
                                        items.append(f"table.cell(colspan: {span})[#strong[{c_clean}]]")
                                        col_idx += span
                                        continue
                                items.append(f"[#strong[{c_clean}]]" if c_clean.strip() else "[]")
                                col_idx += 1
                        else:
                            col = 0
                            for c, span in merged:
                                shaded = re.fullmatch(r"<mark>(.*)</mark>", c)
                                if shaded:
                                    c = shaded.group(1)
                                column_pads = pads[col] if r_idx >= header_rows and span == 1 else None
                                col += span
                                if column_pads and c.strip() in column_pads:
                                    c = column_pads[c.strip()]
                                for tag, mark in CELL_STYLE_TAGS.items():
                                    c = c.replace(f"<{tag}>", f"@@{mark}@@").replace(f"</{tag}>", "@@END@@")
                                c_clean = _escape_table_cell_text(c.replace("<br>", "\\ ").replace("<br/>", "\\ "))
                                for mark in CELL_STYLE_TAGS.values():
                                    c_clean = c_clean.replace(f"@@{mark}@@", f"#{mark}[")
                                c_clean = c_clean.replace("@@END@@", "]")
                                if r_idx == 0 and c_clean.strip() and not c_clean.strip().startswith(("#strong", "**")):
                                    cell = f"[#strong[{c_clean}]]"
                                else:
                                    cell = f"[{c_clean}]"
                                args = ([f"colspan: {span}"] if span > 1 else []) + (["fill: luma(215)"] if shaded else [])
                                items.append(f"table.cell({', '.join(args)}){cell}" if args else cell)
                    if nrows > 1:
                        split = row_starts[header_rows] if header_rows < nrows else len(items)
                        body = ", ".join([f"table.header({', '.join(items[:split])})", *items[split:]])
                    else:
                        body = ", ".join(items)
                    size_pt = "6.8pt" if ncols >= 10 else "7.2pt" if ncols >= 8 else "7.8pt" if ncols >= 6 else "8.2pt" if ncols >= 5 else "8.8pt"
                    prose_cols = any(_is_prose_column([r[c] for r in body_rows]) for c in range(1, ncols))
                    col_def = (
                        _column_weights(parsed_rows[:header_rows], body_rows, ncols, short_auto=prose_cols)
                        if ncols >= 5
                        else f"{ncols}"
                    )
                    if three_line and ncols < 5:
                        weights = [
                            min(THREE_LINE_MAX_WEIGHT, max(THREE_LINE_MIN_WEIGHT, *(_display_width(r[c]) for r in parsed_rows)))
                            for c in range(ncols)
                        ]
                        col_def = "(" + ", ".join(f"{w}fr" for w in weights) + ")"

                    align_str = (
                        f"if row < {header_rows} {{ center + horizon }} else {{ left + top }},\n  inset: (x: 0.5em, y: 0.6em)"
                        if prose_cols
                        else "if col == 0 { left + horizon } else { center + horizon }"
                    )
                    head_rule = "bottom: 0.5pt + luma(30)" if three_line else "bottom: 0.6pt + luma(60)"
                    head_stroke = (
                        f"if y == 0 {{ (top: 1.0pt + luma(30)) }} else if y == 1 {{ ({head_rule}) }}"
                        if header_rows == 2
                        else f"if y == 0 {{ (top: 1.0pt + luma(30), {head_rule}) }}"
                    )
                    if nrows > 1 and three_line and prose_cols:
                        stroke_str = f"  stroke: (x, y) => {head_stroke} else if y == {nrows - 1} {{ (bottom: 1.0pt + luma(30)) }} else {{ (bottom: 0.3pt + luma(190)) }},\n"
                    elif nrows > 1 and three_line:
                        stroke_str = f"  stroke: (x, y) => {head_stroke} else if y == {nrows - 1} {{ (bottom: 1.0pt + luma(30)) }} else {{ none }},\n"
                    elif nrows > 1:
                        stroke_str = f"  stroke: (x, y) => {head_stroke} else if y == {nrows - 1} {{ (bottom: 1.0pt + luma(30)) }} else {{ (bottom: 0.3pt + luma(220)) }},\n"
                    else:
                        stroke_str = "  stroke: (x, y) => (top: 1.0pt + luma(30), bottom: 1.0pt + luma(30)),\n"
                    fill_str = "  fill: (col, row) => if row > 0 and calc.even(row) { luma(252) } else { none },\n" if ncols >= 6 and not three_line else ""
                    typst_table = (
                        f"\n#align(center)[\n"
                        f"#set text(size: {size_pt})\n"
                        f"{'#set par(justify: false)' + chr(10) if prose_cols else ''}"
                        f"#table(\n"
                        f"  columns: {col_def},\n"
                        f"  align: (col, row) => {align_str},\n"
                        f"{stroke_str}"
                        f"{fill_str}"
                        f"  {body}\n"
                        f")\n"
                        f"]\n"
                    )
                    label_at = next((k for k in range(len(out) - 1, -1, -1) if out[k].strip()), None)
                    if label_at is not None and _is_table_label(out[label_at]):
                        out[label_at] = f"#block(sticky: true)[{out[label_at].strip()}]"
                    out.append(typst_table)
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def layout_tables(text: str, tables: list[str], three_line: bool = False, merge_continued: bool = False) -> str:
    """Typst for the tables of a section. `text` holds `@@TABLEBLOCKn@@` for `tables[n]`, and `@@FLIPPEDn@@`
    where an n-column landscape page starts. Each table keeps its label on its page, the panels of a
    multi-column page share one grid, and a run of text-heavy tables moves to its own landscape page."""
    text = re.sub(
        r"^([^\n]+)\n(?:[ \t]*\n)*(?=@@TABLEBLOCK\d+@@)",
        lambda m: f"#block(sticky: true)[{m[1].strip()}]\n\n" if _is_table_label(m[1]) else m[0],
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"@@FLIPPED([2-9])@@(.*?)(?=@@FLIPPED)",
        lambda m: f"@@FLIPPED1@@{grid}" if (grid := _panel_grid(m[2], int(m[1]))) else m[0],
        text,
        flags=re.DOTALL,
    )
    text = _rotate_text_tables(text, tables)
    text = re.sub(
        r"@@TABLEBLOCK(\d+)@@", lambda m: _format_pipe_tables(tables[int(m[1])], three_line, merge_continued), text
    )
    return _format_pipe_tables(text, three_line, merge_continued)
