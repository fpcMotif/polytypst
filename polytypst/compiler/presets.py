from dataclasses import dataclass


@dataclass(frozen=True)
class PublisherPreset:
    key: str
    imprint_name: str
    default_series: str
    cities_line: str
    width_pt: int
    height_pt: int
    margin_inside_pt: int
    margin_outside_pt: int
    margin_top_pt: int
    margin_bottom_pt: int
    body_size_pt: float
    heading_style: str
    header_rule_pt: float
    pandoc_geometry: str


@dataclass(frozen=True)
class LanguageProfile:
    code: str
    typst_lang: str
    font_stack: tuple[str, ...]
    math_font: str
    first_line_indent: str
    leading: str
    par_spacing: str
    hyphenate: bool
    cjk_punctuation_compress: bool
    contents_title: str
    ocr_instruction: str


@dataclass(frozen=True)
class DomainProfile:
    key: str
    equation_numbering: str
    theorem_heads: tuple[str, ...]
    figure_layer_mode: str
    sanitize_inline_math: bool
    drop_cap_chapters: bool


PUBLISHER_PRESETS: dict[str, PublisherPreset] = {
    "cambridge": PublisherPreset(
        key="cambridge",
        imprint_name="Cambridge University Press",
        default_series="Cambridge Studies in Advanced Mathematics",
        cities_line="Cambridge · New York · Melbourne · Madrid · Cape Town · Singapore",
        width_pt=442,
        height_pt=663,
        margin_inside_pt=56,
        margin_outside_pt=56,
        margin_top_pt=56,
        margin_bottom_pt=62,
        body_size_pt=10.0,
        heading_style="ruled",
        header_rule_pt=0.35,
        pandoc_geometry="paperwidth=6.14in,paperheight=9.21in,margin=0.78in",
    ),
    "springer": PublisherPreset(
        key="springer",
        imprint_name="Springer",
        default_series="Graduate Texts in Mathematics",
        cities_line="Berlin · Heidelberg · New York · Tokyo",
        width_pt=440,
        height_pt=666,
        margin_inside_pt=54,
        margin_outside_pt=58,
        margin_top_pt=54,
        margin_bottom_pt=60,
        body_size_pt=10.0,
        heading_style="numbered-block",
        header_rule_pt=0.4,
        pandoc_geometry="paperwidth=6.11in,paperheight=9.25in,margin=0.76in",
    ),
    "mit": PublisherPreset(
        key="mit",
        imprint_name="The MIT Press",
        default_series="MIT Press Series",
        cities_line="Cambridge, Massachusetts · London, England",
        width_pt=504,
        height_pt=648,
        margin_inside_pt=64,
        margin_outside_pt=72,
        margin_top_pt=58,
        margin_bottom_pt=64,
        body_size_pt=10.0,
        heading_style="architectural",
        header_rule_pt=0.5,
        pandoc_geometry="paperwidth=7.0in,paperheight=9.0in,margin=0.9in",
    ),
    "harvard": PublisherPreset(
        key="harvard",
        imprint_name="Harvard University Press",
        default_series="Harvard University Press Monographs",
        cities_line="Cambridge, Massachusetts · London, England",
        width_pt=432,
        height_pt=648,
        margin_inside_pt=58,
        margin_outside_pt=58,
        margin_top_pt=58,
        margin_bottom_pt=66,
        body_size_pt=10.5,
        heading_style="centered-smallcaps",
        header_rule_pt=0.0,
        pandoc_geometry="paperwidth=6.0in,paperheight=9.0in,margin=0.8in",
    ),
    "ams": PublisherPreset(
        key="ams",
        imprint_name="American Mathematical Society",
        default_series="Graduate Studies in Mathematics",
        cities_line="Providence, Rhode Island",
        width_pt=468,
        height_pt=720,
        margin_inside_pt=62,
        margin_outside_pt=62,
        margin_top_pt=60,
        margin_bottom_pt=66,
        body_size_pt=10.0,
        heading_style="ams-sc",
        header_rule_pt=0.35,
        pandoc_geometry="paperwidth=6.5in,paperheight=10.0in,margin=0.86in",
    ),
}


LANGUAGE_PROFILES: dict[str, LanguageProfile] = {
    "en": LanguageProfile(
        code="en",
        typst_lang="en",
        font_stack=("New Computer Modern",),
        math_font="New Computer Modern Math",
        first_line_indent="1.5em",
        leading="0.65em",
        par_spacing="0.85em",
        hyphenate=True,
        cjk_punctuation_compress=False,
        contents_title="Contents",
        ocr_instruction="Transcribe English text and LaTeX math faithfully.",
    ),
    "ja": LanguageProfile(
        code="ja",
        typst_lang="ja",
        font_stack=(
            "New Computer Modern",
            "Hiragino Mincho ProN",
            "Harano Aji Mincho",
        ),
        math_font="New Computer Modern Math",
        first_line_indent="1.0em",
        leading="0.82em",
        par_spacing="0.95em",
        hyphenate=False,
        cjk_punctuation_compress=True,
        contents_title="目次",
        ocr_instruction="Transcribe Japanese kanji/kana and LaTeX math faithfully without dropping okurigana.",
    ),
    "fr": LanguageProfile(
        code="fr",
        typst_lang="fr",
        font_stack=("New Computer Modern",),
        math_font="New Computer Modern Math",
        first_line_indent="1.2em",
        leading="0.66em",
        par_spacing="0.85em",
        hyphenate=True,
        cjk_punctuation_compress=False,
        contents_title="Table des matières",
        ocr_instruction="Transcribe French accents, guillemets, and LaTeX math faithfully.",
    ),
    "zh": LanguageProfile(
        code="zh",
        typst_lang="zh",
        font_stack=("New Computer Modern", "Songti SC", "STSong"),
        math_font="New Computer Modern Math",
        first_line_indent="2.0em",
        leading="0.85em",
        par_spacing="0.95em",
        hyphenate=False,
        cjk_punctuation_compress=True,
        contents_title="目录",
        ocr_instruction="Transcribe Chinese characters, full-width punctuation, and LaTeX math faithfully.",
    ),
}


