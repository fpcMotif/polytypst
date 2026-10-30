# Page verify: one batch of issues

You decide a verdict for each issue in one batch. A checking agent recorded each issue by comparing a transcript page with its scan. The issue is a claim, and about one claim in four is false. The scan is the witness: what the scan prints is correct, even when it is a typo.

Your values are in the prompt:

- `ITEMS` is a JSONL file with one issue per line.
- `OUT` is the JSONL file that you write, with one verdict per line.

Each issue has these fields:

| Field | Meaning |
|---|---|
| `page` | The scan page |
| `kind` | `word`, `number`, `table_cell`, `table_shape`, `missing_text`, `extra_text`, `order`, `mark`, `math` or `sum` |
| `transcript` | What the transcript has. Empty for `missing_text` |
| `scan` | What the checking agent read in the scan. Empty for `extra_text` |
| `note` | The checking agent's note |
| `zoom` | A PNG of the scan at the issue's line, or of the whole page when the line was not found |
| `page_image` | A PNG of the whole scan page |

## Step 1. Read each zoom

For each issue, read its `zoom` image with your image tool. Find the `scan` text, or the place of the `transcript` text, in the image. When the zoom does not show that place, read `page_image` and find it there. Decide only from the images. A verdict from the text alone is wrong when the scan prints a typo.

Done when you read the zoom of every issue in `ITEMS`, and the page image of each issue whose zoom missed its place.

## Step 2. Decide the verdict

| Verdict | The zoom shows |
|---|---|
| `real` | The `scan` text, and the transcript differs from it |
| `scan_typo` | A typo, such as 20 节纪 for 20 世纪, and the transcript lacks the text that makes sense |
| `false_positive` | The transcript's text, or a difference of spacing or mark width only |
| `sum` | A table whose parts do not give its printed total |
| `unsure` | Neither image shows the place of the issue, or the print is too unclear to read |

The verdict says whether the transcript needs a fix:

- When the scan prints a typo and the transcript has the text that makes sense, such as `Journal` for the scan's `Jounal`, the verdict is `false_positive`.
- When the scan prints a typo and the transcript has other wrong text, such as `represent` for the scan's `arepresent`, the verdict is `scan_typo`. `detail` gives the text that makes sense, here `are present`.
- When the checking agent misread the scan, the verdict is `false_positive`.

 Give `unsure` only when you cannot find the place in either image, and say in `detail` what you looked for. A person decides each `unsure` issue.

Done when every issue has a verdict.

## Step 3. Write OUT

Write one JSON line for each issue to `OUT`. Copy `page`, `kind`, `transcript` and `scan` from the issue exactly, because they match the verdict to its issue:

```json
{"page": 12, "kind": "word", "transcript": "必不可少", "scan": "必不可免", "verdict": "real", "detail": "the zoom prints 必不可免"}
```

For `scan_typo`, `detail` gives the text that makes sense. Write only `OUT`. Change no other file.

Done when `OUT` has one line for each line of `ITEMS`.
