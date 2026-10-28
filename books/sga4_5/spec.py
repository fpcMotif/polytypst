"""P. Deligne, avec la collaboration de J. F. Boutot, A. Grothendieck, L. Illusie et J. L. Verdier: Cohomologie étale (SGA 4½)."""

from polytypst.compiler.monograph import ChapterSpec, MonographSpec

RUNNING_HEADERS = (
    r"Arcata|Rapport|Fonction\s+L.*|Cycle|Dualité|Dualite|Sommes\s+trig.*|Th\.\s*finitude.*|"
    r"Catégories\s+dérivées.*|Erratum.*|Table\s+des\s+matières.*|Un\s+fil\s+d'Ariane.*|"
    r"Cohomologie\s+étale.*"
)

RUNNING_HEADER_REGEXES = (
    rf"^(?![#])(?:[0-9A-Z]{{1,3}}\s*[-–]\s*\d{{1,3}}\s*)?(?:{RUNNING_HEADERS})(?:.*)?$",
    rf"^(?![#])(?:{RUNNING_HEADERS})(?:\s*[-–]\s*.*\s*[-–]?)?$",
    r"^[-–]\s*\d{1,3}(?:\s*\([a-z]+\))?\s*[-–](?:\s+.*)?$",
    r"^(?:[IVX]{1,4}|[A-Z])\s*[-–]\s*\d{1,3}$",
    r"^(?:A\.\s*\d{1,2}|C\.D\.)(?:\s*[-–]\s*\d{1,3}\s*[-–])?$",
)

CHAPTERS = [
    ChapterSpec(0, "Introduction", 3, 5, label="Introduction"),
    ChapterSpec(1, "Un fil d'Ariane pour SGA 4, SGA 4 1/2 et SGA 5", 6, 8, label="Fil d'Ariane"),
    ChapterSpec(2, "Cohomologie étale : les points de départ", 9, 80, label="Arcata"),
    ChapterSpec(3, "Rapport sur la formule des traces", 81, 114, label="Rapport"),
    ChapterSpec(4, "Fonctions L modulo l^n et modulo p", 115, 133, label="Fonctions L"),
    ChapterSpec(5, "La classe de cohomologie associée à un cycle", 134, 158, label="Cycle"),
    ChapterSpec(6, "Dualité", 159, 172, label="Dualité"),
    ChapterSpec(7, "Applications de la formule des traces aux sommes trigonométriques", 173, 237, label="Sommes trig."),
    ChapterSpec(8, "Théorèmes de finitude en cohomologie l-adique", 238, 266, label="Th. finitude"),
    ChapterSpec(9, "Catégories dérivées, état 0", 267, 316, label="Catégories dérivées"),
    ChapterSpec(10, "Erratum pour SGA 4", 317, 317, label="Erratum"),
]

SGA4_5_SPEC = MonographSpec(
    slug="sga4_5",
    title="Cohomologie étale (SGA 4½)",
    author="P. Deligne, avec la collaboration de J. F. Boutot, A. Grothendieck, L. Illusie et J. L. Verdier",
    publisher="Springer-Verlag",
    publisher_key="springer",
    series="Lecture Notes in Mathematics 569",
    year=1977,
    lang="fr",
    domain="math",
    source_pdf="Cohomologie étale (Deligne, Pierre etc.).pdf",
    pdf_name_markers=("cohomologie étale", "cohomologie etale", "sga 4", "sga4", "deligne"),
    pdf_page_count=317,
    header_zone_lines=3,
    running_header_regexes=RUNNING_HEADER_REGEXES,
    cross_references=True,
    commutative_diagrams=True,
    chapters=CHAPTERS,
)
