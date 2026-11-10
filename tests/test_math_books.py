from pathlib import Path

from scripts.math_books import script_mismatch

CHINESE = "设 $f$ 是区间上的连续函数, 则它在该区间上有界并且取到最大值与最小值."
FRENCH = "Soit $f$ une fonction continue sur un intervalle fermé; alors elle est bornée."


def store(root: Path, text: str) -> Path:
    pages = root / "markdown_pages"
    pages.mkdir(parents=True)
    (pages / "p_001.md").write_text(text, encoding="utf-8")
    return pages


def test_store_in_the_book_language_passes(tmp_path: Path) -> None:
    assert script_mismatch(store(tmp_path / "book4", CHINESE), "zh") is None


def test_lang_variant_uses_its_language_code(tmp_path: Path) -> None:
    assert script_mismatch(store(tmp_path / "grothendieck", FRENCH), "fr_times") is None


def test_latin_transcript_under_chinese_book_fails(tmp_path: Path) -> None:
    problem = script_mismatch(store(tmp_path / "book4", FRENCH), "zh")

    assert problem is not None and problem.startswith("FAIL store:")
    assert "lang = zh" in problem and "latin" in problem


def test_chinese_transcript_under_latin_book_fails(tmp_path: Path) -> None:
    problem = script_mismatch(store(tmp_path / "weil", CHINESE), "en")

    assert problem is not None and "cjk" in problem
