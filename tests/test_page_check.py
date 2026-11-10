import io
import json
import re
from dataclasses import replace
from pathlib import Path

import numpy as np
import pymupdf
import pytest
from PIL import Image, ImageFilter

import polytypst.page_check.verify as verify_module
from polytypst.edition import Book
from polytypst.ocr.pages import OcrLine
from polytypst.page_check import PageCheck, strip_png
from polytypst.page_check.check import run
from polytypst.page_check.lint import lint, lint_fixups
from polytypst.page_check.render import RenderCheck, caption_label
from polytypst.page_check.results import write_jsonl
from polytypst.page_check.sheet import (
    Strip,
    cases_from_verdicts,
    scan_jpeg,
    scan_sheet,
    sheets,
    write_strips,
)
from polytypst.page_check.verify import gate, triage, verify

SCAN_PAGES = 12
LINE_H = 0.03


@pytest.fixture
def scan(tmp_path: Path) -> Path:
    doc = pymupdf.open()
    for n in range(1, SCAN_PAGES + 1):
        doc.new_page(width=400, height=600).insert_text((40, 60), f"page {n}")
    path = tmp_path / "scan.pdf"
    doc.save(path)
    return path


def ocr_line(text: str, top: float) -> dict:
    return OcrLine(text, x=0.1, y=1 - top - LINE_H, w=0.8, h=LINE_H).__dict__


