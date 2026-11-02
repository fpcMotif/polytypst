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
class NumberingWords:
    item_kinds: str
    reference_kinds: str
    chapter_references: str
    chapter_word: str
    theorems: tuple[tuple[str, str], ...] = ()


ENGLISH_WORDS = NumberingWords(
    item_kinds=r"Proposition|Corollaire|D[ée]finition|Remarques?|Lemme|Th[ée]or[èe]me|Exemples?|Scholie",
    reference_kinds=r"Theorems?|Lemmas?|Corollar(?:y|ies)|Propositions?|Definitions?|Remarks?|Examples?|Exercises?|Sections?|Sects?\.",
    chapter_references=r"Chapters?|Chap\.",
    chapter_word="Chapter",
)
FRENCH_WORDS = ENGLISH_WORDS
CHINESE_WORDS = ENGLISH_WORDS
JAPANESE_WORDS = ENGLISH_WORDS


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
    numbering: NumberingWords


@dataclass(frozen=True)
class DomainProfile:
    key: str
    equation_numbering: str
    theorem_heads: tuple[str, ...]
    proof_end_mark: bool
    layout_theorem_heads: tuple[str, ...] = ()


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
        width_pt=454,
        height_pt=686,
        margin_inside_pt=56,
        margin_outside_pt=60,
        margin_top_pt=58,
        margin_bottom_pt=64,
        body_size_pt=10.0,
        heading_style="numbered-block",
        header_rule_pt=0.45,
        pandoc_geometry="paperwidth=6.3in,paperheight=9.53in,margin=0.8in",
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
    "bourbaki_1970": PublisherPreset(
        key="bourbaki_1970",
        imprint_name="Springer-Verlag",
        default_series="Elements of Mathematics",
        cities_line="Berlin · Heidelberg · New York · London · Paris · Tokyo",
        width_pt=388,
        height_pt=609,
        margin_inside_pt=32,
        margin_outside_pt=32,
        margin_top_pt=74,
        margin_bottom_pt=66,
        body_size_pt=9.6,
        heading_style="bourbaki",
        header_rule_pt=0.0,
        pandoc_geometry="paperwidth=5.39in,paperheight=8.46in,margin=0.45in",
    ),
    "springer_1971": PublisherPreset(
        key="springer_1971",
        imprint_name="Springer-Verlag",
        default_series="Die Grundlehren der mathematischen Wissenschaften",
        cities_line="Berlin · Heidelberg · New York",
        width_pt=344,
        height_pt=572,
        margin_inside_pt=17,
        margin_outside_pt=17,
        margin_top_pt=56,
        margin_bottom_pt=14,
        body_size_pt=9.6,
        heading_style="numbered-block",
        header_rule_pt=0.0,
        pandoc_geometry="paperwidth=4.78in,paperheight=7.95in,margin=0.3in,top=0.78in",
    ),
    "princeton": PublisherPreset(
        key="princeton",
        imprint_name="Princeton University Press",
        default_series="Princeton Mathematical Series",
        cities_line="Princeton, New Jersey",
        width_pt=441,
        height_pt=666,
        margin_inside_pt=54,
        margin_outside_pt=54,
        margin_top_pt=56,
        margin_bottom_pt=58,
        body_size_pt=10.0,
        heading_style="ams-sc",
        header_rule_pt=0.35,
        pandoc_geometry="paperwidth=6.13in,paperheight=9.25in,margin=0.75in",
    ),
}


LANGUAGE_PROFILES: dict[str, LanguageProfile] = {
    "en": LanguageProfile(
        code="en",
        typst_lang="en",
        font_stack=("New Computer Modern",),
        math_font="New Computer Modern Math",
        first_line_indent="1.5em",
        leading="0.78em",
        par_spacing="1.05em",
        hyphenate=True,
        cjk_punctuation_compress=False,
        contents_title="Contents",
        ocr_instruction="Transcribe English text and LaTeX math faithfully.",
        numbering=ENGLISH_WORDS,
    ),
    "en_baskerville": LanguageProfile(
        code="en_baskerville",
        typst_lang="en",
        font_stack=("Baskervville", "STIX Two Text"),
        math_font="STIX Two Math",
        first_line_indent="1.1em",
        leading="4.3pt",
        par_spacing="4.3pt",
        hyphenate=True,
        cjk_punctuation_compress=False,
        contents_title="Contents",
        ocr_instruction="Transcribe English text and LaTeX math faithfully.",
        numbering=ENGLISH_WORDS,
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
        numbering=JAPANESE_WORDS,
    ),
    "fr": LanguageProfile(
        code="fr",
        typst_lang="fr",
        font_stack=("New Computer Modern",),
        math_font="New Computer Modern Math",
        first_line_indent="1.2em",
        leading="0.76em",
        par_spacing="1.0em",
        hyphenate=True,
        cjk_punctuation_compress=False,
        contents_title="Table des matières",
        ocr_instruction="Transcribe French accents, guillemets, and LaTeX math faithfully.",
        numbering=FRENCH_WORDS,
    ),
    "fr_times": LanguageProfile(
        code="fr_times",
        typst_lang="fr",
        font_stack=("STIX Two Text",),
        math_font="STIX Two Math",
        first_line_indent="1.2em",
        leading="0.7em",
        par_spacing="0.7em",
        hyphenate=True,
        cjk_punctuation_compress=False,
        contents_title="Table des matières",
        ocr_instruction="Transcribe French accents, guillemets, and LaTeX math faithfully.",
        numbering=FRENCH_WORDS,
    ),
    "zh": LanguageProfile(
        code="zh",
        typst_lang="zh",
        font_stack=("Songti SC", "STSong", "New Computer Modern"),
        math_font="New Computer Modern Math",
        first_line_indent="2.0em",
        leading="0.85em",
        par_spacing="0.95em",
        hyphenate=False,
        cjk_punctuation_compress=True,
        contents_title="目录",
        ocr_instruction="Transcribe Chinese characters, full-width punctuation, and LaTeX math faithfully.",
        numbering=CHINESE_WORDS,
    ),
}


