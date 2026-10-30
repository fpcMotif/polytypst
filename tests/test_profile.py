import json
import subprocess

import numpy as np
import pymupdf
import pytest

from polytypst import books as books_module
from polytypst import books_cli
from polytypst.compiler.monograph import MonographSpec
from polytypst.compiler.typst_math import compile_typst
from polytypst.edition import Book, Edition
from polytypst.parity.ink_cache import InkCache
from polytypst.parity.words import page_ink

SOURCE = """#set page(width: 10cm, height: auto, margin: 1cm)
#set text(font: "New Computer Modern")
= Probe
#place(dx: 12.5pt)[Text placed on the page.]
More text.
"""


def python_loop() -> int:
    return sum(i * i for i in range(300_000))


def use_book(monkeypatch, tmp_path, build) -> None:
    book = Book(MonographSpec(domain="math", slug="x", title="X", author="A"), tmp_path, {"monograph": Edition(tmp_path / "x.pdf", build)})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})


@pytest.fixture
def probe(monkeypatch, tmp_path):
    def build(source, formats, footnotes):
        python_loop()
        np.linalg.svd(np.random.default_rng(0).random((300, 300)))
        subprocess.run(["sleep", "0.3"], check=True, capture_output=True)
        typ = tmp_path / "x.typ"
        typ.write_text(SOURCE, encoding="utf-8")
        compile_typst(typ, tmp_path / "x.pdf")

    use_book(monkeypatch, tmp_path, build)
    return tmp_path


def owner_rows(out: str) -> dict[str, str]:
    table = out.split("time by owner", 1)[1].split("\n\n", 1)[0]
    return {line[:24].strip(): line for line in table.splitlines()[2:]}


def typst_cases(out: str) -> list[str]:
    table = out.split("Typst compile of the generated .typ", 1)[1]
    return [line.split()[0] for line in table.strip().splitlines()[1:]]


def test_profile_splits_build_time_by_owner(probe, capsys):
    assert books_cli.main("profile", ["probe", "--step", "build"]) == 0
    owners = owner_rows(capsys.readouterr().out)
    assert {"Python bytecode", "numpy", "Typst"} <= owners.keys()


def test_profile_shows_waits_on_a_subprocess_as_their_own_row(probe, capsys):
    assert books_cli.main("profile", ["probe", "--step", "build"]) == 0
    seconds = float(owner_rows(capsys.readouterr().out)["subprocess wait"].split()[-2])
    assert seconds >= 0.25


def test_profile_lists_the_top_functions_by_own_time(probe, capsys):
    assert books_cli.main("profile", ["probe", "--step", "build"]) == 0
    top = capsys.readouterr().out.split("top functions by own time", 1)[1]
    assert "test_profile.py:25(<genexpr>)" in top


def test_profile_times_the_generated_typst_in_three_labeled_cases(probe, capsys):
    assert books_cli.main("profile", ["probe", "--step", "build"]) == 0
    out = capsys.readouterr().out
    assert typst_cases(out)[:3] == ["cold", "edited", "repeat"]
    assert "best case" in out
    assert not (probe / ".profile_x.typ").exists()
    assert (probe / "x.typ").read_text(encoding="utf-8") == SOURCE


def test_profile_json_has_the_rows_of_the_text_and_they_add_up_to_the_wall_time(probe, capsys):
    assert books_cli.main("profile", ["probe", "--step", "build"]) == 0
    text = capsys.readouterr().out
    assert books_cli.main("profile", ["probe", "--step", "build", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert {o["owner"] for o in report["owners"]} == owner_rows(text).keys()
    assert [t["case"] for t in report["typst"]] == typst_cases(text)
    total = sum(o["seconds"] for o in report["owners"])
    assert sum(o["share"] for o in report["owners"]) == pytest.approx(1.0)
    assert total == pytest.approx(report["wall"], rel=0.05)


def test_profile_exits_with_the_steps_exit_code(probe, capsys):
    assert books_cli.main("profile", ["probe", "--step", "audit"]) == 1
    assert "x.pdf is missing" in capsys.readouterr().out


def test_profile_rejects_a_scan_for_audit(probe, capsys):
    with pytest.raises(SystemExit):
        books_cli.main("profile", ["probe", "--step", "audit", "--source", "scan.pdf"])
    assert "--source" in capsys.readouterr().err


def test_profile_cold_leaves_the_real_ink_cache_byte_identical(monkeypatch, tmp_path, capsys):
    scan = tmp_path / "scan.pdf"
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "ink")
    doc.save(scan)
    real = tmp_path / "ink"
    drawn = []

    def build(source, formats, footnotes):
        cache = InkCache(scan, real, page_ink)
        drawn.append(cache.folder.parent == real)
        assert cache(1).any()

    use_book(monkeypatch, tmp_path, build)
    assert books_cli.main("profile", ["probe", "--step", "build"]) == 0
    before = {p: p.read_bytes() for p in real.rglob("*") if p.is_file()}
    assert books_cli.main("profile", ["probe", "--step", "build", "--cold"]) == 0
    assert {p: p.read_bytes() for p in real.rglob("*") if p.is_file()} == before
    assert before
    assert drawn == [True, False]


def test_profile_help_names_the_steps_and_books(probe, capsys):
    with pytest.raises(SystemExit):
        books_cli.main("profile", ["--help"])
    help_text = " ".join(capsys.readouterr().out.split())
    assert "steps: build, parity, audit" in help_text
    assert "books: probe" in help_text
