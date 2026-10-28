"""Alexander Grothendieck: Fondements de la géométrie algébrique."""

from polytypst.compiler.monograph import ChapterSpec, MonographSpec

CHAPTERS = [
    ChapterSpec(0, "Commentaires", 3, 13, label="Complément"),
    ChapterSpec(149, "Théorème de dualité pour les faisceaux algébriques cohérents", 14, 39, label="Exposé 149"),
    ChapterSpec(182, "Géométrie formelle et géométrie algébrique", 40, 67, label="Exposé 182"),
    ChapterSpec(190, "I. Généralités. Descente par morphismes fidèlement plats", 68, 96, label="Exposé 190"),
    ChapterSpec(195, "II. Le théorème d'existence en théorie formelle des modules", 97, 118, label="Exposé 195"),
    ChapterSpec(212, "III. Préschémas quotients", 119, 138, label="Exposé 212"),
    ChapterSpec(221, "IV. Les schémas de Hilbert", 139, 166, label="Exposé 221"),
    ChapterSpec(232, "V. Les schémas de Picard : théorèmes d'existence", 167, 185, label="Exposé 232"),
    ChapterSpec(236, "VI. Les schémas de Picard : propriétés générales", 186, 208, label="Exposé 236"),
]
LATEX_PREAMBLE = (
    r"\usepackage{fancyhdr}" "\n"
    r"\pagestyle{fancy}" "\n"
    r"\fancyhf{}" "\n"
    r"\fancyhead[LE]{\small\thepage\quad\textsc{Alexander Grothendieck}}" "\n"
    r"\fancyhead[RO]{\small\textsc{Fondements de la géométrie algébrique}\quad\thepage}" "\n"
    r"\renewcommand{\headrulewidth}{0pt}"
)
DROP_LINE_REGEXES = (
    r"^(?:C|\d{3})-\d{1,2}$",
    r"^(?:#+\s*)?Séminaire BOURBAKI.*$",
    r"^\d{1,2}e année.*$",
    r"^\(?(?:Janvier|Février|Mars|Avril|Mai|Juin|Juillet|Août|Septembre|Octobre|Novembre|Décembre)\s+\d{4}\)?$",
    r"^(?:#+\s*)?par Alexander GROTHENDIECK$",
    r"^(?:#+\s*)?FONDEMENTS DE LA GÉOMÉTRIE ALGÉBRIQUE\.?$",
    r"^(?:#+\s*)?TECHNIQUE DE DESCENTE ET THÉORÈMES D'EXISTENCE.*$",
    r"^(?:#+\s*)?COMMENTAIRES$",
)


FGA_SPEC = MonographSpec(
    slug="fga",
    title="Fondements de la géométrie algébrique",
    author="Alexander Grothendieck",
    publisher="Secrétariat mathématique",
    publisher_key="springer",
    lang="fr",
    domain="math",
    source_pdf="Fondements de la geometrie algebrique (FGA) (Grothendieck A.).pdf",
    pdf_name_markers=("fondements de la geometrie algebrique", "fga"),
    pdf_page_count=208,
    latex_preamble=LATEX_PREAMBLE,
    drop_line_regexes=DROP_LINE_REGEXES,
    header_zone_lines=6,
    cross_references=True,
    commutative_diagrams=True,
    chapters=CHAPTERS,
)
