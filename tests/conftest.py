from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from polytypst.ocr.pages import PageImage

PAPER = (222, 210, 180)
INK = (40, 35, 30)
COVER = (40, 82, 112)
COVER_INK = (140, 120, 30)

PageRender = Callable[..., PageImage]


def sheet(paper: tuple[int, int, int], ink: tuple[int, int, int] | None) -> Image.Image:
    img = Image.new("RGB", (400, 600), paper)
    draw = ImageDraw.Draw(img)
    for x in range(400):
        shade = 30 * x // 400
        draw.line((x, 0, x, 599), fill=tuple(c - shade for c in paper))
    if ink is not None:
        for row in range(10):
            draw.rectangle((40, 60 + row * 40, 360, 72 + row * 40), fill=ink)
    return img


@pytest.fixture(autouse=True)
def book_state_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "books"
    monkeypatch.setenv("POLYTYPST_BOOKS", str(root))
    return root


@pytest.fixture
def page_render(tmp_path: Path) -> PageRender:
    renders = tmp_path / "page_renders"
    renders.mkdir(exist_ok=True)

    def render(number: int, blank: bool = False, suffix: str = ".png") -> PageImage:
        path = renders / f"p_{number:03d}{suffix}"
        sheet(PAPER, None if blank else INK).save(path)
        return PageImage(number, path)

    return render
