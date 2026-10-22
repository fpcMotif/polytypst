import tempfile
from collections.abc import Iterator, Sequence
from pathlib import Path

from . import gpu_worker
from .pages import PageImage, Transcript


def worker_transcripts(
    pages: Sequence[PageImage], out_dir: Path
) -> Iterator[Transcript]:
    for page in pages:
        path = gpu_worker.worker_transcript_path(out_dir, page.number)
        if path.exists():
            yield Transcript(page.number, path.read_text(encoding="utf-8"))


class LocalGpuTranscriber:
    def __init__(self, model: str, prompt: str, shards: int, provenance: str) -> None:
        self.model = model
        self.prompt = prompt
        self.shards = shards
        self.provenance = provenance

    def transcribe(self, pages: Sequence[PageImage]) -> Iterator[Transcript]:
        with tempfile.TemporaryDirectory(prefix="local_ocr_") as tmp:
            out_dir = Path(tmp)
            try:
                gpu_worker.run_worker(
                    [(page.number, str(page.path)) for page in pages],
                    out_dir,
                    self.prompt,
                    self.shards,
                    self.model,
                )
            finally:
                yield from worker_transcripts(pages, out_dir)
