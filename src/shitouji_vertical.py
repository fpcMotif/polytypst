import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymupdf

from .parity.source import sources_dir

SOURCE_PDF = "石頭記＠四校訖自用.v2.006a.PDF"
FIRST_PAGE = 19
SLOT_PITCH = 27.9
BODY_TOP = 192.7
HEAD_BOTTOM = 180.0
COLUMN_FULL_BOTTOM = 650.0
NUMERALS = set("一二三四五六七八九十")
LABEL_COLORS = {"00AEEF", "000000"}
SIDE_RUN_GAP = 10.0
CN_DIGITS = {c: i for i, c in enumerate("〇一二三四五六七八九")}
TENS_PREFIX = {"廿": 20, "卅": 30, "卌": 40}
HUI_RE = re.compile(r"第([一二三四五六七八九十〇廿卅卌]+)回")


def source_pdf() -> Path:
    return sources_dir(SOURCE_PDF) / SOURCE_PDF


@dataclass
class Glyph:
    ch: str
    x0: float
    y0: float
    size: float
    color: str

    @property
    def black(self) -> bool:
        return self.color == "000000"

    @property
    def label(self) -> bool:
        return self.ch in NUMERALS and self.color in LABEL_COLORS


def _glyphs(page: pymupdf.Page) -> list[Glyph]:
    out: list[Glyph] = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            if abs(line["dir"][1] - 1) > 0.01:
                continue
            for span in line["spans"]:
                if "Segoe" in span["font"]:
                    continue
                color = f"{span['color']:06X}"
                for c in span["chars"]:
                    x0, y0, _, _ = c["bbox"]
                    out.append(Glyph(c["c"], round(x0, 1), round(y0, 1), round(span["size"], 1), color))
    return out


def _kind(g: Glyph) -> str:
    if g.size >= 17:
        return "display"
    if g.size >= 12.5:
        return "body"
    if g.size >= 10.5:
        return "note"
    if g.size >= 8.0:
        return "small"
    if g.size >= 6.5:
        return "side"
    return "drop"


def _cn_number(text: str) -> int:
    if text[:1] in TENS_PREFIX:
        return TENS_PREFIX[text[0]] + (CN_DIGITS.get(text[1:], 0) if text[1:] else 0)
    if text == "十":
        return 10
    if "十" in text:
        tens, _, ones = text.partition("十")
        return (CN_DIGITS.get(tens, 1) if tens else 1) * 10 + (CN_DIGITS.get(ones, 0) if ones else 0)
    return CN_DIGITS.get(text, 0)


def _columns(glyphs: list[Glyph], tol: float = 1.5) -> list[list[Glyph]]:
    cols: list[list[Glyph]] = []
    for g in sorted(glyphs, key=lambda g: (-g.x0, g.y0)):
        if cols and abs(cols[-1][0].x0 - g.x0) <= tol:
            cols[-1].append(g)
        else:
            cols.append([g])
    return [sorted(c, key=lambda g: g.y0) for c in cols]


def _runs(glyphs: list[Glyph]) -> list[dict[str, str]]:
    runs: list[dict[str, str]] = []
    for g in glyphs:
        if runs and runs[-1]["c"] == g.color:
            runs[-1]["s"] += g.ch
        else:
            runs.append({"s": g.ch, "c": g.color})
    return runs


@dataclass
class HeadNote:
    labels: str
    text: str
    color: str
    used: bool = False


def _head_notes(small_head: list[Glyph]) -> list[HeadNote]:
    notes: list[HeadNote] = []
    for col in _columns(small_head, tol=2.0):
        labels = ""
        i = 0
        while i < len(col) and col[i].label:
            labels += col[i].ch
            i += 1
        body = col[i:]
        text = "".join(g.ch for g in body)
        color = next((g.color for g in body), "E73E29")
        if labels or not notes:
            notes.append(HeadNote(labels, text, color))
        else:
            notes[-1].text += text
    return notes


@dataclass
class SourceColumn:
    right_edge: float
    role: str
    items: list[tuple[float, int, dict[str, Any]]]
    first_y: float
    last_y: float