def make_check(
    tmp_path: Path, scan: Path, pages: dict[int, str], lines: dict[int, list[str]] | None = None, key: str = "probe"
) -> PageCheck:
    book = Book.adhoc(scan, out_dir=tmp_path / "out" / key)
    book.transcripts.mkdir(parents=True, exist_ok=True)
    for n, text in pages.items():
        (book.transcripts / f"p_{n:03d}.md").write_text(text, encoding="utf-8")
    book.ocr.mkdir(parents=True, exist_ok=True)
    for n, texts in (lines or {}).items():
        rows = [ocr_line(text, 0.1 + 0.05 * k) for k, text in enumerate(texts)]
        (book.ocr / f"p{n:03d}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return PageCheck(key, book, root=tmp_path / "results", scan_override=scan)


def rules_by_page(check: PageCheck) -> dict[int, list[str]]:
    found: dict[int, list[str]] = {}
    for hit in lint(check):
        found.setdefault(hit["page"], []).append(hit["rule"])
    return found


class FakeAgents:
    def __init__(self, verdict: str = "real") -> None:
        self.prompts: list[str] = []
        self.verdict = verdict

    def __call__(self, runbook: str, prompt: str, model: str, log: Path) -> int:
        self.prompts.append(prompt)
        out = re.search(r"OUT=(\S+?)\.?$", prompt)
        named = re.search(r"ITEMS=(\S+)", prompt)
        if out and named:
            items = named[1]
            if items.endswith(".jsonl"):
                records = [json.loads(line) for line in Path(items).read_text(encoding="utf-8").splitlines()]
                write_jsonl(Path(out[1]), [{**r, "verdict": self.verdict, "detail": runbook} for r in records])
            else:
                write_jsonl(Path(out[1]), [{"label": label} for label in items.split(",")])
        return 0


def test_lint_finds_the_transcript_errors_that_book_4_had(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {
        1: "Institute forHuman Settlements",
        2: "Effects of LandUse Control",
        3: "| 中小企业</ th> |",
        4: "下降了 -0 .4%。",
        5: "② 即《帝国数据库的全国倒闭汇总以及东京商工调查。",
    })
    assert rules_by_page(check) == {
        1: ["glued_words"],
        2: ["glued_words"],
        3: ["broken_tag"],
        4: ["spaced_decimal"],
        5: ["lone_book_mark"],
    }


def test_lint_leaves_correct_text_and_titles_that_run_across_a_page_alone(tmp_path: Path, scan: Path) -> None:
    opens = "首段。\n\n本套丛书包括第三册《国际经济环境的变化"
    check = make_check(tmp_path, scan, {
        1: "MacKinnon (1991) and McDonald test the series.",
        2: "2. 2001 年及以前的数据，增长 0.4%。",
        3: "组织译印了第三册《国际经济环境的变化\n与日本经济》。",
        4: "| 中小企业</th> |",
        5: opens,
        6: "## 2 财政政策与社会保障\n\n与日本经济》等。\n\n下一段。",
        7: opens,
        8: "下一页。",
        9: opens,
        10: "2 宏观经济与产业结构\n\n与日本经济》等。",
    })
    assert rules_by_page(check) == {7: ["lone_book_mark"]}


def test_lint_finds_a_running_head_left_in_the_built_book(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {1: "正文。"}, key="4_不良债权与金融危机")
    typ = "正文一段。\n\n120 不良债权与金融危机\n\n正文。\n#set page(header: [不良债权与金融危机])\n"
    built = next(iter(check.book.editions.values())).source("typ")
    built.parent.mkdir(parents=True)
    built.write_text(typ, encoding="utf-8")
    heads = [hit for hit in lint(check) if hit["rule"] == "running_head"]
    assert [(hit["page"], hit["transcript"]) for hit in heads] == [(None, "120 不良债权与金融危机")]


def test_lint_finds_dead_fixups_from_the_book_spec(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {1: "正文。", 2: "正文。"})
    spec = replace(check.book.spec, transcript_fixups={1: (("不存在", "新值"),), 2: (("正文", "修订正文"),)})
    check = replace(check, book=replace(check.book, spec=spec))
    assert rules_by_page(check) == {1: ["dead_fixup"]}


def test_a_line_fixup_that_deletes_across_lines_under_dotall_is_found() -> None:
    page = "（1）不同年龄段的变化（1980年=0）\n\n表10-1 估计结果\n\n（2）不同学历的变化（高中=100）\n"
    greedy = ((r"(?m)^（[12]）不同.*的变化（.*）\n*", ""),)
    bounded = ((r"(?m)^（[12]）不同[^\n]*的变化（[^\n]*）\n*", ""),)
    assert [h["rule"] for h in lint_fixups(page, greedy)] == ["multiline_delete"]
    assert lint_fixups(page, bounded) == []
    greedy_without_m = ((r"（1）不同.*的变化（.*）\n*", ""),)
    assert [h["rule"] for h in lint_fixups(page, greedy_without_m)] == ["multiline_delete"]
    lazy = ((r"（1）.*?（高中=100）", ""),)
    assert [h["rule"] for h in lint_fixups(page, lazy)] == ["multiline_delete"]


def test_dead_and_misplaced_fixups_are_found() -> None:
    page = "正文①。\n\n<table><tr><th>旧值</th></tr></table>\n\n① 注文原词。\n"
    assert [h["rule"] for h in lint_fixups(page, (("不存在", "新值"),))] == ["dead_fixup"]
    assert [
        h["rule"]
        for h in lint_fixups(page, (), page_fixups=(("<th>旧值</th>", "<th>新值</th>"), ("注文原词", "注文新词")))
    ] == ["dead_fixup", "dead_fixup"]
    assert lint_fixups(
        page, (("<th>旧值</th>", "<th>新值</th>"), ("注文原词", "注文新词")), page_fixups=(("正文", "修订正文"),)
    ) == []
    big = "首行\n" + ("中段文字" * 90) + "\n尾行\n"
    assert [h["rule"] for h in lint_fixups(big, ((r"首行.*尾行", ""),))] == ["multiline_delete"]
    assert lint_fixups(big, ((r"(?s)\A.*?\Z", ""),)) == []
    assert [h["rule"] for h in lint_fixups(big, ((r"首行.*?尾行", ""),))] == ["multiline_delete"]
    assert [h["rule"] for h in lint_fixups(big, ((r"中段文字(中段文字)+", ""),))] == ["multiline_delete"]


def issue(kind: str, transcript: str, scan: str = "", **extra: object) -> dict:
    return {"kind": kind, "transcript": transcript, "scan": scan, **extra}


def test_triage_settles_width_spacing_and_running_head_claims_and_queues_the_rest(tmp_path: Path, scan: Path) -> None:
    check = make_check(
        tmp_path, scan, {1: "x", 2: "x", 3: "x"}, {1: ["Institute forHuman Settlements"]}, key="5_财政政策与社会保障"
    )
    write_jsonl(check.results.folder / "p1-3.jsonl", [
        {"page": 1, "issues": [
            issue("mark", "多大?", "多大？"),
            issue("word", "20 世纪", "20世纪"),
            issue("word", "forHuman", "for Human"),
            issue("table_cell", "</ tr>", "</tr>"),
            issue("sum", "4740", "4740"),
            issue("word", "一已", "一己"),
        ]},
        {"page": 2, "issues": [
            issue("extra_text", "12 财政政策与社会保障"),
            issue("extra_text", "## 2 财政政策与社会保障"),
            issue("extra_text", "财政政策与社会保障 43"),
            issue("extra_text", "2 宏观经济与产业结构"),
            issue("extra_text", "12 财政政策与社会保障", "12 财政政策与社会保障"),
            issue("word", "12 财政政策与社会保障"),
        ]},
        {"page": 3, "issues": [issue("word", "必不可少", "必不可免", line=3, note="")]},
    ])
    write_jsonl(check.results.verdicts_path, [
        {**issue("word", "必不可少", "必不可免"), "page": 3, "line": 9, "verdict": "real", "detail": "p3", "by": "m"}
    ])

    assert triage(check) == (5, 7)

    auto = [v["transcript"] for v in check.results.verdicts() if v["by"] == "auto"]
    assert auto == ["多大?", "20 世纪", "12 财政政策与社会保障", "## 2 财政政策与社会保障", "财政政策与社会保障 43"]
    queue = check.results.queue()
    assert [(q["page"], q["transcript"]) for q in queue] == [
        (1, "forHuman"), (1, "</ tr>"), (1, "4740"), (1, "一已"),
        (2, "2 宏观经济与产业结构"), (2, "12 财政政策与社会保障"), (2, "12 财政政策与社会保障"),
    ]
    with Image.open(queue[0]["zoom"]) as zoomed, Image.open(queue[0]["page_image"]) as page:
        assert zoomed.height < page.height / 3


def test_verify_adds_each_batch_verdict_once_and_skips_batches_that_have_output(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {1: "x"}, {1: ["一已"]})
    write_jsonl(check.results.folder / "p1-1.jsonl", [
        {"page": 1, "issues": [issue("word", "一已", "一己"), issue("word", "甲", "乙"), issue("word", "丙", "丁")]},
    ])
    triage(check)
    agents = FakeAgents()

    lines = list(verify(check, size=2, jobs=2, model="judge", runner=agents))

    assert lines[0] == "3 issues, 2 of 2 batches to run, 2 at a time"
    assert lines[-1] == "3 verdicts added"
    assert len(agents.prompts) == 2
    assert {(v["transcript"], v["verdict"], v["by"]) for v in check.results.verdicts()} == {
        ("一已", "real", "judge"), ("甲", "real", "judge"), ("丙", "real", "judge"),
    }
    rerun = list(verify(check, size=2, jobs=2, model="judge", runner=agents))
    assert rerun[0] == "0 issues, 0 of 0 batches to run, 2 at a time"
    assert len(agents.prompts) == 2


def test_a_failed_verify_batch_reports_the_agent_error(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {1: "x"})
    write_jsonl(check.results.folder / "p1-1.jsonl", [{"page": 1, "issues": [issue("word", "甲", "乙")]}])
    triage(check)

    def failing(runbook: str, prompt: str, model: str, log: Path) -> int:
        log.write_text("starting\nError: No API key found for anthropic\n", encoding="utf-8")
        return 1

    report = list(verify(check, size=5, jobs=1, model="claude-haiku-5-5", runner=failing))[1]
    assert "exit 1" in report
    assert "No API key found for anthropic" in report


def test_verify_ignores_a_verdict_that_is_not_one_of_the_four(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {1: "x"})
    write_jsonl(check.results.folder / "p1-1.jsonl", [{"page": 1, "issues": [issue("word", "甲", "乙")]}])
    triage(check)
    assert list(verify(check, size=5, jobs=1, model="judge", runner=FakeAgents("maybe")))[-1] == "0 verdicts added"


def test_a_page_counts_as_checked_only_with_the_receipt_for_its_scan_png_and_transcript(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {n: f"page {n}" for n in range(1, 6)})
    for n in (1, 2):
        check.page_png(n).parent.mkdir(parents=True, exist_ok=True)
        check.page_png(n).write_bytes(f"png {n}".encode())
    write_jsonl(check.results.folder / "p1-2.jsonl", [
        {"page": 1, "receipt": check.receipt(1), "issues": []},
        {"page": 2, "receipt": "000000000000", "issues": [issue("word", "a", "b")]},
    ])
    tally = check.tally()
    assert (tally.checked, tally.unproven) == ({1}, {2})
    assert check.chunks(2) == [(2, 3), (4, 5)]


def test_a_verdict_line_that_is_not_one_of_the_four_settles_no_claim(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {3: "a"})
    claim = {"page": 3, **issue("word", "a", "b")}
    check.results.add_verdicts([{**claim, "verdict": "unsure"}])
    assert check.results.verdict_keys() == set()
    check.results.add_verdicts([{**claim, "verdict": "real"}])
    assert check.results.verdict_keys() == {(3, "word", "a", "b")}


def test_a_record_with_an_unknown_issue_kind_does_not_check_its_page(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {1: "page 1"})
    check.page_png(1).parent.mkdir(parents=True, exist_ok=True)
    check.page_png(1).write_bytes(b"png 1")
    write_jsonl(check.results.folder / "p1-1.jsonl", [
        {"page": 1, "receipt": check.receipt(1), "issues": [issue("wrod", "a", "b")]},
    ])
    tally = check.tally()
    assert tally.checked == set()
    assert tally.bad_lines


def test_run_starts_one_agent_for_each_chunk_of_unchecked_pages(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {n: f"page {n}" for n in range(1, 6)}, key="4_banks")
    agents = FakeAgents()
    lines = list(run([check], size=2, jobs=2, model="m", runner=agents))
    assert lines[0] == "3 chunks, 2 at a time"
    assert sorted(agents.prompts) == [
        f"Follow this runbook with BOOK=4_banks FIRST={a} LAST={b}." for a, b in ((1, 2), (3, 4), (5, 5))
    ]


def test_suspects_name_the_transcript_line_and_the_scan_band_where_the_ocr_disagrees(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {1: "# 标题\n\n第一行文字。"}, {1: ["标题", "第一行文宇。"]})
    assert check.suspects(1) == ["line 3 band 0.13,0.20 | transcript: 第一行文[字] | ocr: [宇]"]


def test_tables_read_html_and_pipe_tables_as_rows(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {1: "<table><tr><th>年 份</th><td>1</td></tr></table>\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"})
    assert check.tables(1) == [[["年份", "1"]], [["a", "b"], ["1", "2"]]]


@pytest.mark.slow
def test_render_pairs_each_caption_with_its_scan_page_and_skips_sentences_that_name_a_table(
    tmp_path: Path, scan: Path
) -> None:
    captions = [
        "表1-1 GDP 缺口估算方法之比较",
        "图 1-1\n采用生产函数法的 GDP 缺口比较",
        "图 11-2",
        "表 10-5 日本的再配置效应（市场经济，1975—2005 年）",
        "附表5-1 研究会成员",
        "附表 A 统计数据的来源",
        "表1-10",
        "如表1-1所示",
        "表 10-5 的结果显示，从资本和劳动力的整体再配置效应来看",
        "图 11-4 显示了当劳动力努力水平对超额劳动时间的弹性",
    ]
    rebuilt = pymupdf.open()
    for text in captions:
        rebuilt.new_page(width=400, height=600).insert_textbox(pymupdf.Rect(40, 40, 360, 200), text, fontname="china-s")
    rebuilt_path = tmp_path / "rebuilt.pdf"
    rebuilt.save(rebuilt_path)
    check = make_check(tmp_path, scan, {2: "x", 3: "x"}, {2: ["表1-1 GDP 缺口估算方法之比较"], 3: ["图 11-2"]}, key="3_trade")
    rc = RenderCheck(check, rebuilt_path, tmp_path / "rc")

    assert rc.rebuilt == {"表1-1": 1, "图1-1": 2, "图11-2": 3, "表10-5": 4, "附表5-1": 5, "附表A": 6, "表1-10": 7}
    assert rc.scan == {"表1-1": 2, "图11-2": 3}
    assert all(path.is_file() for path in rc.render("表1-1"))
    agents = FakeAgents()
    assert list(rc.run(size=1, jobs=2, model="m", runner=agents)) == [
        "2 pairs, 2 of 2 batches to run, 2 at a time",
        "r1.jsonl: exit 0, 1 of 1 items",
        "r2.jsonl: exit 0, 1 of 1 items",
    ]
    rerun = list(rc.run(size=1, jobs=2, model="m", runner=agents))
    assert rerun == ["2 pairs, 0 of 2 batches to run, 2 at a time"]


def test_the_scan_sheet_shows_each_verdict_as_a_strip_card_in_order(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {12: "x", 74 % SCAN_PAGES: "x"}, {2: ["20 节纪", "<b>"], 12: ["必不可免"]})
    write_jsonl(check.results.verdicts_path, [
        {"page": 2, "kind": "word", "transcript": "20 节纪", "scan": "20 世纪", "verdict": "scan_typo", "detail": "Wrong character", "by": "m"},
        {"page": 12, "kind": "word", "transcript": "必不可少", "scan": "必不可免", "verdict": "real", "detail": "", "by": "m"},
        {"page": 2, "kind": "word", "transcript": "<b>", "scan": "b", "verdict": "scan_typo", "detail": "", "by": "m"},
        {"page": 2, "kind": "word", "transcript": "不在", "scan": "在", "verdict": "scan_typo", "detail": "", "by": "m"},
        {"page": 9, "kind": "mark", "transcript": "", "scan": "、", "verdict": "false_positive", "detail": "", "by": "m"},
    ])
    typos = cases_from_verdicts(check.results.verdicts(), "scan_typo")
    html, missed = scan_sheet(check, typos, "Scan Typos", "Intro", 100)

    assert [case.find for case in missed] == ["不在"]
    assert '<b>p2</b> · scan prints <mark>20 节纪</mark> · meant <span class="ok">20 世纪</span>' in html
    assert "<small>Wrong character</small>" in html
    assert "scan prints <mark>&lt;b&gt;</mark>" in html
    assert html.index("20 节纪") < html.index("&lt;b&gt;")
    assert html.count('src="data:image/png;base64,') == 2
    assert "<title>Scan Typos</title>" in html and "<h1>Scan Typos</h1>" in html
    assert "--mark:#ffe08a" in html and "prefers-color-scheme:dark" in html
    real, _ = scan_sheet(check, cases_from_verdicts(check.results.verdicts(), "real"), "Real", "", 100)
    assert 'transcript has <mark>必不可少</mark> · scan prints <span class="ok">必不可免</span>' in real


def test_sheets_tile_the_queued_zooms_into_contact_sheets(tmp_path: Path, scan: Path) -> None:
    check = make_check(tmp_path, scan, {1: "x"}, {1: ["甲乙丙"]})
    write_jsonl(check.results.folder / "p1-1.jsonl", [
        {"page": 1, "issues": [issue("word", "甲乙", f"甲{n}") for n in range(3)]},
    ])
    triage(check)
    written = sheets(check, size=2)
    assert [path.name for path in written] == ["sheet_01.png", "sheet_02.png"]
    with Image.open(written[0]) as sheet:
        assert sheet.width == 1200


def test_an_english_caption_keeps_an_english_label() -> None:
    assert caption_label("Table 3.5 Growth of output per worker") == "Table3.5"
    assert caption_label("Figure 1: The phase plane") == "Figure1"
    assert caption_label("Fig. 2.4. A torus") == "Figure2.4"
    assert caption_label("Table 2-1") == "Table2-1"


def test_an_english_sentence_that_names_a_figure_is_not_a_caption() -> None:
    assert caption_label("Figure 1 shows that the orbit is closed.") is None
    assert caption_label("Table 3.5 lists the measured values") is None
    assert caption_label("Figures 2 and 3 compare the two methods") is None


def test_a_chinese_label_still_needs_its_chapter_number() -> None:
    assert caption_label("图 3 增长") is None
    assert caption_label("表3.5 产出") is None


JPEG_PAGE = pymupdf.Rect(0, 0, 144, 216)


def scan_page_jpeg(mode: str, size: tuple[int, int]) -> bytes:
    rng = np.random.default_rng(7)
    noise = rng.integers(0, 256, (size[1], size[0], 3 if mode == "RGB" else 1), dtype=np.uint8).squeeze()
    image = Image.fromarray(noise).resize((150, 225)).resize(size, Image.Resampling.BICUBIC)
    out = io.BytesIO()
    image.filter(ImageFilter.GaussianBlur(3)).save(out, "JPEG", quality=92)
    return out.getvalue()


def jpeg_scan(tmp_path: Path, *modes: str, size: tuple[int, int] = (1200, 1800)) -> pymupdf.Document:
    doc = pymupdf.open()
    for mode in modes:
        page = doc.new_page(width=JPEG_PAGE.width, height=JPEG_PAGE.height)
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
        doc.update_stream(contents, f"q {JPEG_PAGE.width} 0 0 {JPEG_PAGE.height} 0 0 cm /Im0 Do Q".encode())
        doc.xref_set_key(page.xref, "Contents", f"{contents} 0 R")
    doc.save(tmp_path / "jpeg_scan.pdf")
    return pymupdf.open(tmp_path / "jpeg_scan.pdf")


def gray(png: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(png)).convert("L"), dtype=float)


