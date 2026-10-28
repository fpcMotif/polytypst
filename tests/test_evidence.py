import json
from pathlib import Path

import pymupdf
from PIL import Image

from polytypst import evidence
from polytypst.ocr.pages import OcrLine
from polytypst.review import Finding


def test_span_box_measures_the_span_in_character_widths_from_the_top_left():
    line = OcrLine("ab一二", x=0.1, y=0.5, w=0.6, h=0.02)
    box = evidence.span_box(line, "一")
    assert round(box.top, 6) == 0.48
    assert round(box.left, 6) == round(0.1 + 0.6 * 1 / 3, 6)
    assert round(box.right, 6) == round(0.1 + 0.6 * 2 / 3, 6)


def test_zoom_draws_a_red_box_where_the_ocr_found_the_span(tmp_path: Path):
    scan = tmp_path / "scan.pdf"
    doc = pymupdf.open()
    doc.new_page(width=200, height=200)
    doc.save(scan)
    ocr = tmp_path / "source_ocr"
    ocr.mkdir()
    (ocr / "p001.json").write_text(
        json.dumps([{"text": "一二三四", "x": 0.2, "y": 0.5, "w": 0.6, "h": 0.05}]),
        encoding="utf-8",
    )
    out = evidence.zoom(scan, ocr, 1, "三", "label", tmp_path / "z.png")
    image = Image.open(out).convert("RGB")
    reds = [image.getpixel((x, 40)) for x in range(image.width)]
    assert any(r > 150 and g < 80 and b < 80 for r, g, b in reds)


def test_note_changes_names_each_note_that_moved_between_note_and_body():
    before = {"book": {"7": [["①", "a list item"]], "8": [["①", "a note"]]}}
    after = {"book": {"8": [["①", "a note"]], "9": [["1", "1990年"]]}}
    assert evidence.note_changes(before, after) == [
        evidence.NoteChange("book", 7, "note->body", "①", "a list item"),
        evidence.NoteChange("book", 9, "body->note", "1", "1990年"),
    ]


def test_sweep_records_the_notes_the_cleaner_cuts_from_each_page(
    tmp_path: Path, book_state_root: Path
):
    pages = book_state_root / "1_书" / "markdown_pages"
    pages.mkdir(parents=True)
    (pages / "p_001.md").write_text("正文估算①。\n\n① 注释的内容。\n", encoding="utf-8")
    (pages / "p_002.md").write_text(
        "主要结论如下：\n\n①结论一。\n\n②结论二。\n", encoding="utf-8"
    )
    assert evidence.sweep([tmp_path / "1_书"]) == {
        "1_书": {"1": [["①", "注释的内容。"]]}
    }


def test_report_embeds_each_evidence_png_and_escapes_the_text(tmp_path: Path):
    shot = tmp_path / "output" / "review_evidence" / "z.png"
    shot.parent.mkdir(parents=True)
    Image.new("RGB", (4, 4), "white").save(shot)
    finding = Finding(
        "B2-39",
        "2 书",
        "P0",
        "transcript",
        "p_147.md:6:383",
        "P① read as <Ω>",
        "See output/review_evidence/z.png",
        "fixed",
    )
    html = evidence.report([finding], "OCR errors", tmp_path)
    assert "data:image/png;base64," in html
    assert "&lt;Ω&gt;" in html
    assert "p_147.md:6:383" in html


def test_report_command_writes_only_the_findings_it_names(tmp_path: Path):
    rows = [
        Finding(f"X-{n}", "b", "P1", "both", "w", f"what {n}", "ev").__dict__
        for n in (1, 2)
    ]
    findings = tmp_path / "findings.jsonl"
    findings.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = tmp_path / "r.html"
    assert (
        evidence.main(["report", str(findings), "--ids", "X-2", "--out", str(out)]) == 0
    )
    html = out.read_text(encoding="utf-8")
    assert "what 2" in html and "what 1" not in html
