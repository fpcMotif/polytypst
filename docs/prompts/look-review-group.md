# Look review of one page group

`scripts/look_review.py brief BOOK GROUP` fills in this prompt for one checking agent. Do not edit the filled copy by hand.

You check rebuilt pages {first} to {last} of `{book}` against the scan at the publisher bar. This brief is your whole task. Your inputs are the sheets under Pages, the transcript pages, and the bar below. Your tools are the two `lr` commands this brief names. Everything you read and write is under `{review}`.

## The bar

Rule 0: the book's own scan wins. A page whose design matches its scan passes, even where a row below asks for another design. Where two rows differ, the first one wins. A row passes only when its PASS rule holds on the page, and a row whose element the page lacks is N/A. Judge every row from the sheets. The `type` field is a measure of the harness, so judge the rest of its row by eye.

{bar}

## Pages

Open each page's pair sheet with the Read tool, one image per page. Paths are relative to `{review}`. A pair sheet sets the scan pages on the left and the rebuilt page on the right, each labelled, at one line height and without white margins. The red ruler at each panel's left edge gives page shares, so it gives the numbers for a crop box. The checker already measured each page. A page with `overflow_pt` above 3 fails the overflow check. A rule name after `checker:` is a defect that `polytypst audit` counts, so the page fails that check and you write no finding for it.

{pages}

A page with no scan page shares no text with any transcript page, as a contents page or a page that lost its text does. Open the scan pages of the pages before and after it, and say in `where` which scan page you compared.

To read a region closer, run `{crop}` from any folder. It writes one sheet with a row per region, the scan box beside the rebuilt box, and prints its path. PAGE is a rebuilt page of this group. BOX is `top`, `middle`, `bottom`, `full`, or L,T,R,B as shares of the page between 0 and 1, read off the ruler, such as `0,0.4,1,0.8`. Write `PAGE:BOX:SCANBOX` when the region sits elsewhere on the scan page. A narrow box zooms further, up to 400 dpi, so box a line or a display, not a band. Put every region you want to compare in one call.

## Checks

Be harsh and strict. A page passes only when it has no defect. A doubt is a FAIL with evidence. Check in this order:

1. Looks: chapter openings (a "CHAPTER N" line under the title, a doubled "§ N. §N.", a chapter title on the page that ends the previous chapter), heading hierarchy, running heads and folios, the index (entries merged into paragraphs, missing entries), tables (the first data row set as a header, scattered cells), widows, orphans, hyphenated headings, and spacing rules of the book's language.
2. Figures: a raster crop where a vector drawing belongs, raw label text such as `T_{{f(x)}}`, doubled captions, and commutative diagrams set as arrays.
3. Numbering: numbers typed as text, gaps or doubles against the scan, equation numbers missing although the text cites them, and equation numbers off the right margin.
4. Content: a lost paragraph, a lost display, a lost table row, and a footnote left in the body. The page check compares words and symbols, so a single wrong word, accent or index gets no finding here.
5. Overflow: from `overflow_pt` above.

## Write

Write exactly two files:

- `{review}/group_{group:02d}.jsonl`: one finding per line, valid JSON, with the fields that "Facts for this review" lists. Write one finding for a defect that repeats on several pages, and list the pages in `where`.
- `{review}/group_{group:02d}.audit.jsonl`: one line per page {first} to {last}, as `{{"page": N, "scan_pages": [..], "result": "PASS" or "FAIL", "checks": {{"looks": .., "figures": .., "numbering": .., "content": .., "overflow": ..}}, "overflow_pt": X}}`. Each check is `PASS`, `FAIL` or `N/A`.

Run the check command that "Facts for this review" names, from any folder. It must print `ok`. Its messages name each bad field and its allowed values. Fix the lines it names.

Reply with one line: the count of findings by severity.