class ShitoujiReader:
    def __init__(self, pdf: Path):
        self.doc = pymupdf.open(pdf)
        self.residual: dict[int, float] = {0: 424.7 % SLOT_PITCH, 1: 439.6 % SLOT_PITCH}

    def _slot_origin(self, body: list[Glyph], parity: int) -> float:
        if body:
            res = Counter(round(g.x0 % SLOT_PITCH, 0) for g in body).most_common(1)[0][0]
            close = [g.x0 % SLOT_PITCH for g in body if abs(round(g.x0 % SLOT_PITCH, 0) - res) < 1]
            self.residual[parity] = sum(close) / len(close)
        return self.residual[parity] + SLOT_PITCH * 20

    def frame_hui(self, pno: int) -> str:
        if pno > self.doc.page_count:
            return ""
        frame = [g for g in _glyphs(self.doc[pno - 1])
                 if _kind(g) == "small" and g.black and (g.x0 > 455 or g.x0 < 50)]
        m = HUI_RE.search("".join(g.ch for col in _columns(frame) for g in col))
        return m.group(1) if m else ""

    def page_units(self, pno: int) -> tuple[list[SourceColumn], list[Glyph], list[Glyph]]:
        glyphs = _glyphs(self.doc[pno - 1])
        frame = [g for g in glyphs if _kind(g) == "small" and g.black and (g.x0 > 455 or g.x0 < 50)]
        glyphs = [g for g in glyphs if g not in frame and _kind(g) != "drop"]
        display = [g for g in glyphs if _kind(g) == "display"]
        body = [g for g in glyphs if _kind(g) == "body"]
        origin = self._slot_origin(body, pno % 2)

        def slot_of(x0: float, offset: float = 0.0) -> int:
            return round((origin + offset - x0) / SLOT_PITCH)

        slots: dict[int, list[tuple[float, int, dict[str, Any]]]] = {}
        heads = _head_notes([g for g in glyphs if _kind(g) == "small" and g.y0 < HEAD_BOTTOM])
        by_label = {lab: n for n in heads for lab in n.labels}
        jp: dict[int, list[Glyph]] = {}
        for g in body:
            slots.setdefault(slot_of(g.x0), []).append((g.y0, 1, {"k": "t", "s": g.ch, "c": g.color}))
        side: dict[tuple[int, int], list[Glyph]] = {}
        for g in glyphs:
            kind = _kind(g)
            if kind == "small" and g.y0 >= HEAD_BOTTOM:
                k_side = slot_of(g.x0, 13.9)
                if g.label and g.x0 > origin - SLOT_PITCH * k_side + 10:
                    note = by_label.get(g.ch)
                    if note and not note.used:
                        note.used = True
                        slots.setdefault(k_side, []).append(
                            (g.y0 - 6, 0, {"k": "m", "s": note.text, "c": note.color, "n": note.labels})
                        )
                    continue
                jp.setdefault(slot_of(g.x0 + 4.6, 6.95), []).append(g)
            elif kind == "side":
                side.setdefault((slot_of(g.x0, 13.9), round(g.x0)), []).append(g)
        for (k, _), chars in side.items():
            run: list[Glyph] = []
            for g in sorted(chars, key=lambda g: g.y0) + [None]:
                if run and (g is None or g.y0 - run[-1].y0 > SIDE_RUN_GAP or g.color != run[-1].color):
                    slots.setdefault(k, []).append(
                        (run[0].y0 - 6, 0, {"k": "c", "s": "".join(x.ch for x in run), "c": run[0].color})
                    )
                    run = []
                if g is not None:
                    run.append(g)
        for k, chars in jp.items():
            slots.setdefault(k, []).extend((g.y0, 2, {"k": "j", "g": g}) for g in chars)
        for note in heads:
            if not note.used and note.text:
                first = min(slots) if slots else 0
                slots.setdefault(first, []).insert(0, (-1.0, 0, {"k": "m", "s": note.text, "c": note.color, "n": note.labels}))

        units: list[SourceColumn] = []
        for k, items in slots.items():
            items.sort(key=lambda it: (it[0], it[1]))
            ys = [y for y, pri, _ in items if pri > 0]
            if not ys:
                continue
            units.append(SourceColumn(origin - SLOT_PITCH * k + 27.8, "body", items, ys[0], ys[-1]))
        for col in _columns([g for g in glyphs if _kind(g) == "note"]):
            items = [(g.y0, 1, {"k": "t", "s": g.ch, "c": g.color}) for g in col]
            units.append(SourceColumn(col[0].x0 + col[0].size, "note", items, col[0].y0, col[-1].y0))
        units.sort(key=lambda u: -u.right_edge)
        return units, display, frame


