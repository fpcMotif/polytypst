"""Transcript text matched to the line cache's scan words.

The line cache knows where each word sits on the scan but misreads old faces and
math; the transcript has the right text but no positions. Matching the two letter
by letter gives each transcript chunk the scan words it covers.
"""

import re
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher

from .parity.words import token

PIECE_RE = re.compile(
    r"(?P<display>\$\$.+?\$\$)|(?P<math>\$(?:[^$\\]|\\.)+?\$)|(?P<space>\s+)|(?P<text>[^\s$]+|\$)",
    re.DOTALL,
)
HEADING_RE = re.compile(r"(?m)^#+\s+(.+?)\s*$")
EMPHASIS_RE = re.compile(r"(\*\*|\*)")
ESCAPE_RE = re.compile(r"\\(?=[^\w\s])")
LATEX_NAME_RE = re.compile(r"\\[A-Za-z]+")
EQUATION_NUMBER_RE = re.compile(r"\(\d+(?:\.\d+)*\)")


@dataclass(frozen=True)
class Piece:
    """Prose (`text`), inline math or a display; math holds its LaTeX. Prose may be italic or bold."""

    kind: str
    text: str
    style: str = ""


Chunk = tuple[Piece, ...]


@dataclass(frozen=True)
class Unit:
    """Consecutive transcript chunks and the scan words they cover, both as indexes."""

    chunks: tuple[int, ...]
    words: tuple[int, ...]


def chunks(markdown: str) -> list[Chunk]:
    """The transcript's runs between spaces, with headings set bold; a display is a chunk of its own."""
    out: list[Chunk] = []
    cur: list[Piece] = []
    bold = italic = False

    def flush() -> None:
        if cur:
            out.append(tuple(cur))
            cur.clear()

    matches = list(PIECE_RE.finditer(HEADING_RE.sub(r"**\1**", markdown)))
    for k, m in enumerate(matches):
        kind, text = m.lastgroup, m.group()
        if kind == "space":
            hyphen_before_math = (
                cur
                and cur[-1].kind == "text"
                and cur[-1].text.endswith("-")
                and "\n" not in text
                and k + 1 < len(matches)
                and matches[k + 1].lastgroup == "math"
            )
            if hyphen_before_math:
                continue
            flush()
            if "\n\n" in text:
                bold = italic = False
        elif kind == "display":
            flush()
            out.append((Piece("display", text[2:-2].strip()),))
        elif kind == "math":
            cur.append(Piece("math", text[1:-1].strip()))
        else:
            for part in EMPHASIS_RE.split(text):
                if part == "**":
                    bold = not bold
                elif part == "*":
                    italic = not italic
                elif part := ESCAPE_RE.sub("", part):
                    cur.append(
                        Piece(
                            "text", part, "bold" if bold else "italic" if italic else ""
                        )
                    )
    flush()
    return out


def plain(chunk: Chunk) -> str:
    """The letters and digits a line reader would see in a chunk; a display has none, as it is placed by lines."""
    if chunk[0].kind == "display":
        return ""
    return "".join(
        token(p.text if p.kind == "text" else LATEX_NAME_RE.sub("", p.text))
        for p in chunk
    )


