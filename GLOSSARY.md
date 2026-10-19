# polytypst

polytypst re-typesets scanned mathematics books as Typst, LaTeX and EPUB. This glossary names the things the checks compare.

## Language

**Source scan**:
The original PDF of a book, as scanned page images. It is the ground truth for text, layout and diagrams.
_Avoid_: original, ground truth PDF, input PDF

**Rebuilt PDF**:
The PDF that polytypst typesets for one edition of a book.
_Avoid_: output, reproduction, ours

**Page map**:
The pairing of each source scan page with the rebuilt PDF page or pages that hold its text.
_Avoid_: page alignment, page mapping

**Scan parity**:
How far each word, line and diagram of a rebuilt PDF page sits from the same ink on its source scan page, in points.
_Avoid_: redshift, overlay score, pixel parity
