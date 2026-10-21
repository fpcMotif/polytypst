"""The OCR engines behind `OCREngine.transcribe_pages`, and the factory that picks one by mode."""

import shutil
from collections.abc import Sequence
from pathlib import Path

from .base import (
    OCREngine,
    OCRPage,
    normalize_ocr_markdown,
    page_number,
    pending_pages,
    read_transcripts,
    text_lines,
    transcript_path,
)
from .ocr_models import DEFAULT_OCR_MODEL

OCR_MODES = ("colab", "jina-cloud", "apple-vision", "local", "cached")


class CachedMarkdownEngine(OCREngine):
    """Serve `p_NNN.md` transcripts from a directory, for offline runs and tests."""

    def __init__(self, source_dir: Path) -> None:
        self.source_dir = Path(source_dir)

    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        cached = transcript_path(self.source_dir, page_number)
        text = cached.read_text(encoding="utf-8") if cached.exists() else ""
        lines = text_lines(text)
        return OCRPage(page_number, 0, 0, lines, raw_text=text)

    def recognize_document(self, image_paths: list[Path]) -> list[OCRPage]:
        return [self.recognize_page(p, page_number(p)) for p in image_paths]


class LocalGPUWorkerEngine(OCREngine):
    """Run the GPU worker with one registered OCR model on this machine's GPU, MPS, or CPU."""

    def __init__(
        self,
        prompt: str | None = None,
        num_shards: int = 1,
        model: str = DEFAULT_OCR_MODEL,
    ) -> None:
        self.prompt = prompt
        self.num_shards = num_shards
        self.model = model

    def transcribe_pages(
        self, pages: Sequence[Path], out_dir: Path
    ) -> list[tuple[int, str]]:
        from .gpu_worker import UNIVERSAL_TEX_PROMPT, run_worker

        pending = pending_pages(pages, out_dir)
        if pending:
            run_worker(
                pending[0].parent,
                out_dir,
                [page_number(p) for p in pending],
                prompt=self.prompt or UNIVERSAL_TEX_PROMPT,
                num_shards=self.num_shards,
                model_key=self.model,
            )
            for p in pending:
                t = transcript_path(out_dir, page_number(p))
                if t.exists():
                    _ = t.write_text(
                        normalize_ocr_markdown(t.read_text(encoding="utf-8")),
                        encoding="utf-8",
                    )
        return read_transcripts(out_dir, pages)

    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        return self.recognize_document([image_path])[0]

    def recognize_document(self, image_paths: list[Path]) -> list[OCRPage]:
        scratch = image_paths[0].parent / "_local_ocr"
        try:
            found = dict(self.transcribe_pages(image_paths, scratch))
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        return [
            OCRPage(page_number(p), 0, 0, [], raw_text=found.get(page_number(p), ""))
            for p in image_paths
        ]


def ocr_engine(
    mode: str,
    *,
    prompt: str | None = None,
    model: str = DEFAULT_OCR_MODEL,
    gpu_type: str = "G4",
    num_colab_workers: int = 2,
    shards_per_gpu: int = 3,
    batch_size: int = 70,
    session_prefix: str = "ocr",
    cache_dir: Path | None = None,
    languages: list[str] | None = None,
) -> OCREngine:
    """The transcription engine for `mode`; `colab` falls back to `local` without Colab."""
    if mode == "colab":
        from .colab_cluster import ColabOCRCluster, ColabOCREngine

        cluster = ColabOCRCluster(
            gpu_type=gpu_type,
            num_workers=num_colab_workers,
            shards_per_gpu=shards_per_gpu,
            session_prefix=session_prefix,
            prompt=prompt,
            model=model,
        )
        if cluster.is_colab_available():
            return ColabOCREngine(cluster, batch_size=batch_size)
        print(f"Colab CLI unavailable; transcribing with {model} on this machine.")
        return LocalGPUWorkerEngine(prompt=prompt, model=model)
    if mode == "jina-cloud":
        from .jina import DEFAULT_JINA_PROMPT, JinaCloudOCREngine

        return JinaCloudOCREngine(prompt=prompt or DEFAULT_JINA_PROMPT)
    if mode == "apple-vision":
        from .apple_vision import AppleVisionOCREngine

        return AppleVisionOCREngine(languages=languages)
    if mode == "local":
        return LocalGPUWorkerEngine(prompt=prompt, model=model)
    if mode == "cached":
        if cache_dir is None:
            raise ValueError("The cached OCR mode needs cache_dir")
        return CachedMarkdownEngine(cache_dir)
    raise ValueError(f"Unknown OCR mode {mode!r}; expected one of {OCR_MODES}")
