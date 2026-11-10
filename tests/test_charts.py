import pytest

from polytypst.books import book_by_key, book_folders
from polytypst.charts.engine import chart_svg
from polytypst.charts.redraw import (
    CHARTS,
    chart_books,
    draw_charts,
    figure_order,
    generators,
)


def test_chart_code_lives_in_its_book_folder():
    assert chart_books() == sorted(key for key, folder in book_folders().items() if (folder / CHARTS).is_dir())
    assert len(chart_books()) == 6


@pytest.mark.slow
@pytest.mark.parametrize("key", chart_books())
def test_each_chart_book_draws_the_same_svg_twice(key: str):
    found = generators(key)
    first = found[min(found, key=figure_order)]
    svg = chart_svg(first, "a")
    assert svg.lstrip().startswith(("<svg", "<?xml"))
    assert chart_svg(first, "a") == svg


def _square(mode: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><title>{mode}</title></svg>'


def test_the_redraw_loop_writes_each_chart_svg_into_the_book_figures(tmp_path):
    drawn = draw_charts({"1-1": _square, "1-2": _square}, tmp_path, ["1-2"])
    assert drawn == ["1-2"]
    assert (tmp_path / "figures" / "fig_1-2.svg").read_text(encoding="utf-8") == chart_svg(_square, "a")
    assert not (tmp_path / "figures" / "fig_1-1.svg").exists()
    assert draw_charts({"1-1": _square}, tmp_path) == ["1-1"]


def test_the_redraw_loop_refuses_an_id_without_a_generator(tmp_path):
    with pytest.raises(SystemExit, match="9-9"):
        _ = draw_charts({"1-1": _square}, tmp_path, ["9-9"])


@pytest.mark.parametrize("key", chart_books())
def test_each_chart_book_draws_its_charts_through_the_figures_hook(key: str):
    assert book_by_key(key).figures is not None
