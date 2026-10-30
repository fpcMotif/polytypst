import json

from scripts.scan_sheet import Case, card, cases_from_verdicts, page_html


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
