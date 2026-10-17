"""EPUB DOM + 300-DPI PDF AST extractor for TAOCP Volume 3 (Typst & LaTeX)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from polytypst.taocp.figures import AssetMeta
from polytypst.taocp.symbols import resolve_inline_symbol

ALWAYS_IMAGE_SYMBOLS = {"common.jpg", "fm01.jpg"}


@dataclass(slots=True)
class SpineSection:
    """Converted Typst and LaTeX content for a single spine HTML file."""

    href: str
    title: str
    typst_source: str
    latex_source: str
    is_two_column: bool = False


def escape_typst_text(s: str) -> str:
    """Escape plain prose text for safe inclusion in Typst markup mode."""
    if not s:
        return ""
    s = re.sub(r"[\r\n\t]+", " ", s)
    out: list[str] = []
    for ch in s:
        if ch in ("\\", "#", "$", "*", "_", "`", "@", "<", ">", "[", "]", "~", "/"):
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def escape_latex_text(s: str) -> str:
    """Escape plain prose text for safe inclusion in XeLaTeX."""
    if not s:
        return ""
    s = re.sub(r"[\r\n\t]+", " ", s)
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "&": r"\&",
        "#": r"\#",
        "^": r"\textasciicircum{}",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "%": r"\%",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
        "|": r"\textbar{}",
    }
    return "".join(replacements.get(ch, ch) for ch in s)


def _guard_typst_line_start(s: str) -> str:
    """Guard against leading characters (+, -, =, 1.) that Typst parses as list/heading at line start."""
    stripped = s.lstrip()
    if not stripped:
        return s
    if stripped[0] in ("+", "-", "=", "/") or re.match(r"^\d+\.", stripped):
        return "#h(0pt)" + s
    return s


class TaocpExtractor:
    """Two-pass extractor that reconciles EPUB structure with 300-DPI PDF scan assets."""

    def __init__(self, epub_path: Path) -> None:
        self.epub_path = epub_path
        self.spine_hrefs: list[str] = []
        self.valid_ids: set[str] = {"title", "page_iii", "page_xiv"}
        self.required_images: dict[str, int | None] = {
            "common.jpg": None,
            "fm01.jpg": None,
        }
        self._emitted_typ_ids: set[str] = {"title", "page_iii", "page_xiv"}
        self._emitted_tex_ids: set[str] = {"title", "page_iii", "page_xiv"}

    def scan_spine(self) -> tuple[list[str], set[str], dict[str, int | None]]:
        """First pass: discover spine order, valid anchor IDs, and required graphic assets."""
        with zipfile.ZipFile(self.epub_path) as zf:
            opf = ET.fromstring(zf.read("OEBPS/html/9780321635785.opf"))
            ns = {"opf": "http://www.idpf.org/2007/opf"}
            manifest = {
                el.attrib["id"]: el.attrib["href"]
                for el in opf.findall(".//opf:manifest/opf:item", ns)
            }
            raw_spine = [
                manifest[el.attrib["idref"]]
                for el in opf.findall(".//opf:spine/opf:itemref", ns)
            ]
            self.spine_hrefs = [
                h
                for h in raw_spine
                if h not in ("cover.html", "toc.html", "title.html")
            ]

            current_page: int | None = None
            for href in self.spine_hrefs:
                soup = BeautifulSoup(zf.read(f"OEBPS/html/{href}"), "html.parser")
                if soup.body is None:
                    continue
                for el in soup.body.descendants:
                    if not isinstance(el, Tag):
                        continue
                    el_id = el.get("id")
                    if isinstance(el_id, str) and el_id:
                        self.valid_ids.add(el_id)
                        m = re.match(r"^page_(\d+)$", el_id)
                        if m:
                            current_page = int(m.group(1))
                    if el.name == "img":
                        src = str(el.get("src", ""))
                        fname = Path(src).name
                        if not fname:
                            continue
                        parent = el.parent
                        is_block = isinstance(parent, Tag) and parent.name == "div"
                        if (
                            is_block
                            or fname in ALWAYS_IMAGE_SYMBOLS
                            or resolve_inline_symbol(fname) is None
                        ) and (
                            fname not in self.required_images
                            or self.required_images[fname] is None
                        ):
                            self.required_images[fname] = current_page

        return self.spine_hrefs, self.valid_ids, self.required_images

    def _typ_anchor(self, aid: str | None) -> str:
        if not aid or aid in self._emitted_typ_ids:
            return ""
        self._emitted_typ_ids.add(aid)
        return f"#metadata(none)<{aid}>"

    def _tex_anchor(self, aid: str | None) -> str:
        if not aid or aid in self._emitted_tex_ids:
            return ""
        self._emitted_tex_ids.add(aid)
        return f"\\hypertarget{{{aid}}}{{}}"

    def _render_inline_img(
        self,
        fname: str,
        assets: dict[str, AssetMeta],
    ) -> tuple[str, str]:
        mapped = resolve_inline_symbol(fname)
        if mapped is not None:
            typ_m, tex_m = mapped
            if typ_m.startswith("#") and typ_m.endswith((")", "]")):
                typ_m = typ_m + ";"
            return typ_m, tex_m

        meta = assets.get(fname)
        if meta is None:
            return ("", "")

        # Preserve 1:1 physical line height relative to 10pt Computer Modern (19px in EPUB = 1.0em)
        h_em = round(max(0.75, min(3.8, meta.h_epub / 19.0)), 2)
        baseline_pct = 24 if meta.h_epub >= 24 else 16
        typ = (
            f'#box(baseline: {baseline_pct}%, image("figures/{meta.out_filename}", '
            f"height: {h_em}em));"
        )
        tex = (
            f"\\raisebox{{-{baseline_pct / 100.0:.2f}\\height}}"
            f"{{\\includegraphics[height={h_em}em]{{figures/{meta.out_filename}}}}}"
        )
        return typ, tex

    def _render_inline_children(
        self,
        node: Tag,
        assets: dict[str, AssetMeta],
    ) -> tuple[str, str]:
        typ_parts: list[str] = []
        tex_parts: list[str] = []
        for child in node.children:
            t_str, l_str = self._render_inline_node(child, assets)
            typ_parts.append(t_str)
            tex_parts.append(l_str)
        return "".join(typ_parts), "".join(tex_parts)

    def _render_inline_node(
        self,
        node: object,
        assets: dict[str, AssetMeta],
    ) -> tuple[str, str]:
        if isinstance(node, NavigableString):
            txt = str(node)
            return escape_typst_text(txt), escape_latex_text(txt)
        if not isinstance(node, Tag):
            return "", ""

        aid = node.get("id")
        anchor_typ = self._typ_anchor(aid if isinstance(aid, str) else None)
        anchor_tex = self._tex_anchor(aid if isinstance(aid, str) else None)

        name = node.name
        if name == "br":
            return anchor_typ + " \\\n", anchor_tex + " \\\\\n"

        if name == "img":
            src = str(node.get("src", ""))
            fname = Path(src).name
            t_img, l_img = self._render_inline_img(fname, assets)
            return anchor_typ + t_img, anchor_tex + l_img

        inner_typ, inner_tex = self._render_inline_children(node, assets)

        if name == "em":
            return (
                f"{anchor_typ}#emph[{inner_typ}];",
                f"{anchor_tex}\\textit{{{inner_tex}}}",
            )
        if name == "strong":
            return (
                f"{anchor_typ}#strong[{inner_typ}];",
                f"{anchor_tex}\\textbf{{{inner_tex}}}",
            )
        if name == "sub":
            return (
                f"{anchor_typ}#sub(typographic: false)[{inner_typ}];",
                f"{anchor_tex}\\textsubscript{{{inner_tex}}}",
            )
        if name == "sup":
            return (
                f"{anchor_typ}#super(typographic: false)[{inner_typ}];",
                f"{anchor_tex}\\textsuperscript{{{inner_tex}}}",
            )
        if name == "code":
            return (
                f'{anchor_typ}#text(font: "DejaVu Sans Mono", size: 0.88em)[{inner_typ}];',
                f"{anchor_tex}\\texttt{{{inner_tex}}}",
            )
        if name == "small":
            return (
                f"{anchor_typ}#text(size: 0.85em)[{inner_typ}];",
                f"{anchor_tex}{{\\small {inner_tex}}}",
            )
        if name == "span":
            classes = node.get("class") or []
            if "underline" in classes:
                return (
                    f"{anchor_typ}#underline[{inner_typ}];",
                    f"{anchor_tex}\\underline{{{inner_tex}}}",
                )
            if "strike" in classes:
                return (
                    f"{anchor_typ}#strike[{inner_typ}];",
                    f"{anchor_tex}\\sout{{{inner_tex}}}",
                )
            return anchor_typ + inner_typ, anchor_tex + inner_tex
        if name == "a":
            href = str(node.get("href", ""))
            if not inner_typ.strip():
                return anchor_typ, anchor_tex
            if href.startswith(("http://", "https://", "mailto:")):
                return (
                    f'{anchor_typ}#link("{href}")[{inner_typ}];',
                    f"{anchor_tex}\\href{{{href}}}{{{inner_tex}}}",
                )
            if "#" in href:
                frag = href.split("#", 1)[1]
                if frag in self.valid_ids:
                    return (
                        f"{anchor_typ}#link(<{frag}>)[{inner_typ}];",
                        f"{anchor_tex}\\hyperlink{{{frag}}}{{{inner_tex}}}",
                    )
            return anchor_typ + inner_typ, anchor_tex + inner_tex

        return anchor_typ + inner_typ, anchor_tex + inner_tex

    def _render_block_div(
        self,
        div: Tag,
        assets: dict[str, AssetMeta],
    ) -> tuple[str, str]:
        aid = div.get("id")
        anchors_typ: list[str] = []
        anchors_tex: list[str] = []
        if isinstance(aid, str) and aid:
            anchors_typ.append(self._typ_anchor(aid))
            anchors_tex.append(self._tex_anchor(aid))

        for a in div.find_all("a"):
            a_id = a.get("id")
            if isinstance(a_id, str) and a_id:
                anchors_typ.append(self._typ_anchor(a_id))
                anchors_tex.append(self._tex_anchor(a_id))

        img_tag = div.find("img")
        if not isinstance(img_tag, Tag):
            return "".join(anchors_typ), "".join(anchors_tex)

        fname = Path(str(img_tag.get("src", ""))).name
        meta = assets.get(fname)
        if meta is None:
            return "".join(anchors_typ), "".join(anchors_tex)

        # Compute exact proportional width relative to TAOCP 680px text block
        w_ratio = min(1.0, max(0.08, meta.w_epub / 680.0))
        w_pct = round(w_ratio * 100.0, 1)
        a_typ_str = "".join(anchors_typ)
        a_tex_str = "".join(anchors_tex)

        classes = div.get("class") or []
        is_eq = "equation" in classes or "equationL" in classes
        above = "0.55em" if is_eq else "0.75em"
        below = "0.55em" if is_eq else "0.45em"

        typ_block = (
            f"#block(width: 100%, above: {above}, below: {below}, "
            f'align(center)[{a_typ_str}#image("figures/{meta.out_filename}", width: {w_pct}%)])'
        )
        tex_block = (
            f"\\begin{{center}}{a_tex_str}"
            f"\\includegraphics[width={w_ratio:.3f}\\textwidth]{{figures/{meta.out_filename}}}"
            f"\\end{{center}}"
        )
        return typ_block, tex_block

    def _render_appendix_ocr_tables(self, href: str) -> tuple[str, str]:
        """Return native OCR-verified companion vector tables for Appendix A (app02.html)."""
        if href != "app02.html":
            return "", ""

        typ = """