DOMAIN_PROFILES: dict[str, DomainProfile] = {
    "math": DomainProfile(
        key="math",
        equation_numbering="(1.1)",
        proof_end_mark=True,
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
        layout_theorem_heads=("Assumption", "Claim", "Notation"),
    ),
    "physics": DomainProfile(
        key="physics",
        equation_numbering="(1.1)",
        proof_end_mark=True,
        theorem_heads=(
            "Postulate",
            "Law",
            "Theorem",
            "Lemma",
            "Definition",
            "Example",
            "Exercise",
        ),
        layout_theorem_heads=("Assumption", "Claim", "Notation"),
    ),
    "economics": DomainProfile(
        key="economics",
        equation_numbering="(1.1)",
        proof_end_mark=False,
        theorem_heads=(
            "Proposition",
            "Theorem",
            "Lemma",
            "Corollary",
            "Assumption",
            "Definition",
            "Example",
        ),
    ),
    "philosophy": DomainProfile(
        key="philosophy",
        equation_numbering="(1)",
        proof_end_mark=False,
        theorem_heads=(
            "Thesis",
            "Proposition",
            "Argument",
            "Objection",
            "Reply",
            "Definition",
        ),
    ),
    "history": DomainProfile(
        key="history",
        equation_numbering="none",
        proof_end_mark=False,
        theorem_heads=(),
    ),
    "novel": DomainProfile(
        key="novel",
        equation_numbering="none",
        proof_end_mark=False,
        theorem_heads=(),
    ),
}


@dataclass(frozen=True)
class CompositionConfig:
    publisher: PublisherPreset
    language: LanguageProfile
    domain: DomainProfile
    theorem_layout: bool = False

    @property
    def theorem_heads(self) -> tuple[str, ...]:
        return self.domain.theorem_heads + (self.domain.layout_theorem_heads if self.theorem_layout else ())

    def typst_font_tuple(self) -> str:
        if len(self.language.font_stack) == 1:
            return f'"{self.language.font_stack[0]}"'
        quoted = ", ".join(f'"{f}"' for f in self.language.font_stack)
        return f"({quoted})"

    def theorem_words(self) -> tuple[tuple[str, str], ...]:
        spelled = dict(self.language.numbering.theorems)
        return tuple((kind, spelled.get(kind, kind)) for kind in self.theorem_heads)

    def typst_heading_rules(self) -> str:
        tests = [
            f'(s.contains("{word.lower()}") and not s.contains("{word.lower()} of"))'
            if kind == "Definition"
            else f's.contains("{word.lower()}")'
            for kind, word in self.theorem_words()
        ]
        is_thm = "\n".join(("    " if i == 0 else "    or ") + test for i, test in enumerate(tests)) or "    false"
        font_expr = self.typst_font_tuple()
        style = self.publisher.heading_style
        use_sc = self.language.code != "zh"
        sc_body = "#smallcaps(it.body)" if use_sc else "#it.body"
        chapter_number = (
            f""" else if it.numbering != none {{
      align(center, text(11pt, weight: "regular", tracking: 0.14em, font: {font_expr})[CHAPTER #counter(heading).display()])
      v(0.4em)
    }}"""
            if self.theorem_layout
            else ""
        )
        if style == "centered-smallcaps":
            h1 = f"""#show heading.where(level: 1): it => {{
  v(2.8em)
  align(center)[
    #text(15pt, weight: "regular", tracking: 0.08em, font: {font_expr})[{sc_body}]
  ]
  v(1.6em)
}}"""
        elif style == "ams-sc":
            h1 = f"""#show heading.where(level: 1): it => {{
  v(2.4em)
  context {{
    let label = chapter-label.get()
    if label != none {{
      align(center, text(11pt, tracking: 0.12em, font: {font_expr})[#smallcaps(label)])
      v(0.9em)
    }}{chapter_number}
  }}
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
  context {{
    let label = chapter-label.get()
    if label != none {{
      align(left, text(11pt, weight: "bold", tracking: 0.08em, fill: luma(70), font: {font_expr})[#smallcaps(label)])
      v(0.4em)
    }}
  }}
  align(left)[
    #text(17pt, weight: "bold", font: {font_expr})[#it.body]
  ]
  v(1.4em)
}}"""
        elif style == "numbered-block":
            h1 = f"""#show heading.where(level: 1): it => {{
  v(2.6em)
  context {{
    let label = chapter-label.get()
    if label != none {{
      align(left, text(11pt, weight: "bold", tracking: 0.08em, fill: luma(70), font: {font_expr})[#smallcaps(label)])
      v(0.55em)
    }}
  }}
  align(left)[
    #text(18pt, weight: "bold", font: {font_expr})[#it.body]
  ]
  v(0.65em)
  line(length: 100%, stroke: 0.75pt + luma(35))
  v(1.8em)
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
        h4_body = "#smallcaps(it.body)" if use_sc else "#it.body"
        if not self.theorem_layout:
            italic_h3 = 'style: "italic", ' if self.language.code != "zh" else ""
            return f"""{h1}

