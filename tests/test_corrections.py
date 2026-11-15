from dataclasses import replace
from pathlib import Path

import pytest

from polytypst.corrections import (
    QUALITY,
    Cause,
    Correction,
    Line,
    Verdict,
    _check_scan_page,
    _rows,
    causes,
    changed_lines,
    history,
    main,
    record,
)

GOURSAT_219 = Line(
    before=r"\int: A \, dx = A \log(x - a)",
    after=r"\int \frac{A \, dx}{x - a} = A \log(x - a)",
)


def _verdict(**fields: object) -> Verdict:
    return Verdict(
        id="Bgoursat-223",
        book="goursat",
        verdict="scan_typo",
        scan_page=219,
        scan_reads="integral A dx / [blank] = A log(x-a)",
        transcript_reads=r"\int: A \, dx",
        **fields,
    )


def test_a_correction_comes_back_with_its_verdict_and_cause(tmp_path: Path) -> None:
    record(
        Cause(
            id="RC-06",
            root_cause="statements print upright",
            layer="code",
            status="fixed",
        ),
        tmp_path,
    )
    record(_verdict(), tmp_path)
    record(
        Correction(
            book="goursat",
            page=219,
            kind="scan_typo",
            lines=(GOURSAT_219,),
            scan_reads="no denominator",
            evidence="scan p219",
            fixed_in="books/goursat/book.toml",
            finding="Bgoursat-223",
            cause="RC-06",
        ),
        tmp_path,
    )
    (got,) = history("goursat", tmp_path).corrections
    assert got.correction.lines == (GOURSAT_219,)
    assert got.verdict is not None and got.verdict.scan_page == 219
    assert got.cause is not None and got.cause.status == "fixed"
    assert history("goursat", tmp_path).open_verdicts == ()


def test_a_verdict_with_no_correction_is_open(tmp_path: Path) -> None:
    record(_verdict(), tmp_path)
    assert [v.id for v in history("goursat", tmp_path).open_verdicts] == [
        "Bgoursat-223"
    ]
    assert history("ahlfors", tmp_path).open_verdicts == ()


def test_causes_lists_the_recorded_causes_of_one_layer(tmp_path: Path) -> None:
    record(
        Cause(id="RC-04", root_cause="heads", layer="code", status="unfixed"), tmp_path
    )
    record(
        Cause(id="RC-08", root_cause="order", layer="workflow", status="unfixed"),
        tmp_path,
    )
    assert [c.id for c in causes("code", tmp_path)] == ["RC-04"]
    assert causes("code", tmp_path / "nothing") == ()


def test_recording_a_cause_again_replaces_it(tmp_path: Path) -> None:
    record(Cause(id="RC-06", root_cause="r", layer="code", status="unfixed"), tmp_path)
    record(
        Cause(
            id="RC-06",
            root_cause="r",
            layer="code",
            status="fixed",
            notes={"commit": "e26d349f"},
        ),
        tmp_path,
    )
    record(
        Correction(
            book="b",
            page=1,
            kind="code",
            lines=(GOURSAT_219,),
            scan_reads="",
            evidence="",
            fixed_in="",
            cause="RC-06",
        ),
        tmp_path,
    )
    (got,) = history("b", tmp_path).corrections
    assert got.cause is not None and got.cause.notes == {"commit": "e26d349f"}


@pytest.mark.parametrize(
    "bad",
    [
        {"kind": "typo"},
        {"lines": ()},
        {"cause": "RC-99"},
        {"finding": "Bgoursat-999"},
    ],
)
def test_a_correction_with_an_unknown_kind_cause_or_finding_or_no_lines_is_refused(
    tmp_path: Path, bad: dict[str, object]
) -> None:
    good = Correction(
        book="goursat",
        page=219,
        kind="scan_typo",
        lines=(GOURSAT_219,),
        scan_reads="",
        evidence="",
        fixed_in="",
    )
    with pytest.raises(ValueError):
        record(replace(good, **bad), tmp_path)


