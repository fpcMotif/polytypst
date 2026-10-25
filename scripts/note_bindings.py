"""List circled-mark notes that would bind to the wrong place in the body of their page.

Usage: uv run python scripts/note_bindings.py output/4_不良债权与金融危机/markdown_pages

The compiler binds note ③ to the first ③ in the page body. When an enumeration such as
"；③其他情况" comes before the real call "其他情况③", the note lands on the enumeration.
Each line printed is a note whose mark occurs more than once in the body, with the first
occurrence (where the note binds) and the later ones. When the first one is an enumeration,
give the real call and its note line a mark that the page does not use, such as ⑳. Typst
numbers notes in order, so the printed mark stays correct.
"""

import argparse
from pathlib import Path

from polytypst.compiler.page_cleaner import split_page_footnotes
from polytypst.ocr.transcripts import TranscriptStore

FOLIO = r"^(?:\d{1,3}|[ivxlcdm]+)$"


def around(text: str, i: int) -> str:
    return text[max(0, i - 10) : i + 8].replace("\n", "⏎")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("transcripts", type=Path)
    args = parser.parse_args()
    store = TranscriptStore(args.transcripts)
    for path in sorted(args.transcripts.glob("p_*.md")):
        body, notes = split_page_footnotes(
            store.text(int(path.stem[2:])) or "", "circled", FOLIO
        )
        for mark, note in notes:
            hits = [i for i, c in enumerate(body) if c == mark]
            if len(hits) > 1:
                later = " | ".join(around(body, i) for i in hits[1:])
                print(
                    f"{path.stem} {mark} binds [{around(body, hits[0])}] later [{later}] note {note[:16]}"
                )


if __name__ == "__main__":
    main()
