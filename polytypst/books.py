"""Registry of the books that ship their own monograph spec."""

from collections.abc import Callable
from pathlib import Path

from .ahlfors.figures import generate_colorful_ahlfors_figures
from .ahlfors.spec import AHLFORS_ILLUSTRATED_SPEC, AHLFORS_SPEC
from .bourbaki import install_bourbaki_diagrams
from .bourbaki.spec import BOURBAKI_1970_SPEC, BOURBAKI_SPEC
from .compiler.monograph import MonographSpec
from .fermat.spec import FERMAT_SPEC
from .fermat.spec_vol2 import FERMAT2_SPEC
from .klein.spec import KLEIN_SPEC
from .klein.zh_spec import KLEIN_ZH_SPEC
from .kodaira.figures import generate_all_kodaira_figures
from .kodaira.spec import KODAIRA_SPEC
from .kashiwara.spec import KASHIWARA_SPEC
from .bourbaki_lie.spec import BOURBAKI_LIE_SPEC

BOOK_SPECS: dict[str, MonographSpec] = {
    spec.slug: spec
    for spec in (
        KODAIRA_SPEC,
        AHLFORS_SPEC,
        AHLFORS_ILLUSTRATED_SPEC,
        FERMAT_SPEC,
        FERMAT2_SPEC,
        KLEIN_SPEC,
        KLEIN_ZH_SPEC,
        BOURBAKI_SPEC,
        BOURBAKI_1970_SPEC,
        KASHIWARA_SPEC,
        BOURBAKI_LIE_SPEC,
    )
}


def _render_ahlfors_figures(out_dir: Path) -> None:
    generate_colorful_ahlfors_figures(out_dir / "figures", out_dir / "figures_color")


BOOK_FIGURE_RENDERERS: dict[str, Callable[[Path], object]] = {
    KODAIRA_SPEC.slug: generate_all_kodaira_figures,
    AHLFORS_SPEC.slug: _render_ahlfors_figures,
    AHLFORS_ILLUSTRATED_SPEC.slug: _render_ahlfors_figures,
    BOURBAKI_SPEC.slug: install_bourbaki_diagrams,
    BOURBAKI_1970_SPEC.slug: install_bourbaki_diagrams,
}


def render_book_figures(slug: str, out_dir: Path) -> bool:
    """Draw the code-reproduced figures of a registered book into `out_dir`."""
    render = BOOK_FIGURE_RENDERERS.get(slug)
    if render is None:
        return False
    _ = render(out_dir)
    return True


def find_known_book(pdf_path: Path, total_pages: int) -> MonographSpec | None:
    """Return the spec whose page count or file-name markers match the PDF."""
    name = pdf_path.name.lower()
    for spec in BOOK_SPECS.values():
        if spec.pdf_page_count == total_pages or any(
            marker in name for marker in spec.pdf_name_markers
        ):
            return spec
    return None
