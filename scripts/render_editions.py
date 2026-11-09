"""Render every monograph edition's Typst, Markdown and LaTeX Markdown without compiling, so a compiler refactor can be diffed.

Usage: uv run python scripts/render_editions.py OUT_DIR [KEY...]

Writes OUT_DIR/<key>.<edition>.typ, .md and .latex.md, plus OUT_DIR/hashes.txt with one sha256 per file.
Run it before and after a change, then `diff BEFORE/hashes.txt AFTER/hashes.txt`.
"""

import argparse
import hashlib
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from polytypst.books import books
from polytypst.compiler.monograph import MonographCompiler, MonographSpec
from polytypst.edition import Edition


@dataclass(frozen=True)
class MonographRun:
    name: str
    spec: MonographSpec
    out_dir: Path


def monograph_run(key: str, edition_name: str, edition: Edition) -> MonographRun | None:
    """The spec and output folder that a `monograph_edition` build closes over, or None for any other edition."""
    if edition.build.__qualname__ != "monograph_edition.<locals>.build":
        return None
    closed = inspect.getclosurevars(edition.build).nonlocals
    return MonographRun(f"{key}.{edition_name}", closed["spec"], Path(closed["out_dir"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path)
    parser.add_argument("keys", nargs="*")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    every = books()
    keys = args.keys or sorted(every)
    hashes: list[str] = []
    failed = 0
    for key in keys:
        for edition_name, edition in every[key].editions.items():
            run = monograph_run(key, edition_name, edition)
            if run is None:
                continue
            try:
                rendered = MonographCompiler(run.spec).render(run.out_dir)
            except Exception as exc:
                print(f"FAIL {run.name}: {type(exc).__name__}: {exc}", file=sys.stderr)
                failed += 1
                continue
            outputs = {"typ": rendered.typst, "md": rendered.markdown, "latex.md": rendered.latex_markdown or ""}
            for ext, text in outputs.items():
                path = args.out / f"{run.name}.{ext}"
                path.write_text(text, encoding="utf-8")
                hashes.append(f"{hashlib.sha256(text.encode()).hexdigest()}  {path.name}")
            print(f"ok   {run.name}")
    (args.out / "hashes.txt").write_text("".join(f"{line}\n" for line in sorted(hashes, key=lambda h: h[66:])), encoding="utf-8")
    print(f"{len(hashes) // 3} editions rendered, {failed} failed -> {args.out / 'hashes.txt'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
