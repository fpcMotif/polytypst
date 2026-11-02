from pathlib import Path

from PIL import Image

from scripts.book_check import (
    auto_verdict,
    contact_sheet,
    issue_key,
    lint_fixups,
    lint_page,
    lint_typ,
    running_head_claim,
)


def rules(markdown: str, before: str = "", after: str = "") -> list[str]:
    return [hit["rule"] for hit in lint_page(markdown, before, after)]


def test_known_transcript_errors_from_book_4_are_found() -> None:
    assert rules("Institute forHuman Settlements") == ["glued_words"]
    assert rules("Effects of LandUse Control") == ["glued_words"]
    assert rules("| 中小企业</ th> |") == ["broken_tag"]
    assert rules("下降了 -0 .4%。") == ["spaced_decimal"]
    assert rules("② 即《帝国数据库的全国倒闭汇总以及东京商工调查。") == [
        "lone_book_mark"
    ]


def test_correct_text_is_not_flagged() -> None:
    assert rules("MacKinnon (1991) and McDonald test the series.") == []
    assert rules("2. 2001 年及以前的数据，增长 0.4%。") == []
    assert rules("组织译印了第三册《国际经济环境的变化\n与日本经济》。") == []
    assert rules("| 中小企业</th> |") == []
    opens = "首段。\n\n本套丛书包括第三册《国际经济环境的变化"
    closes = "## 2 财政政策与社会保障\n\n与日本经济》等。\n\n下一段。"
    assert rules(opens, after=closes) == []
    assert rules(closes, before=opens) == []
    assert rules(opens, after="下一页。") == ["lone_book_mark"]
    assert rules(opens, after="2 宏观经济与产业结构\n\n与日本经济》等。") == []


def test_a_running_head_left_in_the_built_book_is_found() -> None:
    typ = "正文一段。\n\n120 不良债权与金融危机\n\n正文。\n#set page(header: [不良债权与金融危机])\n"
    assert [hit["transcript"] for hit in lint_typ(typ, "不良债权与金融危机")] == [
        "120 不良债权与金融危机"
    ]


def test_width_or_space_only_differences_settle_as_false_positives() -> None:
    assert (
        auto_verdict({"kind": "mark", "transcript": "多大?", "scan": "多大？"})
        == "false_positive"
    )
    assert (
        auto_verdict({"kind": "word", "transcript": "20 世纪", "scan": "20世纪"})
        == "false_positive"
    )
    assert (
        auto_verdict({"kind": "word", "transcript": "forHuman", "scan": "for Human"})
        is None
    )
    assert (
        auto_verdict({"kind": "table_cell", "transcript": "</ tr>", "scan": "</tr>"})
        is None
    )
    assert auto_verdict({"kind": "sum", "transcript": "4740", "scan": "4740"}) is None
    assert auto_verdict({"kind": "word", "transcript": "一已", "scan": "一己"}) is None


def test_a_running_head_claim_is_recognised_for_its_own_book_only() -> None:
    def claim(text: str, scan: str = "") -> dict:
        return {"kind": "extra_text", "transcript": text, "scan": scan}

    title = "财政政策与社会保障"
    assert running_head_claim(claim("12 财政政策与社会保障"), title)
    assert running_head_claim(claim("## 2 财政政策与社会保障"), title)
    assert running_head_claim(claim("财政政策与社会保障 43"), title)
    assert not running_head_claim(claim("2 宏观经济与产业结构"), title)
    assert not running_head_claim(
        claim("12 财政政策与社会保障", scan="12 财政政策与社会保障"), title
    )
    assert not running_head_claim(
        {**claim("12 财政政策与社会保障"), "kind": "word"}, title
    )


def test_a_verdict_matches_its_issue_by_page_kind_and_both_texts() -> None:
    issue = {
        "page": 12,
        "line": 3,
        "kind": "word",
        "transcript": "必不可少",
        "scan": "必不可免",
        "note": "",
    }
    verdict = {**issue, "verdict": "real", "detail": "p12"}
    assert issue_key(12, issue) == issue_key(verdict["page"], verdict)


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
    assert [h["rule"] for h in lint_fixups(page, (("不存在", "新值"),))] == [
        "dead_fixup"
    ]
    assert [
        h["rule"]
        for h in lint_fixups(
            page,
            (),
            page_fixups=(("<th>旧值</th>", "<th>新值</th>"), ("注文原词", "注文新词")),
        )
    ] == ["dead_fixup", "dead_fixup"]
    assert (
        lint_fixups(
            page,
            (("<th>旧值</th>", "<th>新值</th>"), ("注文原词", "注文新词")),
            page_fixups=(("正文", "修订正文"),),
        )
        == []
    )
    big = "首行\n" + ("中段文字" * 90) + "\n尾行\n"
    assert [h["rule"] for h in lint_fixups(big, ((r"首行.*尾行", ""),))] == [
        "multiline_delete"
    ]
    assert lint_fixups(big, ((r"(?s)\A.*?\Z", ""),)) == []
    assert [h["rule"] for h in lint_fixups(big, ((r"首行.*?尾行", ""),))] == [
        "multiline_delete"
    ]
    assert [h["rule"] for h in lint_fixups(big, ((r"中段文字(中段文字)+", ""),))] == [
        "multiline_delete"
    ]


def test_contact_sheet_tiles_strips_into_single_snapshot(tmp_path: Path) -> None:
    strip1 = tmp_path / "s1.png"
    strip2 = tmp_path / "s2.png"
    Image.new("RGB", (600, 80), (255, 255, 255)).save(strip1)
    Image.new("RGB", (600, 120), (240, 240, 240)).save(strip2)
    out = contact_sheet(
        [
            ("#0 p1 L2 [word] | T: a | S: b", strip1),
            ("#1 p2 L5 [math] | T: x | S: y", strip2),
        ],
        tmp_path / "sheet_01.png",
        width=800,
    )
    assert out.exists()
    with Image.open(out) as sheet:
        assert sheet.width == 800
        assert sheet.height > 200


def test_a_failed_verify_batch_reports_the_agent_error(tmp_path: Path, monkeypatch) -> None:
    import subprocess

    from scripts import book_check

    def fake_run(_cmd, stdout, **_kwargs):
        stdout.write("starting\nError: No API key found for anthropic\n")
        return subprocess.CompletedProcess(_cmd, 1)

    monkeypatch.setattr(book_check.subprocess, "run", fake_run)
    items = tmp_path / "items.jsonl"
    items.write_text("{}\n", encoding="utf-8")
    report = book_check.verify_batch(items, tmp_path / "out.jsonl", "claude-haiku-5-5")
    assert "exit 1" in report
    assert "No API key found for anthropic" in report
