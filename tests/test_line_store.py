import json
import shutil
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from polytypst.ocr.lines import ImageLineStore, LineStore
from polytypst.ocr.pages import LinePage, OcrLine, OcrStalled, PageImage
from polytypst.ocr.tesseract import TesseractReader, tesseract_languages, tsv_lines


class FakeReader:
    def __init__(
        self, provenance: str = "fake:lines", skip: Sequence[int] = ()
    ) -> None:
        self.provenance = provenance
        self.skip = set(skip)
        self.seen: list[int] = []

    def read(self, pages: Sequence[PageImage]) -> Iterator[LinePage]:
        for page in pages:
            self.seen.append(page.number)
            if page.number not in self.skip:
                yield LinePage(
                    page.number,
                    (OcrLine(f"line {page.number}", 0.1, 0.8, 0.5, 0.02, 0.9),),
                )


def images(tmp_path: Path, numbers: Sequence[int]) -> list[PageImage]:
    return [PageImage(n, tmp_path / f"page_{n:03d}.png") for n in numbers]


def test_store_reads_only_pages_without_a_cached_file(tmp_path: Path) -> None:
    store_dir = tmp_path / "source_ocr"
    store_dir.mkdir()
    old = [{"text": "kept", "x": 0.2, "y": 0.5, "w": 0.3, "h": 0.01}]
    (store_dir / "p002.json").write_text(json.dumps(old), encoding="utf-8")
    reader = FakeReader()

    found = LineStore(store_dir).read(images(tmp_path, [1, 2, 3]), reader)

    assert reader.seen == [1, 3]
    assert found[2] == (OcrLine("kept", 0.2, 0.5, 0.3, 0.01),)
    assert found[3] == (OcrLine("line 3", 0.1, 0.8, 0.5, 0.02, 0.9),)
    made_by = json.loads((store_dir / "lines.json").read_text(encoding="utf-8"))[
        "pages"
    ]
    assert made_by == {"1": "fake:lines", "3": "fake:lines"}


def test_store_keeps_earlier_provenance_and_leaves_failed_pages_pending(
    tmp_path: Path,
) -> None:
    store = LineStore(tmp_path / "source_ocr")
    store.read(images(tmp_path, [1, 2]), FakeReader("first", skip=[2]))
    second = FakeReader("second")

    found = store.read(images(tmp_path, [1, 2]), second)

    assert second.seen == [2]
    assert set(found) == {1, 2}
    made_by = json.loads((store.directory / "lines.json").read_text(encoding="utf-8"))[
        "pages"
    ]
    assert made_by == {"1": "first", "2": "second"}


class StallingReader(FakeReader):
    def read(self, pages: Sequence[PageImage]) -> Iterator[LinePage]:
        yield from super().read(pages[:1])
        raise OcrStalled("runner stopped")


def figure_files(tmp_path: Path, names: Sequence[str]) -> list[Path]:
    paths = [tmp_path / name for name in names]
    for path in paths:
        path.write_bytes(path.name.encode())
    return paths


def test_image_store_reads_each_image_once_by_its_bytes(tmp_path: Path) -> None:
    store = ImageLineStore(tmp_path / "figure_ocr")
    first, second = figure_files(tmp_path, ["fig_1.png", "fig_2.png"])
    store.read([first, second], FakeReader())
    again = FakeReader()

    store.read([first, second], again)
    second.write_bytes(b"redrawn")
    store.read([first, second], again)

    assert again.seen == [2]
    assert store.lines(first, "fake:lines") == (OcrLine("line 1", 0.1, 0.8, 0.5, 0.02, 0.9),)


def test_image_store_keeps_the_lines_read_before_a_stall(tmp_path: Path) -> None:
    store = ImageLineStore(tmp_path / "figure_ocr")
    first, second = figure_files(tmp_path, ["fig_1.png", "fig_2.png"])

    with pytest.raises(OcrStalled):
        store.read([first, second], StallingReader())
    resumed = FakeReader()
    store.read([first, second], resumed)

    assert resumed.seen == [2]


