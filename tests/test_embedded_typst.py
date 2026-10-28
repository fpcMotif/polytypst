import shutil
import subprocess

import numpy as np
import pymupdf
import pytest

from polytypst.bourbaki.marks import query_marks
from polytypst.compiler import typst_math
from polytypst.compiler.typst_math import REPO_FONTS_DIR, compile_typst

pytestmark = pytest.mark.skipif(shutil.which("typst") is None, reason="needs the typst CLI as the reference")

SOURCE = """#set page(width: 12cm, height: auto, margin: 1cm)
#set text(font: "New Computer Modern")
= Heading
#metadata((kind: "top", key: 3)) <src-mark>
Text with $integral_0^1 f(x) dif x$ and #sys.inputs.at("word", default: "none").
#metadata((kind: "end", key: 3)) <src-mark>
"""


@pytest.fixture(autouse=True)
def no_cli_fallback(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError(f"fell back to the typst CLI: {args}")

    monkeypatch.setattr(typst_math, "run_typst", refuse)


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["typst", args[0], "--font-path", str(REPO_FONTS_DIR), *args[1:]], check=True, capture_output=True, text=True)


def gray(path, page=0) -> np.ndarray:
    pix = pymupdf.open(path)[page].get_pixmap(dpi=100, colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, np.uint8)


def test_embedded_pdf_matches_cli(tmp_path):
    typ = tmp_path / "doc.typ"
    typ.write_text(SOURCE, encoding="utf-8")
    cli("compile", "--input", "word=alpha", str(typ), str(tmp_path / "cli.pdf"))
    compile_typst(typ, tmp_path / "doc.pdf", "--input", "word=alpha")
    assert pymupdf.open(tmp_path / "doc.pdf")[0].get_text() == pymupdf.open(tmp_path / "cli.pdf")[0].get_text()
    assert np.array_equal(gray(tmp_path / "doc.pdf"), gray(tmp_path / "cli.pdf"))


def test_embedded_sees_new_inputs_and_edits(tmp_path):
    typ = tmp_path / "doc.typ"
    typ.write_text(SOURCE, encoding="utf-8")
    compile_typst(typ, tmp_path / "a.pdf", "--input", "word=alpha")
    compile_typst(typ, tmp_path / "b.pdf", "--input", "word=beta")
    typ.write_text(SOURCE.replace("Heading", "Changed"), encoding="utf-8")
    compile_typst(typ, tmp_path / "c.pdf", "--input", "word=beta")
    texts = [pymupdf.open(tmp_path / f"{n}.pdf")[0].get_text() for n in "abc"]
    assert "alpha" in texts[0] and "beta" in texts[1] and "Changed" in texts[2]


def test_embedded_png_matches_cli(tmp_path):
    from PIL import Image

    typ = tmp_path / "doc.typ"
    typ.write_text(SOURCE, encoding="utf-8")
    cli("compile", "--ppi", "150", str(typ), str(tmp_path / "cli.png"))
    compile_typst(typ, tmp_path / "doc.png", "--ppi", "150")
    assert np.array_equal(np.asarray(Image.open(tmp_path / "doc.png")), np.asarray(Image.open(tmp_path / "cli.png")))


def test_query_marks_match_cli(tmp_path):
    typ = tmp_path / "doc.typ"
    typ.write_text(SOURCE, encoding="utf-8")
    import json

    expected = json.loads(cli("query", str(typ), "<src-mark>", "--field", "value").stdout)
    assert query_marks(typ) == expected == [{"kind": "top", "key": 3}, {"kind": "end", "key": 3}]


def test_embedded_error_is_a_called_process_error_naming_the_line(tmp_path):
    typ = tmp_path / "bad.typ"
    typ.write_text("ok\n\n$ x + #nosuch $\n", encoding="utf-8")
    reference = subprocess.run(
        ["typst", "compile", "--diagnostic-format", "short", str(typ), str(tmp_path / "cli.pdf")],
        capture_output=True, text=True, check=False,
    )
    expected = reference.stderr.splitlines()[0].split("bad.typ")[1]
    with pytest.raises(subprocess.CalledProcessError) as raised:
        compile_typst(typ, tmp_path / "bad.pdf", capture_output=True)
    assert expected == ":3:7: error: unknown variable: nosuch"
    assert f"bad.typ{expected}" in raised.value.stderr
