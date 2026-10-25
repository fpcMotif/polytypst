import re
from pathlib import Path

from polytypst import books_cli

SRC = Path(__file__).resolve().parents[1] / "src"


def rows(capsys) -> dict[str, list[str]]:
    assert books_cli.main("rules", []) == 0
    out = capsys.readouterr().out
    return {cells[1]: cells for line in out.splitlines() if len(cells := line.split()) >= 5}


def line_of(path: str, text: str) -> int:
    return next(i for i, line in enumerate((SRC / path).read_text(encoding="utf-8").splitlines(), 1) if text in line)


def test_rules_lists_every_checker_rule_where_its_name_is_written(capsys):
    table = rows(capsys)
    source = (SRC / "checker.py").read_text(encoding="utf-8")
    names = set(re.findall(r'"([A-Z][A-Z_]{3,})",', source)) - {"ERROR", "WARNING", "INFO", "NFKC"}
    assert len(names) >= 27 and names <= set(table)
    margin = line_of("checker.py", '"MARGIN_OVERFLOW"')
    assert table["MARGIN_OVERFLOW"] == ["pdf-layout", "MARGIN_OVERFLOW", "WARNING", "audit", f"src/checker.py:{margin}"]


def test_rules_lists_the_literal_number_parity_and_ocr_rules(capsys):
    table = rows(capsys)
    for prefix in ("TYPST", "LATEX"):
        for rule in ("LITERAL_ITEM_HEAD", "ORPHANED_FIGURE_CAPTION", "RASTER_FIGURE_FALLBACK"):
            assert table[f"{prefix}_{rule}"][:4] == ["source", f"{prefix}_{rule}", "count", "build,audit"]
    overflow = line_of("parity/report.py", "lines cross the scan's right text edge")
    assert table["PARITY_MAX_RIGHT_OVERFLOW_LINES"] == [
        "parity", "PARITY_MAX_RIGHT_OVERFLOW_LINES", "fail", "parity", f"src/parity/report.py:{overflow}",
    ]
    ocr = [cells for cells in table.values() if cells[0] == "ocr"]
    assert len(ocr) == 4 and all(cells[3] == "no" for cells in ocr)