def _unit_segments(unit: SourceColumn, slot_center: float | None) -> list[dict[str, Any]]:
    segs: list[dict[str, Any]] = []
    i = 0
    items = unit.items
    while i < len(items):
        _, _, it = items[i]
        if it["k"] == "j":
            run: list[Glyph] = []
            while i < len(items) and items[i][2]["k"] == "j":
                run.append(items[i][2]["g"])
                i += 1
            center = slot_center if slot_center is not None else sum(g.x0 for g in run) / len(run) + 4.6
            right = [g for g in run if g.x0 + 4.6 >= center]
            left = [g for g in run if g.x0 + 4.6 < center]
            for r in _runs(sorted(right, key=lambda g: g.y0) + sorted(left, key=lambda g: g.y0)):
                segs.append({"k": "j", **r})
            continue
        segs.append(dict(it))
        i += 1
    return segs


def _merge(segs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in segs:
        if out and out[-1]["k"] == s["k"] and out[-1].get("c") == s.get("c") and s["k"] in ("t", "j"):
            out[-1]["s"] += s["s"]
        else:
            out.append(s)
    return out


def extract_chapters(pdf: Path | None = None) -> list[dict[str, Any]]:
    reader = ShitoujiReader(pdf or source_pdf())
    chapters: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] | None = None
    para: dict[str, Any] | None = None
    prev_last_y = 0.0
    juan = ""

    def flush() -> None:
        nonlocal para
        if para and blocks is not None and para["segments"]:
            para["segments"] = _merge(para["segments"])
            blocks.append(para)
        para = None

    for pno in range(FIRST_PAGE, reader.doc.page_count + 1):
        units, display, _frame = reader.page_units(pno)
        if any(g.size > 40 for g in display):
            continue
        titles = [g for g in display if g.black]
        hui = reader.frame_hui(pno) or reader.frame_hui(pno + 1)
        last_num = int(chapters[-1]["slug"][4:]) if chapters else 0
        if titles and hui and _cn_number(hui) > last_num:
            flush()
            red = [g for g in display if not g.black]
            if red:
                juan = "".join(g.ch for col in _columns(red) for g in col)
            num = _cn_number(hui)
            lines = [re.sub(rf"^{HUI_RE.pattern}\s*", "","".join(g.ch for g in col)).strip("　")
                     for col in _columns(titles)]
            lines = [ln for ln in lines if ln]
            title = lines[0] if lines else ""
            blocks = [{"type": "vertical", "role": "title", "juan": juan, "variants": lines[1:], "segments": [
                {"k": "t", "s": f"第{hui}回"}, {"k": "t", "s": title},
            ]}]
            chapters.append({"slug": f"hui-{num:03d}", "number": f"第{hui}回",
                             "title": title.replace("　　", "　"), "blocks": blocks})
            prev_last_y = 0.0
        elif titles and blocks is not None:
            flush()
            blocks.append({"type": "vertical", "role": "body", "indent": 1, "segments": _merge(
                [{"k": "t", "s": g.ch, "c": g.color} for col in _columns(titles) for g in col])})
        if blocks is None:
            continue
        for unit in units:
            role = unit.role
            if role == "note":
                starts_para = para is None or para["role"] != "note" or not 228 < unit.first_y < 236
            else:
                starts_para = (
                    para is None
                    or para["role"] == "note"
                    or unit.first_y > BODY_TOP + 6
                    or prev_last_y < COLUMN_FULL_BOTTOM
                )
            if starts_para:
                flush()
                indent = 2 if unit.first_y > BODY_TOP + 20 else (1 if unit.first_y > BODY_TOP + 6 else 0)
                para = {"type": "vertical", "role": "verse" if role == "body" and indent == 2 else role,
                        "indent": indent, "segments": []}
            slot_center = unit.right_edge - 27.8 + 6.95 if role == "body" else None
            para["segments"].extend(_unit_segments(unit, slot_center))
            prev_last_y = unit.last_y
            if para["role"] == "verse":
                flush()
                prev_last_y = 0.0
    flush()
    for ch in chapters:
        for b in ch["blocks"]:
            for s in b["segments"]:
                if s.get("c") == "000000":
                    s.pop("c")
            if b["role"] != "title" and b["segments"] and b["segments"][0]["k"] == "t":
                b["segments"][0]["s"] = b["segments"][0]["s"].lstrip("　")
    return [c for c in chapters if len(c["blocks"]) > 1]
