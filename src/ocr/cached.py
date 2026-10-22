from collections.abc import Iterator, Sequence

from .pages import PageImage, Transcript
from .transcripts import TranscriptStore


class CachedTranscriber:
    def __init__(self, source: TranscriptStore, provenance: str) -> None:
        self.source = source
        self.provenance = provenance

    def transcribe(self, pages: Sequence[PageImage]) -> Iterator[Transcript]:
        for page in pages:
            if (text := self.source.text(page.number)) is not None:
                yield Transcript(page.number, text)
