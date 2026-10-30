# Render check: tables and figures against the scan

You compare tables and figures of a rebuilt PDF with the scan. Each item is a pair of page images: `LABEL_rebuilt.png` from the rebuilt PDF and `LABEL_scan.png` from the scan. The scan is the witness for content. The rebuilt page must also look like a professionally typeset book: a reader finds it elegant and easy to read.

You only read the books. Write only `OUT` and zoom PNG files in `DIR`.

## Your values

When `scripts/render_check.py --run` starts you, the prompt gives these values:

- `BOOK`: the book number
- `DIR`: the folder that holds the pairs, `DIR/LABEL_rebuilt.png` and `DIR/LABEL_scan.png`
- `ITEMS`: the labels to check, such as `表1-1,图6-4`
- `OUT`: your result file

The pairs already exist, so go straight to "Check each item". Run every command from `/Users/martinfan/devv/polytypst.mixed`, and put each path in double quotes. When a pair shows a page without its item, say so in that item's line.

## Make the pairs

`scripts/render_check.py` pairs each caption of the rebuilt PDF with the scan page that prints the same caption, and renders each side as a spread at 110 dpi: the caption page and the page after it, so that a table that runs on is in view:

```bash
uv run python scripts/render_check.py BOOK --pdf "REBUILT.pdf" --scan "SCAN.pdf"
uv run python scripts/render_check.py BOOK --pdf "REBUILT.pdf" --scan "SCAN.pdf" --labels 表1-1,图6-4 --out "output/render_check/BOOK"
```

The first command lists every caption with its two pages. The second renders the labels you name. When the item is small on the page, zoom on it with `scripts/page_png.py --clip`.

## Check each item

Read both images. Find the item by its caption. Then grade two things.

### Content

The rebuilt item holds what the scan prints:

- a table: every row, every column, every header, every number with its sign and decimal point, the unit, the notes and the source line
- a figure: the chart type, every series, the axis ranges and ticks, the axis titles and units, the legend entries, the notes and the source line

### Presentation

The rebuilt item meets this bar:

| Area | The bar |
|---|---|
| Fit | The item fits inside the text block. No cell, label or rule runs past the margin or is cut off. |
| Space | The cells have room. Text in a cell does not touch a rule or the next cell. A number stays on one line. |
| Type | The table text is readable at the body size or one step smaller. The font matches the body font. |
| Rules | A table has a heavy rule at the top and the bottom and a thin rule under the header. A table uses vertical rules only where the scan needs them to group columns. |
| Alignment | Numbers in a column line up on the right or on the decimal point. Text cells line up on the left. A header that spans columns sits centered over them. |
| Breaks | The item stays on one page. A table that must break repeats its header on the next page. |
| Caption | The caption, the notes and the source sit where the scan puts them, in a consistent style. |
| Figure | Labels are legible and do not overlap the lines or each other. The legend does not cover data. Colours or line styles tell the series apart in print. |

## Record each item

Write one JSON line for each item to `OUT`, or in your reply when the prompt names no `OUT`:

```json
{"book": 1, "label": "表4-7", "grade": "B", "content": ["row 3, column 2: the scan prints 1.25; the rebuilt table prints 1.2"], "presentation": ["Space: the 構成比 column wraps 12.5 onto two lines"]}
```

- `grade`: `A` when content and presentation pass. `B` when content passes and presentation has a flaw that a reader notices. `C` when the content is wrong, or the item is cut off or hard to read.
- `content` and `presentation`: one short entry for each problem, naming the row, the column, the series or the area of the bar. Use an empty list when the part passes.

Done when every item has its line, and each entry names a place that you can point to in the image.
