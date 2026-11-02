import io
import json
from pathlib import Path

import numpy as np
import pymupdf
import pytest
from PIL import Image, ImageFilter

from scripts.scan_sheet import (
    Case,
    Strip,
    card,
    cases_from_verdicts,
    page_html,
    scan_jpeg,
    strip_png,
    write_strips,
)

PAGE = pymupdf.Rect(0, 0, 144, 216)


def scan_page_jpeg(mode: str, size: tuple[int, int]) -> bytes:
    rng = np.random.default_rng(7)
    noise = rng.integers(0, 256, (size[1], size[0], 3 if mode == "RGB" else 1), dtype=np.uint8).squeeze()
    image = Image.fromarray(noise).resize((150, 225)).resize(size, Image.Resampling.BICUBIC)
    out = io.BytesIO()
    image.filter(ImageFilter.GaussianBlur(3)).save(out, "JPEG", quality=92)
    return out.getvalue()


def scan(tmp_path: Path, *modes: str, size: tuple[int, int] = (1200, 1800)) -> pymupdf.Document:
    doc = pymupdf.open()
    for mode in modes:
        page = doc.new_page(width=PAGE.width, height=PAGE.height)
        image = doc.get_new_xref()
        colorspace = "/DeviceRGB" if mode == "RGB" else "/DeviceGray"
        doc.update_object(
            image,
            f"<< /Type /XObject /Subtype /Image /Width {size[0]} /Height {size[1]} /ColorSpace {colorspace} /BitsPerComponent 8 >>",
        )
        doc.update_stream(image, scan_page_jpeg(mode, size), compress=False)
        doc.xref_set_key(image, "Filter", "/DCTDecode")
        doc.xref_set_key(page.xref, "Resources", f"<< /XObject << /Im0 {image} 0 R >> >>")
        contents = doc.get_new_xref()
        doc.update_object(contents, "<< >>")
        doc.update_stream(contents, f"q {PAGE.width} 0 0 {PAGE.height} 0 0 cm /Im0 Do Q".encode())
        doc.xref_set_key(page.xref, "Contents", f"{contents} 0 R")
    doc.save(tmp_path / "scan.pdf")
    return pymupdf.open(tmp_path / "scan.pdf")


def gray(png: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(png)).convert("L"), dtype=float)


@pytest.mark.parametrize(("mode", "size"), [("RGB", (1200, 1800)), ("L", (1200, 1800)), ("RGB", (1203, 1805))])
def test_strips_cut_from_the_scan_jpeg_match_the_mupdf_render(tmp_path: Path, mode: str, size: tuple[int, int]) -> None:
    doc = scan(tmp_path, mode, size=size)
    strips = [
        Strip(1, band, dpi, tmp_path / f"s{k}.png")
        for k, (band, dpi) in enumerate([((0.0, 1.0), 150), ((0.3, 0.42), 300), ((0.9, 1.0), 300), ((0.1, 0.5), 110)])
    ]
    write_strips(doc, strips)
    for s in strips:
        ours, reference = gray(s.out.read_bytes()), gray(strip_png(doc, s.page, s.band, s.dpi))
        assert ours.shape == reference.shape
        assert 10 * np.log10(255**2 / ((ours - reference) ** 2).mean()) > 40


def test_only_a_bare_full_page_jpeg_takes_the_fast_path(tmp_path: Path) -> None:
    doc = scan(tmp_path, "RGB", "RGB", "RGB", "RGB", "RGB")
    doc[1].draw_rect(pymupdf.Rect(10, 10, 50, 50))
    doc[2].insert_text((20, 40), "visible")
    doc[3].set_rotation(90)
    doc[4].insert_text((20, 40), "hidden OCR layer", render_mode=3)
    assert [scan_jpeg(page) is not None for page in doc] == [True, False, False, False, True]


def test_a_scan_typo_card_marks_the_printed_text_and_shows_what_was_meant() -> None:
    html = card(Case(page=74, find="节纪", scan="20 节纪", meant="20 世纪", note="Wrong character"), b"PNG")
    assert "<b>p74</b> · scan prints <mark>20 节纪</mark> · meant <span class=\"ok\">20 世纪</span>" in html
    assert "<small>Wrong character</small>" in html
    assert 'src="data:image/png;base64,UE5H"' in html


def test_a_transcript_error_card_marks_the_transcript_and_shows_the_scan() -> None:
    html = card(Case(page=12, find="必不可免", scan="必不可免", transcript="必不可少"), b"PNG")
    assert "transcript has <mark>必不可少</mark> · scan prints <span class=\"ok\">必不可免</span>" in html


def test_a_card_escapes_its_text() -> None:
    assert "&lt;b&gt;" in card(Case(page=1, find="x", scan="<b>", meant="b"), b"")


def test_verdicts_give_a_case_for_each_record_of_the_chosen_verdict() -> None:
    lines = [
        {"page": 74, "kind": "word", "transcript": "20 节纪", "scan": "20 世纪", "verdict": "scan_typo", "detail": "p74: meant 20 世纪"},
        {"page": 12, "kind": "word", "transcript": "必不可少", "scan": "必不可免", "verdict": "real", "detail": ""},
        {"page": 20, "kind": "mark", "transcript": "", "scan": "、", "verdict": "false_positive", "detail": ""},
    ]
    text = "\n".join(json.dumps(r, ensure_ascii=False) for r in lines)
    assert cases_from_verdicts(text, "scan_typo") == [
        Case(page=74, find="20 节纪", scan="20 节纪", meant="20 世纪", note="p74: meant 20 世纪")
    ]
    assert cases_from_verdicts(text, "real") == [Case(page=12, find="必不可免", scan="必不可免", transcript="必不可少")]


def test_the_page_keeps_both_colour_schemes_and_the_cards_in_order() -> None:
    html = page_html("Scan Typos", "Intro", ["<figure>1</figure>", "<figure>2</figure>"])
    assert "<title>Scan Typos</title>" in html and "<h1>Scan Typos</h1>" in html
    assert "--mark:#ffe08a" in html and "prefers-color-scheme:dark" in html
    assert html.index("<figure>1</figure>") < html.index("<figure>2</figure>")