DOMAIN_PROFILES: dict[str, DomainProfile] = {
    "math": DomainProfile(
        key="math",
        equation_numbering="(1.1)",
        theorem_heads=(
            "Theorem",
            "Lemma",
            "Corollary",
            "Proposition",
            "Definition",
            "Example",
            "Remark",
            "Axiom",
            "Conjecture",
        ),
        figure_layer_mode="four-layer-svg",
        sanitize_inline_math=True,
        drop_cap_chapters=False,
    ),
    "physics": DomainProfile(
        key="physics",
        equation_numbering="(1.1)",
        theorem_heads=(
            "Postulate",
            "Law",
            "Theorem",
            "Lemma",
            "Definition",
            "Example",
            "Exercise",
        ),
        figure_layer_mode="four-layer-svg",
        sanitize_inline_math=True,
        drop_cap_chapters=False,
    ),
    "economics": DomainProfile(
        key="economics",
        equation_numbering="(1.1)",
        theorem_heads=(
            "Proposition",
            "Theorem",
            "Lemma",
            "Corollary",
            "Assumption",
            "Definition",
            "Example",
        ),
        figure_layer_mode="four-layer-svg",
        sanitize_inline_math=True,
        drop_cap_chapters=False,
    ),
    "philosophy": DomainProfile(
        key="philosophy",
        equation_numbering="(1)",
        theorem_heads=(
            "Thesis",
            "Proposition",
            "Argument",
            "Objection",
            "Reply",
            "Definition",
        ),
        figure_layer_mode="minimal",
        sanitize_inline_math=True,
        drop_cap_chapters=False,
    ),
    "history": DomainProfile(
        key="history",
        equation_numbering="none",
        theorem_heads=(),
        figure_layer_mode="archival-plate",
        sanitize_inline_math=False,
        drop_cap_chapters=True,
    ),
    "novel": DomainProfile(
        key="novel",
        equation_numbering="none",
        theorem_heads=(),
        figure_layer_mode="minimal",
        sanitize_inline_math=False,
        drop_cap_chapters=True,
    ),
}


@dataclass(frozen=True)
class CompositionConfig:
    publisher: PublisherPreset
    language: LanguageProfile
    domain: DomainProfile

    def typst_font_tuple(self) -> str:
        if len(self.language.font_stack) == 1:
            return f'"{self.language.font_stack[0]}"'
        quoted = ", ".join(f'"{f}"' for f in self.language.font_stack)
        return f"({quoted})"

    def typst_heading_rules(self) -> str:
        font_expr = self.typst_font_tuple()
        style = self.publisher.heading_style
        if style == "centered-smallcaps":
            h1 = f"""#show heading.where(level: 1): it => {{
  v(2.8em)
  align(center)[
    #text(15pt, weight: "regular", tracking: 0.08em, font: {font_expr})[#smallcaps(it.body)]
  ]
  v(1.6em)
}}"""
        elif style == "ams-sc":
            h1 = f"""#show heading.where(level: 1): it => {{
  v(2.4em)
  align(center)[
    #text(14pt, weight: "bold", tracking: 0.06em, font: {font_expr})[#smallcaps(it.body)]
  ]
  v(0.5em)
  align(center)[#line(length: 40%, stroke: 0.5pt + black)]
  v(1.4em)
}}"""
        elif style == "architectural":
            h1 = f"""#show heading.where(level: 1): it => {{
  v(2.2em)
  line(length: 100%, stroke: 1.2pt + black)
  v(0.5em)
  align(left)[
    #text(17pt, weight: "bold", font: {font_expr})[#it.body]
  ]
  v(1.4em)
}}"""
        else:
            h1 = f"""#show heading.where(level: 1): it => {{
  v(2.4em)
  align(left)[
    #text(16pt, weight: "bold", font: {font_expr})[#it.body]
  ]
  v(0.6em)
  line(length: 100%, stroke: 0.6pt + black)
  v(1.4em)
}}"""
        return f"""{h1}

#show heading.where(level: 2): it => {{
  v(1.4em)
  text(12pt, weight: "bold", font: {font_expr})[#it.body]
  v(0.55em)
}}

#show heading.where(level: 3): it => {{
  v(1.1em)
  text(10.5pt, weight: "bold", style: "italic", font: {font_expr})[#it.body]
  v(0.35em)
}}

#show heading.where(level: 4): it => {{
  v(0.95em)
  text(10pt, weight: "bold", font: {font_expr})[#smallcaps(it.body)]
  v(0.4em)
}}"""


def resolve_composition(
    publisher: str = "cambridge",
    lang: str = "en",
    domain: str = "math",
) -> CompositionConfig:
    pub_key = publisher.strip().lower()
    lang_key = lang.strip().lower().split("-")[0]
    dom_key = domain.strip().lower()
    return CompositionConfig(
        publisher=PUBLISHER_PRESETS.get(pub_key, PUBLISHER_PRESETS["cambridge"]),
        language=LANGUAGE_PROFILES.get(lang_key, LANGUAGE_PROFILES["en"]),
        domain=DOMAIN_PROFILES.get(dom_key, DOMAIN_PROFILES["math"]),
    )
