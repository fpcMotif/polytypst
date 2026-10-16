"""Kerodon Web & DOM Extractor for Mathematical Environments and Diagrams."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class KerodonDiagram:
    tag: str
    index: int
    latex_source: str
    image_path: Optional[str] = None
    caption: Optional[str] = None


@dataclass
class KerodonEnvironment:
    tag: str
    env_type: str  # definition, theorem, proposition, lemma, corollary, remark, example, notation, warning, exercise
    number: str    # e.g. "1.1.0.2"
    title: str     # e.g. "The Simplex Category"
    raw_html: str
    body_markdown: str
    diagrams: List[KerodonDiagram] = field(default_factory=list)


@dataclass
class KerodonSubsection:
    tag: str
    number: str    # e.g. "1.1.1"
    title: str     # e.g. "Face Operators"
    environments: List[KerodonEnvironment] = field(default_factory=list)


@dataclass
class KerodonSection:
    tag: str
    number: str    # e.g. "1.1"
    title: str     # e.g. "Simplicial Sets"
    intro_environments: List[KerodonEnvironment] = field(default_factory=list)
    subsections: List[KerodonSubsection] = field(default_factory=list)


@dataclass
class KerodonChapter:
    tag: str
    number: str    # e.g. "1"
    title: str     # e.g. "The Language of $\\infty$-Categories"
    intro_text: str = ""
    sections: List[KerodonSection] = field(default_factory=list)


class KerodonExtractor:
    """Extracts structured mathematical content from Kerodon cached HTML."""

    SECTION_MAP = {
        "0004": ("1.1", "Simplicial Sets", [
            ("04ZB", "1.1.1", "Face Operators"),
            ("04ZJ", "1.1.2", "Degeneracy Operators"),
            ("04ZS", "1.1.3", "Dimensions of Simplicial Sets"),
            ("0010", "1.1.4", "The Skeletal Filtration"),
            ("00FQ", "1.1.5", "Discrete Simplicial Sets"),
            ("001D", "1.1.6", "Directed Graphs as Simplicial Sets"),
        ]),
        "0508": ("1.2", "From Topological Spaces to Simplicial Sets", [
            ("00G5", "1.2.1", "Connected Components of Simplicial Sets"),
            ("001Q", "1.2.2", "The Singular Simplicial Set of a Topological Space"),
            ("001X", "1.2.3", "The Geometric Realization of a Simplicial Set"),
            ("000K", "1.2.4", "Horns"),
            ("002G", "1.2.5", "Kan Complexes"),
        ]),
        "002L": ("1.3", "From Categories to Simplicial Sets", [
            ("002M", "1.3.1", "The Nerve of a Category"),
            ("04FY", "1.3.2", "Example: Monoids as Simplicial Sets"),
            ("002Y", "1.3.3", "Recovering a Category from its Nerve"),
            ("0030", "1.3.4", "Characterization of Nerves"),
            ("0035", "1.3.5", "The Nerve of a Groupoid"),
            ("00HE", "1.3.6", "The Homotopy Category of a Simplicial Set"),
            ("00HJ", "1.3.7", "Example: The Path Category of a Directed Graph"),
        ]),
        "0039": ("1.4", r"$\infty$-Categories", [
            ("003F", "1.4.1", "Objects and Morphisms"),
            ("003L", "1.4.2", r"The Opposite of an $\infty$-Category"),
            ("003U", "1.4.3", "Homotopies of Morphisms"),
            ("0041", "1.4.4", "Composition of Morphisms"),
            ("0049", "1.4.5", r"The Homotopy Category of an $\infty$-Category"),
            ("004Q", "1.4.6", "Isomorphisms"),
        ]),
        "0055": ("1.5", r"Functors of $\infty$-Categories", [
            ("0057", "1.5.1", "Examples of Functors"),
            ("005H", "1.5.2", "Commutative Diagrams"),
            ("005Z", "1.5.3", r"The $\infty$-Category of Functors"),
            ("006B", "1.5.4", "Digression: Lifting Properties"),
            ("006V", "1.5.5", "Trivial Kan Fibrations"),
            ("0078", "1.5.6", "Uniqueness of Composition"),
            ("00J3", "1.5.7", "Universality of Path Categories"),
        ]),
    }

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)

    def extract_chapter_1(self) -> KerodonChapter:
        """Parse all cached pages into a structured KerodonChapter object."""
        ch_file = self.cache_dir / "tag_0001.html"
        intro_text = ""
        if ch_file.exists():
            html = ch_file.read_text(encoding="utf-8")
            # Extract chapter intro paragraph before first section
            m_intro = re.search(r"<p>(A principal goal of algebraic topology.*?)</p>", html, re.DOTALL)
            if m_intro:
                intro_text = re.sub(r"<[^>]+>", " ", m_intro.group(1)).strip()

        chapter = KerodonChapter(
            tag="0001",
            number="1",
            title=r"The Language of $\infty$-Categories",
            intro_text=intro_text
        )

        for sec_tag, (sec_num, sec_title, subsec_defs) in self.SECTION_MAP.items():
            sec_file = self.cache_dir / f"tag_{sec_tag}.html"
            intro_envs = []
            if sec_file.exists():
                intro_envs = self._parse_environments_from_html(sec_file.read_text(encoding="utf-8"))

            section = KerodonSection(
                tag=sec_tag,
                number=sec_num,
                title=sec_title,
                intro_environments=intro_envs
            )

            for sub_tag, sub_num, sub_title in subsec_defs:
                sub_file = self.cache_dir / f"tag_{sub_tag}.html"
                sub_envs = []
                if sub_file.exists():
                    sub_envs = self._parse_environments_from_html(sub_file.read_text(encoding="utf-8"))

                subsection = KerodonSubsection(
                    tag=sub_tag,
                    number=sub_num,
                    title=sub_title,
                    environments=sub_envs
                )
                section.subsections.append(subsection)

            chapter.sections.append(section)

        return chapter

    def _parse_environments_from_html(self, html: str) -> List[KerodonEnvironment]:
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
                # Match: "Definition 1.1.0.2 (The Simplex Category) ."
                m_num = re.search(r"(\d+\.\d+\.\d+\.\d+)", hdr_text)
                if m_num:
                    num = m_num.group(1)
                m_title = re.search(r"\((.*)\)", hdr_text)
                if m_title:
                    title = m_title.group(1).strip()

            # Extract commutative diagrams
            diagrams = []
            diag_idx = 1
            eq_matches = list(re.finditer(r"<div class=\"equation\">\s*\\\[\s*(.*?)\s*\\\]\s*</div>", body, re.DOTALL))
            for eq_m in eq_matches:
                eq_code = eq_m.group(1).strip()
                if r"\xymatrix" in eq_code or r"\begin{xy}" in eq_code:
                    diagram = KerodonDiagram(
                        tag=tag,
                        index=diag_idx,
                        latex_source=eq_code,
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

        # Replace equation divs containing xymatrix with a special marker
        def replace_eq(m):
            code = m.group(1).strip()
            if r"\xymatrix" in code or r"\begin{xy}" in code:
                return f"\n\n:::COMMUTATIVE_DIAGRAM:::{code}:::END_DIAGRAM:::\n\n"
            else:
                return f"\n\n$$\n{code}\n$$\n\n"

        s = re.sub(r"<div class=\"equation\">\s*\\\[\s*(.*?)\s*\\\]\s*</div>", replace_eq, s, flags=re.DOTALL)

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
