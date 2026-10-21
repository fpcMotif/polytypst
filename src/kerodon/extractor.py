"""Kerodon Web & DOM Extractor for Mathematical Environments and Diagrams."""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class KerodonDiagram:
    tag: str
    index: int
    latex_source: str
    image_path: str | None = None
    caption: str | None = None


@dataclass
class KerodonEnvironment:
    tag: str
    env_type: str  # definition, theorem, proposition, lemma, corollary, remark, example, notation, warning, exercise
    number: str    # e.g. "1.1.0.2"
    title: str     # e.g. "The Simplex Category"
    raw_html: str
    body_markdown: str
    diagrams: list[KerodonDiagram] = field(default_factory=list)


@dataclass
class KerodonSubsection:
    tag: str
    number: str    # e.g. "1.1.1"
    title: str     # e.g. "Face Operators"
    environments: list[KerodonEnvironment] = field(default_factory=list)


@dataclass
class KerodonSection:
    tag: str
    number: str    # e.g. "1.1"
    title: str     # e.g. "Simplicial Sets"
    intro_environments: list[KerodonEnvironment] = field(default_factory=list)
    subsections: list[KerodonSubsection] = field(default_factory=list)


@dataclass
class KerodonChapter:
    tag: str
    number: str    # e.g. "1"
    title: str     # e.g. "The Language of $\\infty$-Categories"
    intro_text: str = ""
    sections: list[KerodonSection] = field(default_factory=list)


