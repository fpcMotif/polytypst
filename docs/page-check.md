# Page check: transcript against scan

You check a range of scan pages of one book. For each page you compare the transcript with the scan, and you record each difference. The scan is the witness: what the scan prints is correct. The local OCR is a second, weaker reading of the scan. It shows you where to look, and the zoom decides.

You only read the books. Write only these files:

- `OUT`, your result file
- PNG and TSV files in `output/page_check/BOOK/png/`

## Your values

The prompt gives `BOOK`, `FIRST` and `LAST`. Find `SCAN` in this table.

| `BOOK` | `SCAN` |
|---|---|
| 1 | `/Users/martinfan/Downloads/1 宏观经济与产业结构.pdf` |
| 2 | `/Users/martinfan/Downloads/2 通缩经济与货币政策.pdf` |
| 3 | `/Users/martinfan/Downloads/3 国际经济环境的变化与日本经济.pdf` |
| 4 | `/Users/martinfan/Downloads/4 不良债权与金融危机.pdf` |
| 5 | `/Users/martinfan/Downloads/5 财政政策与社会保障.pdf` |
| 6 | `/Users/martinfan/Downloads/6 劳动力市场与收入分配.pdf` |

- `PNG` is `output/page_check/BOOK/png/`.
- `OUT` is `output/page_check/BOOK/pFIRST-LAST.jsonl`, such as `output/page_check/4/p51-60.jsonl`.

Obey these rules:

1. Run every command from `/Users/martinfan/devv/polytypst.mixed`.
2. Put each path in double quotes. The names contain spaces and Chinese characters.
3. Run Python as `uv run python`.
4. Read the transcript only through `scripts/page_check.py`. Its line numbers are the ones to record.
5. When `scripts/page_check.py` says a page has no transcript, skip the page.
6. Copy the scan exactly, typos included. When the scan prints a typo and the transcript copies it, record a `scan_typo` issue. For example, the scan prints `零食` where `零售` makes sense, and the transcript also has `零食`. The build corrects scan typos later, so the transcript keeps the scan's text.

## Turn 1: run the batch

In your first turn, run this one command and nothing else. Replace `BOOK`, `FIRST`, `LAST` and `SCAN` with your values first. The command prints the transcript, the suspects and the tables of every page in your range. It also renders each page at 200 dpi and each suspect band at 300 dpi. A range of 10 pages takes about 20 seconds.

```bash
cd "/Users/martinfan/devv/polytypst.mixed"
SCAN="SCAN" BOOK=BOOK FIRST=FIRST LAST=LAST
PNG="output/page_check/$BOOK/png/"
uv run python scripts/page_png.py "$SCAN" "$PNG" --pages "$(seq -s, "$FIRST" "$LAST")" --dpi 200
for N in $(seq "$FIRST" "$LAST"); do
  echo "=== page $N: text"
  uv run python scripts/page_check.py text "$BOOK" "$N"
  echo "=== page $N: suspects"
  SUSPECTS=$(uv run python scripts/page_check.py suspects "$BOOK" "$N")
  echo "$SUSPECTS"
  echo "$SUSPECTS" | awk '$3 == "band" {print NR, $4}' | while read -r K BAND; do
    uv run python scripts/page_png.py "$SCAN" "${PNG}z${N}_${K}_" --pages "$N" --dpi 300 --clip "0,${BAND%,*},1,${BAND#*,}" >/dev/null
  done
  echo "=== page $N: cells"
  uv run python scripts/page_check.py cells "$BOOK" "$N"
done
```

The batch makes these files:

- `PNG/pN.png`: page `N` at 200 dpi.
- `PNG/zN_K_pN.png`: the zoom for suspect `K` of page `N`. `K` counts the suspect lines of the page from 1.

Steps 1, 2 and 4 read this output. Render a new zoom only for a place that the batch did not zoom, such as a table, a footnote or a rotated page:

```bash
uv run python scripts/page_png.py "SCAN" "PNG/zN_" --pages N --dpi 300 --clip 0,TOP,1,BOTTOM
```

`TOP` and `BOTTOM` are shares of the page height, such as `0.35` and `0.41`.

## Steps

Do steps 1 to 5 for each page `N` from `FIRST` to `LAST`, one page at a time. Then do step 6.

### Step 1. Read the scan page and the transcript

Read `PNG/pN.png` and the page's `text` output from the batch.

Done when you know what the page holds: headings, paragraphs, tables, equations, figures and footnotes.

### Step 2. Check each suspect

The page's `suspects` output has one line for each place where the transcript and the local OCR disagree:

```text
line 9 band 0.35,0.41 | transcript: 会对土地[使]用造成影 | ocr: [便]
```

The brackets hold the disagreement. `line` is the transcript line. `band` is the place on the page. Read the zoom `PNG/zN_K_pN.png` of each line, and decide:

| The zoom shows | Decision |
|---|---|
| The transcript text | The OCR misread the scan. Record nothing. |
| The transcript text, with a typo that the scan prints | The transcript copies the scan. Record a `scan_typo` issue. |
| The OCR text, or a third reading | Record an issue with what the zoom shows. |
| A chart, a diagram or an equation | The OCR reads these as noise. Compare the equation in step 3. |
| A running header or a page number | Record nothing. The transcript leaves them out. |

Done when you decided every suspect line.

### Step 3. Read the rest of the page

The local OCR misses some errors, such as a wrong character that the OCR misreads in the same way, and text inside equations. Compare these parts of the zoom with the transcript yourself:

- each equation: symbols, subscripts, superscripts and the equation number
- each heading number and each footnote mark (①②③) with its footnote
- each figure caption, and the notes and the source line under a figure or a table

Done when you compared each of these parts.

### Step 4. Check every table

The page's `cells` output prints each transcript table as rows, with tabs between the cells, and the count of tables. For each table `K` on the page:

1. Zoom on the table at 300 dpi. When the table is printed sideways, add `--rotate 90` or `--rotate -90`, so that the text reads upright.
2. Copy the table from the zoom into `PNG/tN_K.tsv`: one line for each printed row, from top to bottom, and a tab between the cells, from left to right. Write a header box that spans columns as one cell. Copy each number exactly, with its decimal point and sign.
3. Compare:

   ```bash
   uv run python scripts/page_check.py tablediff BOOK N K "PNG/tN_K.tsv"
   ```

4. Look again at the zoom for each line of the output. Correct your TSV when you copied wrong, and run the comparison again. Each line that stays is an issue: a wrong cell or header is `table_cell`, and a row or a column that is missing or extra is `table_shape`.
5. **Sums**: when the table prints a total, a subtotal or shares that make 100, add the scan's parts with Python, such as `uv run python -c "print(round(12.3 + 45.6 + 7.8, 3))"`. When the parts do not give the printed total, after rounding, record a `sum` issue with the note `scan prints this`.

Done when `tablediff` gave its last output for every table, and you checked each line of that output against the zoom.

### Step 5. Record the page

Before you add an issue, confirm that it is a real difference. In the first Book 4 run, 40 of the 177 issues were false, and these checks find many of them:

| Check | Example of a false issue |
|---|---|
| Copy `transcript` from the `text` output, and `scan` from the zoom, character for character. The OCR line gives neither field. | The zoom prints `市场价格`, and the issue gives the OCR's `市场地价` as the scan. |
| Compare characters, and skip spacing and the width of a mark. `）` and `)`, `？` and `?`, `（ * ）` and `（*）` are the same mark. | `监管当局②)` against `监管当局②）` |
| Before you record `missing_text`, search the page's `text` output for the text. A long line holds a whole paragraph, and your shell tool can cut a long line short. | `取得长足发展。`, which the transcript has at the end of a long line |
| Record nothing for the labels inside a chart. The build draws each chart again from the book's figure script, so its labels are not in the transcript. | The shares of a pie chart, recorded as `missing_text` |

Add one line to `OUT` for the page. Each line is one JSON object:

```json
{"book": 4, "page": 57, "issues": [{"kind": "word", "line": 9, "transcript": "使用", "scan": "便用", "note": ""}]}
```

A page with no differences gets `"issues": []`. Each issue has these fields:

| Field | Value |
|---|---|
| `kind` | One of the kinds in the next table |
| `line` | The transcript line number, or `null` when the transcript has no such line |
| `transcript` | The transcript text, copied exactly, at most 40 characters. Empty for `missing_text` |
| `scan` | What the scan prints, at most 40 characters. Empty for `extra_text` |
| `note` | For a table: `table K`, and the row and the column labels. For a `scan_typo`: `meant: ` and the text that makes sense. Otherwise empty |

| `kind` | Use it when |
|---|---|
| `word` | A character or a word differs |
| `number` | A digit, a decimal point or a sign in the body text differs |
| `table_cell` | A table cell or a table header differs |
| `table_shape` | A table row or column is missing or extra |
| `missing_text` | The scan has text that the transcript does not have |
| `extra_text` | The transcript has text that the scan does not have |
| `order` | The same text is in a different order |
| `mark` | Punctuation or a footnote mark differs |
| `math` | An equation or an equation number differs |
| `sum` | The scan's own numbers do not add up |
| `scan_typo` | The scan prints a typo, and the transcript copies it. `transcript` and `scan` hold the same text |

Done when `OUT` has the line for page `N`.

### Step 6. Check your file

```bash
uv run python scripts/page_check.py summary --books BOOK
```

Done when the output names no `bad line` in `OUT`, and no page from `FIRST` to `LAST` is in the `unchecked` list. Then reply with one line: `BOOK FIRST-LAST: P pages, I issues`.
