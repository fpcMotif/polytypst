import shutil
from pathlib import Path

from polytypst.edition import OUTPUT
from polytypst.vision.diagram_crops import scan_diagram_boxes

OUT_DIR = OUTPUT / "sga4_5"
DIAGRAM_DIR = Path(__file__).parent / "diagrams"


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
