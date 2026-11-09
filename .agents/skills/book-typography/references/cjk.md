# Chinese and Japanese pages

CJK books set on a square character grid. Every character takes a 1 em frame and the characters sit solid, with 0 em between them. Latin justification stretches word spaces, but CJK text has no word spaces to stretch. Spacing and compression around punctuation therefore do that job.

## Grid

| Rule | Use | Sources |
|---|---|---|
| Body size | Chinese 10.5 pt (size 5) or 9 pt (new size 5), never under 7.875 pt. Japanese 9–10 pt. | clreq 2.2. jlreq 2.2 |
| Line length | A whole number of characters (text width = n × body size). | jlreq 2.2.4 |
| Pitch | Body size plus a line gap of 0.5–1 em (1.5–2.0 em in all). | jlreq 2.4. clreq 2.2 |
| Indent | Chinese 2 em, Japanese 1 em, on every paragraph including the first after a heading. | clreq 6.2.1.1. jlreq 3.1.5 |
| Block space | A heading, quotation or display takes a whole number of lines, so the body text returns to the grid. | jlreq 2.2.5 (JIS X 4051 8.3.3). clreq 2.3 |

## Punctuation

| Rule | Chinese (GB/T 15834—2011, clreq) | Japanese (JIS X 4051, jlreq) |
|---|---|---|
| Base width | Comma, full stop and brackets take 1 em. —— and …… take 2 em. Middle dot and slash take 0.5 em. | Brackets, comma, full stop and middle dot take 0.5 em plus 0.5 em of spacing. ? and ! take 1 em. |
| Compression | A full-width mark at a line end takes 0.5 em. Two adjacent closing marks lose 0.5 em. | The 0.5 em spacing compresses during justification. |
| Line start (forbidden) | Closing brackets and quotes, and 。，、；：？！ | The same, plus small kana, the iteration marks ゝ々 and the prolonged sound mark ー |
| Line end (forbidden) | Opening brackets and quotes | The same |
| Never split | —— and …… | The same |

## Latin and math inside CJK text

- Put 0.25 em between a CJK character and adjacent Latin letters, numerals or inline math, and none at a line start or line end (jlreq 3.7.4, clreq). Typst does this with `cjk-latin-spacing: auto`. LaTeX does it with `xeCJK` or `ctex` (Chinese) and `luatexja` (Japanese).
- Draw Latin letters from the Latin face and CJK punctuation, including quotes, from the CJK face. In Typst, give the Latin face `covers: "latin-in-cjk"`. Without it, “” come from the Latin face at half width.
- CJK faces have no italic. Keep theorem bodies upright and mark emphasis with 着重号 (emphasis dots) or a bold or kai face, never with a slant.
- Write the chapter label in the book's language: 第1章, and 证明 or 証明 for a proof.
- Vertical setting (tategumi) binds on the right, which makes the left page the recto. This skill covers horizontal setting only.
