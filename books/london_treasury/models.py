"""The parsed reader: PDF lines, extracted links, article entries and chapters."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PdfLine:
    text: str
    size: float
    y0: float
    y1: float


@dataclass(frozen=True)
class ExtractedLink:
    index: int
    src_page: int
    label: str
    en_title: str
    uri: str
    method: str
    clean_chars: int
    clean_text: str


@dataclass(frozen=True)
class ArticleEntry:
    number: int
    src_page: int
    zh_title: str
    en_title: str
    author_line: str
    date_priority_line: str
    background_line: str
    access_line: str
    uri: str
    summary_paragraphs: list[str]
    angle_paragraphs: list[str]
    questions: list[str]
    boundary_paragraphs: list[str]
    original_text: str


@dataclass(frozen=True)
class ChapterContent:
    number: int
    title: str
    intro_paragraphs: list[str]
    entries: list[ArticleEntry] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedReaderBook:
    kicker: str
    title: str
    subtitle: str
    tags: list[str]
    edition_line: str
    intro_sections: list[tuple[str, list[str]]]
    chapters: list[ChapterContent]
    back_sections: list[tuple[str, list[str], list[ExtractedLink]]]
    all_links: list[ExtractedLink]