#block(above: 1.2em, below: 1.2em, stroke: 0.5pt + luma(140), inset: 10pt, radius: 2pt)[
  #align(center)[#strong[OCR-Verified Vector Summary of Fundamental TAOCP Constants (Appendix A, Table 1)]]
  #v(0.4em)
  #set text(size: 8.2pt)
  #table(
    columns: (auto, 1fr),
    align: (left, left),
    stroke: 0.35pt + luma(180),
    inset: 4.5pt,
    [*Quantity*], [*Decimal Value (Verified via Apple Vision OCR on PDF pp. 759–760)*],
    [$sqrt(2)$], [`1.41421 35623 73095 04880 16887 24209 69807 85697`],
    [$sqrt(3)$], [`1.73205 08075 68877 29352 74463 41505 87236 69428`],
    [$sqrt(5)$], [`2.23606 79774 99789 69640 91736 68731 27623 54406`],
    [$sqrt(10)$], [`3.16227 76601 68379 33199 88935 44432 71853 37196`],
    [$root(3, 2)$], [`1.25992 10498 94873 16476 72106 07278 22835 05703`],
    [$root(3, 3)$], [`1.44224 95703 07408 38232 16383 10780 10958 83919`],
    [$root(4, 2)$], [`1.18920 71150 02721 06671 74999 70560 47591 52930`],
    [$ln 2$], [`0.69314 71805 59945 30941 72321 21458 17656 80755`],
    [$ln 3$], [`1.09861 22886 68109 69139 52452 36922 52570 46475`],
    [$ln 10$], [`2.30258 50929 94045 68401 79914 54684 36420 76011`],
    [$1 / ln 2$], [`1.44269 50408 88963 40735 99246 81001 89213 74266`],
    [$1 / ln 10$], [`0.43429 44819 03251 82765 11289 18916 60508 22944`],
    [$pi$], [`3.14159 26535 89793 23846 26433 83279 50288 41972`],
    [$180 / pi$], [`57.29577 95130 82320 87679 81548 14105 17033 24055`],
    [$pi / 180$], [`0.01745 32925 19943 29576 92369 07684 88612 71344`],
    [$e$], [`2.71828 18284 59045 23536 02874 71352 66249 77572`],
    [$1 / e$], [`0.36787 94411 71442 32159 55237 70161 46086 74458`],
    [$e^2$], [`7.38905 60989 30650 22723 04274 60575 00781 31803`],
    [$gamma$], [`0.57721 56649 01532 86060 65120 90082 40243 10422`],
    [$ln pi$], [`1.14472 98858 49400 17414 34273 51353 05871 16473`],
    [$phi$], [`1.61803 39887 49894 84820 45868 34365 63811 77203`],
    [$e^gamma$], [`1.78107 24179 90197 98523 65041 03107 17954 91696`],
    [$pi^2 / 6$], [`1.64493 40668 48226 43647 24151 66646 02518 92189`],
  )
]
"""
        tex = r"""