@pytest.mark.slow
@pytest.mark.parametrize(("mode", "size"), [("RGB", (1200, 1800)), ("L", (1200, 1800)), ("RGB", (1203, 1805))])
def test_strips_cut_from_the_scan_jpeg_match_the_mupdf_render(tmp_path: Path, mode: str, size: tuple[int, int]) -> None:
    doc = jpeg_scan(tmp_path, mode, size=size)
    strips = [
        Strip(1, band, dpi, tmp_path / f"s{k}.png")
        for k, (band, dpi) in enumerate([((0.0, 1.0), 150), ((0.3, 0.42), 300), ((0.9, 1.0), 300), ((0.1, 0.5), 110)])
    ]
    write_strips(doc, strips)
    for s in strips:
        ours, reference = gray(s.out.read_bytes()), gray(strip_png(doc, s.page, s.band, s.dpi))
        assert ours.shape == reference.shape
        assert 10 * np.log10(255**2 / ((ours - reference) ** 2).mean()) > 40


@pytest.mark.slow
def test_only_a_bare_full_page_jpeg_takes_the_fast_path(tmp_path: Path) -> None:
    doc = jpeg_scan(tmp_path, "RGB", "RGB", "RGB", "RGB", "RGB")
    doc[1].draw_rect(pymupdf.Rect(10, 10, 50, 50))
    doc[2].insert_text((20, 40), "visible")
    doc[3].set_rotation(90)
    doc[4].insert_text((20, 40), "hidden OCR layer", render_mode=3)
    assert [scan_jpeg(page) is not None for page in doc] == [True, False, False, False, True]