def test_a_page_past_the_end_of_the_scan_is_refused(tmp_path: Path) -> None:
    # books/kashiwara/book.toml: pdf_page_count = 267
    with pytest.raises(ValueError, match="267"):
        record(replace(_verdict(), book="kashiwara", scan_page=277), tmp_path)
    with pytest.raises(ValueError, match="267"):
        record(
            Correction(
                book="kashiwara",
                page=277,
                kind="code",
                lines=(GOURSAT_219,),
                scan_reads="",
                evidence="",
                fixed_in="",
            ),
            tmp_path,
        )
    record(replace(_verdict(), book="kashiwara", scan_page=267), tmp_path)


def test_every_recorded_page_is_a_page_of_its_scan() -> None:
    entries = [(r["book"], r["scan_page"]) for r in _rows(QUALITY / "verdicts.jsonl")]
    entries += [
        (r["book"], r["page"])
        for path in sorted((QUALITY / "corrections").glob("*.jsonl"))
        for r in _rows(path)
    ]
    for book, page in entries:
        _check_scan_page(book, page)


def test_changed_lines_keeps_each_changed_line_whole_and_names_the_words_that_differ() -> (
    None
):
    before = "**Corollary 1.** *Let G be a group.*\n\n(i) N is a Lie subgroup of G.\n\n(i) has already been proved."
    after = "**Corollary 1.** *Let G be a group.*\n\n(i) *N is a Lie subgroup of G.*\n\n(i) has already been proved."
    (line,) = changed_lines(before, after)
    assert line == Line(
        before="(i) N is a Lie subgroup of G.",
        after="(i) *N is a Lie subgroup of G.*",
        line=2,
    )
    assert line.words() == [
        {"before": "N", "after": "*N"},
        {"before": "G.", "after": "G.*"},
    ]


def test_changed_lines_refuses_a_change_of_line_count() -> None:
    with pytest.raises(ValueError):
        changed_lines("a\nb", "a")


def _record_command(tmp_path: Path, before: str, after: str, *extra: str) -> int:
    old, new = tmp_path / "old.md", tmp_path / "p_091.md"
    old.write_text(before, encoding="utf-8")
    new.write_text(after, encoding="utf-8")
    argv = ["record", "newbook", "91", "--kind", "ocr", "--before", str(old), "--after", str(new)]
    return main([*argv, "--scan-reads", "determinant bars", "--evidence", "page_renders/p_091.png", *extra], tmp_path)


def test_the_record_command_writes_the_lines_that_differ_between_two_page_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _record_command(tmp_path, "17. \\begin{bmatrix} a\n\nkept", "17. \\begin{vmatrix} a\n\nkept")
    assert code == 0
    (linked,) = history("newbook", tmp_path).corrections
    assert linked.correction.page == 91
    assert linked.correction.kind == "ocr"
    assert linked.correction.fixed_in == str(tmp_path / "p_091.md")
    assert linked.correction.lines == (Line(before="17. \\begin{bmatrix} a", after="17. \\begin{vmatrix} a"),)
    assert "'\\\\begin{bmatrix}' -> '\\\\begin{vmatrix}'" in capsys.readouterr().out


def test_the_record_command_keeps_a_block_whole_when_the_line_count_changes(tmp_path: Path) -> None:
    assert _record_command(tmp_path, "top\n<div>\nlost\n</div>\nend", "top\n| a | b |\nend") == 0
    (linked,) = history("newbook", tmp_path).corrections
    assert linked.correction.lines == (Line(before="<div>\nlost\n</div>", after="| a | b |"),)


def test_the_record_command_refuses_two_equal_pages_and_an_unknown_finding(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        _record_command(tmp_path, "same", "same")
    with pytest.raises(SystemExit):
        _record_command(tmp_path, "a", "b", "--finding", "Bnone-1")
    assert history("newbook", tmp_path).corrections == ()
