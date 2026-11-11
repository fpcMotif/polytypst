import json
from pathlib import Path

import pytest

from polytypst.findings import main

FINDINGS = [
    {"id": "Bkashiwara-235", "book": "kashiwara", "severity": "P1", "format": "typst", "where": "rebuilt p229 / scan p253",
     "what": "Equation number (3.2.1) sits on the next line.", "evidence": "r_229.png", "status": "open", "cause_id": "RC-06"},
    {"id": "Bkashiwara-236", "book": "kashiwara", "severity": "P2", "format": "typst", "where": "rebuilt p230",
     "what": "Running head lacks its period.", "evidence": "r_230.png", "status": "fixed"},
    {"id": "Bgoursat-12", "book": "goursat", "severity": "P0", "format": "both", "where": "rebuilt p12 / scan p20",
     "what": "A footnote is lost.", "evidence": "s_020.png", "status": "open", "cause_id": "RC-06"},
]
VERDICTS = [
    {"id": "Bkashiwara-235", "book": "kashiwara", "verdict": "code", "scan_page": 253,
     "scan_reads": "(3.2.1)", "transcript_reads": "(3.2.1)"},
]


@pytest.fixture
def stores(tmp_path: Path) -> tuple[Path, Path]:
    findings, verdicts = tmp_path / "findings.jsonl", tmp_path / "verdicts.jsonl"
    findings.write_text("".join(json.dumps(r) + "\n" for r in FINDINGS), encoding="utf-8")
    verdicts.write_text("".join(json.dumps(r) + "\n" for r in VERDICTS), encoding="utf-8")
    return findings, verdicts


def shown(argv: list[str], stores: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = main([*argv, "--file", str(stores[0]), "--verdicts", str(stores[1])])
    return code, capsys.readouterr().out


def test_a_finding_shown_by_id_carries_its_verdict(stores: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    code, out = shown(["Bkashiwara-235"], stores, capsys)
    assert code == 0
    assert "Equation number (3.2.1)" in out
    assert "verdict code" in out and "scan p253" in out
    assert "Bkashiwara-236" not in out and "1 finding" in out


def test_findings_are_chosen_by_cause_book_and_status(stores: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    _, by_cause = shown(["--cause", "RC-06"], stores, capsys)
    assert "Bkashiwara-235" in by_cause and "Bgoursat-12" in by_cause and "Bkashiwara-236" not in by_cause
    _, open_kashiwara = shown(["--book", "kashiwara", "--status", "open"], stores, capsys)
    assert "Bkashiwara-235" in open_kashiwara and "Bkashiwara-236" not in open_kashiwara and "Bgoursat-12" not in open_kashiwara


def test_findings_are_chosen_by_text(stores: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    _, out = shown(["--match", "footnote"], stores, capsys)
    assert "Bgoursat-12" in out and "Bkashiwara" not in out


def test_an_unknown_id_is_named_and_exits_1(stores: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    code, out = shown(["Bkashiwara-999"], stores, capsys)
    assert code == 1
    assert "Bkashiwara-999" in out
