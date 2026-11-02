import json
import re
from dataclasses import replace
from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from polytypst.edition import Book
from polytypst.ocr.pages import OcrLine
from polytypst.page_check import PageCheck
from polytypst.page_check.check import run
from polytypst.page_check.lint import lint, lint_fixups
from polytypst.page_check.render import RenderCheck
from polytypst.page_check.results import write_jsonl
from polytypst.page_check.sheet import cases_from_verdicts, scan_sheet, sheets
from polytypst.page_check.verify import triage, verify

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
    check.book.out_dir.mkdir(parents=True)
    (check.book.out_dir / "book.typ").write_text(typ, encoding="utf-8")
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
