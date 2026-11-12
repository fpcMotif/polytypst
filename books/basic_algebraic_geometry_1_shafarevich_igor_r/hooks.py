import re

from .figures import draw_figures

_DROP_HEADINGS = re.compile(
    r"^(?:Chapter\s+\d+\b.*|Book\s+\d+:.*|Basic Algebraic Geometry\s+1"
    r"|Varieties in Projective Space|Preface|Basic Notions|Local Properties"
    r"|Divisors and Differential Forms|Intersection Numbers"
    r"|Algebraic Appendix|References|Index)$",
    re.IGNORECASE,
)


def heading_hook(lt: str, chapter: int) -> str | None:
    _ = chapter
    if not lt.startswith("#"):
        return None
    text = re.sub(r"^#+\s*", "", lt).strip()
    if _DROP_HEADINGS.match(text):
        return ""
    if re.match(r"^\d+\.\d+\s+\S", text):
        return f"### {text}"
    if re.match(r"^\d+\s+\S", text):
        return f"## {text}"
    if lt.startswith("## "):
        return f"## {text}"
    return f"### {text}"


__all__ = ["draw_figures", "heading_hook"]