#show heading.where(level: 2): it => block(above: 1.75em, below: 0.75em, sticky: true)[
  #text(12.5pt, weight: "bold", font: {font_expr})[#if it.numbering != none [#counter(heading).display(it.numbering) ]#it.body]
]

#show heading.where(level: 3): it => block(above: 1.3em, below: 0.5em, sticky: true)[
  #text(10.5pt, weight: "bold", {italic_h3}font: {font_expr})[#if it.numbering != none [#counter(heading).display(it.numbering) ]#it.body]
]

#show heading.where(level: 4): it => block(above: 1.1em, below: 0.45em, sticky: true)[
  #text(10pt, weight: "bold", font: {font_expr})[{h4_body}]
]"""
        return f"""#show heading: set block(sticky: true)
#show heading: set text(hyphenate: false)

{h1}

#let is-thm-heading(it) = {{
  let s = lower(repr(it.body))
  (
{is_thm}
  )
}}

#show heading.where(level: 2): it => {{
  if is-thm-heading(it) {{
    block(above: 1.35em, below: 0.55em, sticky: true)[
      #text(10.5pt, weight: "bold", style: "normal", font: {font_expr})[#if it.numbering != none [#counter(heading).display(it.numbering) ]#it.body]
    ]
  }} else {{
    block(above: 1.9em, below: 0.9em, sticky: true)[
      #text(12pt, weight: "bold", font: {font_expr})[#if it.numbering != none [#counter(heading).display(it.numbering) ]{sc_body}]
    ]
  }}
}}

#show heading.where(level: 3): it => {{
  if is-thm-heading(it) {{
    block(above: 1.35em, below: 0.55em, sticky: true)[
      #text(10.5pt, weight: "bold", style: "normal", font: {font_expr})[#if it.numbering != none [#counter(heading).display(it.numbering) ]#it.body]
    ]
  }} else {{
    block(above: 1.6em, below: 0.7em, sticky: true)[
      #text(11pt, weight: "bold", font: {font_expr})[#if it.numbering != none [#counter(heading).display(it.numbering) ]#it.body]
    ]
  }}
}}

#show heading.where(level: 4): it => block(above: 1.1em, below: 0.45em, sticky: true)[
  #text(10pt, weight: "bold", font: {font_expr})[{h4_body}]
]"""


def resolve_composition(
    publisher: str = "cambridge",
    lang: str = "en",
    *,
    domain: str,
    theorem_layout: bool = False,
) -> CompositionConfig:
    pub_key = publisher.strip().lower()
    lang_key = lang.strip().lower().split("-")[0]
    return CompositionConfig(
        publisher=PUBLISHER_PRESETS.get(pub_key, PUBLISHER_PRESETS["cambridge"]),
        language=LANGUAGE_PROFILES.get(lang_key, LANGUAGE_PROFILES["en"]),
        domain=domain_profile(domain),
        theorem_layout=theorem_layout,
    )


def domain_profile(domain: str) -> DomainProfile:
    key = domain.strip().lower()
    if key not in DOMAIN_PROFILES:
        raise ValueError(f"unknown domain {domain!r}; known domains: {', '.join(DOMAIN_PROFILES)}")
    return DOMAIN_PROFILES[key]
