# LaTeX mechanics (XeTeX through tectonic)

[`../templates/book.tex`](../templates/book.tex) applies everything below. Compile it with `tectonic -X compile FILE.tex`. TeX Live is not installed here, so `xelatex`, `latexmk` and `tlmgr` do not exist.

## The engine

- Tectonic runs XeTeX. `microtype` then gives **protrusion only**. Font expansion needs pdfTeX or LuaTeX, which are not available here.
- Load fonts by file name from the TeX bundle (`\setmainfont{STIXTwoText}[Extension=.otf, UprightFont=*-Regular, BoldFont=*-Bold, …]`). macOS ships STIX Two Text as a variable font. XeTeX reads only its regular and italic faces, so headings and theorem heads lose their bold without any error.
- A system font name that fontspec cannot find stops the build. Typst can see fonts (`typst fonts`) that XeTeX does not.

## The frame (memoir)

- `\settrimmedsize`, `\settypeblocksize{N\onelineskip}{W}{*}`, `\setlrmargins{*}{*}{1.5}` and `\setulmargins{*}{*}{1.5}` set the frame. Then run `\checkandfixthelayout[lines]`, which forces a whole number of lines.
- `\linespread` multiplies the class leading. memoir's 10 pt class uses 12 pt, so `\linespread{1.0833}` gives 13 pt. Setting `\baselineskip` in the preamble has no lasting effect.
- `\flushbottom` stretches vertical glue so that every page ends on the same line. Spreads come out level, but pages with displays drift off the baseline grid. This is the opposite of the Typst trade-off.

## Paragraphs and page breaks

```latex
\tolerance=200 \emergencystretch=1.5em
\widowpenalty=10000 \clubpenalty=10000 \brokenpenalty=10000
\doublehyphendemerits=10000 \finalhyphendemerits=5000
```

- `\emergencystretch` gives one extra pass before an overfull line. Read the log for `Overfull \hbox` and fix each one in the text.
- Use `\enlargethispage{\baselineskip}` or `{-\baselineskip}` to run **both** pages of a spread one line long or short.

## Math and theorems

- The display skips scale plain TeX's values to the leading: `13pt plus 3pt minus 9pt` above and below, short skips `0pt plus 3pt` and `7pt plus 3pt minus 4pt`. Set them in `\AtBeginDocument`, because size commands reset them.
- `\numberwithin{equation}{chapter}`. Use `amsthm` styles `plain`, `definition` and `remark`. Its proof ends with an open square, and `\qedhere` places it on the last line of a display.
- `unicode-math` with `\setmathfont{STIXTwoMath-Regular.otf}` matches the text face.

## Chapter openings and running heads

- `openright` puts chapters on rectos, and `\aliaspagestyle{chapter}{plain}` puts the folio at the foot of the opening page.
- A chapter style must reset the font in `\chaptitlefont` (`\normalfont\LARGE`). memoir does not group the name and the title, so a small-caps label leaks into the title.
- `\makepsmarks` with `\createmark{chapter}{left}{nonumber}…` and `\createmark{section}{right}…` gives a chapter head on versos and a section head on rectos.

## Reprint marker

`\marginpar` goes to the outer margin on both sides when the document is `twoside`. Give it room with `\setmarginnotes{1em}{4em}{\baselineskip}` before `\checkandfixthelayout`.
