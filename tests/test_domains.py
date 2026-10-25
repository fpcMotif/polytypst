from typing import Any

import pytest

from polytypst.compiler.monograph import MonographCompiler, MonographSpec
from polytypst.compiler.presets import DOMAIN_PROFILES, resolve_composition


def test_an_unknown_domain_is_an_error_not_math():
    with pytest.raises(ValueError, match="finance"):
        resolve_composition(domain="finance")


def test_each_known_domain_resolves_to_its_own_profile():
    assert {key: resolve_composition(domain=key).domain.key for key in DOMAIN_PROFILES} == {k: k for k in DOMAIN_PROFILES}


def test_a_spec_names_its_domain():
    without_domain: dict[str, Any] = {"slug": "x", "title": "T", "author": "A"}
    with pytest.raises(TypeError, match="domain"):
        MonographSpec(**without_domain)


def test_a_spec_rejects_an_unknown_domain():
    with pytest.raises(ValueError, match="banking"):
        MonographSpec(slug="x", title="T", author="A", domain="banking")


LEGEND = "图中各项如下。\n\n□ 正规雇员\n\n■ 非正规雇员\n"
PROOF = "Hence the map is onto. □\n"


def _typst(domain: str, text: str) -> str:
    return MonographCompiler(MonographSpec(slug="x", title="T", author="A", domain=domain)).format_typst(text)


def test_an_economics_book_keeps_its_legend_squares():
    out = _typst("economics", LEGEND)
    assert "□ 正规雇员" in out and "■ 非正规雇员" in out
    assert "#qed" not in out and "square.stroked" not in out


def test_a_math_book_ends_a_proof_with_a_qed_box():
    assert "#qed" in _typst("math", PROOF)
