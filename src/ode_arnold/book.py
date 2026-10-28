from ..edition import OUTPUT, Book, monograph_edition
from .spec import ODE_ARNOLD_SPEC

OUT_DIR = OUTPUT / "ode_arnold"

BOOK = Book(ODE_ARNOLD_SPEC, OUT_DIR, {"monograph": monograph_edition(ODE_ARNOLD_SPEC, OUT_DIR, "monograph")})