TSV_ROWS = (
    "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext",
    "1\t1\t0\t0\t0\t0\t0\t0\t1000\t2000\t-1\t",
    "4\t1\t1\t1\t1\t0\t100\t200\t300\t40\t-1\t",
    "5\t1\t1\t1\t1\t1\t100\t200\t120\t40\t90\tHello",
    "5\t1\t1\t1\t1\t2\t240\t210\t160\t30\t70\tworld",
    "5\t1\t1\t1\t2\t1\t100\t300\t50\t20\t80\tNext",
    "5\t1\t1\t1\t2\t2\t160\t300\t50\t20\t-1\t ",
    "5\t1\t2\t1\t1\t1\t500\t1000\t100\t100\t60\tOther",
)
TSV = "\n".join(TSV_ROWS)


def test_tsv_words_group_into_lines_with_bottom_left_boxes() -> None:
    lines = tsv_lines(TSV)

    assert [line.text for line in lines] == ["Hello world", "Next", "Other"]
    hello = lines[0]
    assert (hello.x, hello.w) == pytest.approx((0.1, 0.3))
    assert (hello.y, hello.h) == pytest.approx((1 - 240 / 2000, 40 / 2000))
    assert hello.confidence == pytest.approx(0.8)
    assert lines[2].y == pytest.approx(0.45)


def test_tsv_without_a_page_row_has_no_lines() -> None:
    assert (
        tsv_lines(TSV.replace("1\t1\t0\t0\t0\t0\t0\t0\t1000\t2000\t-1\t\n", "")) == ()
    )


def test_spec_languages_map_to_tesseract_codes() -> None:
    assert tesseract_languages(["en-US", "fr-FR", "chi_sim"]) == "eng+fra+chi_sim"


@pytest.mark.skipif(
    shutil.which("tesseract") is None, reason="tesseract is not installed"
)
def test_tesseract_reads_a_rendered_line(tmp_path: Path) -> None:
    image = Image.new("L", (1200, 400), 255)
    ImageDraw.Draw(image).text(
        (100, 150), "HELLO WORLD", fill=0, font=ImageFont.load_default(64)
    )
    path = tmp_path / "page_001.png"
    image.save(path)

    (page,) = TesseractReader(["en-US"]).read([PageImage(1, path)])

    assert page.number == 1
    assert "HELLO WORLD" in [line.text for line in page.lines]
    assert all(0 <= line.y <= 1 for line in page.lines)


def test_line_store_page_and_verifier_reuse_line_cache(tmp_path: Path) -> None:
    import pymupdf

    from polytypst.ocr.lines import LineStore, source_ocr_dir
    from polytypst.ocr.scan import SourceScanError
    from polytypst.ocr.transcripts import TranscriptStore
    from polytypst.ocr.verifier import OCRVerifier

    pdf = tmp_path / "scan.pdf"
    doc = pymupdf.open()
    doc.new_page(width=300, height=500)
    doc.save(pdf)

    store = LineStore(source_ocr_dir(tmp_path))
    img_dir = tmp_path / "page_renders"
    img_dir.mkdir()
    img_path = img_dir / "p_001.png"
    Image.new("L", (300, 500), 255).save(img_path)

    reader = FakeReader("fake:vision")
    store.ensure_pdf(pdf, ("en-US",), reader=reader)
    page = store.page(1)
    assert (page.width, page.height) == (300.0, 500.0)
    assert [line.text for line in page.lines] == ["line 1"]
    assert reader.seen == [1]

    with pytest.raises(SourceScanError):
        store.page(2)

    tx_dir = tmp_path / "markdown_pages"
    tx_dir.mkdir()
    (tx_dir / "p_001.md").write_text("line 1", encoding="utf-8")
    _ = TranscriptStore(tx_dir)

    second_reader = FakeReader("fake:second")
    verifier = OCRVerifier(("en-US",), reader=second_reader)
    report = verifier.verify_pages(img_dir, tx_dir)
    assert report.total_pages_verified == 1
    assert second_reader.seen == []

