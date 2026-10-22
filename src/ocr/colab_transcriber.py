import tempfile
from collections.abc import Iterator, Sequence
from pathlib import Path

from .colab_cluster import ColabOCRCluster
from .local_gpu import worker_transcripts
from .pages import PageImage, Transcript


class ColabTranscriber:
    def __init__(
        self, cluster: ColabOCRCluster, batch_size: int, provenance: str
    ) -> None:
        self.cluster = cluster
        self.batch_size = batch_size
        self.provenance = provenance

    def transcribe(self, pages: Sequence[PageImage]) -> Iterator[Transcript]:
        batches = [
            pages[i : i + self.batch_size]
            for i in range(0, len(pages), self.batch_size)
        ]
        for idx, batch in enumerate(batches, start=1):
            print(f"Colab batch {idx}/{len(batches)}: {len(batch)} pages")
            with tempfile.TemporaryDirectory(prefix="colab_batch_") as tmp:
                out_dir = Path(tmp)
                _ = self.cluster.run_cluster(batch, out_dir)
                yield from worker_transcripts(batch, out_dir)