def claim_display_lines(
    chunks: list[Chunk],
    owned: dict[int, list[int]],
    votes: list[Counter[int]],
    word_lines: list[int],
) -> dict[int, list[int]]:
    """Give each run of displays the whole scan lines between the main lines of the prose around it,
    shared out in order, since a line reader turns display math into letters that match nearby prose.
    An equation number beside the run keeps its own words but does not bound the run, as the scan
    sets it on the display's row."""

    def is_number(c: int) -> bool:
        return len(chunks[c]) == 1 and bool(
            EQUATION_NUMBER_RE.fullmatch(chunks[c][0].text)
        )

    def main_line(c: int) -> int:
        letters: Counter[int] = Counter()
        for j in owned[c]:
            letters[word_lines[j]] += votes[j][c]
        return letters.most_common(1)[0][0]

    i = 0
    while i < len(chunks):
        if chunks[i][0].kind != "display":
            i += 1
            continue
        end = i
        while end < len(chunks) and chunks[end][0].kind == "display":
            end += 1
        before = [c for c in range(i) if c in owned]
        after = [c for c in range(end, len(chunks)) if c in owned]
        prose_before = [c for c in before if not is_number(c)]
        prose_after = [c for c in after if not is_number(c)]
        if prose_before and prose_after:
            lo, hi = main_line(prose_before[-1]), main_line(prose_after[0])
            numbers = {
                j
                for c in range(prose_before[-1] + 1, prose_after[0])
                if c in owned and is_number(c)
                for j in owned[c]
            }
            lines = sorted({line for line in word_lines if lo < line < hi})
            n = end - i
            for k, d in enumerate(range(i, end)):
                mine = set(lines[k * len(lines) // n : (k + 1) * len(lines) // n])
                ws = [
                    j
                    for j, line in enumerate(word_lines)
                    if line in mine and j not in numbers
                ]
                if ws:
                    owned = {
                        c: [j for j in js if word_lines[j] not in mine or j in numbers]
                        for c, js in owned.items()
                    }
                    owned[d] = ws
            owned = {c: js for c, js in sorted(owned.items()) if js}
        elif before or after:
            taken = {word_lines[j] for js in owned.values() for j in js}
            lines = sorted(set(word_lines), reverse=not before)
            start = main_line(before[-1]) if before else main_line(after[0])
            beyond = [
                line for line in lines if (line > start if before else line < start)
            ]
            free = []
            for line in beyond:
                if line in taken:
                    break
                free.append(line)
            displays = range(i, end) if before else reversed(range(i, end))
            for d, line in zip(displays, free):
                owned[d] = [j for j, wl in enumerate(word_lines) if wl == line]
            owned = dict(sorted(owned.items()))
        i = end
    return owned


def match_units(
    chunks: list[Chunk], words: list[str], word_lines: list[int]
) -> list[Unit]:
    """Each scan word goes to the chunk whose letters it matched most. Chunks left without a word take
    the free words between their neighbours on lines that matched elsewhere, or join a neighbour chunk."""
    a_owner = [i for i, c in enumerate(chunks) for _ in plain(c)]
    b_owner = [j for j, w in enumerate(words) for _ in token(w)]
    a = "".join(plain(c) for c in chunks)
    b = "".join(token(w) for w in words)
    votes = [Counter() for _ in words]
    for blk in SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            votes[b_owner[blk.b + k]][a_owner[blk.a + k]] += 1
    owned: dict[int, list[int]] = {}
    for j, v in enumerate(votes):
        if v:
            owned.setdefault(v.most_common(1)[0][0], []).append(j)
    owned = claim_display_lines(chunks, owned, votes, word_lines)
    taken = {j for ws in owned.values() for j in ws}
    matched_lines = {word_lines[j] for j in taken}
    fillable = {j for j, line in enumerate(word_lines) if line in matched_lines}
    units: list[Unit] = []
    i = 0
    while i < len(chunks):
        if i in owned:
            units.append(Unit((i,), tuple(owned[i])))
            i += 1
            continue
        end = i
        while end < len(chunks) and end not in owned:
            end += 1
        lo = units[-1].words[-1] + 1 if units and units[-1].words else 0
        hi = owned[end][0] if end < len(chunks) else len(words)
        free = [j for j in range(lo, hi) if j not in taken and j in fillable]
        run = list(range(i, end))
        if free:
            groups: dict[int, tuple[list[int], list[int]]] = {}
            if len(free) >= len(run):
                for n, j in enumerate(free):
                    groups.setdefault(run[n * len(run) // len(free)], ([], []))[
                        1
                    ].append(j)
                for c in run:
                    groups[c][0].append(c)
            else:
                for n, c in enumerate(run):
                    groups.setdefault(free[n * len(free) // len(run)], ([], []))[
                        0
                    ].append(c)
                for j in groups:
                    groups[j][1].append(j)
            units += [Unit(tuple(cs), tuple(ws)) for cs, ws in groups.values()]
        elif units:
            units[-1] = Unit(units[-1].chunks + tuple(run), units[-1].words)
        else:
            units.append(Unit(tuple(run), ()))
        i = end
    if len(units) > 1 and not units[0].words:
        units[:2] = [Unit(units[0].chunks + units[1].chunks, units[1].words)]
    return units
