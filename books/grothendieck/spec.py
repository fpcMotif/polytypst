"""A. Grothendieck and J. A. Dieudonné: Éléments de Géométrie Algébrique I (Springer-Verlag, 1971)."""

from dataclasses import replace
from pathlib import Path

from polytypst.compiler.monograph import ChapterSpec, MonographSpec

RUNNING_HEADERS = (
    r"Préliminaires|Le langage des schémas|Sommaire|"
    r"Table des matières|Avant-propos|Introduction|"
    r"Foncteurs représentables|Compléments de topologie|Compléments sur les faisceaux|"
    r"Espaces annelés|Faisceaux quasi-cohérents et faisceaux cohérents|"
    r"Compléments d'algèbre commutative|Compléments d'algèbre topologique|"
    r"Schémas affines|Schémas et morphismes de schémas|"
    r"Produit et somme de schémas|Changement de base|Sous-schémas et morphismes d'immersion|"
    r"Schémas réduits|Morphismes séparés|Critères valuatifs|Conditions de finitude relatives|"
    r"Ensembles constructibles dans les schémas|Applications rationnelles|"
    r"Foncteurs représentables élémentaires dans la théorie des schémas|"
    r"Schémas formels|Ultraschémas et espaces algébriques de Serre|"
    r"Spectres maximaux et ultraschémas|Espaces algébriques de Serre|"
    r"Bibliographie|Index des notations|Index terminologique"
)

RUNNING_HEADER_REGEXES = (
    rf"^(?:#+\s*)?(?:[0-9A-Z]{{1,2}}\.\s+)?(?:{RUNNING_HEADERS})(?:\s+\d{{1,3}})?$",
    rf"^\d{{1,3}}\s+(?:[0-9A-Z]{{1,2}}\.\s+)?(?:{RUNNING_HEADERS})$",
)

GROTHENDIECK_OCR_PROMPT = (
    "Transcribe this page from Grothendieck-Dieudonné's Éléments de Géométrie Algébrique I into "
    "clean, high-fidelity TeX-compatible Markdown.\n"
    "Rules:\n"
    "1. Format all mathematical expressions in exact LaTeX syntax: inline $...$ and display $$...$$.\n"
    "2. Transcribe category-theory, sheaf, and scheme notations faithfully: "
    "\\operatorname{Hom}, \\operatorname{Spec}, \\operatorname{Spf}, \\operatorname{Proj}, "
    "\\mathcal{O}_X, \\mathcal{F}, \\mathcal{G}, \\otimes, \\oplus, exact sequences, and commutative diagrams.\n"
    "3. Format chapter, paragraph (§), and section headings with Markdown (#, ##, ###).\n"
    "4. Bold structural environments: (1.1.1), **Définition**, **Proposition**, **Théorème**, **Corollaire**, "
    "**Lemme**, **Remarque**, and italicize *Démonstration.*.\n"
    "5. Label display equations with exact numbering if present.\n"
    "6. Do not omit any prose, definitions, proofs, or footnotes."
)

GROTHENDIECK_SPEC = MonographSpec(
    slug="grothendieck",
    title="Éléments de Géométrie Algébrique I",
    author="A. Grothendieck and J. A. Dieudonné",
    publisher="Springer-Verlag",
    publisher_key="springer",
    series="Die Grundlehren der mathematischen Wissenschaften",
    year=1971,
    lang="fr_times",
    domain="math",
    source_pdf="ega1.pdf",
    pdf_page_count=474,
    preface_page=9,
    running_header_regexes=RUNNING_HEADER_REGEXES,
    figure_pages=frozenset({216}),
    footnote_style="parenthesized",
    footnote_numbering="(1)",
    cross_references=True,
    citation_abbreviations={"M": "2", "G": "5", "T": "6"},
    commutative_diagrams=True,
    ocr_prompt=GROTHENDIECK_OCR_PROMPT,
    chapters=[
        ChapterSpec(0, "Introduction", 12, 26),
        ChapterSpec(1, "Préliminaires", 27, 200, label="Chapitre 0"),
        ChapterSpec(2, "Le langage des schémas", 201, 456, label="Chapitre I"),
        ChapterSpec(3, "Appendice: Ultraschémas et espaces algébriques de Serre", 457, 461),
        ChapterSpec(4, "Bibliographie", 462, 462),
        ChapterSpec(5, "Index des notations", 463, 467),
        ChapterSpec(6, "Index terminologique", 468, 474),
    ],
)

VINTAGE_PREAMBLE = (Path(__file__).parent / "vintage_preamble.typ").read_text(encoding="utf-8")

GROTHENDIECK_1971_SPEC = replace(
    GROTHENDIECK_SPEC,
    slug="grothendieck_1971_vintage",
    publisher_key="springer_1971",
    typst_preamble=VINTAGE_PREAMBLE,
    paginate_like_source=True,
)
