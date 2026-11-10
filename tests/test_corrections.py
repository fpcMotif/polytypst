from dataclasses import replace
from pathlib import Path

import pytest

from polytypst.corrections import (
    Cause,
    Correction,
    Line,
    Verdict,
    causes,
    changed_lines,
    history,
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