class KerodonExtractor:
    """Extracts structured mathematical content from Kerodon cached HTML."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)

    def extract_chapter(self, number: int, tag: str) -> KerodonChapter:
        """Dynamically parse all sections and subsections for any chapter from cache."""
        ch_file = self.cache_dir / f"tag_{tag}.html"
        ch_html = ch_file.read_text(encoding="utf-8") if ch_file.exists() else ""

        # Extract Title
        m_title = re.search(r"<title>(.*?)</title>", ch_html)
        raw_title = m_title.group(1) if m_title else f"Chapter {number}"
        # Clean title: e.g. "Chapter 2 (007J): Examples of $\infty $-Categories&mdash;Kerodon"
        ch_title = re.sub(r"^Chapter\s+\d+.*?:", "", raw_title)
        ch_title = re.sub(r"&mdash;.*$", "", ch_title).strip()

        # Intro text
        intro_text = ""
        m_intro = re.search(r"<div id=\"content\"[^>]*>.*?<p>(.*?)</p>", ch_html, re.DOTALL)
        if m_intro:
            cand = re.sub(r"<[^>]+>", " ", m_intro.group(1)).strip()
            if len(cand) > 30 and not cand.startswith("Chapter"):
                intro_text = cand

        chapter = KerodonChapter(
            tag=tag,
            number=str(number),
            title=ch_title,
            intro_text=intro_text
        )

        # Find section links from chapter sidebar
        sec_links = re.findall(r"<a class=\"sidebar-link\" href=\"/tag/([0-9A-Z]{4})\">([^<]+<span[^>]*>[^<]+</span>)</a>", ch_html)
        if not sec_links:
            sec_links = re.findall(r"<a[^>]*href=\"/tag/([0-9A-Z]{4})\"[^>]*>(?:Section\s+)?([0-9]+\.[0-9]+.*?)</a>", ch_html)

        seen_sec_tags = set()
        for sec_tag, _ in sec_links:
            if sec_tag in seen_sec_tags:
                continue
            seen_sec_tags.add(sec_tag)
            sec_file = self.cache_dir / f"tag_{sec_tag}.html"
            sec_html = sec_file.read_text(encoding="utf-8") if sec_file.exists() else ""

            m_sec_h2 = re.search(r"<h2[^>]*>(.*?)</h2>", sec_html)
            sec_h2_text = re.sub(r"<[^>]+>", " ", m_sec_h2.group(1)).strip() if m_sec_h2 else sec_tag
            m_sec_num = re.search(r"(\d+\.\d+)", sec_h2_text)
            sec_num = m_sec_num.group(1) if m_sec_num else f"{number}.x"
            sec_title = sec_h2_text.replace(sec_num, "").strip() if sec_num else sec_h2_text

            intro_envs = self._parse_environments_from_html(sec_html) if sec_html else []
            section = KerodonSection(
                tag=sec_tag,
                number=sec_num,
                title=sec_title,
                intro_environments=intro_envs
            )

            # Find subsections
            sub_matches = re.findall(r"<a[^>]*href=\"/tag/([0-9A-Z]{4})\"[^>]*>(.*?)</a>", sec_html)
            seen_subs = set()
            for sub_tag, sub_label in sub_matches:
                sub_text = re.sub(r"<[^>]+>", " ", sub_label).strip()
                if "Subsection" in sub_text and sub_tag not in seen_subs:
                    seen_subs.add(sub_tag)
                    sub_file = self.cache_dir / f"tag_{sub_tag}.html"
                    sub_html = sub_file.read_text(encoding="utf-8") if sub_file.exists() else ""

                    m_sub_h3 = re.search(r"<h[23][^>]*>(.*?)</h[23]>", sub_html)
                    sub_h3_text = re.sub(r"<[^>]+>", " ", m_sub_h3.group(1)).strip() if m_sub_h3 else sub_tag
                    m_sub_num = re.search(r"(\d+\.\d+\.\d+)", sub_h3_text)
                    sub_num = m_sub_num.group(1) if m_sub_num else f"{sec_num}.{len(seen_subs)}"
                    sub_title = sub_h3_text.replace(sub_num, "").strip() if sub_num else sub_h3_text

                    sub_envs = self._parse_environments_from_html(sub_html) if sub_html else []
                    section.subsections.append(KerodonSubsection(
                        tag=sub_tag,
                        number=sub_num,
                        title=sub_title,
                        environments=sub_envs
                    ))

            chapter.sections.append(section)

        return chapter

    def extract_chapter_1(self) -> KerodonChapter:
        """Extract Chapter 1."""
        return self.extract_chapter(1, "0001")

    def _parse_environments_from_html(self, html: str) -> list[KerodonEnvironment]:
        """Extract individual articles from HTML page content."""
        envs = []
        for article_m in re.finditer(r"<article class=\"([^\"]+)\" id=\"([^\"]+)\">(.*?)</article>", html, re.DOTALL):
            env_class, tag, body = article_m.groups()
            env_type = env_class.replace("env-", "").strip()

            # Extract identifier line: e.g. "Definition 1.1.0.2 (The Simplex Category)."
            num = ""
            title = ""
            hdr_m = re.search(r"<a class=\"environment-identifier\"[^>]*>(.*?)</a>", body, re.DOTALL)
            if hdr_m:
                hdr_text = re.sub(r"<[^>]+>", " ", hdr_m.group(1)).strip()
                m_num = re.search(r"(\d+\.\d+\.\d+\.\d+)", hdr_text)
                if m_num:
                    num = m_num.group(1)
                m_title = re.search(r"\((.*?)\)", hdr_text)
                if m_title:
                    title = m_title.group(1).strip()

            # Extract commutative diagrams from any equation div
            diagrams = []
            diag_idx = 1
            eq_matches = list(re.finditer(r"<div class=\"equation\">\s*(.*?)\s*</div>", body, re.DOTALL))
            for eq_m in eq_matches:
                eq_code = eq_m.group(1).strip()
                if r"\xymatrix" in eq_code or r"\begin{xy}" in eq_code:
                    clean_diag = re.sub(r"\\label\{[^}]+\}", "", eq_code)
                    clean_diag = re.sub(r"\\begin\{equation\*?\}|\\end\{equation\*?\}|\\begin\{gathered\}|\\end\{gathered\}|\\\[|\\\]", "", clean_diag).strip()
                    diagram = KerodonDiagram(
                        tag=tag,
                        index=diag_idx,
                        latex_source=clean_diag,
                        caption=f"Diagram {diag_idx} in Tag {tag} ({num})"
                    )
                    diagrams.append(diagram)
                    diag_idx += 1

            # Convert body HTML to Markdown
            clean_body = self._clean_body_html(body)

            envs.append(KerodonEnvironment(
                tag=tag,
                env_type=env_type,
                number=num,
                title=title,
                raw_html=body,
                body_markdown=clean_body,
                diagrams=diagrams
            ))

        return envs

    def _clean_body_html(self, html_fragment: str) -> str:
        """Convert Kerodon HTML fragment into clean Markdown with LaTeX math and diagram placeholders."""
        s = html_fragment

        # Remove header link paragraph
        s = re.sub(r"<p><a class=\"environment-identifier\"[^>]*>.*?</a>\s*", "<p>", s, flags=re.DOTALL)

        # Replace any equation div
        def replace_eq(m):
            code = m.group(1).strip()
            clean_c = re.sub(r"\\label\{[^}]+\}", "", code)
            clean_c = re.sub(r"\\begin\{equation\*?\}|\\end\{equation\*?\}|\\begin\{gathered\}|\\end\{gathered\}|\\\[|\\\]", "", clean_c).strip()
            if r"\xymatrix" in clean_c or r"\begin{xy}" in clean_c:
                return f"\n\n:::COMMUTATIVE_DIAGRAM:::{clean_c}:::END_DIAGRAM:::\n\n"
            else:
                return f"\n\n$$\n{clean_c}\n$$\n\n"

        s = re.sub(r"<div class=\"equation\">\s*(.*?)\s*</div>", replace_eq, s, flags=re.DOTALL)
        # Italics and bold
        s = re.sub(r"<em>(.*?)</em>", r"*\1*", s, flags=re.DOTALL)
        s = re.sub(r"<strong>(.*?)</strong>", r"**\1**", s, flags=re.DOTALL)

        # Convert citations <span class="cite">[<a href="/bibliography/ID">ID</a>]</span>
        s = re.sub(r"<span class=\"cite\">\[<a[^>]*>(.*?)</a>\]</span>", r"[\1]", s)

        # Links
        s = re.sub(r"<a[^>]*href=\"/tag/([0-9A-Z]{4})\"[^>]*>(.*?)</a>", r"\2 (Tag \1)", s)

        # Lists
        s = re.sub(r"<li>\s*<p>(.*?)</p>\s*</li>", r"- \1\n", s, flags=re.DOTALL)
        s = re.sub(r"<li>\s*(.*?)\s*</li>", r"- \1\n", s, flags=re.DOTALL)
        s = re.sub(r"</?[uo]l>", "\n", s)

        # Definition lists <dl><dt>...</dt><dd>...</dd></dl>
        s = re.sub(r"<dt>(.*?)</dt>\s*<dd>\s*<p>(.*?)</p>\s*</dd>", r"\n\1 : \2\n", s, flags=re.DOTALL)
        s = re.sub(r"</?d[ldt]>", "\n", s)

        # Paragraphs and divs
        s = re.sub(r"<p>(.*?)</p>", r"\n\n\1\n\n", s, flags=re.DOTALL)
        s = re.sub(r"<[^>]+>", " ", s)

        # Whitespace normalization
        lines = [re.sub(r"[ \t]+", " ", l).strip() for l in s.splitlines()]
        cleaned = "\n".join(lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        return cleaned
