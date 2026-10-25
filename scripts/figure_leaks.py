"""List transcript lines whose text the scan prints inside a figure crop, so the book prints it twice.

Usage: mise exec -- uv run python scripts/figure_leaks.py KEY [--ratio 0.8]

A transcriber often copies a chart's legend, axis title or panel title ("（1）日本") into the
page text. The crop already shows that text, so the rebuilt page prints it under the figure as
well. Each printed line is `pPAGE fig ID LLINE (RATIO): TEXT`, where RATIO is how closely the
line matches an OCR line inside the figure box. Remove each true hit with a page fixup in the
book's spec, such as `71: ((r"(?m)^（[1-6]）(?:日本|美国)\\n*", ""),)`. A caption, table row or
display formula is never printed.
"""

from polytypst.figure_leaks import main

if __name__ == "__main__":
    main()
