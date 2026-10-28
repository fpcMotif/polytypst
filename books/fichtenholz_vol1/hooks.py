import re
from pathlib import Path

from polytypst.vision.diagram_crops import install_scan_diagrams

from .figures import generate_all_fichtenholz_figures

DIAGRAM_DIR = Path(__file__).parent / "diagrams"
DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)

_ARTICLE_TITLE_LEN: tuple[int, ...] = (
    2, 6, 9, 9, 6, 6, 5, 4, 10, 7, 4, 7, 5, 7, 5, 2, 3, 13, 10, 2, 5, 6, 7, 4, 2, 15,
    4, 10, 8, 7, 3, 7, 16, 9, 2, 2, 8, 8, 4, 9, 32, 7, 8, 10, 7, 8, 5, 8, 6, 5, 7, 8,
    9, 2, 7, 2, 7, 12, 10, 6, 6, 5, 5, 3, 6, 13, 9, 7, 9, 7, 11, 8, 7, 8, 17, 14, 15,
    4, 2, 10, 6, 4, 6, 11, 10, 7, 4, 5, 8, 8, 10, 5, 6, 6, 7, 8, 10, 7, 2, 4, 4, 7,
    5, 13, 11, 8, 10, 9, 4, 12, 4, 6, 5, 4, 7, 10, 6, 2, 4, 13, 6, 4, 8, 15, 2, 7, 4,
    15, 9, 14, 8, 8, 6, 11, 8, 2, 4, 7, 10, 3, 8, 10, 7, 9, 2, 5, 7, 11, 2, 10, 18, 7,
    2, 7, 7, 5, 3, 5, 11, 9, 6, 10, 10, 4, 7, 9, 2, 4, 11, 7, 16, 12, 8, 5, 5, 8, 7,
    6, 3, 9, 7, 2, 6, 8, 10, 10, 4, 4, 4, 9, 7, 9, 4, 7, 4, 11, 11, 8, 8, 12, 4, 12,
    7, 12, 8, 6, 7, 6, 8, 2, 4, 9, 9, 6, 9, 7, 4, 2, 10, 5, 7, 2, 9, 2, 8, 10, 8, 6,
    2, 14, 2, 9, 2, 12, 2, 8, 12, 6, 2, 3, 7, 12, 4, 9, 2, 5, 10, 12, 12, 5, 8, 2, 7,
    16, 10, 6, 7, 9, 4, 9, 7, 2,
)
_CHAPTER_ARTICLE_RANGES: dict[int, tuple[int, int]] = {
    0: (1, 21),
    1: (22, 42),
    2: (43, 89),
    3: (90, 130),
    4: (131, 158),
    5: (159, 201),
    6: (202, 222),
    7: (223, 256),
    8: (257, 262),
}


def _split_article_line(rest: str, target_alnum: int) -> tuple[str, str]:
    s = rest.strip()
    if s.startswith("**") and "**" in s[2:]:
        idx = s.index("**", 2)
        title = s[2:idx].strip().rstrip(".")
        tail = s[idx + 2 :].strip()
    else:
        s = re.sub(r"^\*\*|\*\*$", "", s).strip()
        pos = 0
        matched_alnum = 0
        while pos < len(s) and matched_alnum < target_alnum:
            if s[pos].isalnum():
                matched_alnum += 1
            pos += 1
        while pos < len(s) and s[pos] in ")$）":
            pos += 1
        title = s[:pos].strip().rstrip(".")
        tail = s[pos:].strip()
    m_fn = re.match(r"^(\$\^\{\d+\)\}\$|\^\{\d+\)\}|[①-⑳])\s*(.*)$", tail)
    if m_fn:
        title = f"{title}{m_fn.group(1)}"
        tail = m_fn.group(2).strip()
    return title, tail


def _fichtenholz_heading(lt: str, chapter: int) -> str | None:
    if re.match(r"^(?:#+\s*)?(?:绪论\s*实数|第[一二三四五六七]章\s*\S+|附录\s*函数扩充的问题|索引|校订后记)$", lt):
        return ""
    if m_sec := re.match(r"^(?:#+\s*)?(?:\*\*)?§\s*(\d+)\.?\s*(.+?)(?:\*\*)?$", lt):
        return f"## § {m_sec.group(1)}. {m_sec.group(2).strip()}"
    if chapter in _CHAPTER_ARTICLE_RANGES and (
        m_art := re.match(r"^(?:#{2,4}\s*)?(?:\*\*)?(\d{1,3})\.(?:\*\*)?\s*(.+)$", lt)
    ):
        n = int(m_art.group(1))
        lo, hi = _CHAPTER_ARTICLE_RANGES[chapter]
        if lo <= n <= hi:
            title, tail = _split_article_line(m_art.group(2), _ARTICLE_TITLE_LEN[n - 1])
            return f"### {n}. {title}\n\n{tail}" if tail else f"### {n}. {title}"
    return None


def draw_figures(out_dir: Path) -> None:
    generate_all_fichtenholz_figures(out_dir / "figures", out_dir / "figures_color")
    _ = install_scan_diagrams(DIAGRAM_DIR, out_dir)


def fichtenholz_diagram_boxes() -> dict[str, tuple[int, int, int, int]]:
    return {
        "453_001": (1600, 350, 2700, 1600),
        "465_001": (800, 1350, 3200, 2600),
    }
