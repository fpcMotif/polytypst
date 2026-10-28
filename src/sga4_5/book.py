import shutil
from pathlib import Path

from ..edition import OUTPUT, Book, facsimile_edition, monograph_edition
from ..facsimile import FacsimileStyle
from ..parity.diagrams import DiagramText
from ..vision.diagram_crops import scan_diagram_boxes
from .spec import SGA4_5_SPEC

OUT_DIR = OUTPUT / "sga4_5"
DIAGRAM_DIR = Path(__file__).parent / "diagrams"
DIAGRAM_TEXT = DiagramText(font="STIX Two Text", size=9.5, weight=400)


def sga4_5_diagram_boxes() -> dict[str, tuple[int, int, int, int]]:
    boxes = {fig: box for fig, (_, box) in scan_diagram_boxes(OUT_DIR).items()}
    boxes["127_001"] = (279, 762, 593, 906)
    boxes["127_002"] = (215, 1385, 1051, 1531)
    boxes.pop("127_003", None)
    return boxes


def install_diagrams(out_dir: Path) -> list[Path]:
    from PIL import Image
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    written = [
        Path(shutil.copy2(src, fig_dir / src.name))
        for src in sorted(DIAGRAM_DIR.glob("fig_*.typ"))
    ]
    scanned = scan_diagram_boxes(out_dir)
    render_127 = out_dir / "page_renders/p_127.png"
    for fig, box in sga4_5_diagram_boxes().items():
        render = render_127 if fig.startswith("127_") else (scanned[fig][0] if fig in scanned else None)
        if render and box:
            path = fig_dir / f"fig_{fig}.png"
            with Image.open(render) as im:
                im.crop(box).save(path, dpi=(300, 300))
            written.append(path)
    return written


FACSIMILE_STYLE = FacsimileStyle(
    slug="sga4_5_facsimile",
    title="Cohomologie étale (SGA 4½ facsimile)",
    font_file=Path("/System/Library/Fonts/Supplemental/STIXTwoText.ttf"),
    font_stack='("STIX Two Text", "STIX Two Math")',
    size=9.5,
    weight=400,
    diagram_dir=DIAGRAM_DIR,
    diagram_text=DIAGRAM_TEXT,
    install_diagrams=install_diagrams,
    diagram_boxes=sga4_5_diagram_boxes,
    transcripts=SGA4_5_SPEC.markdown_dir,
)


BOOK = Book(
    SGA4_5_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(SGA4_5_SPEC, OUT_DIR, "monograph"),
        "facsimile": facsimile_edition(SGA4_5_SPEC, OUT_DIR, FACSIMILE_STYLE),
    },
    install_diagrams,
)