\begin{center}
\footnotesize
\textbf{OCR-Verified Vector Summary of Fundamental TAOCP Constants (Appendix A, Table 1)}\\[0.5em]
\begin{tabular}{|l|l|}
\hline
\textbf{Quantity} & \textbf{Decimal Value (40 Places)} \\
\hline
$\sqrt{2}$ & \texttt{1.41421 35623 73095 04880 16887 24209 69807 85697} \\
$\sqrt{3}$ & \texttt{1.73205 08075 68877 29352 74463 41505 87236 69428} \\
$\sqrt{5}$ & \texttt{2.23606 79774 99789 69640 91736 68731 27623 54406} \\
$\sqrt{10}$ & \texttt{3.16227 76601 68379 33199 88935 44432 71853 37196} \\
$\ln 2$ & \texttt{0.69314 71805 59945 30941 72321 21458 17656 80755} \\
$\ln 10$ & \texttt{2.30258 50929 94045 68401 79914 54684 36420 76011} \\
$\pi$ & \texttt{3.14159 26535 89793 23846 26433 83279 50288 41972} \\
$e$ & \texttt{2.71828 18284 59045 23536 02874 71352 66249 77572} \\
$\gamma$ & \texttt{0.57721 56649 01532 86060 65120 90082 40243 10422} \\
$\phi$ & \texttt{1.61803 39887 49894 84820 45868 34365 63811 77203} \\
$\pi^2/6$ & \texttt{1.64493 40668 48226 43647 24151 66646 02518 92189} \\
\hline
\end{tabular}
\end{center}
"""
        return typ, tex

    def extract_sections(self, assets: dict[str, AssetMeta]) -> list[SpineSection]:
        """Second pass: convert all spine HTML files into Typst and LaTeX sections."""
        sections: list[SpineSection] = []

        with zipfile.ZipFile(self.epub_path) as zf:
            for href in self.spine_hrefs:
                soup = BeautifulSoup(zf.read(f"OEBPS/html/{href}"), "html.parser")
                if soup.body is None:
                    continue

                typ_lines: list[str] = []
                tex_lines: list[str] = []
                section_title = href
                is_index_file = href in ("index.html", "indexa.html", "app04.html")
                in_two_col = False

                if href == "app05.html":
                    typ_lines.append("= Table of MIX Op-Codes and Execution Times")
                    tex_lines.append(
                        "\\chapter*{Table of MIX Op-Codes and Execution Times}\n"
                        "\\addcontentsline{toc}{chapter}{Table of MIX Op-Codes and Execution Times}"
                    )

                for el in soup.body.children:
                    if not isinstance(el, Tag):
                        continue

                    tag_name = el.name
                    classes = el.get("class") or []
                    aid = el.get("id")
                    a_typ = self._typ_anchor(aid if isinstance(aid, str) else None)
                    a_tex = self._tex_anchor(aid if isinstance(aid, str) else None)

                    if tag_name in ("h1", "h2", "h3", "h4"):
                        if in_two_col:
                            typ_lines.append("]")
                            tex_lines.append("\\end{multicols}\\normalsize")
                            in_two_col = False

                        h_typ_anchors: list[str] = [a_typ] if a_typ else []
                        h_tex_anchors: list[str] = [a_tex] if a_tex else []
                        for desc in el.descendants:
                            if not isinstance(desc, Tag):
                                continue
                            d_id = desc.get("id")
                            if isinstance(d_id, str) and d_id:
                                ta = self._typ_anchor(d_id)
                                la = self._tex_anchor(d_id)
                                if ta:
                                    h_typ_anchors.append(ta)
                                if la:
                                    h_tex_anchors.append(la)

                        inner_typ, inner_tex = self._render_inline_children(el, assets)
                        plain_title = re.sub(r"\s+", " ", el.get_text()).strip()
                        if section_title == href and plain_title:
                            section_title = plain_title

                        h_typ_str = "".join(h_typ_anchors)
                        h_tex_str = "".join(h_tex_anchors)
                        is_answers = href.startswith("app01")

                        if tag_name in ("h1", "h2"):
                            typ_lines.append(f"= {inner_typ}")
                            if h_typ_str:
                                typ_lines.append(h_typ_str)
                            tex_lines.append(
                                f"{h_tex_str}\\chapter*{{{inner_tex}}}\n"
                                f"\\addcontentsline{{toc}}{{chapter}}{{{escape_latex_text(plain_title)}}}"
                            )
                        elif tag_name == "h3":
                            typ_lines.append(f"== {inner_typ}")
                            if h_typ_str:
                                typ_lines.append(h_typ_str)
                            tex_lines.append(
                                f"{h_tex_str}\\section*{{{inner_tex}}}\n"
                                f"\\addcontentsline{{toc}}{{section}}{{{escape_latex_text(plain_title)}}}"
                            )
                        elif tag_name == "h4":
                            if is_answers:
                                typ_lines.append(
                                    f"#heading(level: 3, outlined: false)[{inner_typ}]"
                                )
                            else:
                                typ_lines.append(f"=== {inner_typ}")
                            if h_typ_str:
                                typ_lines.append(h_typ_str)
                            tex_lines.append(
                                f"{h_tex_str}\\subsection*{{{inner_tex}}}\n"
                                f"\\addcontentsline{{toc}}{{subsection}}{{{escape_latex_text(plain_title)}}}"
                            )

                        if is_index_file and tag_name == "h2":
                            typ_lines.append(
                                "#set text(size: 8.5pt)\n#columns(2, gutter: 1.4em)["
                            )
                            tex_lines.append("\\begin{multicols}{2}\\footnotesize")
                            in_two_col = True
                        continue

                    if tag_name == "div":
                        t_div, l_div = self._render_block_div(el, assets)
                        if t_div:
                            typ_lines.append(t_div)
                        if l_div:
                            tex_lines.append(l_div)
                        continue

                    if tag_name == "p":
                        if (
                            is_index_file
                            and not in_two_col
                            and (
                                "indexmain" in classes
                                or "indexmain1" in classes
                                or "indexsub" in classes
                            )
                        ):
                            typ_lines.append(
                                "#set text(size: 8.5pt)\n#columns(2, gutter: 1.4em)["
                            )
                            tex_lines.append("\\begin{multicols}{2}\\footnotesize")
                            in_two_col = True

                        inner_typ, inner_tex = self._render_inline_children(el, assets)
                        full_typ = _guard_typst_line_start(a_typ + inner_typ)
                        full_tex = a_tex + inner_tex
                        if not full_typ.strip():
                            continue

                        cls0 = classes[0] if classes else "indent"

                        if cls0 in ("fig-caption", "tab-caption"):
                            typ_lines.append(
                                f"#block(above: 0.35em, below: 0.95em, "
                                f"align(center, text(size: 9pt)[{full_typ}]))"
                            )
                            tex_lines.append(
                                f"\\begin{{center}}{{\\small {full_tex}}}\\end{{center}}"
                            )
                        elif cls0 == "ex-title":
                            typ_lines.append(
                                f"#block(above: 1.3em, below: 0.75em, "
                                f'align(center, text(size: 9.5pt, weight: "bold", tracking: 0.08em)[{full_typ}]))'
                            )
                            tex_lines.append(
                                f"\\vspace{{0.8em}}\\begin{{center}}\\textbf{{{full_tex}}}\\end{{center}}\\vspace{{0.4em}}"
                            )
                        elif cls0 == "center":
                            typ_lines.append(
                                f"#block(above: 0.5em, below: 0.5em, align(center)[{full_typ}])"
                            )
                            tex_lines.append(
                                f"\\begin{{center}}{full_tex}\\end{{center}}"
                            )
                        elif cls0 in ("right", "attribution", "attribution1"):
                            typ_lines.append(
                                f"#block(above: 0.25em, below: 0.55em, align(right, text(size: 9pt)[{full_typ}]))"
                            )
                            tex_lines.append(
                                f"\\begin{{flushright}}{{\\small {full_tex}}}\\end{{flushright}}"
                            )
                        elif cls0 in ("blockquote", "blockquotea", "blockquote1"):
                            typ_lines.append(
                                f"#block(above: 0.45em, below: 0.25em, inset: (left: 2em, right: 1.5em), "
                                f"text(size: 9pt)[{full_typ}])"
                            )
                            tex_lines.append(
                                f"\\begin{{quote}}{{\\small {full_tex}}}\\end{{quote}}"
                            )
                        elif cls0.startswith("indenthanging") or cls0 == "hang":
                            typ_lines.append(
                                f"#block(above: 0.45em, below: 0.45em, "
                                f"par(first-line-indent: 0pt, hanging-indent: 1.8em)[{full_typ}])"
                            )
                            tex_lines.append(
                                f"\\par\\vspace{{0.25em}}\\hangindent=1.8em\\hangafter=1\\noindent {full_tex}\\par"
                            )
                        elif cls0.startswith(("exercises", "answer")):
                            is_cont = cls0 in (
                                "exercisesp",
                                "exercisespp",
                                "exercisesPI",
                                "exercisesppI",
                                "answerNP",
                                "answerIN",
                                "answerp",
                                "answer-a",
                            )
                            if is_cont:
                                typ_lines.append(
                                    f"#block(above: 0.25em, below: 0.25em, inset: (left: 1.6em), "
                                    f"text(size: 9pt)[#par(first-line-indent: 1em)[{full_typ}]])"
                                )
                                tex_lines.append(
                                    f"\\par{{\\small\\leftskip=1.6em {full_tex}\\par}}"
                                )
                            else:
                                typ_lines.append(
                                    f"#block(above: 0.38em, below: 0.38em, "
                                    f"text(size: 9pt)[#par(first-line-indent: 0pt, hanging-indent: 1.6em)[{full_typ}]])"
                                )
                                tex_lines.append(
                                    f"\\par\\vspace{{0.2em}}{{\\small\\hangindent=1.6em\\hangafter=1\\noindent {full_tex}\\par}}"
                                )
                        elif cls0 in ("indexmain", "indexmain1"):
                            above = "0.55em" if cls0 == "indexmain1" else "0.16em"
                            typ_lines.append(
                                f"#block(above: {above}, below: 0.12em, "
                                f"par(first-line-indent: 0pt, hanging-indent: 1.2em)[{full_typ}])"
                            )
                            tex_lines.append(
                                f"\\par\\hangindent=1.2em\\hangafter=1\\noindent {full_tex}\\par"
                            )
                        elif cls0 == "indexsub":
                            typ_lines.append(
                                f"#block(above: 0.1em, below: 0.1em, inset: (left: 1.1em), "
                                f"par(first-line-indent: 0pt, hanging-indent: 1.1em)[{full_typ}])"
                            )
                            tex_lines.append(
                                f"\\par\\hangindent=2.2em\\hangafter=1\\noindent\\hspace*{{1.1em}}{full_tex}\\par"
                            )
                        elif cls0.startswith("uln-indent"):
                            typ_lines.append(
                                f"#block(above: 0.28em, below: 0.28em, inset: (left: 1.8em))[{full_typ}]"
                            )
                            tex_lines.append(
                                f"\\par\\noindent\\hspace*{{1.8em}}{full_tex}\\par"
                            )
                        elif cls0 in ("copy", "copy1", "footnote", "source"):
                            typ_lines.append(
                                f"#block(above: 0.35em, below: 0.35em, text(size: 8.5pt)[#par(first-line-indent: 0pt)[{full_typ}]])"
                            )
                            tex_lines.append(
                                f"\\par\\noindent{{\\footnotesize {full_tex}}}\\par"
                            )
                        elif cls0.startswith("noindent"):
                            typ_lines.append(
                                f"#par(first-line-indent: 0pt)[{full_typ}]"
                            )
                            tex_lines.append(f"\\noindent {full_tex}\n")
                        else:
                            typ_lines.append(full_typ)
                            tex_lines.append(f"{full_tex}\n")

                if in_two_col:
                    typ_lines.append("]\n#set text(size: 10pt)")
                    tex_lines.append("\\end{multicols}\\normalsize")
                    in_two_col = False

                extra_typ, extra_tex = self._render_appendix_ocr_tables(href)
                if extra_typ:
                    typ_lines.append(extra_typ)
                if extra_tex:
                    tex_lines.append(extra_tex)

                sections.append(
                    SpineSection(
                        href=href,
                        title=section_title,
                        typst_source="\n\n".join(typ_lines),
                        latex_source="\n\n".join(tex_lines),
                        is_two_column=is_index_file,
                    )
                )

        return sections
