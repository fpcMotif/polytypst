import io
from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from polytypst import pipeline as pipeline_module
from polytypst.ocr.scan import RENDERS_MANIFEST, SourceScan, SourceScanError
from polytypst.pipeline import UniversalPDFPipeline


def photo(path: Path, size: tuple[int, int] = (300, 400), color: str = "white") -> Path:
    Image.new("RGB", size, color).save(path)
    return path


def spread_pdf(path: Path, sheets: int = 3) -> Path:
    """Landscape sheets with ink on the left half only."""
    doc = pymupdf.open()
    for _ in range(sheets):
        page = doc.new_page(width=800, height=500)
        page.draw_rect(pymupdf.Rect(50, 50, 350, 450), color=(0, 0, 0), fill=(0, 0, 0))
    doc.save(path)
    return path


def test_folder_pages_follow_natural_name_order_not_trailing_numbers(
    tmp_path: Path,
) -> None:
    photos = tmp_path / "photos"
    photos.mkdir()
    for name, color in (
        ("IMG_1234.png", "red"),
        ("IMG_99.png", "green"),
        ("IMG_100.png", "blue"),
    ):
        photo(photos / name, color=color)
    (photos / "notes.txt").write_text("not a page", encoding="utf-8")

    scan = SourceScan(photos)
    pages = scan.pages(tmp_path / "renders")

    assert scan.page_count == 3
    assert scan.pdf is None
    assert [p.number for p in pages] == [1, 2, 3]
    assert [p.path.read_bytes() for p in pages] == [
        (photos / name).read_bytes()
        for name in ("IMG_99.png", "IMG_100.png", "IMG_1234.png")
    ]


def test_a_single_image_is_a_one_page_scan(tmp_path: Path) -> None:
    (page,) = SourceScan(photo(tmp_path / "page.jpg")).pages(tmp_path / "renders")
    assert page.number == 1
    assert page.path.name == "p_001.jpg"


def test_exif_rotated_photo_is_rendered_upright(tmp_path: Path) -> None:
    source = tmp_path / "phone.jpg"
    exif = Image.Exif()
    exif[0x0112] = 6
    Image.new("RGB", (400, 300), "white").save(source, exif=exif)

    (page,) = SourceScan(source).pages(tmp_path / "renders")

    with Image.open(page.path) as im:
        assert im.size == (300, 400)


def test_two_up_spreads_split_into_twice_as_many_pages(tmp_path: Path) -> None:
    scan = SourceScan(spread_pdf(tmp_path / "spreads.pdf"))
    pages = scan.pages(tmp_path / "renders", dpi=72)

    assert scan.split
    assert scan.page_count == 6
    assert scan.pdf is None
    with Image.open(pages[0].path) as left, Image.open(pages[1].path) as right:
        assert left.size == (400, 500)
        assert left.convert("L").getextrema()[0] == 0
        assert right.convert("L").getextrema() == (255, 255)


def test_portrait_pdf_is_its_own_page_map(tmp_path: Path) -> None:
    path = tmp_path / "book.pdf"
    doc = pymupdf.open()
    for _ in range(4):
        doc.new_page(width=500, height=800)
    doc.save(path)

    scan = SourceScan(path)

    assert (scan.page_count, scan.split, scan.pdf) == (4, False, path)


def test_large_embedded_png_passes_through_and_grey_renders_fresh(
    tmp_path: Path,
) -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 1600), "white").save(buffer, format="PNG")
    path = tmp_path / "scan.pdf"
    doc = pymupdf.open()
    doc.new_page(width=600, height=800).insert_image(
        pymupdf.Rect(0, 0, 600, 800), stream=buffer.getvalue()
    )
    doc.save(path)
    scan = SourceScan(path)

    (native,) = scan.pages(tmp_path / "native")
    (grey,) = scan.pages(tmp_path / "grey", dpi=72, grey=True)

    assert (
        native.path.read_bytes()
        == pymupdf.open(path).extract_image(pymupdf.open(path)[0].get_images()[0][0])[
            "image"
        ]
    )
    with Image.open(grey.path) as im:
        assert (im.mode, im.size) == ("L", (600, 800))


def test_renders_are_reused_until_the_settings_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scan = SourceScan(spread_pdf(tmp_path / "spreads.pdf"))
    renders = tmp_path / "renders"
    first = scan.pages(renders, dpi=72)
    first[2].path.unlink()
    rendered: list[int] = []
    original = SourceScan._render

    def spy(self: SourceScan, number: int, out_dir: Path, dpi: int, grey: bool) -> Path:
        rendered.append(number)
        return original(self, number, out_dir, dpi, grey)

    monkeypatch.setattr(SourceScan, "_render", spy)

    _ = scan.pages(renders, dpi=72)
    assert rendered == [3]

    rendered.clear()
    _ = scan.pages(renders, dpi=36, numbers=[1])
    assert rendered == [1]
    assert sorted(p.name for p in renders.iterdir()) == sorted(
        [RENDERS_MANIFEST, "p_001.png"]
    )


def test_bad_inputs_are_named(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(SourceScanError, match="no page images"):
        _ = SourceScan(empty)
    with pytest.raises(SourceScanError, match="not a PDF"):
        _ = SourceScan(_write(tmp_path / "notes.txt"))
    with pytest.raises(SourceScanError, match="not found"):
        _ = SourceScan(tmp_path / "missing.pdf")
    with pytest.raises(SourceScanError, match="no page 2"):
        _ = SourceScan(photo(tmp_path / "one.png")).pages(
            tmp_path / "renders", numbers=[2]
        )


def test_pipeline_matches_books_by_their_page_count_after_the_split(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[int] = []

    def stop(source: Path, total_pages: int, **_: object) -> None:
        seen.append(total_pages)
        raise RuntimeError("stop after spec lookup")

    monkeypatch.setattr(pipeline_module, "resolve_monograph_spec", stop)
    with pytest.raises(RuntimeError, match="stop after spec lookup"):
        _ = UniversalPDFPipeline(
            spread_pdf(tmp_path / "spreads.pdf"), tmp_path / "out"
        ).process()
    assert seen == [6]


def _write(path: Path) -> Path:
    path.write_text("text", encoding="utf-8")
    return path