@pytest.fixture
def gated(tmp_path: Path, scan: Path, monkeypatch: pytest.MonkeyPatch) -> PageCheck:
    """A two-page book whose pages are checked, linted and verified, with figure 图1-1 in the scan,
    the manifest and the rebuilt PDF, and an audit that exits 0."""
    check = make_check(tmp_path, scan, {1: "第1页。\n", 2: "第2页。\n"}, {1: ["图 1-1 增长率"], 2: ["表 1-1 数据"]}, key="x")
    monkeypatch.setattr(verify_module, "audit", lambda _check: (0, "all counts at or below the baseline"))
    check_pages(check, [issue("word", "甲", "乙")])
    check.results.write_lint([])
    write_jsonl(check.results.verdicts_path, [{"page": 1, **issue("word", "甲", "乙"), "verdict": "real"}])
    write_manifest(tmp_path, ["图 1-1 增长率"])
    write_pdf(tmp_path / "x.pdf", ["图 1-1 增长率", "表 1-1 数据"])
    return check


def check_pages(check: PageCheck, issues: list[dict] | None = None) -> None:
    records = []
    for page in check.pages():
        check.page_png(page).parent.mkdir(parents=True, exist_ok=True)
        check.page_png(page).write_bytes(f"scan image {page}".encode())
        records.append({"page": page, "issues": issues if page == 1 and issues else [], "receipt": check.receipt(page)})
    write_jsonl(check.results.folder / f"p1-{len(records)}.jsonl", records)


