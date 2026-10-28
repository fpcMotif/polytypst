from pathlib import Path

import numpy as np
import pytest

from polytypst.facsimile_figures import (
    FigureArt,
    Placed,
    drawing_gaps,
    figure_typst,
    slices,
)


def two_panels(tmp_path: Path) -> Path:
    svg = tmp_path / "fig.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
        '<rect x="0" y="0" width="100" height="40" fill="#000"/>'
        '<rect x="0" y="60" width="100" height="40" fill="#000"/></svg>',
        encoding="utf-8",
    )
    return svg


def test_drawing_gaps_finds_the_blank_band_between_panels(tmp_path):
    assert drawing_gaps(two_panels(tmp_path)) == [(pytest.approx(0.5, abs=0.02), pytest.approx(0.2, abs=0.02))]


def test_split_figure_is_cut_at_the_widest_gap_in_reach(tmp_path):
    svg = tmp_path / "fig.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
        '<rect x="0" y="0" width="100" height="40" fill="#000"/>'
        '<rect x="0" y="44" width="100" height="6" fill="#000"/>'
        '<rect x="0" y="70" width="100" height="30" fill="#000"/></svg>',
        encoding="utf-8",
    )
    top, bottom = np.zeros((1000, 500), bool), np.zeros((1000, 500), bool)
    top[600:, :] = True
    bottom[:400, :] = True
    full = (0.0, 0.0, 1.0, 1.0)
    arts = {1: [FigureArt("1-1", full, svg)], 2: [FigureArt("1-1", full, svg)]}
    bands = slices(arts, {1: top, 2: bottom}, {svg: drawing_gaps(svg)})
    assert bands[1][0].end == pytest.approx(0.6, abs=0.02)


def test_drawing_is_stretched_onto_a_scan_box_of_another_aspect(tmp_path):
    svg = two_panels(tmp_path)
    placed = Placed(FigureArt("1-1", (0.0, 0.0, 1.0, 1.0), svg), (10.0, 20.0, 210.0, 120.0), 0.0, 1.0)
    typst = figure_typst(placed, (100.0, 100.0, 0.0, 0.0, 100.0, 100.0), svg)
    assert '.svg", width: 200.00pt, height: 100.00pt' in typst


def test_split_figure_takes_the_nearest_of_equally_wide_gaps(tmp_path):
    svg = tmp_path / "fig.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
        '<rect x="0" y="0" width="100" height="20" fill="#000"/>'
        '<rect x="0" y="30" width="100" height="10" fill="#000"/>'
        '<rect x="0" y="50" width="100" height="10" fill="#000"/>'
        '<rect x="0" y="70" width="100" height="30" fill="#000"/></svg>',
        encoding="utf-8",
    )
    top, bottom = np.zeros((1000, 500), bool), np.zeros((1000, 500), bool)
    top[550:, :] = True
    bottom[:550, :] = True
    full = (0.0, 0.0, 1.0, 1.0)
    arts = {1: [FigureArt("1-1", full, svg)], 2: [FigureArt("1-1", full, svg)]}
    bands = slices(arts, {1: top, 2: bottom}, {svg: drawing_gaps(svg)})
    assert bands[1][0].end == pytest.approx(0.45, abs=0.02)


def test_split_figure_is_cut_at_the_panel_gap_not_by_ink_share(tmp_path):
    svg = two_panels(tmp_path)
    top, bottom = np.zeros((1000, 500), bool), np.zeros((1000, 500), bool)
    top[700:, :] = True
    bottom[:700, :] = True
    full = (0.0, 0.0, 1.0, 1.0)
    arts = {1: [FigureArt("1-1", full, svg)], 2: [FigureArt("1-1", full, svg)]}
    bands = slices(arts, {1: top, 2: bottom}, {svg: drawing_gaps(svg)})
    assert bands[1][0].end == pytest.approx(0.5, abs=0.02)
    assert bands[2][0].start == bands[1][0].end
    assert bands[2][0].end == 1.0