def write_manifest(root: Path, captions: list[str]) -> None:
    figures = [
        {"figure_id": str(n), "caption": c, "image_rel_path": f"figures/{n}.png", "source_page": 1}
        for n, c in enumerate(captions, 1)
    ]
    (root / "figures_manifest.json").write_text(json.dumps(figures, ensure_ascii=False), encoding="utf-8")


def write_pdf(path: Path, captions: list[str]) -> None:
    doc = pymupdf.open()
    for caption in captions:
        doc.new_page().insert_text((72, 72), caption, fontname="china-s")
    doc.save(path)


def run_gate(check: PageCheck, tmp_path: Path) -> list[str]:
    return gate(check, tmp_path / "x.pdf", tmp_path / "figures_manifest.json")


def fails(lines: list[str]) -> list[str]:
    return [line for line in lines if line.startswith("FAIL")]


def test_a_book_that_meets_every_check_passes(gated: PageCheck, tmp_path: Path) -> None:
    lines = run_gate(gated, tmp_path)
    assert fails(lines) == []
    assert lines[-1] == "PASS"


def test_a_page_without_a_valid_receipt_fails_the_gate(gated: PageCheck, tmp_path: Path) -> None:
    gated.store.path(2).write_text("第二页，改过。\n", encoding="utf-8")
    lines = run_gate(gated, tmp_path)
    assert any("page check" in line and "2" in line for line in fails(lines))
    assert lines[-1].startswith("FAIL")


def test_a_book_whose_lint_has_not_run_fails(gated: PageCheck, tmp_path: Path) -> None:
    gated.results.lint_path.unlink()
    assert any("lint" in line for line in fails(run_gate(gated, tmp_path)))


def test_an_issue_with_no_verdict_fails(gated: PageCheck, tmp_path: Path) -> None:
    gated.results.verdicts_path.unlink()
    assert any("verdicts" in line and "1 unverified" in line for line in fails(run_gate(gated, tmp_path)))


def test_no_issues_from_more_than_100_pages_gives_a_warning(gated: PageCheck, tmp_path: Path) -> None:
    for path in gated.results.chunk_files():
        path.unlink()
    for page in range(3, 102):
        gated.store.path(page).write_text(f"第{page}页。\n", encoding="utf-8")
    check_pages(gated)
    lines = run_gate(gated, tmp_path)
    assert any(line.startswith("WARN") and "0 issues from 101 pages" in line for line in lines)
    assert lines[-1] == "PASS"


def test_an_empty_figure_manifest_fails_and_names_the_missing_figure(gated: PageCheck, tmp_path: Path) -> None:
    write_manifest(tmp_path, [])
    assert any("manifest" in line and "图1-1" in line for line in fails(run_gate(gated, tmp_path)))


def test_a_scan_figure_missing_from_the_rebuilt_pdf_fails(gated: PageCheck, tmp_path: Path) -> None:
    write_pdf(tmp_path / "x.pdf", ["表 1-1 数据"])
    assert any("rebuilt PDF" in line and "图1-1" in line for line in fails(run_gate(gated, tmp_path)))


def test_a_missing_rebuilt_pdf_fails(gated: PageCheck, tmp_path: Path) -> None:
    (tmp_path / "x.pdf").unlink()
    assert any("rebuilt PDF" in line for line in fails(run_gate(gated, tmp_path)))


def test_an_audit_that_exits_1_fails_with_its_last_line(
    gated: PageCheck, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(verify_module, "audit", lambda _check: (1, "glued_words rose from 3 to 9"))
    assert any("audit" in line and "glued_words rose from 3 to 9" in line for line in fails(run_gate(gated, tmp_path)))
